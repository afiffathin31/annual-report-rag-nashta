import sys
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

BASE_DIR = Path(r"c:\Users\Apip\Downloads\Annual Report")
SRC_DOCS_DIR = BASE_DIR / "src" / "docs"
MASTER_ADOC = SRC_DOCS_DIR / "arc42.adoc"
PDF_OUT = BASE_DIR / "build" / "docs" / "pdf" / "arc42.pdf"
IMAGES_DIR = SRC_DOCS_DIR / "images"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress header/footer on cover page
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header
        self.drawString(54, 800, "PT Nashta Global Nusantara — Software Architecture Document (arc42)")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 792, 541, 792)
        
        # Footer
        self.line(54, 45, 541, 45)
        self.drawString(54, 32, "Nashta Annual Report RAG & AI Assistant v2.2.0")
        page_str = f"Halaman {self._pageNumber} dari {page_count}"
        self.drawRightString(541, 32, page_str)
        self.restoreState()

def resolve_includes(file_path: Path, visited=None) -> str:
    if visited is None:
        visited = set()
    file_path = file_path.resolve()
    if file_path in visited:
        return ""
    visited.add(file_path)
    if not file_path.exists():
        return ""
    lines = file_path.read_text(encoding="utf-8").splitlines()
    res = []
    pat = re.compile(r"^include::([^\[]+)\[(.*?)\]")
    for line in lines:
        m = pat.match(line.strip())
        if m:
            res.append(resolve_includes(file_path.parent / m.group(1).strip(), visited))
        else:
            res.append(line)
    return "\n".join(res)

def build_pdf():
    PDF_OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=24
    )
    h1_style = ParagraphStyle(
        'ChapterH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'ChapterH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )
    callout_style = ParagraphStyle(
        'DocCallout',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=4,
        spaceAfter=4
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )
    table_head_style = ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    # Cover Page
    story.append(Spacer(1, 100))
    story.append(Paragraph("Nashta Annual Report RAG & AI Assistant", title_style))
    story.append(Paragraph("Software Architecture Document based on arc42 Standard", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284c7"), spaceAfter=20))
    story.append(Paragraph("<b>Organisasi:</b> PT Nashta Global Nusantara", body_style))
    story.append(Paragraph("<b>Versi Dokumen:</b> v2.2.0 (Standard arc42 Release)", body_style))
    story.append(Paragraph("<b>Tanggal Rilis:</b> 4 September 2026", body_style))
    story.append(Paragraph("<b>Klasifikasi:</b> Internal & Partner Architecture Reference", body_style))
    story.append(Spacer(1, 150))
    story.append(Paragraph("<i>Dokumen ini memuat spesifikasi arsitektur komprehensif sistem True RAG, integrasi Laporan Tahunan emiten BEI, metodologi perhitungan matematis 10 Pilar Solusi, serta Architectural Decision Records (ADR).</i>", body_style))
    story.append(PageBreak())

    raw_adoc = resolve_includes(MASTER_ADOC)
    lines = raw_adoc.splitlines()

    in_table = False
    table_rows = []

    def clean_text(t):
        import html as pyhtml
        codes = []
        def code_repl(m):
            codes.append(m.group(1))
            return f"___CODE_{len(codes)-1}___"
        t = re.sub(r"`([^`]+)`", code_repl, t)
        t = re.sub(r"latexmath:\[(.*?)\]", r"<b>\1</b>", t)
        t = re.sub(r"https?://[^\s\[\]]+\[(.*?)\]", r"\1", t)
        t = pyhtml.escape(t, quote=False)
        t = re.sub(r"\*([^\*]+)\*", r"<b>\1</b>", t)
        for idx, c in enumerate(codes):
            esc = pyhtml.escape(c, quote=False)
            t = t.replace(f"___CODE_{idx}___", f"<font face='Courier' color='#0369a1'>{esc}</font>")
        return t.strip()

    def flush_pdf_table():
        nonlocal in_table, table_rows
        if not in_table or not table_rows:
            in_table = False
            table_rows = []
            return
        
        # Build ReportLab Table
        data = []
        num_cols = max(len(r) for r in table_rows)
        for row_idx, r in enumerate(table_rows):
            formatted_row = []
            for cell_idx, c in enumerate(r):
                st = table_head_style if row_idx == 0 else table_cell_style
                formatted_row.append(Paragraph(clean_text(c), st))
            while len(formatted_row) < num_cols:
                formatted_row.append(Paragraph("", table_cell_style))
            data.append(formatted_row)
        
        available_width = 487
        col_w = available_width / num_cols
        t = Table(data, colWidths=[col_w] * num_cols)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))
        in_table = False
        table_rows = []

    for line in lines:
        s = line.strip()
        if not s:
            if in_table:
                flush_pdf_table()
            continue

        if s == "|===":
            if in_table:
                flush_pdf_table()
            else:
                in_table = True
                table_rows = []
            continue

        if in_table:
            if s.startswith("|"):
                cells = [c.strip() for c in s.split("|")[1:]]
                if cells:
                    table_rows.append(cells)
            continue

        if s.startswith("==") and not s.startswith("==="):
            h_text = clean_text(s.replace("==", "").strip())
            story.append(Paragraph(h_text, h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
            continue

        if s.startswith("===") and not s.startswith("===="):
            h_text = clean_text(s.replace("===", "").strip())
            story.append(Paragraph(h_text, h2_style))
            continue

        if s.startswith("* "):
            b_text = clean_text(s[2:])
            story.append(Paragraph(f"• {b_text}", bullet_style))
            continue

        # Admonition
        ad_match = re.match(r"^(NOTE|TIP|IMPORTANT|WARNING):\s*(.*)", s)
        if ad_match:
            ad_type = ad_match.group(1)
            ad_content = clean_text(ad_match.group(2))
            box_data = [[Paragraph(f"<b>[{ad_type}]</b> {ad_content}", callout_style)]]
            box_table = Table(box_data, colWidths=[487])
            box_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0284c7")),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(box_table)
            story.append(Spacer(1, 6))
            continue

        # Image
        img_match = re.match(r"^image::([^\[]+)\[(.*?)\]", s)
        if img_match:
            img_file = img_match.group(1).replace("images/", "").strip()
            caption = img_match.group(2).strip()
            img_path = IMAGES_DIR / img_file
            if img_path.exists():
                try:
                    story.append(KeepTogether([
                        Image(str(img_path), width=480, height=270),
                        Paragraph(f"<i>Gambar: {caption}</i>", ParagraphStyle('Cap', parent=body_style, fontSize=7.5, textColor=colors.HexColor("#64748b"), alignment=1)),
                        Spacer(1, 8)
                    ]))
                except Exception as e:
                    print(f"[WARN] Error embedding image {img_file}: {e}")
            continue

        if s.startswith(":") or s.startswith("//") or s.startswith("[") or s.startswith("----") or s.startswith("++++"):
            continue

        story.append(Paragraph(clean_text(s), body_style))

    if in_table:
        flush_pdf_table()

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] PDF generated at {PDF_OUT} ({PDF_OUT.stat().st_size} bytes)")

if __name__ == "__main__":
    build_pdf()
