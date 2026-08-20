"""PDF Processing and Semantic Extraction Module."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pypdf

logger = logging.getLogger("pdf_processor")

SECTION_PATTERNS = {
    "it_governance": re.compile(r"(?i)(tata\s+kelola\s+teknologi\s+informasi|it\s+governance|pengelolaan\s+ti)"),
    "risk_management": re.compile(r"(?i)(manajemen\s+risiko|profil\s+risiko|risiko\s+operasional|risiko\s+siber|cyber\s+risk)"),
    "digital_transformation": re.compile(r"(?i)(transformasi\s+digital|ekosistem\s+digital|pengembangan\s+teknologi|inovasi\s+digital)"),
    "operational_review": re.compile(r"(?i)(tinjauan\s+operasional|kinerja\s+operasional|layanan\s+kesehatan|jaringan\s+cabang)"),
    "capex_finance": re.compile(r"(?i)(belanja\s+modal|capex|anggaran\s+ti|investasi\s+teknologi)"),
    "human_capital": re.compile(r"(?i)(pengembangan\s+sdm|sumber\s+daya\s+manusia|pelatihan\s+karyawan|human\s+capital)"),
}


class PDFProcessor:
    """Extracts structured text, identifies key IT/operational chapters, and builds evidence chunks."""

    def __init__(self) -> None:
        pass

    def extract_text_from_pdf(self, pdf_path: Path, max_pages: int = 500) -> Dict[str, Any]:
        """Extracts text per page with section tagging."""
        if not pdf_path.exists():
            return {"success": False, "error": f"File not found: {pdf_path}"}

        pages_data: List[Dict[str, Any]] = []
        total_chars = 0
        detected_sections: Dict[str, List[int]] = {k: [] for k in SECTION_PATTERNS}

        try:
            reader = pypdf.PdfReader(str(pdf_path))
            num_pages = min(len(reader.pages), max_pages)

            for page_idx in range(num_pages):
                page = reader.pages[page_idx]
                text = page.extract_text() or ""
                text_clean = " ".join(text.split())
                total_chars += len(text_clean)

                current_page_sections = []
                for sec_name, pattern in SECTION_PATTERNS.items():
                    if pattern.search(text_clean):
                        detected_sections[sec_name].append(page_idx + 1)
                        current_page_sections.append(sec_name)

                pages_data.append({
                    "page_number": page_idx + 1,
                    "char_count": len(text_clean),
                    "sections": current_page_sections,
                    "text": text_clean,
                })

            return {
                "success": True,
                "total_pages": len(reader.pages),
                "processed_pages": num_pages,
                "total_characters": total_chars,
                "detected_sections": detected_sections,
                "pages": pages_data,
            }
        except Exception as e:
            logger.error(f"Error parsing PDF {pdf_path}: {e}")
            return {"success": False, "error": str(e)}

    def search_keywords(self, extracted_data: Dict[str, Any], keywords: List[str]) -> List[Dict[str, Any]]:
        """Search keywords across pages and return snippets with exact page numbers."""
        results = []
        if not extracted_data.get("success"):
            return results

        pages = extracted_data.get("pages", [])
        for page in pages:
            text = page.get("text", "")
            for kw in keywords:
                pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
                matches = list(pattern.finditer(text))
                if matches:
                    # Extract surrounding context snippet (up to 250 chars)
                    for match in matches[:3]:  # max 3 per page to avoid flooding
                        start = max(0, match.start() - 100)
                        end = min(len(text), match.end() + 150)
                        snippet = text[start:end].strip()
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(text):
                            snippet = snippet + "..."

                        results.append({
                            "keyword": kw,
                            "page_number": page.get("page_number"),
                            "sections": page.get("sections", []),
                            "snippet": snippet,
                        })
        return results


pdf_processor = PDFProcessor()
