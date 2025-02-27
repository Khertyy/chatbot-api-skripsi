import aiohttp
import json
from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse
from app.services.session_manager import session_manager
from typing import Optional
from datetime import datetime
import re
import logging
import sys
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
        self.session_manager = session_manager
        logger.info("ChatService initialized with API URL: %s", self.api_url)
        
        # Muat dataset dari file
        with open('dataset.txt', 'r', encoding='utf-8') as f:
            self.dataset = f.read()
        
        self.system_prompt = f"""Anda adalah asisten virtual DP3A Sulawesi Utara. Gunakan bahasa Indonesia yang santai dan natural seperti manusia. 
        
Ikuti panduan ini:
1. Gunakan kalimat pendek dan mudah dimengerti
2. Tambahkan emoji yang relevan untuk membuat lebih ramah
3. Untuk pertanyaan di luar topik dataset, jawab dengan sopan
4. Gunakan informasi dari dataset berikut:
{self.dataset}

Contoh respons yang baik:
- "Halo juga! 😊 Ada yang bisa saya bantu terkait DP3A Sulut?"
- "Untuk layanan hukum, kita punya tim khusus yang siap membantu. Mau saya jelaskan lebih detail?"
"""

    def _format_response(self, text: str) -> str:
        """Helper method untuk memformat response text"""
        # Mengganti newlines dengan spasi jika diikuti list item
        text = text.replace('\n-', ' -')
        # Mengganti multiple newlines dengan single newline
        text = ' '.join(line.strip() for line in text.split('\n') if line.strip())
        return text

    async def _get_gemini_response(self, prompt: str, context: dict = None) -> str:
        """Mendapatkan response dari Gemini API"""
        try:
            # Siapkan prompt dengan context
            full_prompt = f"{self.system_prompt}\n\nContext: {json.dumps(context) if context else ''}\n\nUser: {prompt}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    params={"key": self.api_key},
                    json={
                        "contents": [{
                            "role": "user",
                            "parts": [{"text": full_prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.7,
                            "topP": 0.8,
                            "topK": 40
                        }
                    },
                    ssl=False
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        raise Exception(f"Gemini API error: {response.status}")
        except Exception as e:
            return f"Maaf, sedang ada gangguan teknis. Silakan coba lagi nanti ya 🙏"

    async def handle_chat(self, request: ChatRequest, session_id: Optional[str] = None):
        if not session_id or not await self.session_manager.get_session(session_id):
            session_id = await self.session_manager.create_session()
            session = await self.session_manager.get_session(session_id)
            session["history"] = []
        else:
            session = await self.session_manager.get_session(session_id)
        
        # Tambahkan ke riwayat percakapan
        session["history"].append({"role": "user", "content": request.message})
        
        try:
            # Cari jawaban langsung dari dataset
            direct_response = self._find_direct_answer(request.message)
            if direct_response:
                response_text = direct_response
            else:
                # Jika tidak ditemukan, gunakan Gemini dengan konteks percakapan
                context = {
                    "history": session["history"][-5:],  # Ambil 5 pesan terakhir
                    "dataset": self.dataset
                }
                response_text = await self._get_gemini_response(request.message, context)
                
                # Post-processing untuk membuat lebih natural
                response_text = self._humanize_response(response_text)
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            response_text = "Maaf, sedang ada gangguan teknis. Silakan coba lagi nanti ya 🙏"

        # Simpan respons dan update session
        session["history"].append({"role": "assistant", "content": response_text})
        await self.session_manager.set_session(session_id, session)
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            next_steps=[],
            requires_follow_up=False
        )

    def _find_direct_answer(self, message: str) -> Optional[str]:
        """Cari jawaban langsung dari dataset"""
        message_lower = message.lower()
        
        # Mapping intent sederhana
        intent_mapping = {
            'salam': ['halo', 'hi', 'selamat'],
            'goodbye': ['bye', 'sampai', 'tinggal'],
            'tanya_dp3a': ['apa itu dp3a'],
            'layanan_dp3a': ['layanan dp3a'],
            # ... tambahkan mapping untuk semua intent di dataset
        }
        
        # Cari intent yang cocok
        for intent, keywords in intent_mapping.items():
            if any(kw in message_lower for kw in keywords):
                return self._get_response_from_dataset(intent)
        
        return None

    def _get_response_from_dataset(self, intent: str) -> str:
        """Ambil response dari dataset berdasarkan intent"""
        # Implementasi parsing dataset.txt untuk mencari response
        # Contoh sederhana:
        if "salam" in intent:
            return "Halo! Senang bisa membantu. Ada yang bisa saya bantu hari ini? 😊"
        elif "goodbye" in intent:
            return "Sampai jumpa! Jangan ragu untuk kembali jika butuh bantuan lagi 🙋♂️"
        # ... dan seterusnya
        
        return ""

    def _humanize_response(self, text: str) -> str:
        """Buat respons lebih seperti manusia"""
        # Tambahkan variasi kalimat
        variations = {
            "Ya,": ["Iya nih,", "Betul,", "Benar sekali,"],
            "Tentu": ["Pastinya dong", "Tentu saja", "Bisa banget"],
        }
        
        # Ganti beberapa kata kunci
        for key, options in variations.items():
            if key in text:
                text = text.replace(key, random.choice(options), 1)
        
        # Tambahkan emoji acak di akhir kalimat
        emojis = ["😊", "🙏", "👍", "💡", "👋"]
        if text[-1] not in ["!", "?", "."]:
            text += random.choice([".", "!"]) + " " + random.choice(emojis)
        else:
            text += " " + random.choice(emojis)
        
        return text