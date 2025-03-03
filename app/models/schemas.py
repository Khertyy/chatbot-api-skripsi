from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Client should send this after first response

class ChatResponse(BaseModel):
    response: str
    session_id: str  # Client must store and send this back
    next_steps: List[str]
    requires_follow_up: bool
    emergency_contact: str = "129"  # Nomor Darurat DP3A Sulut