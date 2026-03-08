# Backend/app.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from transformers import pipeline

app = FastAPI(title="Conversation Analytics API (HF zero-shot)")

# -----------------------------
# Allow frontend communication
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# n8n webhook URL
# -----------------------------
N8N_WEBHOOK = "https://n8n-production-308b.up.railway.app/webhook/transcript"

# -----------------------------
# Zero-shot classifier
# -----------------------------
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# -----------------------------
# Confidence threshold for relevance
# -----------------------------
CONFIDENCE_THRESHOLD = 0.7  # Only consider relevant if score >= 0.7

# -----------------------------
# Conversation history storage
# -----------------------------
conversation_sessions: Dict[str, List[str]] = {}

# -----------------------------
# Data model
# -----------------------------
class Transcript(BaseModel):
    conversation_id: str
    text: str

# -----------------------------
# Relevance check using classifier
# -----------------------------
def is_relevant(segment: str) -> bool:
    candidate_labels = ["relevant", "irrelevant"]
    result = classifier(segment, candidate_labels=candidate_labels)
    top_label = result["labels"][0].lower()
    top_score = result["scores"][0]

    print("Classifier result:", result)
    print(f"Top label: {top_label}, Score: {top_score}")

    # Only return True if top label is 'relevant' and score >= threshold
    return top_label == "relevant" and top_score >= CONFIDENCE_THRESHOLD

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def home():
    return {"message": "Conversation Analytics API running (HF zero-shot)"}

@app.post("/transcript")
async def receive_transcript(data: Transcript):
    conversation_id = data.conversation_id
    text = data.text.strip()

    # Initialize conversation history if new
    if conversation_id not in conversation_sessions:
        conversation_sessions[conversation_id] = []

    # Relevance check via zero-shot classifier
    if not is_relevant(text):
        return {"message": "Skipped irrelevant message", "analytics": None}

    # Add to conversation history
    conversation_sessions[conversation_id].append(text)
    print(f"Conversation ({conversation_id}): {conversation_sessions[conversation_id]}")

    # Build aggregated context
    aggregated_context = " ".join(conversation_sessions[conversation_id])
    print(f"Aggregated context sent to n8n ({conversation_id}): {aggregated_context}")

    # Minimum context length before sending to n8n
    MIN_CONTEXT_LENGTH = 10
    if len(aggregated_context) < MIN_CONTEXT_LENGTH:
        return {
            "message": "Waiting for more context",
            "analytics": {
                "intent": None,
                "topic": None,
                "sentiment": None,
                "escalation_risk": None,
                "status": "pending"
            }
        }

    # Send aggregated context to n8n webhook
    payload = {"conversation_id": conversation_id, "text": aggregated_context}
    try:
        import requests
        response = requests.post(N8N_WEBHOOK, json=payload, timeout=15)
        result = response.json()
    except Exception as e:
        result = {"error": str(e)}

    return {"message": "Transcript processed", "analytics": result}
