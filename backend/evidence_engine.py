"""Evidence & Weakness Discovery Engine (High-Performance True RAG & Fast Pre-Filtering)."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from backend.catalog import catalog_manager
from backend.rag_indexer import rag_indexer

logger = logging.getLogger("evidence_engine")

PAIN_TRIGGER_WORDS = [
    "kendala", "hambatan", "kelemahan", "keterbatasan", "tantangan", "risiko", "insiden",
    "gangguan", "downtime", "kebocoran", "serangan", "kerentanan", "kegagalan", "keterlambatan",
    "inefisiensi", "beban biaya", "ketergantungan", "human error", "kesenjangan", "unbanked",
    "pemeliharaan", "overstock", "stock-out", "latensi", "ransomware"
]

NOISE_PATTERNS = [
    r"(?i)daftar\s+isi",
    r"(?i)table\s+of\s+contents",
    r"(?i)halaman\s+ini\s+sengaja\s+dikosongkan",
    r"(?i)laporan\s+tahunan\s+\|\s+annual\s+report",
    r"(?i)ikhtisar\s+keuangan\s+utama",
]


class EvidenceEngine:
    """Discovers high-value, verifiable weaknesses directly from indexed document chunks with sub-millisecond pre-filtering."""

    def __init__(self) -> None:
        self.pillars = catalog_manager.get_pillars()
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    def clear_cache(self, emiten_code: Optional[str] = None) -> None:
        if emiten_code:
            self._cache.pop(emiten_code.upper(), None)
        else:
            self._cache.clear()

    def discover_weaknesses(self, emiten_code: str) -> List[Dict[str, Any]]:
        c_code = emiten_code.upper().strip()
        if c_code in self._cache:
            return self._cache[c_code]

        chunks = rag_indexer.get_chunks_for_emiten(c_code)
        if not chunks:
            issuer = catalog_manager.get_issuer_by_code(c_code)
            results = issuer.get("verified_weaknesses", []) if issuer else []
            self._cache[c_code] = results
            return results

        weakness_results: List[Dict[str, Any]] = []

        # Fast pre-filtering: only inspect chunks that contain at least one pain keyword
        for chunk in chunks:
            raw_para = chunk.get("raw_paragraph", "")
            if len(raw_para) < 80 or len(raw_para) > 1200:
                continue

            raw_lower = raw_para.lower()
            if not any(pw in raw_lower for pw in PAIN_TRIGGER_WORDS):
                continue

            if any(re.search(np, raw_para) for np in NOISE_PATTERNS):
                continue

            sentences = chunk.get("sentences", [])
            page_num = chunk.get("page_number", 1)
            doc_name = chunk.get("doc_name", "Annual_Report.pdf")
            chapter = chunk.get("chapter_title", "Tinjauan Operasional")
            year = chunk.get("year", 2024)

            for pillar in self.pillars:
                pillar_id = pillar["id"]
                pillar_keywords = pillar.get("keywords", [])

                matched_kws = [kw for kw in pillar_keywords if kw in raw_lower]
                if matched_kws:
                    best_sentence = ""
                    for s in sentences:
                        s_clean = s.strip()
                        s_lower = s_clean.lower()
                        if len(s_clean) < 30:
                            continue
                        if any(pw in s_lower for pw in PAIN_TRIGGER_WORDS) and any(kw in s_lower for kw in matched_kws):
                            best_sentence = s_clean
                            break
                        elif not best_sentence and any(pw in s_lower for pw in PAIN_TRIGGER_WORDS):
                            best_sentence = s_clean

                    if not best_sentence and sentences:
                        valid_sentences = [s for s in sentences if len(s.strip()) > 35]
                        best_sentence = valid_sentences[0] if valid_sentences else raw_para[:200]

                    best_sentence = re.sub(r"^\d+\s+", "", best_sentence).strip()
                    if len(best_sentence) < 35:
                        continue

                    is_high = any(w in raw_lower for w in ["insiden", "siber", "pdp", "gangguan", "kegagalan", "kritis", "tinggi", "serangan", "kebocoran", "ransomware"])
                    severity = "High" if is_high else "Medium"
                    confidence = 95 if is_high else 89
                    title = self._generate_weakness_title(matched_kws, chapter, best_sentence)
                    opportunity = self._get_tailored_solution(pillar, matched_kws)
                    page_display = chunk.get("page_display") or f"Halaman {page_num}"
                    printed_page = chunk.get("printed_page", page_num)
                    physical_page = chunk.get("physical_page", page_num)

                    weakness_results.append({
                        "pillar_id": pillar_id,
                        "pillar_name": pillar["name"],
                        "title": title,
                        "severity": severity,
                        "match_confidence": confidence,
                        "evidence_quote": best_sentence,
                        "context_window": raw_para,
                        "report_year": year,
                        "page_ref": f"{page_display} ({chapter})",
                        "page_display": page_display,
                        "page_number": printed_page,
                        "printed_page": printed_page,
                        "physical_page": physical_page,
                        "doc_name": doc_name,
                        "chapter_title": chapter,
                        "matched_keywords": matched_kws,
                        "nashta_opportunity": opportunity,
                    })

        # Deduplicate & rank
        grouped_by_pillar: Dict[str, List[Dict[str, Any]]] = {}
        for w in weakness_results:
            p_id = w["pillar_id"]
            if p_id not in grouped_by_pillar:
                grouped_by_pillar[p_id] = []
            grouped_by_pillar[p_id].append(w)

        final_weaknesses = []
        for p_id, items in grouped_by_pillar.items():
            items.sort(key=lambda x: (1 if x["severity"] == "High" else 0, x["match_confidence"], len(x["evidence_quote"])), reverse=True)
            for top_item in items[:2]:
                final_weaknesses.append(top_item)

        final_weaknesses.sort(key=lambda x: (1 if x["severity"] == "High" else 0, x["match_confidence"]), reverse=True)
        self._cache[c_code] = final_weaknesses
        return final_weaknesses

    def _generate_weakness_title(self, keywords: List[str], chapter: str, sentence: str) -> str:
        kw_str = ", ".join(keywords[:2]).title()
        s_lower = sentence.lower()
        if "siber" in s_lower or "keamanan" in s_lower or "ransomware" in s_lower:
            return f"Penguatan Ketahanan Keamanan Siber & Mitigasi Risiko ({kw_str})"
        if "jaringan" in s_lower or "sd-wan" in s_lower or "konektivitas" in s_lower or "infrastruktur" in s_lower:
            return f"Tantangan Konektivitas & Modernisasi Jaringan Multi-Site ({kw_str})"
        if "cloud" in s_lower or "biaya" in s_lower or "finops" in s_lower:
            return f"Optimalisasi Biaya Infrastruktur & Adopsi Hybrid Cloud ({kw_str})"
        if "talenta" in s_lower or "sdm" in s_lower or "upskilling" in s_lower or "pelatihan" in s_lower:
            return f"Kesenjangan Kompetensi SDM IT & Program Corporate Upskilling ({kw_str})"
        if "api" in s_lower or "open api" in s_lower or "gateway" in s_lower:
            return f"Stabilitas Integrasi Open API & Layanan Ekosistem Digital ({kw_str})"
        if "cold chain" in s_lower or "iot" in s_lower or "telemetri" in s_lower:
            return f"Telemetri Monitoring Suhu & Pelacakan Aset Pintar IoT ({kw_str})"
        if "rekam medis" in s_lower or "simrs" in s_lower or "antrean" in s_lower or "core banking" in s_lower:
            return f"Optimalisasi Alur Operasional & Modernisasi Core System ({kw_str})"
        return f"Kebutuhan Modernisasi & Peningkatan Operasional IT ({kw_str})"

    def _get_tailored_solution(self, pillar: Dict[str, Any], matched_kws: List[str]) -> str:
        solutions = pillar.get("solutions", [])
        return solutions[0] if solutions else "Nashta Custom Enterprise Solution & Advisory"


evidence_engine = EvidenceEngine()
