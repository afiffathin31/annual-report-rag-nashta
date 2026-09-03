"""AI Assistant RAG & Business Intelligence Copilot for Nashta 10 Pillars (True Document Retrieval)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.catalog import catalog_manager
from backend.evidence_engine import FINANCIAL_NOISE_TERMS, evidence_engine
from backend.llm_provider import llm_provider
from backend.rag_indexer import rag_indexer
from backend.scoring_engine import scoring_engine

logger = logging.getLogger("rag_engine")

PILLAR_KEYWORDS_MAP = {
    1: ["managed service", "sla", "helpdesk", "noc", "support 24/7", "pemeliharaan", "maintenance", "outsourcing it"],
    2: ["hybrid infrastructure", "infrastruktur", "sd-wan", "datacenter", "data center", "jaringan", "konektivitas", "lan", "wan", "server"],
    3: ["business app", "aplikasi bisnis", "core banking", "finacle", "erp", "sap", "crm", "workflow", "otomatisasi", "simrs", "rekam medis"],
    4: ["cyber security", "keamanan siber", "keamanan informasi", "soc", "vapt", "ransomware", "pdp", "uu pdp", "iso 27001", "kebocoran data", "firewall", "waf"],
    5: ["data & ai", "lakehouse", "data warehouse", "analytics", "business intelligence", "bi", "artificial intelligence", "machine learning", "big data", "dashboard"],
    6: ["digital business platform", "superapp", "super app", "mobile banking", "byond", "aladin app", "open api", "api gateway", "omnichannel"],
    7: ["iot", "internet of things", "sensor", "telemetry", "cold chain", "smart asset", "tracking", "edge computing"],
    8: ["consulting", "advisory", "it master plan", "it roadmap", "tata kelola ti", "governance", "cobit", "togaf", "konsultan ti"],
    9: ["cloud services", "cloud", "multi-cloud", "aws", "gcp", "azure", "migrasi cloud", "finops", "cloud dr", "draas", "disaster recovery"],
    10: ["bootcamp", "pelatihan", "talent", "sdm ti", "upskilling", "academy", "devsecops training", "sertifikasi ti", "enablement"],
}

GREETING_TRIGGERS = [
    "hai", "halo", "hello", "hi", "pagi", "siang", "sore", "malam",
    "assalamualaikum", "apa kabar", "siapa kamu", "siapa anda", "bantu saya", "tolong bantu"
]


class AIAssistantRAGEngine:
    """True RAG Assistant with Hybrid Generative LLM & Deterministic Precision Synthesis."""

    def __init__(self) -> None:
        self.pillars = catalog_manager.get_pillars()

    def process_chat(self, query: str, active_emiten: Optional[str] = None) -> Dict[str, Any]:
        q_lower = query.lower().strip()
        active_code = active_emiten.upper() if active_emiten else None

        # Auto-detect emiten in query if not explicitly passed
        if not active_code:
            for issuer in catalog_manager.get_all_issuers():
                if issuer["code"].lower() in q_lower or issuer["name"].lower() in q_lower:
                    active_code = issuer["code"]
                    break

        target_code = active_code or "BRIS"
        analysis = scoring_engine.analyze_issuer(target_code)
        issuer_info = analysis.get("issuer", {})
        weaknesses = analysis.get("verified_weaknesses", [])
        strategic_recs = analysis.get("strategic_recommendations", [])

        # 0. Intent: Greetings / Small Talk / Conversational Welcome
        if q_lower in GREETING_TRIGGERS or any(q_lower == gt or q_lower.startswith(gt + " ") or q_lower.startswith(gt + ",") for gt in GREETING_TRIGGERS):
            return self._answer_greeting(target_code, issuer_info)

        # Retrieve matching chunks from RAG index with strict noise gatekeeping
        chunks = rag_indexer.get_chunks_for_emiten(target_code)
        retrieved_chunks = self._search_chunks(chunks, query, target_code=target_code)

        # 1. Intent: Proposal / Pitch Deck Generation
        if any(w in q_lower for w in ["proposal", "pitch", "penawaran", "buatkan proposal"]):
            return self.generate_proposal(target_code)

        # If a live Generative LLM is configured (Gemini / OpenAI / Groq / Ollama), use it!
        if llm_provider.is_llm_available():
            llm_res = self._generate_llm_rag_answer(query, target_code, issuer_info, retrieved_chunks, strategic_recs, analysis)
            if llm_res:
                return llm_res

        # --- Deterministic Expert Fallback (Offline Mode) ---
        # 2. Intent: Specific Finding / Quote Solution Inquiry (From "Analisis dengan AI Copilot" Button)
        if ("bagaimana nashta dapat menawarkan solusi" in q_lower or "bagaimana solusi" in q_lower) and ("halaman" in q_lower or "temuan" in q_lower or '"' in query or '“' in query):
            return self._answer_quote_solution_inquiry(target_code, issuer_info, query, analysis)

        # 3. Intent: Specific Pillar Inquiries (e.g. Cyber Security, Cloud, Data & AI)
        matched_pillar_id = self._detect_pillar_inquiry(q_lower)
        if matched_pillar_id:
            return self._answer_pillar_inquiry(target_code, issuer_info, matched_pillar_id, analysis, retrieved_chunks)

        # 4. Intent: Technology Stack & Enterprise Architecture
        if any(w in q_lower for w in ["teknologi", "tech stack", "arsitektur", "sistem", "software", "infrastruktur eksisting"]):
            return self._answer_tech_stack_inquiry(target_code, issuer_info, analysis, retrieved_chunks)

        # 5. Intent: Weaknesses / Gaps / Diagnoses / Evidence
        if any(w in q_lower for w in ["kelemahan", "weakness", "gap", "masalah", "bukti", "insiden", "gangguan", "risiko"]):
            return self._answer_weaknesses_rag(target_code, issuer_info, strategic_recs or weaknesses, retrieved_chunks)

        # 6. Intent: Scoring / Ranking / Benchmark
        if any(w in q_lower for w in ["skor", "scoring", "radar", "peringkat", "benchmark", "indeks", "peluang"]):
            return self._answer_scoring_rag(target_code, issuer_info, analysis)

        # 7. General RAG QA Synthesis
        return self._answer_general_rag(target_code, issuer_info, query, retrieved_chunks, strategic_recs, analysis)

    def _answer_greeting(self, code: str, issuer: Dict[str, Any]) -> Dict[str, Any]:
        """Provides a natural, welcoming conversational response when the user says hi."""
        name = issuer.get("name", code)
        reply = f"""Halo! 👋 Senang bertemu dengan Anda.

Saya adalah **AI Business Copilot Nashta**, asisten cerdas yang siap membantu Anda menganalisis Laporan Tahunan resmi **{name} ({code})** dan merancang strategi solusi digital berbasis **10 Pilar Layanan Nashta**.

💡 **Beberapa hal yang dapat Anda tanyakan:**
- **🔍 Temuan Masalah & Bukti**: *"Apa kelemahan operasional & risiko TI di {code}?"*
- **🏛️ Analisis Pilar Layanan**: *"Jelaskan tentang Cyber Security / Cloud / Data & AI untuk {code}"*
- **💻 Profil Arsitektur & Teknologi**: *"Apa teknologi eksisting yang digunakan {code}?"*
- **📄 Draf Pitch Proposal Eksekutif**: *"Tolong buatkan proposal penawaran untuk {code}"*
- **❓ Pertanyaan Bebas**: Tanyakan topik apa saja seputar inisiatif transformasi digital atau regulasi di laporan tahunan.

Ada yang bisa saya bantu analisis hari ini? 😊"""

        return {
            "emiten_code": code,
            "title": f"AI Copilot - {code}",
            "reply": reply,
            "citations": [],
        }

    def _generate_llm_rag_answer(
        self,
        query: str,
        code: str,
        issuer: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        recs: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Synthesizes rich generative answer from active LLM with footnote citations and complete output."""
        provider_info = llm_provider.get_active_provider_info()
        name = issuer.get("name", code)
        subsector = issuer.get("subsector", "Umum")
        overall = analysis.get("overall_opportunity_score", 80)

        # Build Context Block from chunks with clear numbered evidence
        context_parts = []
        for idx, c in enumerate(chunks[:5], 1):
            p_display = c.get("page_display") or f"Hal. {c.get('printed_page', c.get('page_number'))}"
            doc_name = c.get("doc_name", f"AR_{code}.pdf")
            year = c.get("year", 2025)
            chapter = c.get("chapter_title", "Tata Kelola TI & Operasional")
            context_parts.append(
                f"[Sumber ({idx})]\n"
                f"- Dokumen & Tahun: {doc_name} ({year})\n"
                f"- Halaman & Bab: {p_display} ({chapter})\n"
                f"- Kutipan Fakta Dokumen: \"{c.get('raw_paragraph')}\""
            )
        context_text = "\n\n".join(context_parts) if context_parts else "Tidak ada teks langsung yang cocok secara persis."

        # Build Domain Knowledge Block
        rec_parts = []
        for r in recs[:3]:
            rec_parts.append(
                f"- {r.get('title')} (Pilar: {r.get('pillar_name')} | Prioritas: {r.get('severity')})\n"
                f"  Diagnosa Masalah: {r.get('problem_synthesis')}\n"
                f"  Solusi Terpilih Nashta: {r.get('nashta_opportunity')}"
            )
        recs_text = "\n".join(rec_parts) if rec_parts else "Belum ada rekomendasi khusus."

        system_prompt = (
            "Anda adalah Senior AI Business Copilot & Enterprise Solution Architect untuk PT Nashta Global Nusantara. "
            "Tugas Anda adalah menganalisis Laporan Tahunan resmi emiten BEI dan merumuskan paket solusi transformasi digital "
            "berdasarkan 10 Pilar Layanan Nashta (Managed Service, IT Hybrid Infra, Business App, Cyber Security, Data & AI, "
            "Digital Business Platform, IoT, Consulting, Cloud Services, Bootcamp).\n\n"
            "STRUKTUR JAWABAN YANG WAJIB DIIKUTI:\n"
            "1. 🔍 Diagnosa Utama dari Laporan Tahunan {code}\n"
            "   - Jabarkan indikator kunci masalah/risiko dengan footnote berurutan seperti (1), (2), (3) tepat setelah klaim temuan dokumen.\n"
            "   - DILARANG menuliskan referensi kurung halaman di tengah kalimat narasi seperti '(Halaman 281)' atau '(Kutipan 1, Halaman 412)'.\n"
            "   - Contoh yang BENAR:\n"
            "     'Uji coba BCP/DRP dilakukan secara periodik (1), tetapi tidak dijelaskan apakah menggunakan teknologi otomatisasi (misal: AI-driven threat detection).'\n"
            "   - Tepat di bagian akhir dari sesi 'Diagnosa Utama' ini (sebelum lanjut ke Solusi), WAJIB buat sub-bagian 'Bukti Dokumen' dengan format:\n"
            "     ### 📑 Bukti Dokumen\n"
            "     (1) \"[Kutipan kalimat fakta persis dari dokumen]\" — [Nama Laporan Tahunan] ([Tahun]), [Halaman & Bab]\n"
            "     (2) \"[Kutipan kalimat fakta persis dari dokumen]\" — [Nama Laporan Tahunan] ([Tahun]), [Halaman & Bab]\n\n"
            "2. 🚀 Rekomendasi Solusi Nashta\n"
            "   - Uraikan paket solusi terintegrasi, komponen arsitektur, dan tabel fitur & manfaat secara ringkas, padat, dan terstruktur.\n\n"
            "3. 🛠️ Rencana Kerja & Tahapan Implementasi\n"
            "   - Paparkan tahapan implementasi secara tuntas (Fase 1 s/d Fase 3/4) hingga kesimpulan akhir.\n\n"
            "KELENGKAPAN OUTPUT (PENTING): Tulis respon secara LENGKAP, MENYELURUH, dan TUNTAS. JANGAN PERNAH menghentikan respon atau membiarkan tabel/fase implementasi terpotong di tengah kalimat."
        )

        user_prompt = f"""Target Klien: {name} ({code}) | Sektor: {subsector} | Skor Peluang Nashta: {overall}/100

[DATA REFERENSI RESMI BUKTI LAPORAN TAHUNAN]:
{context_text}

[DIAGNOSA & REKOMENDASI 10 PILAR NASHTA]:
{recs_text}

[PERTANYAAN PENGGUNA]:
{query}

Tolong berikan jawaban konsultasi yang cerdas, komprehensif, dan solutif. Ingat aturan sitasi: gunakan penomoran footnote (1), (2) di dalam narasi kalimat diagnosa, dan cantumkan rincian kutipannya di sub-bagian 'Bukti Dokumen' tepat di akhir sesi diagnosa. Pastikan seluruh penjelasan, tabel solusi, dan fase implementasi ditulis lengkap sampai tuntas tanpa terpotong:"""

        llm_reply = llm_provider.generate(user_prompt, system_prompt=system_prompt, temperature=0.2, max_tokens=8192)
        if not llm_reply or len(llm_reply.strip()) < 20:
            return None

        citations = []
        for idx, c in enumerate(chunks[:5], 1):
            p_display = c.get("page_display") or f"Hal. {c.get('printed_page', c.get('page_number'))}"
            citations.append({
                "citation_index": idx,
                "title": c.get("chapter_title", "Tata Kelola TI & Operasional"),
                "doc_name": c.get("doc_name", f"AR_{code}.pdf"),
                "page_number": c.get("printed_page", c.get("page_number")),
                "page_display": p_display,
                "quote": c.get("raw_paragraph"),
                "context": c.get("raw_paragraph"),
                "year": c.get("year", 2025),
            })

        return {
            "emiten_code": code,
            "title": f"AI Copilot ({provider_info['provider'].upper()}) - {code}",
            "reply": llm_reply.strip(),
            "citations": citations,
            "llm_provider": provider_info
        }

    def _detect_pillar_inquiry(self, q_lower: str) -> Optional[int]:
        """Detects if query targets a specific pillar."""
        for pillar_id, keywords in PILLAR_KEYWORDS_MAP.items():
            for kw in keywords:
                if kw in q_lower:
                    return pillar_id
        return None

    def _search_chunks(self, chunks: List[Dict[str, Any]], query: str, top_k: int = 5, target_code: str = "") -> List[Dict[str, Any]]:
        """Performs noise-filtered semantic keyword search over indexed chunks using database FTS or fallback scan."""
        if target_code:
            try:
                from backend.repository import doc_repo
                db_results = doc_repo.search_chunks(target_code, query, top_k=top_k)
                if db_results:
                    return db_results
            except Exception as e:
                logger.debug(f"DB search fallback: {e}")

        if not chunks:
            return []

        # Tokenize query keywords (exclude short stop words)
        stop_words = {"apa", "siapa", "dimana", "kapan", "bagaimana", "mengapa", "yang", "dan", "dari", "untuk", "pada", "dengan", "ini", "itu", "saya", "anda", "kami", "mereka"}
        keywords = [w.strip() for w in re.findall(r"\w+", query.lower()) if len(w.strip()) > 2 and w.strip() not in stop_words]

        if not keywords:
            return chunks[:top_k]

        scored_chunks = []
        for c in chunks:
            text = (c.get("raw_paragraph", "") + " " + c.get("chapter_title", "")).lower()

            # Filter out financial noise
            has_noise = any(nt in text for nt in FINANCIAL_NOISE_TERMS)
            if has_noise:
                continue

            match_count = sum(1 for kw in keywords if kw in text)
            if match_count > 0:
                # Extra weight if keywords appear in chapter title or positive IT context
                bonus = 2 if any(it_kw in text for it_kw in ["teknologi", "sistem", "digital", "siber", "cloud", "data"]) else 0
                scored_chunks.append((match_count + bonus, c))

        if not scored_chunks:
            clean_chunks = [c for c in chunks if not any(nt in (c.get("raw_paragraph", "") + " " + c.get("chapter_title", "")).lower() for nt in FINANCIAL_NOISE_TERMS)]
            return clean_chunks[:top_k]

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_chunks[:top_k]]

    def _answer_quote_solution_inquiry(self, code: str, issuer: Dict[str, Any], query: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Directly answers solution inquiry generated from clicking Copilot button on specific finding card."""
        recs = analysis.get("strategic_recommendations", [])
        matched_rec = None

        # Try to find corresponding recommendation card
        for r in recs:
            if r.get("pillar_name", "").lower() in query.lower() or r.get("title", "").lower() in query.lower():
                matched_rec = r
                break
        if not matched_rec and recs:
            matched_rec = recs[0]

        pillar_name = matched_rec.get("pillar_name", "Solusi Terintegrasi Nashta") if matched_rec else "Solusi Terintegrasi Nashta"
        solution = matched_rec.get("nashta_opportunity", "Modernisasi Sistem & SLA-based Managed Operations") if matched_rec else "Enterprise Transformation Package"
        problem = matched_rec.get("problem_synthesis", "Ditemukan kebutuhan perbaikan arsitektur dan peningkatan keandalan sistem operasional.") if matched_rec else ""
        citations = matched_rec.get("supporting_citations", []) if matched_rec else []

        reply_lines = [
            f"### 💡 Rekomendasi Solusi & Action Plan Nashta: {issuer.get('name')} ({code})",
            f"Berdasarkan temuan dokumen Laporan Tahunan resmi yang Anda tanyakan, berikut rancangan solusi strategis yang disiapkan oleh **Nashta Enterprise Architecture Team**:\n",
            f"#### 1. 🔍 Analisis Akar Masalah (*Root Cause Analysis*):",
            f"> *\"{problem}\"*\n",
            f"#### 2. 🚀 Paket Solusi Nashta: **{solution}** (`Pilar: {pillar_name}`)",
            f"- **Tahap 1: Discovery & Assessment (Bulan 1)**: Audit kepatuhan, pemetaan arsitektur eksisting, dan identifikasi celah operasional.",
            f"- **Tahap 2: Modernization & Deployment (Bulan 2–4)**: Implementasi platform baru, konfigurasi *high availability* (HA), integrasi API, dan migrasi data aman.",
            f"- **Tahap 3: SLA-Based Managed Operations 24/7 (Bulan 5+)**: Monitoring berkelanjutan dengan jaminan *zero-downtime*, mitigasi ancaman otomatis, dan tim support dedicated.\n",
            f"#### 3. 📈 Nilai Tambah Bisnis (*Value Proposition* & ROI):",
            f"- **Eliminasi Risiko Kepatuhan**: Menjamin pemenuhan regulasi nasional (POJK Siber, UU PDP, ISO 27001).",
            f"- **Efisiensi Biaya Operasional (OPEX)**: Mengurangi beban pemeliharaan internal hingga 25–35%.",
            f"- **Keandalan Layanan**: Peningkatan SLA sistem hingga 99.98% ketersediaan.\n",
        ]

        if citations:
            reply_lines.append("#### 📑 Rujukan Sitasi Dokumen Laporan Tahunan Terkait:")
            for idx, cit in enumerate(citations[:2], 1):
                reply_lines.append(
                    f"{idx}. **{cit.get('page_display')}** (*{cit.get('chapter_title')}* — `{cit.get('doc_name')}`)\n"
                    f"   > *\"{cit.get('evidence_quote')}\"*"
                )

        reply_lines.append("\n💬 *Ketik 'Buat proposal' untuk men-generate draf proposal eksekutif lengkap.*")

        return {
            "emiten_code": code,
            "title": f"Solusi Strategis Nashta - {code}",
            "reply": "\n".join(reply_lines),
            "citations": citations,
        }

    def _answer_pillar_inquiry(self, code: str, issuer: Dict[str, Any], pillar_id: int, analysis: Dict[str, Any], retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Provides in-depth consultation on a specific Nashta pillar."""
        pillar_info = next((p for p in self.pillars if p.get("number") == pillar_id or p.get("id") == str(pillar_id)), None)
        pillar_scores = analysis.get("pillar_scores", [])
        matched_score = next((ps for ps in pillar_scores if ps.get("pillar_number") == pillar_id), None)
        recs = analysis.get("strategic_recommendations", [])
        p_name = pillar_info.get("name") if pillar_info else f"Pilar {pillar_id}"
        pillar_recs = [r for r in recs if r.get("pillar_id") == pillar_id or r.get("pillar_name") == p_name]

        p_name = pillar_info.get("name") if pillar_info else f"Pilar {pillar_id}"
        score_val = matched_score.get("score", 75) if matched_score else 75
        maturity = matched_score.get("maturity_level", "Tingkat Menengah") if matched_score else "Tingkat Menengah"
        deal_range = matched_score.get("estimated_deal_range", "Rp 500 Jt - Rp 1.5 M") if matched_score else "Rp 500 Jt - Rp 1.5 M"
        solution = matched_score.get("proposed_solution", pillar_info.get("primary_service", "Solusi Enterprise") if pillar_info else "Solusi Enterprise") if matched_score else ""
        justification = matched_score.get("justification", "") if matched_score else ""

        reply_lines = [
            f"### 🏛️ Analisis Mendalam: Pilar {pillar_id} - {p_name}",
            f"**Klien Target:** {issuer.get('name')} ({code}) | **Sektor:** {issuer.get('subsector')}\n",
            f"#### 📊 Metrik Kesiapan & Peluang:",
            f"- **Opportunity Score:** **{score_val} / 100** ({maturity})",
            f"- **Estimasi Nilai Proyek (Deal Range):** `{deal_range}`",
            f"- **Rekomendasi Paket Nashta:** **{solution}**\n",
            f"#### 📋 Justifikasi Kebutuhan Berdasarkan Laporan Tahunan:",
            f"> *\"{justification}\"*\n",
        ]

        if pillar_recs:
            reply_lines.append("#### 🎯 Rekomendasi Solusi & Diagnosa Khusus:")
            for r in pillar_recs:
                reply_lines.append(f"**• {r.get('title')}** ({r.get('severity')} Priority)")
                reply_lines.append(f"  - *Diagnosa Masalah:* {r.get('problem_synthesis')}")
                reply_lines.append(f"  - *Solusi:* {r.get('nashta_opportunity')}\n")

        citations = []
        if retrieved_chunks:
            reply_lines.append("#### 📑 Bukti Dokumen Asli Terindeks (RAG Chunks):")
            for idx, c in enumerate(retrieved_chunks[:2], 1):
                page_str = f"Hal. {c.get('printed_page', c.get('page_number'))}"
                reply_lines.append(
                    f"{idx}. **{page_str}** (*{c.get('chapter_title')}* — `{c.get('doc_name')}`)\n"
                    f"   > *\"{c.get('raw_paragraph')}\"*"
                )
                citations.append({
                    "title": p_name,
                    "doc_name": c.get("doc_name"),
                    "page_number": c.get("printed_page", c.get("page_number")),
                    "quote": c.get("raw_paragraph"),
                    "context": c.get("raw_paragraph"),
                })

        reply_lines.append("\n💬 *Ketik 'Buat proposal' untuk menyusun dokumen penawaran resmi untuk pilar ini.*")

        return {
            "emiten_code": code,
            "title": f"Konsultasi Pilar {p_name} - {code}",
            "reply": "\n".join(reply_lines),
            "citations": citations,
        }

    def _answer_tech_stack_inquiry(self, code: str, issuer: Dict[str, Any], analysis: Dict[str, Any], chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Answers inquiries regarding technology stack and enterprise IT architecture."""
        tech_stack = issuer.get("technology_stack", "Sistem TI Terintegrasi")
        overall = analysis.get("overall_opportunity_score", 80)
        top3 = analysis.get("top_priority_pillars", [])

        reply_lines = [
            f"### 💻 Profil Arsitektur & Teknologi: {issuer.get('name')} ({code})",
            f"Berdasarkan tinjauan Laporan Tahunan resmi, berikut ringkasan arsitektur teknologi eksisting dan area modernisasi:\n",
            f"#### 🛠️ Infrastruktur & Stack Teknologi yang Teridentifikasi:",
            f"- **Stack / Core Platform:** `{tech_stack}`",
            f"- **Status Kesiapan Adopsi Digital:** Tergolong aktif bertransformasi dengan agregat peluang **{overall}/100**.\n",
            f"#### 🚀 Area Modernisasi Prioritas Nashta:",
        ]

        for idx, p in enumerate(top3, 1):
            reply_lines.append(f"{idx}. **{p.get('pillar_name')}** (Skor: {p.get('score')}/100) — `{p.get('proposed_solution')}`")

        citations = []
        if chunks:
            reply_lines.append("\n#### 📑 Catatan Laporan Tahunan Terkait Infrastruktur TI:")
            for idx, c in enumerate(chunks[:2], 1):
                page_str = f"Hal. {c.get('printed_page', c.get('page_number'))}"
                reply_lines.append(
                    f"{idx}. **{page_str}** (*{c.get('chapter_title')}*)\n"
                    f"   > *\"{c.get('raw_paragraph')}\"*"
                )
                citations.append({
                    "title": c.get("chapter_title"),
                    "doc_name": c.get("doc_name"),
                    "page_number": c.get("printed_page", c.get("page_number")),
                    "quote": c.get("raw_paragraph"),
                    "context": c.get("raw_paragraph"),
                })

        return {
            "emiten_code": code,
            "title": f"Profil Teknologi - {code}",
            "reply": "\n".join(reply_lines),
            "citations": citations,
        }

    def _answer_weaknesses_rag(self, code: str, issuer: Dict[str, Any], weaknesses_or_recs: List[Dict[str, Any]], retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        recs = evidence_engine.discover_recommendations(code)
        if not recs:
            return {
                "emiten_code": code,
                "title": f"Hasil Analisis Dokumen - {code}",
                "reply": f"Berdasarkan penelusuran RAG pada seluruh chunk Laporan Tahunan {code}, tidak ditemukan kata kunci anomali atau insiden kritis terbuka.",
                "citations": [],
            }

        reply_lines = [
            f"### 🎯 Rekomendasi Solusi Strategis & Klaster Bukti Laporan Tahunan: {issuer.get('name')} ({code})\n"
        ]
        all_citations = []

        for idx, rec in enumerate(recs, 1):
            severity_badge = "🔴 [HIGH PRIORITY]" if rec.get("severity") == "High" else "🟡 [MEDIUM PRIORITY]"
            reply_lines.append(
                f"#### **{idx}. {rec.get('title')}** {severity_badge}\n"
                f"* **Pilar Layanan Nashta:** `{rec.get('pillar_name')}`\n"
                f"* **📋 Diagnosa Masalah Emiten:**\n"
                f"  > *\"{rec.get('problem_synthesis')}\"*\n"
                f"* **💼 Peluang Solusi Nashta:** **{rec.get('nashta_opportunity')}**\n"
                f"  *{rec.get('value_proposition')}*\n"
                f"* **📑 Klaster Sitasi Bukti Dokumen Asli ({len(rec.get('supporting_citations', []))} Bukti Terverifikasi):**"
            )

            for c_idx, cit in enumerate(rec.get("supporting_citations", []), 1):
                reply_lines.append(
                    f"  {c_idx}. **{cit.get('page_display')}** (*{cit.get('chapter_title')}* — `{cit.get('doc_name')}`)\n"
                    f"     - *Kutipan:* \"{cit.get('evidence_quote')}\""
                )
                all_citations.append({
                    "title": rec.get("title"),
                    "doc_name": cit.get("doc_name"),
                    "page_number": cit.get("printed_page"),
                    "page_display": cit.get("page_display"),
                    "printed_page": cit.get("printed_page"),
                    "physical_page": cit.get("physical_page"),
                    "quote": cit.get("evidence_quote"),
                    "context": cit.get("context_window"),
                    "chapter": cit.get("chapter_title"),
                    "solution": rec.get("nashta_opportunity"),
                })
            reply_lines.append("")

        reply_lines.append("💡 *Seluruh kutipan di atas diekstrak dan disintesis langsung dari chunk dokumen asli Laporan Tahunan.*")

        return {
            "emiten_code": code,
            "title": f"Rekomendasi Strategis & Multi-Sitasi RAG - {code}",
            "reply": "\n".join(reply_lines),
            "citations": all_citations,
            "recommendations": recs,
        }

    def _answer_scoring_rag(self, code: str, issuer: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        overall = analysis.get("overall_opportunity_score", 0)
        top3 = analysis.get("top_priority_pillars", [])
        scores = analysis.get("pillar_scores", [])

        reply_lines = [
            f"### 📊 Skor Peluang Bisnis 10 Pilar Nashta: {issuer.get('name')} ({code})",
            f"**Skor Agregat Peluang Bisnis:** **{overall} / 100**\n",
            "**🏆 3 Pilar Peluang Tertinggi Berdasarkan Bukti Dokumen:**",
        ]
        for idx, p in enumerate(top3, 1):
            reply_lines.append(
                f"**{idx}. {p['pillar_name']}** — Skor **{p['score']}/100** ({p['maturity_level']})\n"
                f"   - *Estimasi Nilai Proyek:* `{p['estimated_deal_range']}`\n"
                f"   - *Justifikasi Bukti:* {p['justification']}\n"
                f"   - *Paket Solusi:* `{p['proposed_solution']}`\n"
            )

        reply_lines.append("\n**📋 Rincian 10 Pilar Nashta:**")
        for p in scores:
            reply_lines.append(f"- **Pilar {p['pillar_number']}: {p['pillar_name']}** : Skor **{p['score']}** | `{p['readiness']}`")

        return {
            "emiten_code": code,
            "title": f"Skor 10 Pilar Nashta - {code}",
            "reply": "\n".join(reply_lines),
            "citations": [],
        }

    def _answer_general_rag(self, code: str, issuer: Dict[str, Any], query: str, chunks: List[Dict[str, Any]], recs: List[Dict[str, Any]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        reply_lines = [
            f"### 🤖 RAG Business Copilot: {issuer.get('name')} ({code})",
            f"Berdasarkan penelusuran dokumen Laporan Tahunan resmi {code}, berikut sintesis jawaban atas pertanyaan Anda:\n",
        ]

        citations = []
        if chunks:
            reply_lines.append("#### 📑 Temuan Fakta & Kutipan dari Laporan Tahunan:")
            for idx, c in enumerate(chunks[:3], 1):
                page_str = f"Hal. {c.get('printed_page', c.get('page_number'))}"
                reply_lines.append(
                    f"**{idx}. {page_str} — {c.get('chapter_title')}** (`{c.get('doc_name')}`)\n"
                    f"> *\"{c.get('raw_paragraph')}\"*\n"
                )
                citations.append({
                    "title": c.get("chapter_title"),
                    "doc_name": c.get("doc_name"),
                    "page_number": c.get("printed_page", c.get("page_number")),
                    "quote": c.get("raw_paragraph"),
                    "context": c.get("raw_paragraph"),
                })

        top_pillars = analysis.get("top_priority_pillars", [])
        if top_pillars:
            p = top_pillars[0]
            reply_lines.append(f"#### 🎯 Keselarasan dengan Solusi Nashta:")
            reply_lines.append(f"- **Pilar Relevan:** `{p.get('pillar_name')}` (Opportunity Score: {p.get('score')}/100)")
            reply_lines.append(f"- **Rekomendasi Paket:** `{p.get('proposed_solution')}`")
            reply_lines.append(f"- **Estimasi Nilai:** `{p.get('estimated_deal_range')}`")

        reply_lines.append("\n💬 *Ketik 'Buat proposal' untuk membuat draf penawaran formal atau tanyakan pilar spesifik (misal: 'Jelaskan pilar Cyber Security').*")

        return {
            "emiten_code": code,
            "title": f"Analisis Dokumen RAG - {code}",
            "reply": "\n".join(reply_lines),
            "citations": citations,
        }

    def _generate_llm_proposal(
        self,
        code: str,
        issuer: Dict[str, Any],
        analysis: Dict[str, Any],
        recs: List[Dict[str, Any]],
        top_pillars: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Synthesizes bespoke executive proposal via active LLM (Ministral / Gemini / OpenAI)."""
        name = issuer.get("name", code)
        subsector = issuer.get("subsector", "Perbankan / Enterprise")
        overall = analysis.get("overall_opportunity_score", 85)

        # Build context from recommendations & citations
        rec_summary = []
        for r in recs[:5]:
            cit_strs = [f"{c.get('page_display', '')}: \"{c.get('evidence_quote', '')}\"" for c in r.get("supporting_citations", [])[:2]]
            rec_summary.append(
                f"- Pilar: {r.get('pillar_name')} ({r.get('severity')} Priority)\n"
                f"  Diagnosa Masalah: {r.get('problem_synthesis')}\n"
                f"  Solusi Nashta: {r.get('nashta_opportunity')}\n"
                f"  Bukti Dokumen: {'; '.join(cit_strs)}"
            )
        recs_text = "\n\n".join(rec_summary)

        system_prompt = (
            "Anda adalah Senior Enterprise Solution Architect & Business Advisory Lead untuk PT Nashta Global Nusantara. "
            "Tugas Anda adalah menyusun dokumen Executive Proposal formal, komprehensif, dan elegan untuk klien target "
            "berdasarkan hasil audit Laporan Tahunan resmi dan portofolio 10 Pilar Layanan Nashta.\n"
            "Format dokumen wajib menggunakan format Markdown rapi dengan struktur:\n"
            "# EXECUTIVE PROPOSAL: NASHTA DIGITAL TRANSFORMATION ACCELERATOR\n"
            "**Klien Target:** ...\n"
            "**Sektor:** ...\n"
            "**Tanggal:** 28 Agustus 2026\n"
            "**Disusun Oleh:** Nashta Solution Advisory & Enterprise Architecture Team\n\n"
            "---\n\n"
            "## 1. Executive Summary & Dasar Dokumen\n"
            "(Jelaskan urgensi transformasi, latar belakang emiten, dan 3 pilar prioritas teratas)\n\n"
            "## 2. Diagnosa Kebutuhan Strategis & Klaster Bukti Laporan Tahunan\n"
            "(Jabarkan temuan masalah dan bukti kutipan halaman nyata untuk tiap rekomendasi pilar secara mendalam)\n\n"
            "## 3. Paket Penawaran Solusi 10 Pilar Nashta\n"
            "(Wajib sertakan tabel perbandingan 10 pilar dengan format tabel markdown | No | Pilar Nashta | Rekomendasi Solusi Khusus | Nilai Tambah |)\n\n"
            "## 4. Rencana Kerja & Tahapan Implementasi\n"
            "(Bagi dalam fase 1 hingga fase 4 dengan durasi dan output yang jelas)\n\n"
            "## 5. Hubungi Tim Nashta\n"
            "- Email: business@nashta.co.id\n"
            "- Website: https://nashta.co.id\n"
        )

        user_prompt = f"""Target Klien: {name} ({code})
Sektor: {subsector}
Skor Peluang Agregat: {overall}/100

[DATA REKOMENDASI DAN BUKTI DOKUMEN LAPORAN TAHUNAN]:
{recs_text}

Tolong susun draf Executive Pitch Proposal formal lengkap dalam bahasa Indonesia profesional sekarang:"""

        return llm_provider.generate(user_prompt, system_prompt=system_prompt, temperature=0.2)

    def generate_proposal(self, code: str) -> Dict[str, Any]:
        analysis = scoring_engine.analyze_issuer(code)
        issuer = analysis.get("issuer", {})
        weaknesses = analysis.get("verified_weaknesses", [])
        top_pillars = analysis.get("top_priority_pillars", [])
        recs = analysis.get("strategic_recommendations", [])

        # 1. If Generative LLM (Ministral / Gemini / OpenAI) is configured, generate dynamic bespoke proposal!
        if llm_provider.is_llm_available():
            llm_proposal = self._generate_llm_proposal(code, issuer, analysis, recs, top_pillars)
            if llm_proposal and len(llm_proposal.strip()) > 300:
                return {
                    "emiten_code": code,
                    "title": f"Executive Proposal 10 Pilar Nashta - {issuer.get('name')}",
                    "reply": f"📄 **Draf Proposal Penawaran 10 Pilar Berhasil Disintesis oleh AI!**\n\nDokumen proposal lengkap untuk **{issuer.get('name')} ({code})** telah disusun secara dinamis berdasarkan audit dokumen laporan tahunan dan kapabilitas 10 Pilar Nashta.",
                    "proposal_markdown": llm_proposal,
                    "citations": weaknesses,
                }

        # 2. Deterministic Fallback
        proposal_md = f"""# EXECUTIVE PROPOSAL: NASHTA DIGITAL TRANSFORMATION ACCELERATOR
**Klien Target:** {issuer.get('name')} ({code})  
**Sektor:** {issuer.get('subsector')}  
**Tanggal:** 28 Agustus 2026  
**Disusun Oleh:** Nashta Solution Advisory & Enterprise Architecture Team  

---

## 1. Executive Summary & Dasar Dokumen
Proposal ini disusun berbasis audit langsung terhadap Laporan Tahunan resmi {issuer.get('name')} ({code}). Melalui True RAG Document Extraction, kami mengidentifikasi pain points operasional dan merumuskan paket solusi **10 Pilar Layanan Nashta** yang terfokus pada:
"""
        for idx, p in enumerate(top_pillars, 1):
            proposal_md += f"\n### Prioritas {idx}: Pilar {p['pillar_name']} (Opportunity Score: {p['score']}/100)\n"
            proposal_md += f"- **Kebutuhan Dokumen:** {p['justification']}\n"
            proposal_md += f"- **Paket Solusi Nashta:** `{p['proposed_solution']}`\n"
            proposal_md += f"- **Estimasi Nilai Investasi:** `{p['estimated_deal_range']}`\n"

        recs = analysis.get("strategic_recommendations", [])
        proposal_md += "\n---\n\n## 2. Diagnosa Kebutuhan Strategis & Klaster Bukti Laporan Tahunan\n"
        if recs:
            for r_idx, r in enumerate(recs, 1):
                proposal_md += f"""
### 🎯 Rekomendasi {r_idx}: {r.get('title')} ({r.get('severity')} Priority)
* **Pilar Terkait:** `{r.get('pillar_name')}` (Tingkat Keyakinan: {r.get('confidence')}%)
* **📋 Diagnosa Masalah Emiten:**
  > "{r.get('problem_synthesis')}"
* **💼 Rekomendasi Solusi Nashta:** **{r.get('nashta_opportunity')}**  
  *{r.get('value_proposition')}*
* **📑 Klaster Sitasi Bukti Dokumen Terverifikasi:**
"""
                for c_idx, cit in enumerate(r.get("supporting_citations", []), 1):
                    proposal_md += f"""  {c_idx}. **{cit.get('page_display')}** (*{cit.get('chapter_title')}* — `{cit.get('doc_name')}`)
     - *Kutipan Persis:* "{cit.get('evidence_quote')}"
"""
        elif weaknesses:
            for w in weaknesses:
                proposal_md += f"""
### 📌 {w.get('title')}
- **Dokumen Sumber:** `{w.get('doc_name')}`
- **Nomor Halaman:** {w.get('page_display', 'Halaman ' + str(w.get('page_number')))} ({w.get('chapter_title')})
- **Kutipan Persis Kalimat Laporan:** *"{w.get('evidence_quote')}"*
- **Konteks Paragraf Asli Dokumen:**
> "{w.get('context_window')}"
- **Dampak Bisnis & Severity:** {w.get('severity')} Severity
- **Rekomendasi Solusi Nashta:** {w.get('nashta_opportunity')}
"""

        proposal_md += """
---

## 3. Paket Penawaran Solusi 10 Pilar Nashta

| No | Pilar Nashta | Rekomendasi Solusi Khusus | Nilai Tambah (Business Value) |
|---|---|---|---|
| 1 | **Managed Service** | 24/7 SLA-based Dedicated IT Support & Helpdesk | Mengurangi beban OPEX IT hingga 30% dan menjamin zero-downtime |
| 2 | **IT Hybrid Infrastructure** | Multi-Branch SD-WAN & Modern Datacenter Interconnect | Konektivitas stabil dengan latensi < 10ms antar titik layanan |
| 3 | **Business Application** | Core Application Modernization & Workflow Automation | Otomatisasi proses bisnis dan eliminasi input manual |
| 4 | **Cyber Security** | Managed SOC 24/7, VAPT & UU PDP Compliance Shield | Perlindungan data nasabah/pasien dari ancaman ransomware |
| 5 | **Data & AI** | Enterprise Data Lakehouse & Predictive Analytics BI | Keputusan bisnis berbasis data real-time dan analisis prediktif |
| 6 | **Digital Business Platform** | Omnichannel Mobile Platform & API Integration Hub | Peningkatan adopsi digital pengguna dan integrasi ekosistem nasional |
| 7 | **IoT & Edge Computing** | Smart Asset Tracking & Telemetry Monitoring | Efisiensi utilitas fasilitas dan monitoring suhu cold chain otomatis |
| 8 | **Consulting & Advisory** | IT Master Plan 2025–2030 & IT Governance (COBIT/TOGAF) | Penyelarasan investasi teknologi dengan target pertumbuhan korporasi |
| 9 | **Cloud Services** | Managed Multi-Cloud Migration & FinOps Optimization | Efisiensi biaya komputasi cloud dan implementasi Cloud DR |
| 10 | **Bootcamp** | Corporate Talent Enablement & DevSecOps Academy | Peningkatan kapabilitas dan kesiapan tim internal mengelola teknologi baru |

---

## 4. Rencana Kerja & Tahapan Implementasi
1. **Bulan 1: Discovery & IT Assessment** (Audit arsitektur eksisting, validasi gap operasional, dan blueprint solusi).
2. **Bulan 2-3: Solution Architecture & PoC** (Uji coba pada unit percontohan dengan KPI terukur).
3. **Bulan 4-6: Enterprise Deployment & Integration** (Implementasi menyeluruh dan migrasi sistem).
4. **Bulan 7+: 24/7 SLA Managed Operations** (Pemeliharaan berkala dan monitoring performa).

---

## 5. Hubungi Tim Nashta
- **Email:** business@nashta.co.id
- **Website:** https://nashta.co.id
"""
        return {
            "emiten_code": code,
            "title": f"Executive Proposal 10 Pilar Nashta - {issuer.get('name')}",
            "reply": f"📄 **Draf Proposal Penawaran 10 Pilar Berhasil Dibuat!**\n\nProposal lengkap telah disiapkan untuk **{issuer.get('name')} ({code})** berdasarkan audit laporan tahunan dan rekomendasi 10 Pilar Nashta.",
            "proposal_markdown": proposal_md,
            "citations": weaknesses,
        }


rag_engine = AIAssistantRAGEngine()
