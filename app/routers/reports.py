from fastapi import APIRouter, HTTPException
from app.services.chat_service import ChatService
from app.models.schemas import ChatResponse
from datetime import datetime
import aiohttp
import traceback
from app.config import settings

router = APIRouter()

@router.get("/")
async def get_reports():
    return {"message": "Reports endpoint"}

@router.post("/test-submission")
async def test_report_submission():
    """Endpoint khusus testing submission laporan"""
    try:
        # Data test dengan semua field yang diperlukan
        test_data = {
            "violence_category": "Kekerasan Fisik",
            "chronology": "Kronologi test lengkap dengan detail kejadian",
            "date": "2024-03-15",
            "scene": "Jalan Sudirman No. 123, Manado",
            "victim_name": "Nama Test Korban",
            "victim_phone": "08123456789",
            "victim_address": "Jl. Test Alamat Korban No. 45",
            "victim_age": "15",
            "victim_gender": "Wanita",
            "victim_description": "Korban menggunakan baju merah saat kejadian",
            "perpetrator_name": "Nama Test Pelaku",
            "perpetrator_age": "35",
            "perpetrator_gender": "Pria",
            "perpetrator_description": "Pelaku menggunakan kacamata hitam",
            "reporter_name": "Nama Test Pelapor",
            "reporter_phone": "08213456789",
            "reporter_address": "Jl. Test Alamat Pelapor No. 67",
            "reporter_relationship_between": "Tetangga"
        }

        async with aiohttp.ClientSession() as http_session:
            # Tambahkan parameter ssl=False untuk menonaktifkan verifikasi SSL
            async with http_session.post(
                f"{settings.base_api_url}/api/chatbot/report",
                data=test_data,
                ssl=False
            ) as response:
                response_data = await response.json()
                return {
                    "status_code": response.status,
                    "backend_response": response_data,
                    "sent_data": test_data,
                    "success": response.status == 200
                }

    except Exception as e:
        return {
            "error": str(e),
            "stack_trace": traceback.format_exc()
        } 