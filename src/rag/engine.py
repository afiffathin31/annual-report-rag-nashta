import json
import sqlite3
import html
from typing import Dict, List, Optional, Any
from pathlib import Path
from mistralai.client import Mistral
import config
from src.rag.vector_store import VectorStoreManager
from src.rag.nashta_pillars import NASHTA_PILLARS, PILLAR_DICT

class RAGEngine:
    """Core RAG engine providing structured 10-Pillar recommendations and free Q&A."""

    def __init__(self, db_path: Path = config.SQLITE_DB_PATH):
        self.db_path = Path(db_path)
        self.vector_store = VectorStoreManager()
        self.mistral_client = Mistral(api_key=config.MISTRAL_API_KEY)
        self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite caching and session tables."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pillar_cache (
                emiten_code TEXT,
                pillar_id TEXT,
                problem_summary TEXT,
                citation_doc TEXT,
                citation_location TEXT,
                citation_quote TEXT,
                solutions_json TEXT,
                raw_response TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (emiten_code, pillar_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                user_id INTEGER PRIMARY KEY,
                selected_emiten TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def set_user_emiten(self, user_id: int, emiten_code: str):
        """Sets user selected emiten in SQLite."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_sessions (user_id, selected_emiten, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                selected_emiten = excluded.selected_emiten,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, emiten_code.upper()))
        conn.commit()
        conn.close()

    def get_user_emiten(self, user_id: int) -> Optional[str]:
        """Gets user selected emiten from SQLite."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT selected_emiten FROM user_sessions WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def _stringify(self, val: Any) -> str:
        """Helper to ensure value is a clean string (flattens lists/dicts)."""
        if isinstance(val, list):
            return "\n".join(f"• {str(item)}" for item in val)
        elif isinstance(val, dict):
            return "\n".join(f"• {k}: {v}" for k, v in val.items())
        return str(val) if val is not None else ""

    def analyze_single_pillar(self, emiten_code: str, pillar_id: str, force_refresh: bool = False) -> Dict:
        """Analyzes an emiten for a specific Nashta pillar with structured citation and solution points."""
        emiten_code = emiten_code.upper()
        pillar = PILLAR_DICT.get(pillar_id)
        if not pillar:
            raise ValueError(f"Unknown pillar ID: {pillar_id}")

        # Check SQLite Cache
        if not force_refresh:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT problem_summary, citation_doc, citation_location, citation_quote, solutions_json
                FROM pillar_cache
                WHERE emiten_code = ? AND pillar_id = ?
            """, (emiten_code, pillar_id))
            row = cursor.fetchone()
            conn.close()
            if row and row[0] and row[4]:
                try:
                    sols = json.loads(row[4])
                except Exception:
                    sols = [{"title": f"Solusi {pillar['name']}", "description": row[4]}]

                return {
                    "pillar_id": pillar_id,
                    "pillar_name": pillar["name"],
                    "icon": pillar["icon"],
                    "problem_summary": row[0],
                    "citation_doc": row[1] or f"Laporan Tahunan {emiten_code}",
                    "citation_location": row[2] or "Bagian Terkait",
                    "citation_quote": row[3] or "-",
                    "solutions": sols
                }

        # Retrieve Context Chunks
        queries = pillar["search_queries"]
        all_chunks = []
        seen_texts = set()
        for q in queries:
            matched = self.vector_store.query(q, emiten_code=emiten_code, top_k=3)
            for m in matched:
                if m["text"] not in seen_texts:
                    seen_texts.add(m["text"])
                    all_chunks.append(m)

        # Build Context String with Citation Headers
        context_parts = []
        for i, c in enumerate(all_chunks[:5]):
            meta = c["metadata"]
            header = f"[Dokumen: {meta.get('doc_name', '')} | Halaman: {meta.get('page_number', '')} | Bagian: {meta.get('section_header', '')}]"
            context_parts.append(f"{header}\n{c['text']}")

        context_str = "\n\n---\n\n".join(context_parts) if context_parts else "Tidak ada dokumen relevan yang ditemukan."

        # Prompt Mistral LLM
        prompt = f"""Anda adalah Senior IT & Management Consultant di Nashta Global Utama.
Tugas Anda adalah menganalisis dokumen Laporan Tahunan emiten {emiten_code} dan memberikan rekomendasi solusi berbasis pilar layanan Nashta: **{pillar['name']}**.

DESKRIPSI PILAR NASHTA ({pillar['name']}):
{pillar['description']}

POTONGAN DOKUMEN LAPORAN TAHUNAN ({emiten_code}):
{context_str}

INSTRUKSI FORMAT OUTPUT:
Kembalikan HANYA format JSON valid persis dengan struktur berikut:
{{
  "problem_summary": "Poin-poin kesimpulan masalah/tantangan/inisiatif yang ditemukan (gunakan bullet point '• Poin...'). Buat padat, tajam, dan langsung ke inti.",
  "citation_doc": "Nama dokumen dan tahun (contoh: Laporan Tahunan {emiten_code} 2024/2025)",
  "citation_location": "Nomor halaman dan bab/bagian dokumen tempat fakta tersebut ditemukan (contoh: Halaman 58, Bab Manajemen Risiko TI)",
  "citation_quote": "Kutipan kalimat atau frasa penting dari dokumen yang menjadi bukti fakta masalah tersebut.",
  "solutions": [
    {{
      "title": "Nama Solusi Nashta 1 (contoh: Nashta Managed SOC 24/7)",
      "description": "Rencana tindakan dan manfaat konkret yang diperoleh emiten."
    }},
    {{
      "title": "Nama Solusi Nashta 2",
      "description": "Rencana tindakan dan manfaat konkret yang diperoleh emiten."
    }}
  ]
}}

PENTING:
- Jawaban WAJIB berbasis fakta dalam potongan dokumen di atas.
- Struktur citation harus terpisah jelas antara nama dokumen, lokasi halaman, dan kutipan kalimat.
- Solusi harus berbentuk daftar (minimal 2 solusi konkret bernomor).
- Kembalikan HANYA format JSON valid tanpa kata pengantar atau penutup.
"""

        try:
            resp = self.mistral_client.chat.complete(
                model=config.MISTRAL_CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content
            parsed = json.loads(content)

            prob = self._stringify(parsed.get("problem_summary", "• Evaluasi umum terhadap sistem dan operasional perusahaan."))
            cit_doc = self._stringify(parsed.get("citation_doc", f"Laporan Tahunan {emiten_code}"))
            cit_loc = self._stringify(parsed.get("citation_location", "Bab Terkait"))
            cit_quote = self._stringify(parsed.get("citation_quote", "-"))

            raw_solutions = parsed.get("solutions", [])
            if isinstance(raw_solutions, dict):
                raw_solutions = [raw_solutions]
            elif not isinstance(raw_solutions, list):
                raw_solutions = [{"title": f"Solusi {pillar['name']}", "description": str(raw_solutions)}]

            cleaned_solutions = []
            for s in raw_solutions:
                if isinstance(s, dict):
                    cleaned_solutions.append({
                        "title": str(s.get("title", f"Solusi {pillar['name']}")),
                        "description": str(s.get("description", ""))
                    })
                elif isinstance(s, str):
                    cleaned_solutions.append({
                        "title": f"Solusi {pillar['name']}",
                        "description": s
                    })

            if not cleaned_solutions:
                cleaned_solutions = [{"title": f"Solusi {pillar['name']}", "description": "Konsultasi kapabilitas solusi Nashta."}]

            solutions_json = json.dumps(cleaned_solutions, ensure_ascii=False)

            # Save to SQLite Cache
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO pillar_cache
                (emiten_code, pillar_id, problem_summary, citation_doc, citation_location, citation_quote, solutions_json, raw_response, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (emiten_code, pillar_id, prob, cit_doc, cit_loc, cit_quote, solutions_json, content))
            conn.commit()
            conn.close()

            return {
                "pillar_id": pillar_id,
                "pillar_name": pillar["name"],
                "icon": pillar["icon"],
                "problem_summary": prob,
                "citation_doc": cit_doc,
                "citation_location": cit_loc,
                "citation_quote": cit_quote,
                "solutions": cleaned_solutions
            }
        except Exception as e:
            print(f"Error analyzing pillar {pillar_id} for {emiten_code}: {e}")
            return {
                "pillar_id": pillar_id,
                "pillar_name": pillar["name"],
                "icon": pillar["icon"],
                "problem_summary": f"• Evaluasi umum operasional emiten {emiten_code}.",
                "citation_doc": f"Laporan Tahunan {emiten_code}",
                "citation_location": "Bagian Operasional",
                "citation_quote": "-",
                "solutions": [{"title": f"Solusi {pillar['name']}", "description": "Implementasi sistem terpadu dari Nashta."}]
            }

    def analyze_all_10_pillars(self, emiten_code: str, force_refresh: bool = False) -> List[Dict]:
        """Analyzes all 10 pillars for the emiten."""
        results = []
        for pillar in NASHTA_PILLARS:
            res = self.analyze_single_pillar(emiten_code, pillar["id"], force_refresh=force_refresh)
            results.append(res)
        return results

    def answer_free_query(self, emiten_code: str, user_query: str) -> str:
        """Answers arbitrary user question about the emiten with strict citations and Nashta recommendations."""
        emiten_code = emiten_code.upper()
        matched = self.vector_store.query(user_query, emiten_code=emiten_code, top_k=5)

        context_parts = []
        for c in matched:
            meta = c["metadata"]
            header = f"[Dokumen: {meta.get('doc_name', '')} | Halaman: {meta.get('page_number', '')} | Bagian: {meta.get('section_header', '')}]"
            context_parts.append(f"{header}\n{c['text']}")

        context_str = "\n\n---\n\n".join(context_parts) if context_parts else "Tidak ada konteks yang cocok."

        prompt = f"""Anda adalah AI Advisory Assistant dari Nashta Global Utama.
Pengguna bertanya mengenai emiten **{emiten_code}**:
"{user_query}"

POTONGAN KONTEKS DOKUMEN LAPORAN TAHUNAN {emiten_code}:
{context_str}

KEMAMPUAN 10 PILAR NASHTA:
1. Managed Service (Operasional TI, Helpdesk 24/7, NOC)
2. IT Hybrid Infrastructure (Server, Data Center, DRC, Storage)
3. Business Application (ERP, CRM, Supply Chain, HRIS)
4. Cyber Security (SOC 24/7, VAPT, UU PDP Compliance)
5. Data & AI (Data Warehouse, BI Dashboard, Predictive AI)
6. Digital Business Platform (Mobile Apps, Marketplace, API Gateway)
7. IoT & Edge Computing (Smart Sensor Pabrik/Gudang, Asset Tracking)
8. Consulting & Advisory (IT Master Plan, Enterprise Architecture, Audit TI)
9. Cloud Services (Cloud Migration, Multi-Cloud, FinOps, DevOps)
10. Bootcamp (Corporate IT Training, Talent Upskilling)

FORMAT STRUKTUR JAWABAN:
Sajikan jawaban Anda secara rapi dengan 3 bagian wajib:

📋 **RINGKASAN JAWABAN:**
(Poin-poin penjelasan langsung menjawab pertanyaan pengguna secara jelas)

📖 **SUMBER DOKUMEN (CITATION):**
📄 **Dokumen:** (Nama dokumen dan tahun)
📑 **Halaman / Bab:** (Halaman X, Bagian Y)
💬 **Kutipan Kunci:** "(Kutipan kalimat asli dokumen)"

💡 **REKOMENDASI SOLUSI NASHTA:**
1️⃣ **[Nama Solusi Nashta 1]**: (Penjelasan implementasi & manfaat nyata)
2️⃣ **[Nama Solusi Nashta 2]**: (Penjelasan implementasi & manfaat nyata)
"""

        try:
            resp = self.mistral_client.chat.complete(
                model=config.MISTRAL_CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Maaf, terjadi kendala dalam memproses pertanyaan Anda: {e}"
