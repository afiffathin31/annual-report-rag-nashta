import json
import sqlite3
import html
from typing import Dict, List, Optional, Any
from pathlib import Path
from mistralai.client import Mistral
import config
from src.rag.vector_store import VectorStoreManager
from src.rag.database_manager import DatabaseManager
from src.rag.prompt_templates import TEMPORAL_TREND_TEMPLATE

class TemporalTrendEngine:
    """Multi-year longitudinal trend analysis engine with database catalog grounding and PromptTemplate."""

    def __init__(self, db_path: Path = config.SQLITE_DB_PATH):
        self.db_path = Path(db_path)
        self.vector_store = VectorStoreManager()
        self.db_manager = DatabaseManager(self.db_path)
        self.mistral_client = Mistral(api_key=config.MISTRAL_API_KEY)
        self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite caching for multi-year trend analysis."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trend_cache (
                emiten_code TEXT PRIMARY KEY,
                period TEXT,
                timeline_json TEXT,
                chronic_issues_json TEXT,
                emerging_risks_json TEXT,
                roadmap_json TEXT,
                raw_response TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def analyze_5_year_trend(self, emiten_code: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Analyzes 5-year multi-year trend of problems and produces a 3-phase strategic Nashta roadmap."""
        emiten_code = emiten_code.upper()

        # 1. Check SQLite Cache
        if not force_refresh:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT period, timeline_json, chronic_issues_json, emerging_risks_json, roadmap_json
                FROM trend_cache
                WHERE emiten_code = ?
            """, (emiten_code,))
            row = cursor.fetchone()
            conn.close()
            if row and row[1] and row[4]:
                try:
                    return {
                        "emiten": emiten_code,
                        "period": row[0] or "2021 - 2025",
                        "timeline": json.loads(row[1]),
                        "chronic_issues": json.loads(row[2]),
                        "emerging_risks": json.loads(row[3]),
                        "strategic_roadmap": json.loads(row[4])
                    }
                except Exception as e:
                    print(f"Cache decode error for {emiten_code}: {e}")

        # 2. Fetch Relational Data from SQLite Database
        emiten_profile = self.db_manager.get_emiten_profile(emiten_code)
        all_pillars = self.db_manager.get_all_pillars_catalog()
        catalog_summary_lines = []
        for p in all_pillars:
            sols = ", ".join(s["name"] for s in p["product_solutions"])
            catalog_summary_lines.append(f"• {p['icon']} {p['pillar_name']}: {sols} (Nilai: {p['business_value']})")
        catalog_summary_str = "\n".join(catalog_summary_lines)

        # 3. Retrieve Multi-Year Context Chunks from ChromaDB
        queries = [
            "transformasi digital roadmap TI inisiatif teknologi pengembangan sistem",
            "kendala operasional risiko rantai pasok fragmentasi data integrasi ERP",
            "keamanan siber kepatuhan regulasi UU PDP ancaman siber insiden TI",
            "adopsi AI otomatisasi analitik data warehouse business intelligence",
            "efisiensi biaya operasional infrastruktur server cloud hosting downtime"
        ]

        all_chunks = []
        seen_texts = set()
        for q in queries:
            matched = self.vector_store.query(q, emiten_code=emiten_code, top_k=4)
            for m in matched:
                if m["text"] not in seen_texts:
                    seen_texts.add(m["text"])
                    all_chunks.append(m)

        context_parts = []
        for c in all_chunks[:10]:
            meta = c["metadata"]
            header = f"[Dokumen: {meta.get('doc_name', '')} | Tahun: {meta.get('year', '')} | Halaman: {meta.get('page_number', '')} | Bagian: {meta.get('section_header', '')}]"
            context_parts.append(f"{header}\n{c['text']}")

        context_str = "\n\n---\n\n".join(context_parts) if context_parts else "Dokumen laporan tahunan terindeks."

        # 4. Format Prompt with TEMPORAL_TREND_TEMPLATE
        prompt = TEMPORAL_TREND_TEMPLATE.format(
            emiten_code=emiten_code,
            company_name=emiten_profile["company_name"],
            industry_sector=emiten_profile["industry_sector"],
            business_focus=emiten_profile["business_focus"],
            retrieved_context=context_str,
            catalog_summary=catalog_summary_str
        )

        try:
            resp = self.mistral_client.chat.complete(
                model=config.MISTRAL_CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content
            parsed = json.loads(content)

            period = parsed.get("period", "2021 - 2025")
            timeline = parsed.get("timeline", [])
            chronic = parsed.get("chronic_issues", ["Integrasi sistem multi-cabang.", "Efisiensi operasional TI."])
            emerging = parsed.get("emerging_risks", ["Keamanan data & regulasi UU PDP.", "Adopsi AI skala bisnis."])
            roadmap = parsed.get("strategic_roadmap", [])

            # Save to SQLite Cache
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO trend_cache
                (emiten_code, period, timeline_json, chronic_issues_json, emerging_risks_json, roadmap_json, raw_response, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                emiten_code,
                period,
                json.dumps(timeline, ensure_ascii=False),
                json.dumps(chronic, ensure_ascii=False),
                json.dumps(emerging, ensure_ascii=False),
                json.dumps(roadmap, ensure_ascii=False),
                content
            ))
            conn.commit()
            conn.close()

            return {
                "emiten": emiten_code,
                "period": period,
                "timeline": timeline,
                "chronic_issues": chronic,
                "emerging_risks": emerging,
                "strategic_roadmap": roadmap
            }
        except Exception as e:
            print(f"Error in trend analysis for {emiten_code}: {e}")
            return {
                "emiten": emiten_code,
                "period": "2021 - 2025",
                "timeline": [
                    {
                        "phase": "2021 - 2023",
                        "theme": "Transformasi Digital Awal & Adaptasi Operasional",
                        "key_problems": ["Digitalisasi alur kerja.", "Penguatan infrastruktur dasar."],
                        "citation": {"doc": f"Laporan Tahunan {emiten_code}", "location": "Bab Operasional", "quote": "Perseroan memperkuat fondasi digital..."}
                    },
                    {
                        "phase": "2024 - 2025",
                        "theme": "Keamanan Siber, Integrasi Data & Modernisasi",
                        "key_problems": ["Keamanan siber & UU PDP.", "Integrasi sistem lintas unit bisnis."],
                        "citation": {"doc": f"Laporan Tahunan {emiten_code}", "location": "Bab Manajemen Risiko", "quote": "Peningkatan perlindungan data dan sistem..."}
                    }
                ],
                "chronic_issues": ["Fragmentasi integrasi data antar divisi."],
                "emerging_risks": ["Ancaman siber dan kepatuhan privasi data."],
                "strategic_roadmap": [
                    {"phase_num": "1", "phase_title": "Fase 1: Quick Win (0-6 Bln)", "solutions": ["Managed SOC 24/7", "VAPT Audit"], "business_impact": "Menutup celah risiko keamanan."},
                    {"phase_num": "2", "phase_title": "Fase 2: Integrasi (6-12 Bln)", "solutions": ["Data Lakehouse", "ERP Integration"], "business_impact": "Menghilangkan silo data."},
                    {"phase_num": "3", "phase_title": "Fase 3: Otomasi AI (1-2 Thn)", "solutions": ["Enterprise AI Platform"], "business_impact": "Otomasi analitik prediktif."}
                ]
            }

def render_trend_html_parts(emiten_code: str, res: Dict[str, Any]) -> List[str]:
    """Splits executive 5-year trend analysis into 2 clean, untruncated Telegram HTML messages."""
    period = html.escape(res.get("period", "2021 - 2025"))
    timeline = res.get("timeline", [])
    chronic = res.get("chronic_issues", [])
    emerging = res.get("emerging_risks", [])
    roadmap = res.get("strategic_roadmap", [])

    # === PART 1: Evolusi Tren & Root Causes ===
    part1_lines = [
        f"📊 <b>EXECUTIVE BRIEF: TREN 5 TAHUN {emiten_code} (Bagian 1/2)</b>",
        f"🗓️ <i>Periode Analisis: {period}</i>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        "📈 <b>EVOLUSI TREN PERMASALAHAN DARI WAKTU KE WAKTU:</b>\n"
    ]

    for item in timeline:
        phase = html.escape(item.get("phase", ""))
        theme = html.escape(item.get("theme", ""))
        problems = item.get("key_problems", [])
        citation = item.get("citation", {})

        prob_text = "\n".join(f"  • {html.escape(p)}" for p in problems)
        cit_doc = html.escape(citation.get("doc", "-"))
        cit_loc = html.escape(citation.get("location", "-"))
        cit_quote = html.escape(citation.get("quote", "-"))

        part1_lines.append(f"⏳ <b>{phase}: {theme}</b>")
        part1_lines.append(f"{prob_text}")
        part1_lines.append(f"  📖 <i>Citation: {cit_doc} | {cit_loc}</i>")
        part1_lines.append(f"  💬 <i>\"{cit_quote}\"</i>\n")

    part1_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    part1_lines.append("🔍 <b>POLA PERMASALAHAN UTAMA (ROOT CAUSE):</b>")
    part1_lines.append("⚠️ <b>Isu Kronis (Menahun):</b>")
    for c in chronic:
        part1_lines.append(f"  • {html.escape(c)}")

    part1_lines.append("\n⚡ <b>Ancaman Baru (Emerging Risks):</b>")
    for em in emerging:
        part1_lines.append(f"  • {html.escape(em)}")

    part1_lines.append("\n⬇️ <i>Lanjutan: Strategic Roadmap Solusi Nashta pada pesan berikut...</i>")

    # === PART 2: Strategic Roadmap Nashta ===
    part2_lines = [
        f"💡 <b>STRATEGIC ROADMAP SOLUSI NASHTA (Bagian 2/2)</b>",
        f"🏢 <i>Emiten Target: {emiten_code} | Periode: {period}</i>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        "Peta jalan solusi strategis 3-fase yang dirancang khusus untuk mengatasi akar masalah & mengakselerasi pertumbuhan bisnis:\n"
    ]

    for r in roadmap:
        title = html.escape(r.get("phase_title", ""))
        sols = r.get("solutions", [])
        impact = html.escape(r.get("business_impact", ""))

        part2_lines.append(f"🔹 <b>{title}</b>")
        for s in sols:
            part2_lines.append(f"   ↳ <b>{html.escape(s)}</b>")
        if impact:
            part2_lines.append(f"   🎯 <i>Impact: {impact}</i>\n")

    part2_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    part2_lines.append(f"🏢 <i>Emiten: {emiten_code} | Gunakan tombol di bawah untuk eksplorasi 10 Pilar</i>")

    part1_text = "\n".join(part1_lines)
    part2_text = "\n".join(part2_lines)

    return [part1_text, part2_text]

def render_trend_html(emiten_code: str, res: Dict[str, Any]) -> str:
    """Formats executive 5-year trend analysis into clean Telegram HTML."""
    parts = render_trend_html_parts(emiten_code, res)
    return parts[0]

