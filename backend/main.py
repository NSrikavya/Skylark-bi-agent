"""
FastAPI wrapper around the Skylark BI agent.
Exposes a single POST /chat endpoint the frontend will call.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from agent import ask_agent
from google.genai import types

app = FastAPI(title="Skylark BI Agent")

# Allow requests from any frontend for now (fine for a hosted prototype;
# tighten this to specific origins for production).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory session store ---
# Keyed by session_id, holds each conversation's Gemini `contents` history.
# NOTE: this resets if the server restarts, and doesn't scale across
# multiple server instances. Fine for a hosted prototype / demo; a real
# production version would persist this in a database.
sessions: dict = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Skylark BI Agent is running"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = sessions.get(req.session_id, [])

    reply_text = ask_agent(req.message, history)

    # Persist the updated conversation for this session.
    # ask_agent's internal `contents` list already includes tool-call turns,
    # but since ask_agent builds it internally, we reconstruct a simple
    # history here: just user + final text turns, which is enough context
    # for follow-up questions without resending large tool results.
    history.append(types.Content(role="user", parts=[types.Part(text=req.message)]))
    history.append(types.Content(role="model", parts=[types.Part(text=reply_text)]))
    sessions[req.session_id] = history

    return ChatResponse(reply=reply_text)