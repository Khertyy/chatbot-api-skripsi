from fastapi import APIRouter, HTTPException, status
from app.services.chat_service import ChatService
from app.models.schemas import ChatResponse
from datetime import datetime
import aiohttp
import traceback
from app.config import settings
import random
from datetime import datetime, timedelta
import string

router = APIRouter()

def generate_random_string(length=8):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length))

def generate_random_phone():
    return f"08{random.randint(10**9, 9*10**9)}"

def generate_random_date():
    start_date = datetime.now() - timedelta(days=365*2)
    end_date = datetime.now()
    random_date = start_date + (end_date - start_date) * random.random()
    return random_date.strftime("%Y-%m-%d")

@router.get("/")
async def get_reports():
    return {"message": "Reports endpoint"}

@router.post("/test-submission")
async def test_report_submission():
    """Endpoint testing submission dengan data acak"""
    try:
        # Generate random test data
        test_data = {
            "violence_category": random.choice([
                "Kekerasan Fisik",
                "Kekerasan Psikis",
                "Kekerasan Seksual",
                "Eksploitasi Anak",
                "Penelantaran Anak",
            ]),
            "chronology": f"Kronologi test acak {generate_random_string(12)}",
            "date": generate_random_date(),
            "scene": f"Jalan {generate_random_string(6)} No. {random.randint(1, 100)}",
            "victim_name": f"Korban {generate_random_string(4)}",
            "victim_phone": generate_random_phone(),
            "victim_address": f"Jl. {generate_random_string(8)} No. {random.randint(1, 50)}",
            "victim_age": str(random.randint(5, 60)),
            "victim_gender": random.choice(["Pria", "Wanita"]),
            "victim_description": f"Ciri: {generate_random_string(10)}",
            "perpetrator_name": f"Pelaku {generate_random_string(5)}",
            "perpetrator_age": str(random.randint(15, 70)),
            "perpetrator_gender": random.choice(["Pria", "Wanita"]),
            "perpetrator_description": f"Ciri pelaku: {generate_random_string(8)}",
            "reporter_name": f"Pelapor {generate_random_string(6)}",
            "reporter_phone": generate_random_phone(),
            "reporter_address": f"Jl. {generate_random_string(7)} No. {random.randint(1, 30)}",
            "reporter_relationship_between": random.choice([
                "Keluarga", 
                "Tetangga",
                "Teman",
                "Saksi",
                "Tidak Dikenal"
            ])
        }

        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                f"{settings.base_api_url}/api/chatbot/report",
                data=test_data,
                ssl=False
            ) as response:
                response_data = await response.json()
                
                # Return status code sesuai respons backend
                return {
                    "status_code": response.status,
                    "backend_response": response_data,
                    "sent_data": test_data,
                    "success": response.status == 200
                }

    except Exception as e:
        # Return error dengan status code 500 dan detail error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": str(e),
                "stack_trace": traceback.format_exc(),
                "message": "Gagal melakukan test submission"
            }
        )