import os
import re
import sys
import html
from pathlib import Path

BASE_DIR = Path(r"c:\Users\Apip\Downloads\Annual Report")
SRC_DOCS_DIR = BASE_DIR / "src" / "docs"
MASTER_ADOC = SRC_DOCS_DIR / "arc42.adoc"
BUILD_DIR = BASE_DIR / "build" / "docs"
HTML_OUT_DIR = BUILD_DIR / "html5"
PDF_OUT_DIR = BUILD_DIR / "pdf"

def resolve_includes(file_path: Path, visited=None) -> str:
    if visited is None:
        visited = set()
    file_path = file_path.resolve()
    if file_path in visited:
        return ""
    visited.add(file_path)
    if not file_path.exists():
        print(f"[WARN] File not found: {file_path}")
        return ""
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    resolved_lines = []
    include_pattern = re.compile(r"^include::([^\[]+)\[(.*?)\]")
    for line in lines:
        match = include_pattern.match(line.strip())
        if match:
            inc_rel = match.group(1).strip()
            inc_path = file_path.parent / inc_rel
            resolved_lines.append(resolve_includes(inc_path, visited))
        else:
            resolved_lines.append(line)
    return "\n".join(resolved_lines)

def adoc_to_html(raw_adoc: str):
    lines = raw_adoc.splitlines()
    body_html = []
    toc_items = []
    in_code_block = False
    code_lang = ""
    code_buffer = []
    in_math_block = False
    math_buffer = []
    in_table = False
    table_headers = []
    table_rows = []

    def flush_table():
        nonlocal in_table, table_headers, table_rows
        if not in_table:
            return
        t_html = ['<div class="table-container"><table class="doc-table">']
        if table_headers:
            t_html.append("<thead><tr>")
            for h in table_headers:
                t_html.append(f"<th>{inline_format(h.strip())}</th>")
            t_html.append("</tr></thead>")
        t_html.append("<tbody>")
        for row in table_rows:
            t_html.append("<tr>")
            for cell in row:
                t_html.append(f"<td>{inline_format(cell.strip())}</td>")
            t_html.append("</tr>")
        t_html.append("</tbody></table></div>")
        body_html.append("\n".join(t_html))
        in_table = False
        table_headers = []
        table_rows = []

    def inline_format(text: str) -> str:
        text = re.sub(r"latexmath:\[(.*?)\]", r'<span class="math-inline">\(\1\)</span>', text)
        text = re.sub(r"\*([^\*]+)\*", r"<strong>\1</strong>", text)
        text = re.sub(r"_([^_]+)_", r"<em>\1</em>", text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        text = re.sub(r"(https?://[^\s\[\]]+)\[(.*?)\]", r'<a href="\1" target="_blank" rel="noopener">\2</a>', text)
        return text

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("----") or stripped.startswith("```"):
            if in_code_block:
                escaped = html.escape("\n".join(code_buffer))
                body_html.append(f'<div class="code-wrapper"><div class="code-header"><span>{code_lang.upper() or "CODE"}</span><button onclick="navigator.clipboard.writeText(this.closest(\'.code-wrapper\').querySelector(\'pre\').innerText); this.innerText=\'Copied!\'; setTimeout(()=>this.innerText=\'Copy\', 2000)">Copy</button></div><pre><code class="language-{code_lang}">{escaped}</code></pre></div>')
                in_code_block = False
                code_buffer = []
                code_lang = ""
            else:
                if in_table:
                    flush_table()
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_buffer.append(line)
            i += 1
            continue

        if stripped.startswith("[source"):
            m = re.search(r"\[source,\s*([a-zA-Z0-9_\-]+)\]", stripped)
            if m:
                code_lang = m.group(1)
            i += 1
            continue

        if stripped == "++++":
            if in_math_block:
                math_raw = "\n".join(math_buffer)
                body_html.append(f'<div class="math-block">\\[{math_raw}\\]</div>')
                in_math_block = False
                math_buffer = []
            else:
                if in_table:
                    flush_table()
                in_math_block = True
            i += 1
            continue

        if in_math_block:
            math_buffer.append(line)
            i += 1
            continue

        if stripped.startswith("[latexmath]"):
            i += 1
            continue

        admon_match = re.match(r"^(NOTE|TIP|IMPORTANT|WARNING|CAUTION):\s*(.*)", stripped)
        if admon_match:
            if in_table:
                flush_table()
            a_type = admon_match.group(1).lower()
            a_text = inline_format(admon_match.group(2))
            body_html.append(f'<div class="admonition {a_type}"><div class="admonition-title">{a_type.upper()}</div><div class="admonition-body"><p>{a_text}</p></div></div>')
            i += 1
            continue

        if stripped.startswith("[NOTE]") or stripped.startswith("[TIP]") or stripped.startswith("[IMPORTANT]") or stripped.startswith("[WARNING]"):
            i += 1
            continue

        if stripped == "|===":
            if in_table:
                flush_table()
            else:
                in_table = True
                table_headers = []
                table_rows = []
            i += 1
            continue

        if in_table:
            if stripped.startswith("|"):
                cells = [c for c in stripped.split("|")[1:]]
                if not table_headers and len(cells) > 0:
                    table_headers = cells
                else:
                    table_rows.append(cells)
            i += 1
            continue

        if stripped.startswith("[cols="):
            i += 1
            continue

        img_match = re.match(r"^image::([^\[]+)\[(.*?)\]", stripped)
        if img_match:
            if in_table:
                flush_table()
            img_src = img_match.group(1).strip()
            if not img_src.startswith("images/") and not img_src.startswith("http"):
                img_src = f"images/{img_src}"
            caption = img_match.group(2).strip()
            body_html.append(f'<figure class="doc-figure"><img src="{img_src}" alt="{caption}" loading="lazy"><figcaption>{caption}</figcaption></figure>')
            i += 1
            continue

        heading_match = re.match(r"^(={1,5})\s+(.*)", stripped)
        if heading_match:
            if in_table:
                flush_table()
            level = len(heading_match.group(1))
            h_text = heading_match.group(2).strip()
            slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", h_text.lower()).strip("-")
            if level == 1:
                body_html.append(f'<h1 id="{slug}" class="doc-title">{h_text}</h1>')
            elif level == 2:
                toc_items.append((2, slug, h_text))
                body_html.append(f'<h2 id="{slug}" class="doc-h2"><a href="#{slug}" class="header-link">#</a> {h_text}</h2>')
            elif level == 3:
                toc_items.append((3, slug, h_text))
                body_html.append(f'<h3 id="{slug}" class="doc-h3"><a href="#{slug}" class="header-link">#</a> {h_text}</h3>')
            elif level == 4:
                body_html.append(f'<h4 id="{slug}" class="doc-h4">{h_text}</h4>')
            i += 1
            continue

        if stripped.startswith("* "):
            if in_table:
                flush_table()
            item_text = inline_format(stripped[2:].strip())
            body_html.append(f'<ul class="doc-list"><li>{item_text}</li></ul>')
            i += 1
            continue

        if stripped.startswith(":") or stripped.startswith("//") or stripped.startswith("[preface]"):
            i += 1
            continue

        if not stripped:
            if in_table:
                flush_table()
            i += 1
            continue

        if in_table:
            flush_table()
        p_text = inline_format(stripped)
        body_html.append(f"<p>{p_text}</p>")
        i += 1

    if in_table:
        flush_table()

    toc_html = ['<ul class="toc-list">']
    for level, slug, text in toc_items:
        indent_class = f"toc-level-{level}"
        toc_html.append(f'<li class="{indent_class}"><a href="#{slug}">{text}</a></li>')
    toc_html.append('</ul>')

    return "\n".join(body_html), "\n".join(toc_html)

def build_full_html(body_content: str, toc_content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nashta Annual Report RAG - arc42 Software Architecture Document</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
          onload="renderMathInElement(document.body, {{delimiters: [{{left: '\\\\[', right: '\\\\]', display: true}}, {{left: '\\\\(', right: '\\\\)', display: false}}]}});"></script>
  <style>
    :root {{
      --bg-primary: #0b1120;
      --bg-secondary: #0f172a;
      --bg-card: #1e293b;
      --text-main: #e2e8f0;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.2);
      --border: #334155;
      --code-bg: #030712;
      --table-stripe: rgba(30, 41, 59, 0.6);
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --info: #3b82f6;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-primary);
      color: var(--text-main);
      line-height: 1.68;
      display: flex;
      min-height: 100vh;
    }}
    .topbar {{
      position: fixed;
      top: 0; left: 0; right: 0;
      height: 58px;
      background: rgba(15, 23, 42, 0.92);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 2rem;
      z-index: 100;
    }}
    .topbar-brand {{
      font-weight: 700;
      font-size: 1.1rem;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .topbar-brand .badge {{
      background: #0284c7;
      color: #fff;
      font-size: 0.72rem;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      text-transform: uppercase;
      font-weight: 800;
      letter-spacing: 0.05em;
    }}
    .topbar-actions {{
      display: flex;
      gap: 0.75rem;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.45rem 0.95rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--bg-card);
      color: var(--text-main);
      transition: all 0.2s ease;
    }}
    .btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
      box-shadow: 0 0 12px var(--accent-glow);
    }}
    .btn-primary {{
      background: #0284c7;
      border-color: #0284c7;
      color: #fff;
    }}
    .sidebar {{
      position: fixed;
      top: 58px;
      bottom: 0;
      left: 0;
      width: 320px;
      background: var(--bg-secondary);
      border-right: 1px solid var(--border);
      overflow-y: auto;
      padding: 1.5rem 1rem;
      font-size: 0.9rem;
    }}
    .sidebar-title {{
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--text-muted);
      margin-bottom: 0.85rem;
      padding-left: 0.5rem;
      font-weight: 700;
    }}
    .toc-list {{ list-style: none; }}
    .toc-list li {{ margin-bottom: 0.35rem; }}
    .toc-list a {{
      color: var(--text-muted);
      text-decoration: none;
      display: block;
      padding: 0.35rem 0.6rem;
      border-radius: 6px;
      transition: all 0.15s ease;
      line-height: 1.35;
    }}
    .toc-list a:hover {{
      color: var(--accent);
      background: rgba(56, 189, 248, 0.08);
    }}
    .toc-level-3 {{ padding-left: 1.25rem; font-size: 0.85rem; }}
    .content {{
      margin-top: 58px;
      margin-left: 320px;
      padding: 3rem 4rem;
      max-width: 1040px;
      width: 100%;
    }}
    h1.doc-title {{ font-size: 2.2rem; color: #fff; margin-bottom: 0.5rem; border-bottom: 2px solid var(--accent); padding-bottom: 0.75rem; }}
    h2.doc-h2 {{ font-size: 1.55rem; color: #f8fafc; margin-top: 2.8rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; }}
    h3.doc-h3 {{ font-size: 1.22rem; color: #38bdf8; margin-top: 1.8rem; margin-bottom: 0.75rem; }}
    h4.doc-h4 {{ font-size: 1.05rem; color: #93c5fd; margin-top: 1.3rem; margin-bottom: 0.5rem; }}
    p {{ margin-bottom: 1rem; color: var(--text-main); }}
    .header-link {{ color: var(--text-muted); text-decoration: none; opacity: 0.4; margin-right: 0.25rem; }}
    .header-link:hover {{ opacity: 1; color: var(--accent); }}
    ul.doc-list {{ margin-left: 1.75rem; margin-bottom: 1rem; }}
    ul.doc-list li {{ margin-bottom: 0.35rem; }}
    strong {{ color: #fff; }}
    code {{ background: var(--code-bg); color: #38bdf8; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.88em; border: 1px solid rgba(255, 255, 255, 0.08); font-family: monospace; }}
    .code-wrapper {{ background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px; margin: 1.25rem 0; overflow: hidden; }}
    .code-header {{ background: #0f172a; padding: 0.4rem 0.85rem; font-size: 0.75rem; color: var(--text-muted); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); }}
    .code-header button {{ background: transparent; border: 1px solid var(--border); color: var(--text-muted); padding: 0.2rem 0.5rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; }}
    pre {{ padding: 1rem; overflow-x: auto; font-size: 0.88rem; line-height: 1.5; }}
    .table-container {{ overflow-x: auto; margin: 1.5rem 0; border-radius: 8px; border: 1px solid var(--border); }}
    table.doc-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; text-align: left; }}
    table.doc-table th {{ background: #1e293b; color: #f8fafc; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); font-weight: 600; }}
    table.doc-table td {{ padding: 0.7rem 1rem; border-bottom: 1px solid rgba(51, 65, 85, 0.4); color: var(--text-main); }}
    table.doc-table tr:nth-child(even) td {{ background: var(--table-stripe); }}
    figure.doc-figure {{ margin: 2rem 0; text-align: center; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }}
    figure.doc-figure img {{ max-width: 100%; height: auto; border-radius: 6px; }}
    figcaption {{ margin-top: 0.75rem; font-size: 0.85rem; color: var(--text-muted); font-style: italic; }}
    .admonition {{ border-left: 4px solid var(--info); background: rgba(59, 130, 246, 0.08); padding: 1rem 1.25rem; border-radius: 0 8px 8px 0; margin: 1.25rem 0; }}
    .admonition.note {{ border-color: var(--info); background: rgba(59, 130, 246, 0.08); }}
    .admonition.tip {{ border-color: var(--success); background: rgba(16, 185, 129, 0.08); }}
    .admonition.important {{ border-color: var(--warning); background: rgba(245, 158, 11, 0.08); }}
    .admonition.warning {{ border-color: var(--danger); background: rgba(239, 68, 68, 0.08); }}
    .admonition-title {{ font-weight: 700; font-size: 0.8rem; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.35rem; color: #fff; }}
    .math-block {{ background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin: 1.25rem 0; text-align: center; overflow-x: auto; }}
  </style>
</head>
<body>
  <div class="topbar">
    <div class="topbar-brand">
      <span>Nashta Annual Report RAG</span>
      <span class="badge">arc42 Standard</span>
    </div>
    <div class="topbar-actions">
      <a href="/docs/system/" class="btn">MkDocs System</a>
      <a href="/docs/arc42/arc42.pdf" class="btn btn-primary" download>Unduh PDF</a>
      <button onclick="window.print()" class="btn">Cetak Dokumen</button>
    </div>
  </div>
  <nav class="sidebar">
    <div class="sidebar-title">Daftar Bab arc42</div>
    {toc_content}
  </nav>
  <main class="content">
    {body_content}
  </main>
</body>
</html>
"""

def build_pdf(html_path: Path, pdf_path: Path):
    try:
        from xhtml2pdf import pisa
        html_text = html_path.read_text(encoding="utf-8")
        pdf_html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
  @page {{ size: a4 portrait; margin: 2cm; @bottom-right {{ content: "Halaman " counter(page) " dari " counter(pages); font-size: 8pt; color: #666; }} }}
  body {{ font-family: Helvetica, Arial, sans-serif; font-size: 9pt; line-height: 1.45; color: #222; }}
  h1 {{ font-size: 18pt; color: #0284c7; border-bottom: 1.5pt solid #0284c7; padding-bottom: 4pt; margin-bottom: 10pt; }}
  h2 {{ font-size: 13pt; color: #0369a1; border-bottom: 0.5pt solid #ccc; padding-bottom: 3pt; margin-top: 16pt; }}
  h3 {{ font-size: 11pt; color: #0f172a; margin-top: 10pt; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8pt 0; }}
  th {{ background-color: #f1f5f9; color: #0f172a; font-weight: bold; padding: 4pt; border: 0.5pt solid #cbd5e1; font-size: 8pt; text-align: left; }}
  td {{ padding: 4pt; border: 0.5pt solid #cbd5e1; font-size: 8pt; }}
  pre {{ background-color: #f8fafc; border: 0.5pt solid #e2e8f0; padding: 5pt; font-size: 7.5pt; }}
  .admonition {{ border-left: 3pt solid #0284c7; background-color: #f0f9ff; padding: 5pt; margin: 6pt 0; }}
  img {{ max-width: 100%; height: auto; }}
</style></head><body>"""
        m = re.search(r"<main class=\"content\">(.*?)</main>", html_text, re.DOTALL)
        if m:
            c = m.group(1)
            c = re.sub(r"<button.*?</button>", "", c)
            c = re.sub(r"<a href=\"#[^\"]*\" class=\"header-link\">#</a>", "", c)
            pdf_html += c
        pdf_html += "</body></html>"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        with open(pdf_path, "wb") as f_out:
            pisa.CreatePDF(pdf_html, dest=f_out)
        print(f"[SUCCESS] PDF tersimpan di: {pdf_path} ({pdf_path.stat().st_size} bytes)")
    except Exception as ex:
        print(f"[ERROR] Gagal membuat PDF: {ex}")

if __name__ == "__main__":
    print("Membaca arc42.adoc...")
    raw = resolve_includes(MASTER_ADOC)
    print(f"Total baris: {len(raw.splitlines())}")
    body, toc = adoc_to_html(raw)
    full = build_full_html(body, toc)
    HTML_OUT_DIR.mkdir(parents=True, exist_ok=True)
    PDF_OUT_DIR.mkdir(parents=True, exist_ok=True)
    src_images = SRC_DOCS_DIR / "images"
    dst_images = HTML_OUT_DIR / "images"
    if src_images.exists():
        dst_images.mkdir(parents=True, exist_ok=True)
        for img in src_images.glob("*.png"):
            (dst_images / img.name).write_bytes(img.read_bytes())
    html_f = HTML_OUT_DIR / "arc42.html"
    html_f.write_text(full, encoding="utf-8")
    print(f"[SUCCESS] HTML tersimpan di: {html_f}")
    pdf_f = PDF_OUT_DIR / "arc42.pdf"
    build_pdf(html_f, pdf_f)
