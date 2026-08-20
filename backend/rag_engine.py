"""AI Assistant RAG & Business Intelligence Copilot for Nashta 10 Pillars (True Document Retrieval)."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from backend.catalog import catalog_manager
from backend.evidence_engine import evidence_engine
from backend.rag_indexer import rag_indexer
from backend.scoring_engine import scoring_engine


class AIAssistantRAGEngine:
    """True RAG Assistant that searches indexed document chunks, cites exact pages, and presents surrounding paragraph context."""

    def __init__(self) -> None:
        self.pillars = catalog_manager.get_pillars()

    def process_chat(self, query: str, active_emiten: Optional[str] = None) -> Dict[str, Any]:
        q_lower = query.lower()
        active_code = active_emiten.upper() if active_emiten else None

        # Auto-detect emiten in query if not specified
        if not active_code:
            for issuer in catalog_manager.get_all_issuers():
                if issuer["code"].lower() in q_lower or issuer["name"].lower() in q_lower:
                    active_code = issuer["code"]
                    break

        target_code = active_code or "BRIS"
        analysis = scoring_engine.analyze_issuer(target_code)
        issuer_info = analysis.get("issuer", {})
        weaknesses = analysis.get("verified_weaknesses", [])

        # Retrieve matching chunks from RAG index
        chunks = rag_indexer.get_chunks_for_emiten(target_code)
        retrieved_chunks = self._search_chunks(chunks, query)

        # Check intent
        if "proposal" in q_lower or "pitch" in q_lower or "penawaran" in q_lower:
            return self.generate_proposal(target_code)

        if "kelemahan" in q_lower or "weakness" in q_lower or "gap" in q_lower or "masalah" in q_lower or "bukti" in q_lower:
            return self._answer_weaknesses_rag(target_code, issuer_info, weaknesses, retrieved_chunks)

        if "skor" in q_lower or "scoring" in q_lower or "radar" in q_lower:
            return self._answer_scoring_rag(target_code, issuer_info, analysis)

        return self._answer_general_rag(target_code, issuer_info, query, retrieved_chunks, weaknesses, analysis)

    def _search_chunks(self, chunks: List[Dict[str, Any]], query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        keywords = [w.strip() for w in re.findall(r"\w+", query.lower()) if len(w.strip()) > 3]
        if not keywords:
            return chunks[:top_k]

        scored_chunks = []
        for c in chunks:
            text = (c.get("raw_paragraph", "") + " " + c.get("chapter_title", "")).lower()
            match_count = sum(1 for kw in keywords if kw in text)
            if match_count > 0:
                scored_chunks.append((match_count, c))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_chunks[:top_k]] or chunks[:top_k]

    def _answer_weaknesses_rag(self, code: str, issuer: Dict[str, Any], weaknesses: List[Dict[str, Any]], retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
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

    def _answer_general_rag(self, code: str, issuer: Dict[str, Any], query: str, chunks: List[Dict[str, Any]], weaknesses: List[Dict[str, Any]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        reply_lines = [
            f"### 🤖 RAG Business Copilot: {issuer.get('name')} ({code})",
            f"Berdasarkan analisis dokumen Laporan Tahunan resmi {code}, berikut rangkuman temuan terkait pertanyaan Anda:\n",
        ]

        citations = []
        if chunks:
            reply_lines.append("#### 📑 Paragraf Relevan yang Ditemukan pada Laporan Tahunan:")
            for idx, c in enumerate(chunks[:2], 1):
                reply_lines.append(
                    f"**{idx}. Halaman {c.get('page_number')} — {c.get('chapter_title')}** (`{c.get('doc_name')}`)\n"
                    f"> *\"{c.get('raw_paragraph')}\"*\n"
                )
                citations.append({
                    "title": c.get("chapter_title"),
                    "doc_name": c.get("doc_name"),
                    "page_number": c.get("page_number"),
                    "quote": c.get("raw_paragraph"),
                    "context": c.get("raw_paragraph"),
                })

        if weaknesses:
            top_w = weaknesses[0]
            reply_lines.append(f"\n#### 🎯 Implikasi Terhadap Solusi Nashta:")
            reply_lines.append(f"- **Isu Operasional:** {top_w.get('title')}")
            reply_lines.append(f"- **Rekomendasi Paket Nashta:** `{top_w.get('nashta_opportunity')}`")

        reply_lines.append("\n💬 *Ketik 'Buat proposal' untuk membuat proposal penawaran terintegrasi.*")

        return {
            "emiten_code": code,
            "title": f"Analisis Dokumen RAG - {code}",
            "reply": "\n".join(reply_lines),
            "citations": citations,
        }

    def generate_proposal(self, code: str) -> Dict[str, Any]:
        analysis = scoring_engine.analyze_issuer(code)
        issuer = analysis.get("issuer", {})
        weaknesses = analysis.get("verified_weaknesses", [])
        top_pillars = analysis.get("top_priority_pillars", [])

        proposal_md = f"""# EXECUTIVE PROPOSAL: NASHTA DIGITAL TRANSFORMATION ACCELERATOR
**Klien Target:** {issuer.get('name')} ({code})  
**Sektor:** {issuer.get('subsector')}  
**Tanggal:** 18 Agustus 2026  
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
            "title": f"Proposal Penawaran Bisnis 10 Pilar Nashta - {issuer.get('name')}",
            "reply": proposal_md,
            "proposal_markdown": proposal_md,
            "citations": weaknesses,
        }


rag_engine = AIAssistantRAGEngine()
