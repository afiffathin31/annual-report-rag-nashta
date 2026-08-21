import sqlite3
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
import config

class DatabaseManager:
    """Manages SQLite relational database for Nashta Service Catalog, Emiten Profiles, and Persistent Chat Memory."""

    def __init__(self, db_path: Path = config.SQLITE_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
        self._seed_data()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a SQLite connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initializes all relational schema tables."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. Nashta Service Catalog Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nashta_service_catalog (
                pillar_id TEXT PRIMARY KEY,
                pillar_name TEXT NOT NULL,
                icon TEXT NOT NULL,
                category TEXT NOT NULL,
                core_capabilities TEXT NOT NULL,
                product_solutions TEXT NOT NULL,
                business_value TEXT NOT NULL,
                sla_standard TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Emiten Profiles Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emiten_profiles (
                emiten_code TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                industry_sector TEXT NOT NULL,
                business_focus TEXT NOT NULL,
                key_tech_stack TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Persistent Chat Memory Table (Multi-turn conversational history)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                emiten_code TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. User Session Tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                user_id INTEGER PRIMARY KEY,
                current_emiten TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def _seed_data(self):
        """Seed official Nashta 10 Pillars and Emiten Profiles if empty."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if catalog is already seeded
        cursor.execute("SELECT COUNT(*) as cnt FROM nashta_service_catalog")
        if cursor.fetchone()["cnt"] == 0:
            catalog_items = [
                (
                    "managed_service",
                    "IT Managed Services",
                    "🛠️",
                    "Operations & Support",
                    json.dumps(["24/7 IT Operations Center", "Level 1-3 Technical Support", "Infrastructure Monitoring", "SLA-Driven Maintenance"]),
                    json.dumps([
                        {"name": "Nashta Managed Operations 24/7", "description": "Layanan pemeliharaan dan monitoring proaktif infrastruktur TI end-to-end dengan jaminan SLA 99.9%."},
                        {"name": "Dedicated On-site & Remote Engineers", "description": "Penyediaan tenaga ahli TI tersertifikasi untuk operasional harian dan troubleshooting cepat."},
                        {"name": "IT Service Desk & Incident Management", "description": "Manajemen tiket insiden berbasis ITIL v4 untuk standardisasi alur penanganan masalah sistem."}
                    ]),
                    "Menurunkan beban OPEX hingga 35% dan menjamin stabilitas ketersediaan sistem bisnis kritikal.",
                    "SLA Respon <15 menit, Uptime 99.9%"
                ),
                (
                    "hybrid_infra",
                    "IT Hybrid Infrastructure",
                    "🖥️",
                    "Infrastructure & Hardware",
                    json.dumps(["Data Center Modernization", "SD-WAN & Network Architecture", "HCI Deployment", "Disaster Recovery Center (DRC)"]),
                    json.dumps([
                        {"name": "Nashta Hyperconverged Infrastructure (HCI)", "description": "Konsolidasi server fisik, storage, dan komputasi dalam arsitektur virtual terdistribusi yang fleksibel."},
                        {"name": "SD-WAN & High-Availability Network", "description": "Modernisasi jaringan WAN antar cabang/pabrik dengan keamanan enkripsi dan failover otomatis."},
                        {"name": "DRC as a Service (Disaster Recovery)", "description": "Pusat pemulihan bencana berbasis hybrid cloud dengan RPO <1 jam dan RTO <2 jam."}
                    ]),
                    "Meningkatkan skalabilitas komputasi dan menjamin kelangsungan bisnis saat terjadi gangguan fisik.",
                    "RPO <1 Jam, RTO <2 Jam"
                ),
                (
                    "business_app",
                    "Business Application Development",
                    "💼",
                    "Enterprise Software",
                    json.dumps(["Custom ERP & CRM Integration", "Supply Chain Management (SCM)", "Core Banking/Hospital Systems", "API Middleware"]),
                    json.dumps([
                        {"name": "Nashta Enterprise SCM & ERP Customization", "description": "Pengembangan dan kustomisasi modul ERP terpadu untuk integrasi rantai pasok dan inventaris real-time."},
                        {"name": "Hospital Information System (HIS) Integration", "description": "Sistem informasi rumah sakit dan farmasi terintegrasi rekam medis elektronik (RME)."},
                        {"name": "Enterprise Service Bus (ESB) & API Middleware", "description": "Platform integrasi data antar aplikasi legacy dan microservices multi-anak perusahaan."}
                    ]),
                    "Menghilangkan silo proses bisnis dan mempercepat siklus transaksi operasional.",
                    "End-to-End API Integration"
                ),
                (
                    "cyber_security",
                    "Cyber Security Management",
                    "🛡️",
                    "Security & Compliance",
                    json.dumps(["Managed SOC 24/7", "VAPT & Threat Assessment", "UU PDP & ISO 27001 Compliance", "Privilege Access Management (PAM)"]),
                    json.dumps([
                        {"name": "Nashta Managed SOC 24/7 & Threat Intelligence", "description": "Pusat pemantauan ancaman siber 24 jam dengan deteksi dini anomali dan respon insiden otomatis."},
                        {"name": "Vulnerability Assessment & Penetration Testing (VAPT)", "description": "Audit penetrasi berkala pada web, mobile app, dan infrastruktur perimeter korporasi."},
                        {"name": "Data Privacy & UU PDP Compliance Framework", "description": "Pendampingan tata kelola perlindungan data pribadi sesuai UU PDP No. 27/2022 dan ISO 27701."}
                    ]),
                    "Melindungi aset data kritikal dari serangan ransomware dan menjamin kepatuhan hukum regulator.",
                    "SOC Monitoring 24/7/365, ISO 27001 Certified"
                ),
                (
                    "data_ai",
                    "Data Analytics & Artificial Intelligence",
                    "📊",
                    "Data & AI",
                    json.dumps(["Enterprise Data Lakehouse", "Predictive Analytics & Forecasting", "Computer Vision & OCR", "Generative AI Agents"]),
                    json.dumps([
                        {"name": "Nashta Unified Data Lakehouse", "description": "Konsolidasi data multi-sumber (ERP, CRM, IoT) ke arsitektur data lakehouse modern untuk single-source-of-truth."},
                        {"name": "Computer Vision & AI Quality Inspection", "description": "Otomasi inspeksi cacat produk manufaktur dan pengenalan dokumen medis/klaim via AI Vision."},
                        {"name": "Enterprise Generative AI & Knowledge Assistant", "description": "Implementasi sistem RAG dan asisten AI internal berbasis data korporasi untuk akselerasi keputusan."}
                    ]),
                    "Mengubah data pasif menjadi wawasan prediktif dan otomasi cerdas berstandar tinggi.",
                    "Real-time ETL, High Model Accuracy"
                ),
                (
                    "digital_platform",
                    "Digital Platform & Mobile Solutions",
                    "📱",
                    "Digital Experience",
                    json.dumps(["Omnichannel SuperApp", "Open API Gateway", "Customer Portal & Loyalty", "Payment Gateway Integration"]),
                    json.dumps([
                        {"name": "Nashta Omnichannel Customer SuperApp", "description": "Aplikasi seluler berkinerja tinggi untuk layanan nasabah/pasien dengan UI/UX modern."},
                        {"name": "Open API Management Platform", "description": "Manajemen API terstandarisasi untuk kolaborasi ekosistem kemitraan B2B dan B2B2C."},
                        {"name": "Customer Loyalty & Self-Service Portal", "description": "Portal mandiri pelanggan untuk pemesanan, klaim, dan tracking transaksi real-time."}
                    ]),
                    "Meningkatkan kepuasan retensi pelanggan dan memperluas kanal pendapatan digital.",
                    "Mobile Native/Flutter, 99.95% Availability"
                ),
                (
                    "iot_edge",
                    "IoT & Smart Edge Computing",
                    "📡",
                    "IoT & Automation",
                    json.dumps(["Industrial IoT Telemetry", "Smart Factory Monitoring", "Cold-Chain Logistics Tracking", "Edge Computing Nodes"]),
                    json.dumps([
                        {"name": "Nashta Industrial IoT Telemetry", "description": "Sensor pintar pemantau suhu, getaran, dan utilisasi mesin pabrik secara real-time."},
                        {"name": "Cold-Chain Monitoring System", "description": "Pelacakan suhu dan kelembaban distribusi produk farmasi/makanan secara presisi."},
                        {"name": "Edge AI Gateway", "description": "Komputasi analitik langsung di perangkat pabrik tanpa bergantung pada latensi cloud."}
                    ]),
                    "Mencegah kerusakan mesin mendadak (predictive maintenance) dan menjaga kualitas produk higienis.",
                    "Sensor Data Latency <1s"
                ),
                (
                    "consulting_advisory",
                    "IT Consulting & Strategic Advisory",
                    "🧭",
                    "Strategy & Governance",
                    json.dumps(["IT Master Plan (ITMP)", "Enterprise Architecture Design", "COBIT & TOGAF Alignment", "IT Governance Audit"]),
                    json.dumps([
                        {"name": "IT Master Plan (ITMP) Formulation", "description": "Penyusunan peta jalan strategis teknologi 3-5 tahun yang selaras dengan sasaran ekspansi bisnis."},
                        {"name": "IT Governance & Risk Management Advisory", "description": "Standardisasi tata kelola TI berbasis COBIT 2019, ITIL, dan regulasi OJK/Kemenkes."},
                        {"name": "Enterprise Architecture Blueprints", "description": "Rancang bangun arsitektur aplikasi dan data korporasi untuk skalabilitas jangka panjang."}
                    ]),
                    "Menyelaraskan investasi belanja TI dengan ROI bisnis nyata dan kepatuhan audit.",
                    "TOGAF & COBIT Certified Consultants"
                ),
                (
                    "cloud_services",
                    "Cloud & DevOps Solutions",
                    "☁️",
                    "Cloud & Platform",
                    json.dumps(["Cloud Migration & Architecture", "Kubernetes & Microservices", "CI/CD Automation", "Cloud FinOps & Cost Optimization"]),
                    json.dumps([
                        {"name": "Nashta Cloud Migration & Landing Zone", "description": "Migrasi beban kerja on-premise ke multi-cloud (AWS, GCP, Azure, Local Cloud) tanpa downtime."},
                        {"name": "Cloud FinOps & Cost Optimization", "description": "Audit dan optimasi arsitektur cloud untuk memangkas pemborosan tagihan bulanan hingga 30%."},
                        {"name": "CI/CD Automation & Container Orchestration", "description": "Otomatisasi deployment aplikasi berbasis Docker dan Kubernetes untuk rilis fitur yang cepat dan aman."}
                    ]),
                    "Mempercepat time-to-market aplikasi baru dan menekan pemborosan biaya langganan cloud.",
                    "Zero-Downtime Migration"
                ),
                (
                    "bootcamp",
                    "Talent Incubation & IT Bootcamp",
                    "🎓",
                    "People & Capability",
                    json.dumps(["Custom Corporate Upskilling", "Full-stack & AI Engineering", "Cybersecurity Training", "Dedicated IT Talent Sourcing"]),
                    json.dumps([
                        {"name": "Nashta Corporate Tech Academy", "description": "Program pelatihan dan sertifikasi intensif untuk tim internal dalam bidang Cloud, AI, dan Cyber Security."},
                        {"name": "Dedicated Squad Incubation", "description": "Penyediaan tim developer dan engineer yang telah dilatih khusus sesuai kebutuhan spesifik stack teknologi klien."},
                        {"name": "Executive Digital Leadership Workshop", "description": "Pelatihan strategis bagi level manajerial mengenai pemanfaatan GenAI dan transformasi digital."}
                    ]),
                    "Menutup kesenjangan keahlian digital (digital talent gap) dan mempercepat adopsi teknologi baru.",
                    "Curriculum Customized per Industry"
                )
            ]
            cursor.executemany("""
                INSERT INTO nashta_service_catalog 
                (pillar_id, pillar_name, icon, category, core_capabilities, product_solutions, business_value, sla_standard)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, catalog_items)

        # Check if emiten profiles are seeded
        cursor.execute("SELECT COUNT(*) as cnt FROM emiten_profiles")
        if cursor.fetchone()["cnt"] == 0:
            emiten_items = [
                ("KLBF", "PT Kalbe Farma Tbk", "Farmasi & Kesehatan", "Manufaktur obat, produk nutrisi, distribusi farmasi, dan layanan diagnostik digital.", "ERP SAP, VisionX AI, PACS Elvasoft, Hybrid Cloud"),
                ("SIDO", "PT Industri Jamu dan Farmasi Sido Muncul Tbk", "Consumer Goods & Herbal", "Produksi herbal Tolak Angin, minuman energi, ekstraksi minyak atsiri, dan ekspor global.", "SCM ERP, IoT Mesin Ekstraksi Pabrik, Automated Packaging"),
                ("BANK", "PT Bank Aladin Syariah Tbk", "Perbankan Digital Syariah", "Layanan perbankan digital tanpa kantor fisik (B2C & B2B2C), integrasi ritel minimarket.", "Core Banking Cloud-Native, Open API, Microservices, SD-WAN"),
                ("CARE", "PT Metro Healthcare Indonesia Tbk", "Layanan Kesehatan & Rumah Sakit", "Jaringan rumah sakit terpadu, poliklinik, dan fasilitas medis spesialis.", "Hospital Information System (HIS), Radiologi Digital, Local Servers"),
                ("HEAL", "PT Medikaloka Hermina Tbk", "Layanan Kesehatan Ibu & Anak", "Jaringan 45+ rumah sakit umum Hermina dengan fokus spesialisasi maternal dan anak.", "Hermina Central HIS, Telemedicine Mobile App, Electronic Medical Records (EMR)"),
                ("PDSB", "PT Bank Syariah Bukopin Tbk (KB Bank Syariah)", "Perbankan Syariah & Finansial", "Layanan perbankan komersial, pembiayaan syariah, dan modernisasi kanal digital.", "Core Banking Syariah, Mobile Banking, Open API, SD-WAN")
            ]
            cursor.executemany("""
                INSERT INTO emiten_profiles
                (emiten_code, company_name, industry_sector, business_focus, key_tech_stack)
                VALUES (?, ?, ?, ?, ?)
            """, emiten_items)

        conn.commit()
        conn.close()

    # --- Query Methods ---

    def get_pillar_catalog(self, pillar_id: str) -> Optional[Dict[str, Any]]:
        """Fetch specific pillar details from SQLite database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM nashta_service_catalog WHERE pillar_id = ?", (pillar_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "pillar_id": row["pillar_id"],
            "pillar_name": row["pillar_name"],
            "icon": row["icon"],
            "category": row["category"],
            "core_capabilities": json.loads(row["core_capabilities"]),
            "product_solutions": json.loads(row["product_solutions"]),
            "business_value": row["business_value"],
            "sla_standard": row["sla_standard"]
        }

    def get_all_pillars_catalog(self) -> List[Dict[str, Any]]:
        """Fetch all 10 pillars catalog from SQLite database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM nashta_service_catalog ORDER BY ROWID")
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                "pillar_id": row["pillar_id"],
                "pillar_name": row["pillar_name"],
                "icon": row["icon"],
                "category": row["category"],
                "core_capabilities": json.loads(row["core_capabilities"]),
                "product_solutions": json.loads(row["product_solutions"]),
                "business_value": row["business_value"],
                "sla_standard": row["sla_standard"]
            })
        return result

    def get_emiten_profile(self, emiten_code: str) -> Dict[str, str]:
        """Fetch emiten profile from SQLite database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM emiten_profiles WHERE emiten_code = ?", (emiten_code.upper(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "emiten_code": row["emiten_code"],
                "company_name": row["company_name"],
                "industry_sector": row["industry_sector"],
                "business_focus": row["business_focus"],
                "key_tech_stack": row["key_tech_stack"]
            }
        return {
            "emiten_code": emiten_code.upper(),
            "company_name": f"Emiten {emiten_code.upper()}",
            "industry_sector": "Korporasi Publik",
            "business_focus": "Operasional bisnis terdaftar BEI",
            "key_tech_stack": "Enterprise Systems"
        }

    # --- Persistent Chat Memory Methods ---

    def save_chat_message(self, user_id: int, emiten_code: str, role: str, message: str):
        """Saves a user or assistant message to persistent SQLite chat memory."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_memory (user_id, emiten_code, role, message)
            VALUES (?, ?, ?, ?)
        """, (user_id, emiten_code.upper(), role, message))
        conn.commit()
        conn.close()

    def get_recent_chat_history(self, user_id: int, emiten_code: str, limit: int = 6) -> List[Dict[str, str]]:
        """Retrieves recent conversation turns for user & emiten from SQLite database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, message, created_at FROM chat_memory
            WHERE user_id = ? AND emiten_code = ?
            ORDER BY id DESC LIMIT ?
        """, (user_id, emiten_code.upper(), limit))
        rows = cursor.fetchall()
        conn.close()

        history = []
        for r in reversed(rows):
            history.append({
                "role": r["role"],
                "message": r["message"],
                "time": r["created_at"]
            })
        return history

    def format_chat_history_for_prompt(self, user_id: int, emiten_code: str, limit: int = 6) -> str:
        """Formats recent chat history as a clean string block for prompt injection."""
        history = self.get_recent_chat_history(user_id, emiten_code, limit=limit)
        if not history:
            return "Tidak ada riwayat percakapan sebelumnya (percakapan baru)."
        
        lines = []
        for h in history:
            role_label = "Pengguna" if h["role"] == "user" else "Asisten Nashta"
            lines.append(f"{role_label}: {h['message']}")
        return "\n".join(lines)

    def clear_chat_history(self, user_id: int, emiten_code: str):
        """Clears chat history for a user and emiten session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_memory WHERE user_id = ? AND emiten_code = ?", (user_id, emiten_code.upper()))
        conn.commit()
        conn.close()

    # --- User Session Management ---

    def get_user_emiten(self, user_id: int) -> Optional[str]:
        """Get currently selected emiten for user from SQLite."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT current_emiten FROM user_sessions WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row["current_emiten"]:
                conn.close()
                return row["current_emiten"]
        except Exception:
            pass

        try:
            cursor.execute("SELECT selected_emiten FROM user_sessions WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row["selected_emiten"]:
                conn.close()
                return row["selected_emiten"]
        except Exception:
            pass

        conn.close()
        return None

    def set_user_emiten(self, user_id: int, emiten_code: str):
        """Save selected emiten for user into SQLite."""
        conn = self.get_connection()
        cursor = conn.cursor()
        emiten_code = emiten_code.upper()
        try:
            cursor.execute("""
                INSERT INTO user_sessions (user_id, current_emiten, selected_emiten, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET 
                    current_emiten=excluded.current_emiten,
                    selected_emiten=excluded.selected_emiten,
                    updated_at=CURRENT_TIMESTAMP
            """, (user_id, emiten_code, emiten_code))
        except Exception:
            cursor.execute("""
                INSERT OR REPLACE INTO user_sessions (user_id, current_emiten, selected_emiten, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, emiten_code, emiten_code))
        conn.commit()
        conn.close()

