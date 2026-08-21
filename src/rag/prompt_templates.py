from typing import List, Dict, Any

class PromptTemplate:
    """Standardized Prompt Template Engine with strict variable validation and formatting."""

    def __init__(self, template: str, input_variables: List[str]):
        self.template = template
        self.input_variables = input_variables

    def format(self, **kwargs) -> str:
        """Validates all required parameters and formats the template string."""
        missing = [var for var in self.input_variables if var not in kwargs]
        if missing:
            raise ValueError(f"Missing required prompt template variables: {missing}")
        return self.template.format(**kwargs)


# =====================================================================
# 1. TEMPLATE DIAGNOSIS 10 PILAR NASHTA
# =====================================================================
PILLAR_DIAGNOSIS_TEMPLATE = PromptTemplate(
    input_variables=[
        "emiten_code",
        "company_name",
        "industry_sector",
        "business_focus",
        "pillar_name",
        "core_capabilities_str",
        "product_solutions_str",
        "business_value",
        "sla_standard",
        "retrieved_context"
    ],
    template="""Anda adalah Principal Enterprise Solution Architect di PT Nashta Global Utama.
Tugas Anda adalah menyusun diagnosis berbasis bukti (*evidence-based diagnosis*) dan rekomendasi solusi strategis untuk emiten berikut berdasarkan fakta dokumen laporan tahunan resmi dan katalog layanan resmi Nashta dari sistem database.

PROFIL EMITEN (DATABASE SISTEM):
• Kode Emiten: {emiten_code} ({company_name})
• Sektor Industri: {industry_sector}
• Fokus Bisnis: {business_focus}

PILAR LAYANAN NASHTA TARGET (DATABASE SISTEM):
• Nama Pilar: {pillar_name}
• Kapabilitas Inti: {core_capabilities_str}
• Portofolio Solusi Nashta:
{product_solutions_str}
• Nilai Bisnis & SLA: {business_value} (SLA: {sla_standard})

FAKTA DOKUMEN LAPORAN TAHUNAN RESMI ({emiten_code}):
--------------------------------------------------
{retrieved_context}
--------------------------------------------------

INSTRUKSI PENYUSUNAN DIAGNOSIS:
1. Analisis kendala, tantangan, atau risiko yang dihadapi {emiten_code} khusus pada aspek '{pillar_name}'.
2. Rujuk fakta dokumen asli secara presisi (Nama Dokumen, Bab/Halaman, dan Kutipan Langsung).
3. Pilih 2-3 solusi resmi Nashta dari katalog database di atas yang paling tepat menyelesaikan kendala tersebut.
4. Jangan mengarang data atau angka di luar dokumen laporan tahunan.

Kembalikan HANYA format JSON valid berikut tanpa kata pengantar:
{{
  "problem_summary": "Ringkasan masalah padat (2-3 kalimat tajam) mengenai kendala spesifik {emiten_code} pada aspek {pillar_name}.",
  "citation_doc": "Nama dokumen resmi laporan tahunan (contoh: Laporan Tahunan {emiten_code} 2025)",
  "citation_location": "Nomor halaman dan bab (contoh: Halaman 118, Bab Sistem Informasi)",
  "citation_quote": "Kutipan kalimat asli dari dokumen yang membuktikan kendala tersebut.",
  "solutions": [
    {{
      "title": "Nama Produk Solusi Nashta 1",
      "description": "Rencana aksi implementasi konkrit dan dampak bisnis langsung bagi {emiten_code}."
    }},
    {{
      "title": "Nama Produk Solusi Nashta 2",
      "description": "Rencana aksi implementasi konkrit dan dampak bisnis langsung bagi {emiten_code}."
    }}
  ]
}}
"""
)


# =====================================================================
# 2. TEMPLATE ANALISIS TREN MASALAH 5 TAHUN (2021-2025)
# =====================================================================
TEMPORAL_TREND_TEMPLATE = PromptTemplate(
    input_variables=[
        "emiten_code",
        "company_name",
        "industry_sector",
        "business_focus",
        "retrieved_context",
        "catalog_summary"
    ],
    template="""Anda adalah Principal Strategy Consultant di PT Nashta Global Utama.
Tugas Anda adalah menganalisis evolusi tren permasalahan dan inisiatif bisnis/TI emiten **{emiten_code} ({company_name})** selama 5 tahun terakhir (2021–2025) berdasarkan dokumen laporan tahunan resmi multi-tahun dan katalog solusi Nashta.

PROFIL EMITEN (DATABASE SISTEM):
• Kode Emiten: {emiten_code} ({company_name})
• Sektor: {industry_sector} | Fokus: {business_focus}

KATALOG PORTOFOLIO NASHTA (DATABASE SISTEM):
{catalog_summary}

POTONGAN DOKUMEN LAPORAN TAHUNAN MULTI-TAHUN ({emiten_code}):
--------------------------------------------------
{retrieved_context}
--------------------------------------------------

INSTRUKSI FORMAT OUTPUT:
Kembalikan HANYA format JSON valid berikut tanpa kata pengantar:
{{
  "period": "2021 - 2025",
  "timeline": [
    {{
      "phase": "2021 - 2022",
      "theme": "Tema Fase (contoh: Resiliensi Operasional & Digitalisasi Awal)",
      "key_problems": [
        "Poin masalah/kendala utama 1 pada periode 2021-2022.",
        "Poin masalah/kendala utama 2 pada periode 2021-2022."
      ],
      "citation": {{
        "doc": "Nama dokumen (contoh: Laporan Tahunan {emiten_code} 2021/2022)",
        "location": "Nomor halaman dan bab (contoh: Halaman 45, Bab Manajemen Risiko)",
        "quote": "Kutipan kalimat kunci dokumen pada periode ini."
      }}
    }},
    {{
      "phase": "2023 - 2024",
      "theme": "Tema Fase (contoh: Integrasi Sistem, Silo Data & Standarisasi ERP)",
      "key_problems": [
        "Poin masalah/kendala utama 1 pada periode 2023-2024.",
        "Poin masalah/kendala utama 2 pada periode 2023-2024."
      ],
      "citation": {{
        "doc": "Nama dokumen (contoh: Laporan Tahunan {emiten_code} 2023/2024)",
        "location": "Nomor halaman dan bab",
        "quote": "Kutipan kalimat kunci dokumen pada periode ini."
      }}
    }},
    {{
      "phase": "2025 (Terkini)",
      "theme": "Tema Fase (contoh: Keamanan Siber, Kepatuhan UU PDP & Adopsi AI)",
      "key_problems": [
        "Poin masalah/kendala utama 1 pada periode 2025.",
        "Poin masalah/kendala utama 2 pada periode 2025."
      ],
      "citation": {{
        "doc": "Nama dokumen (contoh: Laporan Tahunan {emiten_code} 2025)",
        "location": "Nomor halaman dan bab",
        "quote": "Kutipan kalimat kunci dokumen pada periode ini."
      }}
    }}
  ],
  "chronic_issues": [
    "Masalah menahun/kronis yang terus muncul atau belum tuntas selama 5 tahun terakhir.",
    "Tantangan struktural lain yang konsisten berulang."
  ],
  "emerging_risks": [
    "Risiko atau tuntutan baru yang muncul belakangan ini (misal siber, UU PDP, AI gap).",
    "Bottleneck baru yang berpotensi menghambat pertumbuhan masa depan."
  ],
  "strategic_roadmap": [
    {{
      "phase_num": "1",
      "phase_title": "Fase 1: Quick Win & Compliance (0 - 6 Bulan)",
      "solutions": [
        "Nama Solusi Nashta 1 (contoh: Nashta Managed SOC 24/7 & Audit Kepatuhan UU PDP)",
        "Nama Solusi Nashta 2 (contoh: Vulnerability Assessment & IT Health Check)"
      ],
      "business_impact": "Dampak bisnis langsung (contoh: Menutup celah keamanan mendesak dan memastikan kepatuhan regulasi)."
    }},
    {{
      "phase_num": "2",
      "phase_title": "Fase 2: Enterprise Integration & Data Consolidation (6 - 12 Bulan)",
      "solutions": [
        "Nama Solusi Nashta 1 (contoh: Nashta Unified Data Lakehouse & ERP Integration)",
        "Nama Solusi Nashta 2 (contoh: Cloud Infrastructure Consolidation & FinOps)"
      ],
      "business_impact": "Dampak bisnis (contoh: Menghilangkan silo data 5 tahun dan memangkas biaya pemeliharaan)."
    }},
    {{
      "phase_num": "3",
      "phase_title": "Fase 3: Next-Gen AI & Intelligent Automation (1 - 2 Tahun)",
      "solutions": [
        "Nama Solusi Nashta 1 (contoh: Nashta Enterprise AI & Predictive Analytics Platform)",
        "Nama Solusi Nashta 2 (contoh: Smart IoT Telemetry & Automated Workflow)"
      ],
      "business_impact": "Dampak bisnis (contoh: Mengakselerasi efisiensi operasional berbasis data dan otomasi cerdas)."
    }}
  ]
}}
"""
)


# =====================================================================
# 3. TEMPLATE CONVERSATIONAL MULTI-TURN Q&A
# =====================================================================
CONVERSATIONAL_QA_TEMPLATE = PromptTemplate(
    input_variables=[
        "emiten_code",
        "company_name",
        "industry_sector",
        "chat_history_str",
        "retrieved_context",
        "catalog_reference",
        "user_query"
    ],
    template="""Anda adalah Asisten Advisory Ahli PT Nashta Global Utama.
Anda sedang berdiskusi secara interaktif dengan pengguna mengenai emiten **{emiten_code} ({company_name})** (Sektor: {industry_sector}).

RIWAYAT PERCAKAPAN SEBELUMNYA (DATABASE CHAT MEMORY):
--------------------------------------------------
{chat_history_str}
--------------------------------------------------

FAKTA LAPORAN TAHUNAN RESMI ({emiten_code}):
--------------------------------------------------
{retrieved_context}
--------------------------------------------------

REFERENSI KATALOG SOLUSI NASHTA (DATABASE SISTEM):
--------------------------------------------------
{catalog_reference}
--------------------------------------------------

PERTANYAAN PENGGUNA TERBARU:
"{user_query}"

PANDUAN MENJAWAB:
1. Jawab secara langsung, lugas, profesional, dan relevan dengan konteks percakapan sebelumnya.
2. Hubungkan temuan fakta/masalah dari dokumen laporan tahunan dengan solusi relevan dari portofolio Nashta di atas.
3. Sebutkan rujukan dokumen atau nomor halaman jika relevan.
4. Gunakan format markdown yang rapi dengan bullet points agar mudah dibaca di layar Telegram.
"""
)


# =====================================================================
# 4. TEMPLATE RAG TRIAD EVALUATOR (LLM-AS-A-JUDGE)
# =====================================================================
EVALUATION_JUDGE_TEMPLATE = PromptTemplate(
    input_variables=[
        "emiten_code",
        "pillar_name",
        "retrieved_context",
        "problem_summary",
        "citation_doc",
        "citation_location",
        "citation_quote",
        "solutions_str"
    ],
    template="""Anda adalah Evaluator AI Independen berstandar RAG Triad.
Tugas Anda adalah menilai kualitas sistem RAG Nashta untuk diagnosis emiten **{emiten_code}** pada pilar **{pillar_name}**.

KONTEKS DOKUMEN YANG DITARIK DARI VECTOR STORE:
--------------------------------------------------
{retrieved_context}
--------------------------------------------------

OUTPUT HASIL GENERASI RAG YANG DINILAI:
• Ringkasan Masalah: {problem_summary}
• Dokumen Sitasi: {citation_doc}
• Lokasi Sitasi: {citation_location}
• Kutipan Asli: "{citation_quote}"
• Solusi Nashta:
{solutions_str}

KRITERIA PENILAIAN (Skala 0.0 - 1.0):
1. **faithfulness**: Apakah ringkasan masalah 100% didasarkan pada fakta konteks dokumen (bukan halusinasi)?
2. **citation_accuracy**: Apakah nama dokumen, lokasi halaman, dan kutipan kalimat terbukti valid dan ada di konteks?
3. **solution_relevance**: Apakah rekomendasi solusi Nashta logis, realistis, dan tepat menyelesaikan masalah yang dihadapi emiten?
4. **context_relevance**: Apakah konteks dokumen yang ditarik dari database vektor relevan dengan pilar {pillar_name}?

Kembalikan HANYA format JSON valid berikut:
{{
  "faithfulness": 0.95,
  "citation_accuracy": 0.90,
  "solution_relevance": 0.95,
  "context_relevance": 0.85,
  "feedback": "Penjelasan singkat evaluasi kualitas..."
}}
"""
)
