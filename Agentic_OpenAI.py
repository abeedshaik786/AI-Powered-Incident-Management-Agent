from openai import OpenAI
from dotenv import load_dotenv
import numpy as np
import json
import os
import pdb


# CONFIG

load_dotenv(override=True)

API_KEY= os.getenv("OPENAI_API_KEY")
# os.getenv("OPENAI_API_KEY")
endpoint = os.getenv("endpoint")
deployment_name = os.getenv("deployment_name")
EMBED_MODEL = "text-embedding-3-small-1"
FILE_NAME = "incidents.json"

client = OpenAI(
    api_key=API_KEY,
    base_url=endpoint
)


# LOAD / SAVE

def load_memory():
    if not os.path.exists(FILE_NAME):
        return []

    with open(FILE_NAME, "r") as f:
        content = f.read().strip()
        return json.loads(content) if content else []

def save_memory(data):
    with open(FILE_NAME, "w") as f:
        json.dump(data, f, indent=2)


# EMBEDDING

def get_embedding(text):
    if not isinstance(text, str):
        text = str(text)

    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return response.data[0].embedding


# INCIDENT → TEXT

def incident_to_text(inc):
    return f"""
Incident {inc['incident_number']}:
{inc['description']}.
Priority: {inc['priority']}.
Root cause: {inc['RCA']}.
Assigned to: {inc['assigned_to']}.
"""


# STORE MEMORY

def store_memory(inc):
    data = load_memory()

    text = incident_to_text(inc)
    embedding = get_embedding(text)

    data.append({
        "user_id": inc["user_id"],
        "incident_number": inc["incident_number"],
        "text": text,
        "embedding": embedding,
        "metadata": {
            "priority": inc["priority"],
            "caller": inc["caller"],
            "assigned_to": inc["assigned_to"],
            "created_date": inc["created_date"],
            "resolved_date": inc["resolved_date"]
        }
    })

    save_memory(data)
    print("Stored:", inc["incident_number"])


# SIMILARITY

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# RETRIEVE MEMORY

def retrieve_memory(user_id, query, top_k=3):
    data = load_memory()
    query_embedding = get_embedding(query)

    scored = []

    for item in data:
        if item.get("user_id") != user_id:
            continue
        if "embedding" not in item:
            continue

        sim = cosine_similarity(query_embedding, item["embedding"])
        scored.append((float(sim), item["text"]))

    scored.sort(key=lambda x: x[0], reverse=True)

    return scored[:top_k]


# LLM RESPONSE

def agent_mode(message):
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "Respond like a professional incident expert."},
            {"role": "user", "content": message}
        ]
    )

    return response.choices[0].message.content   # return string


# PROMPT

def Prompt_archestration(user_id, query):
    similar = retrieve_memory(user_id, query)

    memories = [text for score, text in similar]
    memory_context = "\n".join(memories)

    prompt = f"""
You are an Incident Management AI Assistant.

If similar issue exists:
- Explain Root Cause
- Suggest Resolution
- Explain WHY

If not:
- Infer RCA
- Suggest fix
- Mention it's new

Context:
{memory_context}

User Issue:
{query}

Output:
Root Cause:
Resolution:
Why this solution:
"""

    return agent_mode(prompt)


# INTENT DETECTION

def detect_intent(query):
    prompt = f"""
    Classify:
    NEW_INCIDENT or QUERY

    Input: {query}
    """

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


# MAIN HANDLER

def handle_user(user_id, query):

    # ensure string
    if isinstance(query, dict):
        query = incident_to_text(query)

    similar = retrieve_memory(user_id, query)

    if similar and similar[0][0] > 0.75:
        print("Similar incident found")
        return Prompt_archestration(user_id, query)

    print(" No match found")

    intent = detect_intent(query)

    if intent == "NEW_INCIDENT":
        inc = {
            "user_id": user_id,
            "incident_number": f"INC{np.random.randint(1000,9999)}",
            "description": query,
            "priority": "P2",
            "caller": user_id,
            "assigned_to": "TBD",
            "RCA": "To be analyzed",
            "created_date": "2026-04-23T10:00:00",
            "resolved_date": None
        }

        store_memory(inc)
        print(" New incident stored")

    return Prompt_archestration(user_id, query)


# RUN

if __name__ == "__main__":
    user = "axv523p"

    answer = handle_user(user, "SFTC_REP_ID is coming as null")
    print("\n Jarvis:\n", answer)
