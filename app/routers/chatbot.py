from fastapi import APIRouter, BackgroundTasks, HTTPException, Response
from app.services.chat_service import ChatService
from app.models.schemas import ChatRequest, ChatResponse
from app.services.session_manager import session_manager
from app.services.redis_service import redis_service

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,
    response: Response
):
    # Tambahkan header CORS secara eksplisit
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    
    service = ChatService()
    response = await service.handle_chat(request, request.session_id)
    
    background_tasks.add_task(session_manager.cleanup_sessions)
    
    return response

# Tambahkan endpoint OPTIONS untuk pre-flight requests
@router.options("/chat")
async def chat_options(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return {"message": "OK"}

@router.get("/debug/session/{session_id}")
async def get_session_debug(session_id: str):
    """Endpoint untuk debugging session data"""
    session = await redis_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "data": session,
        "chat_history": session.get("history", []),
        "report_data": session.get("report_data", {})
    }

@router.get("/debug/sessions")
async def list_sessions():
    """Endpoint untuk melihat semua active sessions"""
    try:
        await redis_service.connect()
        keys = await redis_service.redis.keys("session:*")
        
        sessions = []
        for key in keys:
            session_id = key.replace("session:", "")
            session_data = await redis_service.get_session(session_id)
            if session_data:
                sessions.append({
                    "session_id": session_id,
                    "created_at": session_data.get("created_at"),
                    "message_count": len(session_data.get("history", [])),
                })
        
        return {"active_sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))