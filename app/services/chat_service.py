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
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.session_manager = session_manager
        self.system_prompt = """Anda adalah asisten spesialis perlindungan anak dari SIPPAT (Sistem Informasi Pelaporan Kekerasan Terhadap Anak) DP3A Sulawesi Utara. Tugas Anda:

1. Membantu pengguna melalui proses pelaporan langkah demi langkah
2. Mengumpulkan informasi penting:
   - Jenis insiden kekerasan
   - Lokasi kejadian
   - Tanggal kejadian
   - Usia korban
   - Informasi pelaku
3. Memberikan dukungan emosional dan sumber daya yang tepat
4. Menjelaskan langkah-langkah selanjutnya dalam proses pelaporan
5. Menjawab pertanyaan tentang hukum perlindungan anak

Informasi Kontak Penting:
- Nomor Telepon: 129
- Email: pppa_sulut@yahoo.com
- Alamat: Jalan 17 Agustus, Manado, Sulawesi Utara

Selalu gunakan Bahasa Indonesia yang sopan dan empatik dalam merespons."""
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

    async def handle_chat(self, request: ChatRequest, session_id: Optional[str] = None):
        if not session_id or not await self.session_manager.get_session(session_id):
            session_id = await self.session_manager.create_session()
            session = await self.session_manager.get_session(session_id)
            session["is_first_message"] = True
        else:
            session = await self.session_manager.get_session(session_id)
        
        session["history"].append({"role": "user", "content": request.message})

        # Cek jika ini adalah sapaan awal
        message_lower = request.message.lower()
        is_greeting = any(greeting in message_lower for greeting in self.initial_greetings)
        
        if is_greeting and session.get("is_first_message", False):
            assistant_response = """Hai! 👋 Selamat datang di layanan SIPPAT DP3A Sulawesi Utara. Saya siap membantu Anda, apa yang bisa saya bantu hari ini?"""
            session["is_first_message"] = False
        else:
            # Cek konfirmasi pembuatan laporan
            if "iya" in request.message.lower() and session.get("ready_to_submit"):
                return await self._submit_report(session)

            if "report_data" not in session:
                session["report_data"] = {}
                session["current_field"] = None

            # Update data berdasarkan input user
            self._update_report_data(request.message, session)

            # Siapkan prompt yang lebih ringkas
            if self._is_report_complete(session["report_data"]):
                if not session.get("ready_to_submit"):
                    session["ready_to_submit"] = True
                    assistant_response = self._generate_short_confirmation(session["report_data"])
            else:
                # Dapatkan pertanyaan berikutnya
                next_question = self._get_next_questions(session)
                if next_question:
                    assistant_response = next_question
                else:
                    assistant_response = "Mohon maaf, saya tidak mengerti. Bisakah Anda mengulangi jawaban Anda?"

        session["history"].append({"role": "assistant", "content": assistant_response})

        return ChatResponse(
            response=assistant_response,
            session_id=session_id,
            next_steps=self._determine_next_steps(session),
            requires_follow_up=True
        )

    def _update_report_data(self, message: str, session: dict):
        message_lower = message.lower()
        
        # Kamus kata kunci untuk setiap field
        keywords = {
            "violence_category": {
                "kekerasan fisik": ["pukul", "tendang", "aniaya", "tampar", "siksa", "dianiaya"],
                "kekerasan seksual": ["perkosa", "leceh", "cabul", "pemerkosaan", "pelecehan"],
                "kekerasan psikis": ["ancam", "intimidasi", "teror", "kata kasar", "memaki"],
                "penelantaran": ["telantarkan", "tidak diberi makan", "tidak diurus"],
                "trafficking": ["jual", "perdagangan", "eksploitasi"]
            },
            "perpetrator_relationship_between": {
                "orang tua": ["ayah", "ibu", "orang tua"],
                "keluarga": ["paman", "bibi", "kakek", "nenek", "sepupu"],
                "kekasih": ["pacar", "kekasih", "pacarnya"],
                "tetangga": ["tetangga"],
                "guru": ["guru", "pengajar"],
                "teman": ["teman", "temannya"]
            }
        }

        # Ekstrak informasi tambahan dari pesan
        for field, categories in keywords.items():
            if field not in session["report_data"]:
                for category, words in categories.items():
                    if any(word in message_lower for word in words):
                        session["report_data"][field] = category
                        break

        # Ekstrak tanggal jika ada format tanggal dalam pesan
        if "date" not in session["report_data"]:
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',  # Format YYYY-MM-DD
                r'\d{2}/\d{2}/\d{4}'   # Format DD/MM/YYYY
            ]
            for pattern in date_patterns:
                match = re.search(pattern, message)
                if match:
                    try:
                        date_str = match.group(0)
                        if '/' in date_str:
                            # Konversi DD/MM/YYYY ke YYYY-MM-DD
                            day, month, year = date_str.split('/')
                            date_str = f"{year}-{month}-{day}"
                        datetime.strptime(date_str, "%Y-%m-%d")
                        session["report_data"]["date"] = date_str
                    except ValueError:
                        pass

        # Ekstrak usia jika ada angka dengan kata "tahun" atau "umur"
        age_fields = ["victim_age", "perpetrator_age"]
        for field in age_fields:
            if field not in session["report_data"]:
                age_pattern = r'\b(\d+)\s*(?:tahun|thn)\b'
                match = re.search(age_pattern, message_lower)
                if match:
                    age = int(match.group(1))
                    if 0 < age < 150:
                        session["report_data"][field] = str(age)

        # Ekstrak lokasi jika ada kata kunci lokasi
        if "scene" not in session["report_data"]:
            location_keywords = ["di", "lokasi", "tempat", "jalan", "jl.", "desa", "kelurahan"]
            for keyword in location_keywords:
                if keyword in message_lower:
                    # Ambil teks setelah kata kunci lokasi
                    loc_idx = message_lower.find(keyword)
                    if loc_idx != -1:
                        location = message[loc_idx:].split('.')[0].strip()
                        if len(location) > 5:  # Minimal 5 karakter untuk lokasi valid
                            session["report_data"]["scene"] = location
                            break

        # Tentukan field yang sedang dikumpulkan jika belum ada
        if not session.get("current_field"):
            for field in self.report_fields:
                if field not in session["report_data"]:
                    session["current_field"] = field
                    break

        # Update data untuk field saat ini jika belum terisi
        if session.get("current_field") and session["current_field"] not in session["report_data"]:
            # Simpan teks untuk field yang sedang dikumpulkan
            cleaned_message = message.strip()
            if len(cleaned_message) > 2:  # Minimal 2 karakter untuk input valid
                session["report_data"][session["current_field"]] = cleaned_message
                session["current_field"] = None

        # Ekstrak jenis kelamin
        gender_keywords = {
            "victim_gender": {
                "wanita": ["wanita", "perempuan", "cewek", "permpuan"],
                "pria": ["pria", "laki-laki", "cowok", "laki"]
            },
            "perpetrator_gender": {
                "wanita": ["wanita", "perempuan", "cewek", "permpuan"],
                "pria": ["pria", "laki-laki", "cowok", "laki"]
            }
        }
        
        for field in ["victim_gender", "perpetrator_gender"]:
            if field not in session["report_data"]:
                for gender, keywords in gender_keywords[field].items():
                    if any(kw in message_lower for kw in keywords):
                        session["report_data"][field] = gender.capitalize()
                        break

    def _is_report_complete(self, report_data: dict) -> bool:
        return all(field in report_data for field in self.report_fields)

    def _generate_short_confirmation(self, report_data: dict) -> str:
        # Hanya tampilkan informasi penting untuk konfirmasi
        important_fields = {
            "violence_category": "Jenis Kekerasan",
            "chronology": "Kronologi",
            "scene": "Lokasi",
            "victim_name": "Korban"
        }
        
        confirmation = "Saya sudah mengumpulkan semua informasi yang diperlukan. Berikut ringkasannya:\n\n"
        for field, label in important_fields.items():
            confirmation += f"{label}: {report_data.get(field, '-')}\n"
        confirmation += "\nApakah Anda ingin membuat laporan dengan data tersebut? (Jawab: Iya/Tidak)"
        return confirmation

    def _get_next_questions(self, session: dict) -> str:
        # Urutan pertanyaan yang lebih natural dan satu per satu
        question_flow = [
            ("violence_category", """Saya akan membantu Anda membuat laporan. Mohon beritahu jenis kekerasan yang terjadi:

- Kekerasan Fisik
- Kekerasan Seksual
- Kekerasan Psikis
- Penelantaran
- Trafficking"""),
            ("victim_name", "Baik, mohon beritahu nama korban yang mengalami kekerasan. 🙏"),
            ("date", "Kapan kejadian ini terjadi? (Contoh: 25/03/2024)"),
            ("scene", "Di mana lokasi kejadian ini terjadi?"),
            ("chronology", "Mohon ceritakan secara singkat kronologi kejadiannya."),
            ("victim_age", "Berapa usia korban saat ini?"),
            ("victim_gender", "Mohon beritahu jenis kelamin korban (Pria/Wanita)."),
            ("victim_phone", "Boleh saya tahu nomor telepon korban yang bisa dihubungi?"),
            ("victim_address", "Di mana alamat tempat tinggal korban saat ini?"),
            ("victim_description", "Mohon berikan deskripsi singkat tentang korban."),
            ("perpetrator_name", "Siapa nama pelaku dalam kejadian ini?"),
            ("perpetrator_age", "Berapa usia pelaku?"),
            ("perpetrator_gender", "Apa jenis kelamin pelaku (Pria/Wanita)?"),
            ("perpetrator_description", "Mohon berikan deskripsi singkat tentang pelaku."),
            ("reporter_name", "Boleh saya tahu nama Anda sebagai pelapor?"),
            ("reporter_phone", "Nomor telepon yang bisa kami hubungi?"),
            ("reporter_address", "Di mana alamat tempat tinggal Anda?"),
            ("reporter_relationship_between", """Apa hubungan Anda dengan korban?

- Keluarga
- Tetangga
- Teman
- Saksi
- Tidak Dikenal"""),
        ]

        # Cari field yang belum terisi dan berikan pertanyaan berikutnya
        for field, question in question_flow:
            if field not in session["report_data"]:
                session["current_field"] = field  # Tandai field yang sedang ditanyakan
                return question
        
        # Jika semua field sudah terisi
        return None

    async def _submit_report(self, session: dict) -> ChatResponse:
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                f"{settings.base_api_url}/api/chatbot/report",
                data=session["report_data"]
            ) as response:
                result = await response.json()
                
                response_message = f"Laporan berhasil dibuat dengan nomor tiket: {result['ticket_number']}"
                if not result['success']:
                    response_message = "Maaf, terjadi kesalahan dalam pembuatan laporan. Silakan coba lagi nanti."

                return ChatResponse(
                    response=response_message,
                    session_id=session["session_id"],
                    next_steps=["Laporan telah selesai dibuat"],
                    requires_follow_up=False
                )

    def _determine_next_steps(self, session: dict) -> list[str]:
        if session.get("ready_to_submit"):
            return ["Konfirmasi pengiriman laporan"]
        elif session.get("current_field"):
            return [f"Jawab pertanyaan tentang {self.report_fields[session['current_field']]}"]
        return ["Mulai proses pelaporan"]