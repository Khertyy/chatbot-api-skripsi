import aiohttp
import json
from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse
from app.services.session_manager import session_manager
from typing import Optional
from datetime import datetime
import re

class ChatService:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
        self.session_manager = session_manager
        self.system_prompt = """Anda adalah asisten spesialis perlindungan anak dari SIPPAT (Sistem Informasi Pelaporan Kekerasan Terhadap Anak) DP3A Sulawesi Utara.

Tugas utama Anda:
1. Membantu proses pelaporan kekerasan terhadap anak
2. Memberikan dukungan emosional
3. Mengumpulkan informasi dengan sensitif dan empatik
4. Memberikan informasi tentang layanan dan bantuan

Panduan penting:
1. Gunakan bahasa Indonesia yang sopan dan empatik
2. Berikan respons yang mendukung dan tidak menghakimi
3. Fokus pada kebutuhan pelapor dan korban
4. Jaga kerahasiaan informasi

Informasi Kontak:
- Nomor Darurat: 129
- Email: pppa_sulut@yahoo.com
- Alamat: Jalan 17 Agustus, Manado

Saat mengumpulkan informasi laporan, pastikan data berikut terkumpul dengan baik:
{report_fields}

Selalu berikan respons yang membantu dan mendukung."""
        self.report_fields = {
            "violence_category": "Kategori Kekerasan",
            "chronology": "Kronologi Kejadian",
            "date": "Tanggal Kejadian",
            "scene": "Lokasi Kejadian",
            "victim_name": "Nama Korban",
            "victim_phone": "Nomor Telepon Korban",
            "victim_address": "Alamat Korban",
            "victim_age": "Usia Korban",
            "victim_gender": "Jenis Kelamin Korban",
            "victim_description": "Deskripsi Korban",
            "perpetrator_name": "Nama Pelaku",
            "perpetrator_age": "Usia Pelaku",
            "perpetrator_gender": "Jenis Kelamin Pelaku",
            "perpetrator_description": "Deskripsi Pelaku",
            "reporter_name": "Nama Pelapor",
            "reporter_phone": "Nomor Telepon Pelapor",
            "reporter_address": "Alamat Pelapor",
            "reporter_relationship_between": "Hubungan dengan Korban"
        }
        self.initial_greetings = [
            "hai", "halo", "hi", "hello", "selamat"
        ]
        self.report_keywords = [
            "lapor", "laporkan", "melapor", "buat laporan", "membuat laporan",
            "laporin", "melaporkan", "ingin melapor", "mau melapor", "mau lapor"
        ]

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
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        raise Exception(f"Gemini API error: {response.status}")
        except Exception as e:
            return f"Maaf, terjadi kesalahan dalam berkomunikasi: {str(e)}"

    async def handle_chat(self, request: ChatRequest, session_id: Optional[str] = None):
        if not session_id or not await self.session_manager.get_session(session_id):
            session_id = await self.session_manager.create_session()
            session = await self.session_manager.get_session(session_id)
            session["is_first_message"] = True
        else:
            session = await self.session_manager.get_session(session_id)
        
        session["history"].append({"role": "user", "content": request.message})
        message_lower = request.message.lower()

        # Inisialisasi report_data jika belum ada
        if "report_data" not in session:
            session["report_data"] = {}

        # Cek jika ini adalah sapaan awal
        is_greeting = any(greeting in message_lower for greeting in self.initial_greetings)
        wants_to_report = any(keyword in message_lower for keyword in self.report_keywords)
        
        # Reset session jika user memulai percakapan baru
        if is_greeting:
            session["is_first_message"] = True
            session["reporting_mode"] = False
            session["current_field"] = None
            session["report_data"] = {}
            response_text = [
                "Hai! 👋 Selamat datang di layanan SIPPAT DP3A Sulawesi Utara.",
                "Saya adalah asisten yang siap membantu Anda untuk:",
                "1. Membuat laporan kekerasan terhadap anak",
                "2. Memberikan informasi tentang perlindungan anak",
                "3. Memberikan bantuan darurat",
                "Apa yang bisa saya bantu hari ini?"
            ]
            assistant_response = " ".join(response_text)
        
        elif wants_to_report:
            # Mulai mode pelaporan
            session["reporting_mode"] = True
            session["current_field"] = "violence_category"
            session["report_data"] = {}  # Reset report data
            response_text = [
                "Baik, saya akan membantu Anda membuat laporan. Mohon beritahu jenis kekerasan yang terjadi:",
                "- Kekerasan Fisik",
                "- Kekerasan Seksual",
                "- Kekerasan Psikis",
                "- Penelantaran",
                "- Trafficking"
            ]
            assistant_response = " ".join(response_text)

        else:
            if session.get("reporting_mode"):
                # Update data berdasarkan input user
                self._update_report_data(request.message, session)

                # Tentukan respons berikutnya
                if session.get("ready_to_submit"):
                    if "iya" in message_lower:
                        return await self._submit_report(session)
                    assistant_response = self._generate_short_confirmation(session["report_data"])
                else:
                    next_question = self._get_next_questions(session)
                    if next_question:
                        assistant_response = next_question
                    else:
                        assistant_response = "Mohon maaf, saya tidak mengerti. Bisakah Anda mengulangi jawaban Anda?"
            else:
                # Mode percakapan umum
                if "bantuan darurat" in message_lower:
                    response_text = [
                        "Untuk bantuan darurat, silakan:",
                        "1. Hubungi nomor darurat kami: 129",
                        "2. Kirim SMS/WA ke: [nomor hotline]",
                        "3. Datang langsung ke kantor kami di: [alamat]"
                    ]
                    assistant_response = " ".join(response_text)
                elif "informasi" in message_lower:
                    response_text = [
                        "Saya dapat memberikan informasi tentang:",
                        "1. Jenis-jenis kekerasan terhadap anak",
                        "2. Hak-hak anak",
                        "3. Prosedur pelaporan",
                        "4. Bantuan hukum",
                        "Informasi apa yang Anda butuhkan?"
                    ]
                    assistant_response = " ".join(response_text)
                else:
                    response_text = [
                        "Saya siap membantu Anda. Silakan pilih:",
                        "1. Ketik \"lapor\" untuk membuat laporan kekerasan",
                        "2. Ketik \"informasi\" untuk mendapatkan informasi",
                        "3. Ketik \"bantuan darurat\" untuk bantuan segera"
                    ]
                    assistant_response = " ".join(response_text)

        session["history"].append({"role": "assistant", "content": assistant_response})
        await self.session_manager.set_session(session_id, session)
        
        return ChatResponse(
            response=assistant_response,
            session_id=session_id,
            next_steps=self._determine_next_steps(session),
            requires_follow_up=True
        )

    def _update_report_data(self, message: str, session: dict):
        message_lower = message.lower()
        current_field = session.get("current_field")
        
        # Jika ada field yang sedang aktif, coba update berdasarkan field tersebut
        if current_field:
            # Khusus untuk violence_category, cek kata kunci spesifik
            if current_field == "violence_category":
                categories = {
                    "kekerasan fisik": ["fisik", "pukul", "tendang", "aniaya"],
                    "kekerasan seksual": ["seksual", "perkosa", "leceh", "cabul"],
                    "kekerasan psikis": ["psikis", "mental", "ancam", "intimidasi"],
                    "penelantaran": ["telantar", "tidak diurus"],
                    "trafficking": ["trafficking", "perdagangan", "eksploitasi"]
                }
                
                for category, keywords in categories.items():
                    if any(keyword in message_lower for keyword in keywords):
                        session["report_data"][current_field] = category
                        session["current_field"] = None
                        return
            
            # Untuk field lainnya, terima input langsung
            cleaned_message = message.strip()
            if len(cleaned_message) > 2:
                session["report_data"][current_field] = cleaned_message
                session["current_field"] = None
                
                # Cek apakah semua field sudah terisi
                if self._is_report_complete(session["report_data"]):
                    session["ready_to_submit"] = True

    def _is_report_complete(self, report_data: dict) -> bool:
        return all(field in report_data for field in self.report_fields)

    def _generate_short_confirmation(self, report_data: dict) -> str:
        important_fields = {
            "violence_category": "Jenis Kekerasan",
            "chronology": "Kronologi",
            "scene": "Lokasi",
            "victim_name": "Korban"
        }
        
        response_text = [
            "Saya sudah mengumpulkan semua informasi yang diperlukan. Berikut ringkasannya:"
        ]
        
        for field, label in important_fields.items():
            response_text.append(f"{label}: {report_data.get(field, '-')}")
        
        response_text.append("Apakah Anda ingin membuat laporan dengan data tersebut? (Jawab: Iya/Tidak)")
        
        return " ".join(response_text)

    def _get_next_questions(self, session: dict) -> str:
        question_flow = [
            ("violence_category", """Saya mengerti Anda ingin membuat laporan. Untuk membantu kami menangani kasus ini dengan tepat, mohon beritahu jenis kekerasan yang terjadi:

- Kekerasan Fisik
- Kekerasan Seksual
- Kekerasan Psikis
- Penelantaran
- Trafficking"""),
            ("victim_name", """Terima kasih atas informasinya. Untuk melanjutkan proses pelaporan, boleh saya tahu nama korban yang mengalami kekerasan? Kami akan menjaga kerahasiaan identitas dengan sangat baik. 🙏"""),
            ("date", """Untuk membantu kami memahami kronologi kejadian dengan lebih baik, kapan kejadian ini terjadi? Anda bisa memberikan tanggal seperti contoh: 25/03/2024"""),
            ("scene", """Kami juga perlu mengetahui lokasi kejadian untuk penanganan yang tepat. Boleh diceritakan di mana kejadian ini terjadi? Bisa disebutkan alamat lengkap atau daerahnya."""),
            ("chronology", """Saya memahami ini mungkin sulit, tapi bisakah Anda menceritakan secara singkat bagaimana kejadian ini terjadi? Informasi ini sangat penting untuk membantu kami mengambil tindakan yang tepat."""),
            ("victim_age", """Untuk memastikan penanganan yang sesuai, boleh saya tahu berapa usia korban saat ini?"""),
            ("victim_gender", """Mohon beritahu jenis kelamin korban (Pria/Wanita). Informasi ini penting untuk penanganan kasus yang lebih tepat."""),
            ("victim_phone", """Jika memungkinkan, boleh kami minta nomor telepon korban yang bisa dihubungi? Ini akan membantu kami untuk koordinasi lebih lanjut jika diperlukan."""),
            ("victim_address", """Untuk keperluan pendampingan dan perlindungan, boleh kami tahu alamat tempat tinggal korban saat ini?"""),
            ("victim_description", """Untuk membantu identifikasi, bisakah Anda memberikan deskripsi singkat tentang korban? Misalnya: ciri-ciri fisik atau hal khusus yang perlu kami ketahui."""),
            ("perpetrator_name", """Jika Anda mengetahuinya, boleh beritahu nama pelaku dalam kejadian ini? Informasi ini akan sangat membantu proses penanganan kasus."""),
            ("perpetrator_age", """Sejauh yang Anda ketahui, kira-kira berapa usia pelaku?"""),
            ("perpetrator_gender", """Untuk melengkapi data, mohon beritahu jenis kelamin pelaku (Pria/Wanita)."""),
            ("perpetrator_description", """Bisakah Anda memberikan deskripsi singkat tentang pelaku? Misalnya: ciri-ciri fisik, atau informasi lain yang bisa membantu identifikasi."""),
            ("reporter_name", """Terima kasih atas kepedulian Anda dalam melaporkan kasus ini. Boleh kami tahu nama Anda sebagai pelapor?"""),
            ("reporter_phone", """Agar kami bisa menghubungi Anda untuk informasi lebih lanjut, boleh kami minta nomor telepon yang bisa dihubungi?"""),
            ("reporter_address", """Untuk keperluan administrasi, boleh kami tahu alamat tempat tinggal Anda saat ini?"""),
            ("reporter_relationship_between", """Terakhir, boleh kami tahu apa hubungan Anda dengan korban? Ini akan membantu kami dalam proses penanganan kasus.

- Keluarga
- Tetangga
- Teman
- Saksi
- Tidak Dikenal""")
        ]

        # Cari field yang belum terisi dan berikan pertanyaan berikutnya
        for field, question in question_flow:
            if field not in session["report_data"]:
                session["current_field"] = field  # Tandai field yang sedang ditanyakan
                return question
        
        # Jika semua field sudah terisi
        return None

    async def _submit_report(self, session: dict) -> ChatResponse:
        """Submit laporan ke endpoint backend"""
        try:
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    f"{settings.base_api_url}/api/chatbot/report",
                    json=session["report_data"]  # Menggunakan json= untuk mengirim JSON
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_message = f"Laporan berhasil dibuat dengan nomor tiket: {result.get('ticket_number', 'N/A')}"
                    else:
                        response_message = "Maaf, terjadi kesalahan dalam pembuatan laporan. Silakan coba lagi nanti."

                    return ChatResponse(
                        response=response_message,
                        session_id=session["session_id"],
                        next_steps=["Laporan telah selesai dibuat"],
                        requires_follow_up=False
                    )
        except Exception as e:
            return ChatResponse(
                response=f"Terjadi kesalahan: {str(e)}",
                session_id=session["session_id"],
                next_steps=["Silakan coba lagi"],
                requires_follow_up=True
            )

    def _determine_next_steps(self, session: dict) -> list[str]:
        if session.get("ready_to_submit"):
            return ["Konfirmasi pengiriman laporan"]
        elif session.get("reporting_mode"):
            if session.get("current_field"):
                return [f"Jawab pertanyaan tentang {self.report_fields[session['current_field']]}"]
            return ["Lanjutkan menjawab pertanyaan"]
        return ["Pilih layanan yang dibutuhkan"]