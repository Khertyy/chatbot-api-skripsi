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
            "hai", "halo", "hi", "hello", "selamat pagi", "selamat siang", 
            "selamat sore", "selamat malam"
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

        # Cek jika ini adalah sapaan awal - hanya jika pesan HANYA berisi sapaan
        is_greeting = message_lower in self.initial_greetings or message_lower.strip() in self.initial_greetings
        wants_to_report = any(keyword in message_lower for keyword in self.report_keywords)
        
        # Reset session HANYA jika ini adalah sapaan awal dan bukan dalam mode pelaporan
        if is_greeting and not session.get("reporting_mode"):
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
            
            # Cek apakah jenis kekerasan sudah disebutkan dalam pesan
            violence_detected = self._detect_violence_category(message_lower)
            if violence_detected:
                session["report_data"]["violence_category"] = violence_detected
                session["current_field"] = "victim_name"  # Lanjut ke pertanyaan berikutnya
                assistant_response = """Terima kasih atas informasinya. Untuk melanjutkan proses pelaporan, boleh saya tahu nama korban yang mengalami kekerasan? Kami akan menjaga kerahasiaan identitas dengan sangat baik. 🙏"""
            else:
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
        try:
            message_lower = message.lower()
            current_field = session.get("current_field")
            logger.info("Updating report data for field: %s with message: %s", current_field, message)
            
            if current_field:
                cleaned_message = message.strip()
                if len(cleaned_message) > 2:
                    # Khusus untuk field nomor telepon
                    if current_field in ["victim_phone", "reporter_phone"]:
                        # Validasi nomor telepon
                        is_valid, _ = self._validate_report_data({current_field: cleaned_message})
                        if not is_valid:
                            # Tetap di field yang sama dan minta input ulang
                            logger.info(f"Invalid phone number for {current_field}: {cleaned_message}")
                            return
                    
                    session["report_data"][current_field] = cleaned_message
                    session["current_field"] = None
                    logger.info("Updated field %s with value: %s", current_field, cleaned_message)
                    
                    if self._is_report_complete(session["report_data"]):
                        # Validasi seluruh data sebelum set ready_to_submit
                        is_valid, _ = self._validate_report_data(session["report_data"])
                        session["ready_to_submit"] = is_valid
                        if is_valid:
                            logger.info("Report is complete and valid, ready to submit")
                        else:
                            logger.info("Report is complete but has invalid data")
        except Exception as e:
            logger.exception("Error updating report data: %s", str(e))

    def _is_report_complete(self, report_data: dict) -> bool:
        return all(field in report_data for field in self.report_fields)

    def _validate_report_data(self, report_data: dict) -> tuple[bool, list[str]]:
        """Validasi data laporan dan return list field yang perlu diperbaiki"""
        invalid_fields = []
        
        # Helper function untuk validasi nomor telepon
        def is_valid_phone(phone: str) -> bool:
            # Bersihkan string dari karakter non-digit
            digits = ''.join(filter(str.isdigit, phone))
            # Cek panjang minimal dan tidak boleh kosong/tidak ada
            return len(digits) >= 10 and not any(skip in phone.lower() for skip in 
                ["tidak", "ga", "gak", "tidak ada", "kosong", "tidak punya", "-"])

        # Aturan validasi untuk setiap field
        validation_rules = {
            "victim_phone": is_valid_phone,
            "reporter_phone": is_valid_phone,
            "victim_age": lambda x: bool(re.search(r'\d+', x)),
            "perpetrator_age": lambda x: bool(re.search(r'\d+', x)),
            "victim_gender": lambda x: any(gender in x.lower() for gender in ["pria", "wanita", "laki", "perempuan"]),
            "perpetrator_gender": lambda x: any(gender in x.lower() for gender in ["pria", "wanita", "laki", "perempuan"])
        }

        for field, rule in validation_rules.items():
            if field in report_data and not rule(report_data[field]):
                invalid_fields.append(field)
                logger.warning(f"Invalid data for field {field}: {report_data[field]}")

        return len(invalid_fields) == 0, invalid_fields

    def _get_reask_message(self, invalid_fields: list[str]) -> str:
        """Generate pesan untuk meminta ulang data yang tidak valid"""
        field_messages = {
            "victim_phone": """Nomor telepon korban sangat penting untuk koordinasi dan penanganan kasus. 
Mohon berikan nomor telepon yang valid (minimal 10 digit). 
Contoh format: 081234567890""",
            "reporter_phone": """Sebagai pelapor, nomor telepon Anda WAJIB diisi untuk:
1. Koordinasi penanganan kasus
2. Pembaruan status laporan
3. Informasi tindak lanjut

Mohon berikan nomor telepon yang dapat dihubungi (minimal 10 digit).
Contoh format: 081234567890""",
            "victim_age": "Mohon berikan usia korban dalam bentuk angka, contoh: 15 tahun.",
            "perpetrator_age": "Mohon berikan perkiraan usia pelaku dalam bentuk angka, contoh: 35 tahun.",
            "victim_gender": "Mohon tentukan jenis kelamin korban (Pria/Wanita).",
            "perpetrator_gender": "Mohon tentukan jenis kelamin pelaku (Pria/Wanita)."
        }

        messages = ["Untuk dapat memproses laporan Anda, mohon lengkapi informasi berikut:"]
        for field in invalid_fields:
            messages.append(f"\n{field_messages.get(field)}")
        
        if any(field in ["victim_phone", "reporter_phone"] for field in invalid_fields):
            messages.append("\n⚠️ Nomor telepon wajib diisi untuk memastikan laporan dapat ditindaklanjuti dengan baik.")
        
        return "\n".join(messages)

    def _generate_short_confirmation(self, report_data: dict) -> str:
        # Validasi data sebelum konfirmasi
        is_valid, invalid_fields = self._validate_report_data(report_data)
        
        if not is_valid:
            return self._get_reask_message(invalid_fields)
        
        # Jika valid, lanjutkan dengan konfirmasi normal
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
            ("violence_category", "Saya mengerti Anda ingin membuat laporan. Untuk membantu kami menangani kasus ini dengan tepat, mohon beritahu jenis kekerasan yang terjadi:\n\n- Kekerasan Fisik\n- Kekerasan Seksual\n- Kekerasan Psikis\n- Penelantaran\n- Trafficking"),
            ("victim_name", "Terima kasih atas informasinya. Untuk melanjutkan proses pelaporan, boleh saya tahu nama korban yang mengalami kekerasan? Kami akan menjaga kerahasiaan identitas dengan sangat baik. 🙏"),
            ("date", "Untuk membantu kami memahami kronologi kejadian dengan lebih baik, kapan kejadian ini terjadi? Anda bisa memberikan tanggal seperti contoh: 25/03/2024"),
            ("scene", "Kami juga perlu mengetahui lokasi kejadian untuk penanganan yang tepat. Boleh diceritakan di mana kejadian ini terjadi? Bisa disebutkan alamat lengkap atau daerahnya."),
            ("chronology", "Saya memahami ini mungkin sulit, tapi bisakah Anda menceritakan secara singkat bagaimana kejadian ini terjadi? Informasi ini sangat penting untuk membantu kami mengambil tindakan yang tepat."),
            ("victim_age", "Untuk memastikan penanganan yang sesuai, boleh saya tahu berapa usia korban saat ini?"),
            ("victim_gender", "Mohon beritahu jenis kelamin korban (Pria/Wanita). Informasi ini penting untuk penanganan kasus yang lebih tepat."),
            ("victim_phone", "Jika memungkinkan, boleh kami minta nomor telepon korban yang bisa dihubungi? Ini akan membantu kami untuk koordinasi lebih lanjut jika diperlukan."),
            ("victim_address", "Untuk keperluan pendampingan dan perlindungan, boleh kami tahu alamat tempat tinggal korban saat ini?"),
            ("victim_description", "Untuk membantu identifikasi, bisakah Anda memberikan deskripsi singkat tentang korban? Misalnya: ciri-ciri fisik atau hal khusus yang perlu kami ketahui."),
            ("perpetrator_name", "Jika Anda mengetahuinya, boleh beritahu nama pelaku dalam kejadian ini? Informasi ini akan sangat membantu proses penanganan kasus."),
            ("perpetrator_age", "Sejauh yang Anda ketahui, kira-kira berapa usia pelaku?"),
            ("perpetrator_gender", "Untuk melengkapi data, mohon beritahu jenis kelamin pelaku (Pria/Wanita)."),
            ("perpetrator_description", "Bisakah Anda memberikan deskripsi singkat tentang pelaku? Misalnya: ciri-ciri fisik, atau informasi lain yang bisa membantu identifikasi."),
            ("reporter_name", "Terima kasih atas kepedulian Anda dalam melaporkan kasus ini. Boleh kami tahu nama Anda sebagai pelapor?"),
            ("reporter_phone", "Agar kami bisa menghubungi Anda untuk informasi lebih lanjut, boleh kami minta nomor telepon yang bisa dihubungi?"),
            ("reporter_address", "Untuk keperluan administrasi, boleh kami tahu alamat tempat tinggal Anda saat ini?"),
            ("reporter_relationship_between", "Terakhir, boleh kami tahu apa hubungan Anda dengan korban? Ini akan membantu kami dalam proses penanganan kasus.\n\n- Keluarga\n- Tetangga\n- Teman\n- Saksi\n- Tidak Dikenal")
        ]

        # Cari field yang belum terisi dan berikan pertanyaan berikutnya
        for field, question in question_flow:
            if field not in session["report_data"]:
                session["current_field"] = field
                return question
        
        return None

    def _clean_report_data(self, report_data: dict) -> dict:
        """Membersihkan dan memformat data laporan"""
        try:
            logger.info("Cleaning report data before submission")
            
            # Helper function untuk ekstrak angka
            def extract_number(text: str) -> str:
                numbers = re.findall(r'\d+', text)
                return numbers[0] if numbers else "0"
            
            # Helper function untuk ekstrak gender
            def extract_gender(text: str) -> str:
                text_lower = text.lower()
                if any(word in text_lower for word in ["pria", "laki", "cowok", "pria"]):
                    return "Pria"
                elif any(word in text_lower for word in ["wanita", "perempuan", "cewek"]):
                    return "Wanita"
                return "Tidak Diketahui"

            # Helper function untuk ekstrak tanggal
            def extract_date(text: str) -> str:
                """Ekstrak dan format tanggal ke YYYY-MM-DD"""
                text_lower = text.lower()
                
                # Coba ekstrak pola tanggal DD/MM/YYYY atau DD-MM-YYYY
                date_pattern = r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})'
                match = re.search(date_pattern, text)
                if match:
                    day, month, year = match.groups()
                    return f"{year}-{int(month):02d}-{int(day):02d}"
                
                # Coba ekstrak tahun, bulan, dan tanggal dari teks
                year_pattern = r'20\d{2}'
                year_match = re.search(year_pattern, text)
                
                months = {
                    'januari': '01', 'februari': '02', 'maret': '03', 'april': '04',
                    'mei': '05', 'juni': '06', 'juli': '07', 'agustus': '08',
                    'september': '09', 'oktober': '10', 'november': '11', 'desember': '12',
                    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                    'mei': '05', 'jun': '06', 'jul': '07', 'agu': '08',
                    'sep': '09', 'okt': '10', 'nov': '11', 'des': '12'
                }
                
                if year_match:
                    year = year_match.group()
                    # Cari bulan
                    month = '01'  # default
                    for month_name, month_num in months.items():
                        if month_name in text_lower:
                            month = month_num
                            break
                    
                    # Cari tanggal
                    day_pattern = r'\b(\d{1,2})\b'
                    day_matches = re.findall(day_pattern, text)
                    day = '01'  # default
                    if day_matches:
                        for d in day_matches:
                            if 1 <= int(d) <= 31:
                                day = f"{int(d):02d}"
                                break
                    
                    return f"{year}-{month}-{day}"
                
                # Jika tidak bisa mengekstrak tanggal, gunakan tanggal hari ini
                today = datetime.now()
                logger.warning(f"Could not extract date from '{text}', using today's date")
                return today.strftime("%Y-%m-%d")

            cleaned_data = {
                "violence_category": report_data["violence_category"].title(),
                "chronology": report_data["chronology"].strip(),
                "date": extract_date(report_data["date"]),
                "scene": report_data["scene"].strip(),
                "victim_name": report_data["victim_name"].split("adalah")[-1].strip(),
                "victim_phone": report_data["victim_phone"].split("adalah")[-1].strip(),
                "victim_address": report_data["victim_address"].split("di")[-1].strip(),
                "victim_age": extract_number(report_data["victim_age"]),
                "victim_gender": extract_gender(report_data["victim_gender"]),
                "victim_description": report_data["victim_description"].strip(),
                "perpetrator_name": report_data["perpetrator_name"].split("adalah")[-1].strip(),
                "perpetrator_age": extract_number(report_data["perpetrator_age"]),
                "perpetrator_gender": extract_gender(report_data["perpetrator_gender"]),
                "perpetrator_description": report_data["perpetrator_description"].strip(),
                "reporter_name": report_data["reporter_name"].split("adalah")[-1].strip(),
                "reporter_phone": report_data["reporter_phone"].split("adalah")[-1].strip(),
                "reporter_address": report_data["reporter_address"].split("di")[-1].strip(),
                "reporter_relationship_between": report_data["reporter_relationship_between"].split("adalah")[-1].strip().title()
            }

            logger.info("Cleaned report data: %s", cleaned_data)
            return cleaned_data
        except Exception as e:
            logger.exception("Error cleaning report data: %s", str(e))
            return report_data

    async def _submit_report(self, session: dict) -> ChatResponse:
        """Submit laporan ke endpoint backend"""
        try:
            # Bersihkan dan format data sebelum dikirim
            report_data = self._clean_report_data(session["report_data"])

            logger.info("Submitting report with cleaned data: %s", report_data)
            logger.info("Submitting to URL: %s", f"{settings.base_api_url}/api/chatbot/report")

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    f"{settings.base_api_url}/api/chatbot/report",
                    json=report_data,
                    headers=headers,
                    ssl=False
                ) as response:
                    response_data = await response.json()
                    logger.info("Received response with status %d: %s", response.status, response_data)
                    
                    if response.status == 200 and response_data.get("success", False):
                        response_message = f"Laporan berhasil dibuat dengan nomor tiket: {response_data.get('ticket_number', 'N/A')}"
                        logger.info("Report submitted successfully with ticket: %s", response_data.get('ticket_number'))
                    else:
                        error_detail = response_data.get("detail", "Unknown error")
                        logger.error("Error submitting report: %s", error_detail)
                        logger.error("Full response: %s", response_data)
                        raise Exception(f"Error from server: {error_detail}")

                    return ChatResponse(
                        response=response_message,
                        session_id=session.get("session_id"),
                        next_steps=["Laporan telah selesai dibuat"],
                        requires_follow_up=False
                    )
        except Exception as e:
            logger.exception("Exception while submitting report: %s", str(e))
            logger.error("Session data: %s", session)
            return ChatResponse(
                response=f"Maaf, terjadi kesalahan dalam pembuatan laporan: {str(e)}. Silakan coba lagi nanti.",
                session_id=session.get("session_id"),
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

    def _detect_violence_category(self, message: str) -> str | None:
        """Deteksi kategori kekerasan dari pesan user"""
        categories = {
            "kekerasan fisik": ["kekerasan fisik", "fisik", "pukul", "tendang", "aniaya", "tampar", "siksa"],
            "kekerasan seksual": ["kekerasan seksual", "seksual", "perkosa", "leceh", "cabul"],
            "kekerasan psikis": ["kekerasan psikis", "psikis", "mental", "ancam", "intimidasi"],
            "penelantaran": ["penelantaran", "telantar", "tidak diurus"],
            "trafficking": ["trafficking", "perdagangan", "eksploitasi"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in message.lower() for keyword in keywords):
                return category
        
        return None