import sqlite3
import json
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from mistralai.client import Mistral
import config
from src.rag.vector_store import VectorStoreManager
from src.rag.database_manager import DatabaseManager
from src.rag.prompt_templates import PILLAR_DIAGNOSIS_TEMPLATE, CONVERSATIONAL_QA_TEMPLATE

class RAGEngine:
    """Core RAG Engine combining ChromaDB Vector Retrieval, SQLite Relational Catalog, and Centralized Prompt Templates."""

    def __init__(self, db_path: Path = config.SQLITE_DB_PATH):
        self.db_path = Path(db_path)
        self.vector_store = VectorStoreManager()
        self.db_manager = DatabaseManager(self.db_path)
        self.mistral_client = Mistral(api_key=config.MISTRAL_API_KEY)
        self._init_sqlite_cache()

    def _init_sqlite_cache(self):
        """Initialize SQLite caching for structured pillar recommendations."""
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
        conn.commit()
        conn.close()

    def _clean_json_string(self, raw: str) -> str:
        """Sanitizes raw LLM output to extract pure JSON block."""
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return match.group(0)
        return raw.strip()

    def analyze_single_pillar(self, emiten_code: str, pillar_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Analyzes a specific Nashta pillar for an emiten using Database-grounded Prompt Templates."""
        emiten_code = emiten_code.upper()

        # 1. Fetch Relational Data from SQLite Database
        pillar_catalog = self.db_manager.get_pillar_catalog(pillar_id)
        if not pillar_catalog:
            pillar_catalog = {
                "pillar_id": pillar_id,
                "pillar_name": pillar_id.replace("_", " ").title(),
                "icon": "📌",
                "core_capabilities": ["Solusi Terpadu Nashta"],
                "product_solutions": [{"name": f"Nashta {pillar_id.title()}", "description": "Solusi terintegrasi."}],
                "business_value": "Efisiensi operasional.",
                "sla_standard": "Standar SLA 99.9%"
            }

        emiten_profile = self.db_manager.get_emiten_profile(emiten_code)

        # 2. Check SQLite Persistent Cache
        if not force_refresh:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT problem_summary, citation_doc, citation_location, citation_quote, solutions_json, raw_response
                FROM pillar_cache
                WHERE emiten_code = ? AND pillar_id = ?
            """, (emiten_code, pillar_id))
            row = cursor.fetchone()
            conn.close()

            if row:
                try:
                    sols = json.loads(row[4]) if row[4] else []
                except Exception:
                    sols = [{"title": "Solusi Nashta", "description": str(row[4])}]

                return {
                    "emiten_code": emiten_code,
                    "pillar_id": pillar_id,
                    "pillar_name": pillar_catalog["pillar_name"],
                    "icon": pillar_catalog["icon"],
                    "problem_summary": row[0] or "",
                    "citation_doc": row[1] or f"Laporan Tahunan {emiten_code}",
                    "citation_location": row[2] or "Bab Laporan Manajemen",
                    "citation_quote": row[3] or "",
                    "solutions": sols,
                    "raw_response": row[5]
                }

        # 3. Retrieve Context from ChromaDB Vector Store
        query = f"kendala tantangan risiko inisiatif teknologi {pillar_catalog['pillar_name']} {emiten_code}"
        matched_chunks = self.vector_store.query(query, emiten_code=emiten_code, top_k=5)

        context_parts = []
        for c in matched_chunks:
            meta = c["metadata"]
            header = f"[Dokumen: {meta.get('doc_name', '')} | Tahun: {meta.get('year', '')} | Halaman: {meta.get('page_number', '')} | Bagian: {meta.get('section_header', '')}]"
            context_parts.append(f"{header}\n{c['text']}")

        context_str = "\n\n---\n\n".join(context_parts) if context_parts else "Informasi dokumen terindeks dalam basis data."

        # 4. Format Prompt using Centralized PILLAR_DIAGNOSIS_TEMPLATE
        core_caps_str = ", ".join(pillar_catalog["core_capabilities"])
        product_sols_lines = []
        for p in pillar_catalog["product_solutions"]:
            product_sols_lines.append(f"  • {p['name']}: {p['description']}")
        product_solutions_str = "\n".join(product_sols_lines)

        prompt = PILLAR_DIAGNOSIS_TEMPLATE.format(
            emiten_code=emiten_code,
            company_name=emiten_profile["company_name"],
            industry_sector=emiten_profile["industry_sector"],
            business_focus=emiten_profile["business_focus"],
            pillar_name=pillar_catalog["pillar_name"],
            core_capabilities_str=core_caps_str,
            product_solutions_str=product_solutions_str,
            business_value=pillar_catalog["business_value"],
            sla_standard=pillar_catalog["sla_standard"],
            retrieved_context=context_str
        )

        # 5. Generate with Mistral LLM
        try:
            resp = self.mistral_client.chat.complete(
                model=config.MISTRAL_CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            raw_content = resp.choices[0].message.content
            parsed = json.loads(self._clean_json_string(raw_content))

            problem_summary = str(parsed.get("problem_summary", f"Analisis kebutuhan {pillar_catalog['pillar_name']}."))
            citation_doc = str(parsed.get("citation_doc", f"Laporan Tahunan {emiten_code}"))
            citation_loc = str(parsed.get("citation_location", "Bab Laporan Manajemen"))
            citation_quote = str(parsed.get("citation_quote", "Perseroan senantiasa meningkatkan kapabilitas operasional."))
            solutions = parsed.get("solutions", [])

            # 6. Save to SQLite Cache
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO pillar_cache 
                (emiten_code, pillar_id, problem_summary, citation_doc, citation_location, citation_quote, solutions_json, raw_response, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                emiten_code,
                pillar_id,
                problem_summary,
                citation_doc,
                citation_loc,
                citation_quote,
                json.dumps(solutions, ensure_ascii=False),
                raw_content
            ))
            conn.commit()
            conn.close()

            return {
                "emiten_code": emiten_code,
                "pillar_id": pillar_id,
                "pillar_name": pillar_catalog["pillar_name"],
                "icon": pillar_catalog["icon"],
                "problem_summary": problem_summary,
                "citation_doc": citation_doc,
                "citation_location": citation_loc,
                "citation_quote": citation_quote,
                "solutions": solutions,
                "raw_response": raw_content
            }
        except Exception as e:
            print(f"Error in RAG generation for {emiten_code} ({pillar_id}): {e}")
            fallback_solutions = [
                {"title": f"Nashta {pillar_catalog['pillar_name']}", "description": f"Implementasi solusi sesuai standar {pillar_catalog['sla_standard']}."}
            ]
            return {
                "emiten_code": emiten_code,
                "pillar_id": pillar_id,
                "pillar_name": pillar_catalog["pillar_name"],
                "icon": pillar_catalog["icon"],
                "problem_summary": f"Tantangan dalam penguatan {pillar_catalog['pillar_name']} untuk mendukung efisiensi bisnis {emiten_code}.",
                "citation_doc": f"Laporan Tahunan {emiten_code}",
                "citation_location": "Bab Transformasi & Teknologi Informasi",
                "citation_quote": "Pengembangan berkelanjutan pada sistem dan teknologi.",
                "solutions": fallback_solutions,
                "raw_response": "{}"
            }

    def answer_free_query(self, emiten_code: str, user_query: str, user_id: Optional[int] = None) -> str:
        """Answers free-form questions using Persistent Database Chat Memory and CONVERSATIONAL_QA_TEMPLATE."""
        emiten_code = emiten_code.upper()

        # 1. Retrieve Chat History from Database Memory
        chat_history_str = "Tidak ada riwayat percakapan sebelumnya."
        if user_id:
            chat_history_str = self.db_manager.format_chat_history_for_prompt(user_id, emiten_code, limit=6)

        # 2. Retrieve Vector Chunks
        matched = self.vector_store.query(user_query, emiten_code=emiten_code, top_k=5)
        context_parts = []
        for c in matched:
            meta = c["metadata"]
            header = f"[Dokumen: {meta.get('doc_name', '')} | Halaman: {meta.get('page_number', '')} | Bab: {meta.get('section_header', '')}]"
            context_parts.append(f"{header}\n{c['text']}")

        context_str = "\n\n---\n\n".join(context_parts) if context_parts else "Konteks dokumen laporan tahunan."

        # 3. Retrieve Nashta Catalog Reference from SQLite
        all_pillars = self.db_manager.get_all_pillars_catalog()
        catalog_lines = []
        for p in all_pillars:
            sols_summary = ", ".join(s["name"] for s in p["product_solutions"])
            catalog_lines.append(f"• {p['icon']} {p['pillar_name']}: {sols_summary}")
        catalog_ref_str = "\n".join(catalog_lines)

        emiten_profile = self.db_manager.get_emiten_profile(emiten_code)

        # 4. Format Prompt using CONVERSATIONAL_QA_TEMPLATE
        prompt = CONVERSATIONAL_QA_TEMPLATE.format(
            emiten_code=emiten_code,
            company_name=emiten_profile["company_name"],
            industry_sector=emiten_profile["industry_sector"],
            chat_history_str=chat_history_str,
            retrieved_context=context_str,
            catalog_reference=catalog_ref_str,
            user_query=user_query
        )

        try:
            resp = self.mistral_client.chat.complete(
                model=config.MISTRAL_CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            answer = resp.choices[0].message.content

            # 5. Save to Persistent Database Chat Memory
            if user_id:
                self.db_manager.save_chat_message(user_id, emiten_code, "user", user_query)
                self.db_manager.save_chat_message(user_id, emiten_code, "assistant", answer)

            return answer
        except Exception as e:
            return f"Maaf, terjadi kendala saat memproses jawaban: {e}"

    def get_user_emiten(self, user_id: int) -> Optional[str]:
        """Get selected emiten for user from SQLite via DatabaseManager."""
        return self.db_manager.get_user_emiten(user_id)

    def set_user_emiten(self, user_id: int, emiten_code: str):
        """Save selected emiten for user into SQLite via DatabaseManager."""
        self.db_manager.set_user_emiten(user_id, emiten_code)

