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

    # --- Backend Input Validation ---
    if not data.text.strip():
        return {
            "message": "Invalid service input, please enter a valid input",
            "analytics": None
        }

    payload = {
        "conversation_id": data.conversation_id,
        "text": data.text
    }

    try:
        # Send transcript to n8n webhook
        response = requests.post(N8N_WEBHOOK, json=payload)
        result = response.json()

        # Validate n8n response
        if not result or "error" in result:
            return {
                "message": "Invalid service input, please enter a valid input",
                "analytics": None
            }

    except Exception as e:
        # Handle request errors
        return {
            "message": "Invalid service input, please enter a valid input",
            "analytics": {"error": str(e)}
        }

    # --- Successful Response ---
    return {
        "message": "Transcript received",
        "analytics": result
    }
