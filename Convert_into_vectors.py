from openai import OpenAI
from dotenv import load_dotenv
import numpy as np
import json
import os
import pdb
load_dotenv(override=True)
API_KEY= os.getenv("OPENAI_API_KEY")
# os.getenv("OPENAI_API_KEY")
endpoint = os.getenv("endpoint")
deployment_name = os.getenv("deployment_name")
EMBED_MODEL = "text-embedding-3-small-1"
FILE_NAME = "incidents.json"
client = OpenAI(
    base_url=endpoint,
    api_key=API_KEY
)
# Load your JSON
def load_memory():
    if not os.path.exists(FILE_NAME):
        return []
    with open(FILE_NAME, "r") as f:
        return json.load(f)
#Embedding 
def get_embedding(text):
    if not isinstance(text, str):
        text = str(text)
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return response.data[0].embedding
   
def save_memory(data):
    with open(FILE_NAME, "w") as f:
        json.dump(data, f, indent=2)
# with open("incidents.json") as f:
#     incidents = json.load(f)
# Conver incident into incident
def incident_to_text(inc):
    return f"""
Incident {inc['incident_number']}:
{inc['description']}.
Priority: {inc['priority']}.
Root cause: {inc['RCA']}.
Assigned to: {inc['assigned_to']}.
"""
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
    print("✅ Stored:", text)
    return
inc ={}
inc["user_id"] = "axv523p"
inc["incident_number"] = "INC3456732"
inc["description"] ="SFTC_REP_ID is coming as null. Hence the filter in EM_PHARMA_REP_DAILY_STATUS table is not allowing data to flow."
inc["priority"] = "P2"
inc["caller"] = "Abeed Shaik"
inc["assigned_to"] = "Smruti Samal"
inc["RCA"] = "Created an incident to source and we got to know SFTC_REP_ID column is decommisioned and will not flow in future. Hence removing the filter from the table. "
inc["created_date"] = "2026-01-12T10:15:00"
inc["resolved_date"] ="2026-01-18T10:15:00"

store_memory(inc)
print("Data stored")
