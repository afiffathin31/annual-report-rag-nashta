import os
from pathlib import Path
from typing import Optional
from llama_parse import LlamaParse
import config

try:
    import fitz  # PyMuPDF fallback
except ImportError:
    fitz = None

class DocumentParser:
    """Parses PDF documents into markdown using LlamaParse with PyMuPDF fallback."""

    def __init__(self, output_dir: Path = config.PARSED_MD_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llama_key = config.LLAMA_API_KEY

    def get_parsed_path(self, pdf_path: Path) -> Path:
        """Returns expected markdown output file path."""
        stem = pdf_path.stem
        return self.output_dir / f"{stem}.md"

    def parse_with_llama(self, pdf_path: Path) -> Optional[str]:
        """Parse using LlamaParse for superior table and diagram structure."""
        if not self.llama_key:
            print("No LLAMA_API_KEY found, skipping LlamaParse.")
            return None

        print(f"Parsing {pdf_path.name} with LlamaParse...")
        try:
            parser = LlamaParse(
                api_key=self.llama_key,
                extract_charts=True,
                auto_mode=True,
                auto_mode_trigger_on_image_in_page=True,
                auto_mode_trigger_on_table_in_page=True,
                result_type="markdown",
            )
            extra_info = {"file_name": pdf_path.name}
            with open(pdf_path, "rb") as f:
                documents = parser.load_data(f, extra_info=extra_info)

            full_text = []
            for i, doc in enumerate(documents):
                full_text.append(f"\n\n<!-- PAGE_BREAK {i+1} -->\n\n" + doc.text)

            return "\n".join(full_text)
        except Exception as e:
            print(f"LlamaParse error on {pdf_path.name}: {e}")
            return None

    def parse_with_fitz(self, pdf_path: Path) -> str:
        """Fallback fast parser using PyMuPDF."""
        print(f"Parsing {pdf_path.name} with PyMuPDF (fast local fallback)...")
        if not fitz:
            raise ImportError("PyMuPDF (fitz) is not installed.")

        doc = fitz.open(pdf_path)
        full_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            full_text.append(f"\n\n<!-- PAGE_BREAK {page_num + 1} -->\n\n## Halaman {page_num + 1}\n\n{text}")

        return "\n".join(full_text)

    def parse_document(self, pdf_path: Path, force: bool = False) -> Path:
        """Parses a PDF and caches the output .md file."""
        pdf_path = Path(pdf_path)
        out_path = self.get_parsed_path(pdf_path)

        if out_path.exists() and not force and out_path.stat().st_size > 100:
            print(f"Parsed markdown already cached: {out_path.name}")
            return out_path

        # Try LlamaParse first
        content = self.parse_with_llama(pdf_path)

        # If LlamaParse fails or has no quota, use PyMuPDF
        if not content:
            content = self.parse_with_fitz(pdf_path)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Saved parsed markdown: {out_path.name} ({out_path.stat().st_size / 1024:.1f} KB)")
        return out_path

if __name__ == "__main__":
    parser = DocumentParser()
    sample_pdf = config.RAW_PDF_DIR / "SIDO_AR-2024.pdf"
    if sample_pdf.exists():
        parser.parse_document(sample_pdf)
