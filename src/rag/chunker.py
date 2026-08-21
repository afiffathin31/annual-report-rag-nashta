import re
from typing import List, Dict
from pathlib import Path
import config

class DocumentChunker:
    """Smart Markdown chunker with page number tracking and section header preservation."""

    def __init__(self, chunk_size: int = config.CHUNK_SIZE, overlap: int = config.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_markdown_file(self, md_path: Path, emiten_code: str) -> List[Dict]:
        """Parses a markdown file and returns list of chunk dictionaries with metadata."""
        md_path = Path(md_path)
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract year from filename if present (e.g. SIDO_AR-2024.md -> 2024)
        year_match = re.search(r"20\d{2}", md_path.stem)
        year = year_match.group(0) if year_match else "Latest"

        # Split by page breaks
        pages_raw = re.split(r"<!-- PAGE_BREAK (\d+) -->", content)
        pages = []
        if len(pages_raw) > 1:
            for i in range(1, len(pages_raw), 2):
                page_num = int(pages_raw[i])
                page_text = pages_raw[i+1] if i+1 < len(pages_raw) else ""
                pages.append((page_num, page_text))
        else:
            pages.append((1, content))

        all_chunks = []
        chunk_counter = 0

        for page_num, page_text in pages:
            lines = page_text.splitlines()
            current_heading = f"Halaman {page_num}"
            current_buffer = []
            current_len = 0

            for line in lines:
                # Detect Markdown headings
                if line.startswith("#"):
                    heading_clean = line.strip("#").strip()
                    if heading_clean:
                        current_heading = f"{heading_clean} (Halaman {page_num})"

                line_len = len(line)
                if current_len + line_len > self.chunk_size and current_buffer:
                    chunk_text = "\n".join(current_buffer).strip()
                    if len(chunk_text) > 80: # Skip trivial tiny chunks
                        chunk_id = f"{emiten_code}_{year}_p{page_num}_c{chunk_counter}"
                        all_chunks.append({
                            "id": chunk_id,
                            "text": chunk_text,
                            "metadata": {
                                "emiten_code": emiten_code.upper(),
                                "doc_name": md_path.name,
                                "year": year,
                                "page_number": int(page_num),
                                "section_header": current_heading[:150],
                                "chunk_id": chunk_id
                            }
                        })
                        chunk_counter += 1

                    # Overlap handling
                    overlap_chars = 0
                    overlap_buffer = []
                    for prev_line in reversed(current_buffer):
                        if overlap_chars + len(prev_line) <= self.overlap:
                            overlap_buffer.insert(0, prev_line)
                            overlap_chars += len(prev_line)
                        else:
                            break
                    current_buffer = overlap_buffer
                    current_len = sum(len(l) for l in current_buffer)

                current_buffer.append(line)
                current_len += line_len + 1

            # Leftover buffer in page
            if current_buffer:
                chunk_text = "\n".join(current_buffer).strip()
                if len(chunk_text) > 80:
                    chunk_id = f"{emiten_code}_{year}_p{page_num}_c{chunk_counter}"
                    all_chunks.append({
                        "id": chunk_id,
                        "text": chunk_text,
                        "metadata": {
                            "emiten_code": emiten_code.upper(),
                            "doc_name": md_path.name,
                            "year": year,
                            "page_number": int(page_num),
                            "section_header": current_heading[:150],
                            "chunk_id": chunk_id
                        }
                    })
                    chunk_counter += 1

        print(f"Generated {len(all_chunks)} chunks for {emiten_code} ({md_path.name})")
        return all_chunks
