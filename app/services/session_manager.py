from uuid import uuid4
from datetime import datetime, timedelta
from app.config import settings

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.session_duration = timedelta(minutes=30)  # Session timeout

    def create_session(self) -> str:
        session_id = str(uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "history": [],
            "report_data": {}  # For storing partial report information
        }
        return session_id

    def get_session(self, session_id: str):
        if session_id in self.sessions:
            # Reset timeout on access
            self.sessions[session_id]["created_at"] = datetime.now()
            return self.sessions[session_id]
        return None

    def cleanup_sessions(self):
        now = datetime.now()
        expired = [sid for sid, session in self.sessions.items() 
                  if now - session["created_at"] > self.session_duration]
        for sid in expired:
            del self.sessions[sid]

session_manager = SessionManager()