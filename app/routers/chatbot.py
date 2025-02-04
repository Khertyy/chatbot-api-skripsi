from fastapi import APIRouter, BackgroundTasks
from app.services.chat_service import ChatService
from app.models.schemas import ChatRequest, ChatResponse
from app.services.session_manager import session_manager

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    background_tasks: BackgroundTasks
):
    service = ChatService()
    response = await service.handle_chat(request, request.session_id)
    
    # Cleanup old sessions in background
    background_tasks.add_task(session_manager.cleanup_sessions)
    
    return response