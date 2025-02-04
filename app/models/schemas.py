from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # Client should send this after first response

class ChatResponse(BaseModel):
    response: str
    session_id: str  # Client must store and send this back
    next_steps: list[str]
    requires_follow_up: bool
    emergency_contact: str = "129"  # Nomor Darurat DP3A Sulut