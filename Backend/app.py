from fastapi import FastAPI
from pydantic import BaseModel
import requests

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

N8N_WEBHOOK = "https://n8n-production-308b.up.railway.app/webhook/transcript"


class Transcript(BaseModel):
    conversation_id: str
    text: str


@app.get("/")
def home():
    return {"message": "Conversation Analytics API running"}


@app.post("/transcript")
async def receive_transcript(data: Transcript):

    payload = {
        "conversation_id": data.conversation_id,
        "text": data.text
    }

    try:
        response = requests.post(N8N_WEBHOOK, json=payload)
        result = response.json()
    except Exception as e:
        result = {"error": str(e)}

    return {
        "message": "Transcript received",
        "analytics": result
    }