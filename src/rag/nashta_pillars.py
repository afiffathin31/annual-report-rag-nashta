from typing import List, Dict

NASHTA_PILLARS: List[Dict] = [
    {
        "id": "managed_service",
        "name": "Managed Service",
        "icon": "🛠️",
        "description": "Layanan pengelolaan operasional TI terpadu: monitoring infrastruktur 24/7, helpdesk, network operations center (NOC), pemeliharaan hardware/software, dan SLA tingkat tinggi.",
        "search_queries": [
            "operasional TI kendala pemeliharaan sistem downtime pemadaman sistem helpdesk SLA kontinuitas operasional",
            "biaya maintenance perbaikan sistem informasi tenaga kerja TI pihak ketiga outsource"
        ]
    },
    {
        "id": "hybrid_infra",
        "name": "IT Hybrid Infrastructure",
        "icon": "🖥️",
        "description": "Modernisasi infrastruktur server on-premise, data center, storage, network architecture, virtualisasi hyperconverged, dan disaster recovery center (DRC).",
        "search_queries": [
            "infrastruktur server data center kapasitas penyimpanan DRC disaster recovery hardware jaringan konektivitas",
            "peremajaan perangkat keras utilisasi server interkoneksi cabang dan pusat"
        ]
    },
    {
        "id": "business_app",
        "name": "Business Application",
        "icon": "💼",
        "description": "Pengembangan & integrasi aplikasi bisnis enterprise: ERP (Enterprise Resource Planning), CRM, Supply Chain Management, HRIS, Finance & Accounting System, dan Custom App.",
        "search_queries": [
            "aplikasi ERP sistem supply chain rantai pasok CRM pelanggan HRIS manajemen persediaan akuntansi otomatisasi alur kerja",
            "integrasi sistem informasi transaksi penjualan distribusi pelaporan operasional"
        ]
    },
    {
        "id": "cyber_security",
        "name": "Cyber Security",
        "icon": "🛡️",
        "description": "Layanan keamanan siber menyeluruh: Managed SOC 24/7, Penetration Testing (VAPT), Vulnerability Assessment, SIEM, kepatuhan UU Perlindungan Data Pribadi (UU PDP), dan Incident Response.",
        "search_queries": [
            "keamanan siber serangan siber risiko TI perlindungan data pribadi kebocoran data malware firewall audit keamanan VAPT ISO 27001",
            "mitigasi risiko teknologi kepatuhan regulasi OJK kerahasiaan informasi data pelanggan"
        ]
    },
    {
        "id": "data_ai",
        "name": "Data & AI",
        "icon": "📊",
        "description": "Pengolahan data cerdas: Data Warehouse, Data Lake, Business Intelligence (BI) Dashboard real-time, Machine Learning, Predictive Analytics, dan solusi Generative AI.",
        "search_queries": [
            "pengolahan data analitik business intelligence data warehouse pelaporan manual konsolidasi data forecasting prediksi penjualan",
            "pemanfaatan artificial intelligence machine learning otomasi analitik pengambilan keputusan berbasis data"
        ]
    },
    {
        "id": "digital_platform",
        "name": "Digital Business Platform",
        "icon": "🌐",
        "description": "Platform digital interaktif: Customer Portal, B2B/B2C Mobile Apps, E-commerce, Marketplace, Microservices Architecture, API Gateway, dan Omnichannel Solution.",
        "search_queries": [
            "platform digital aplikasi mobile portal pelanggan kanal penjualan digital omnichannel layanan digital e-commerce interaksi konsumen",
            "pengalaman pelanggan digitalisasi layanan adopsi kanal online transaksi digital"
        ]
    },
    {
        "id": "iot_edge",
        "name": "IoT & Edge Computing",
        "icon": "📡",
        "description": "Solusi IoT & Edge: Smart Telemetry, sensor otomatisasi pabrik/gudang, monitoring aset real-time, SCADA integration, smart logistics, dan predictive maintenance.",
        "search_queries": [
            "monitoring sensor pabrik logistik pelacakan aset efisiensi energi otomatisasi mesin pabrikasi SCADA utilitas",
            "pemantauan fasilitas suhu gudang armada pengiriman preventive maintenance peralatan produksi"
        ]
    },
    {
        "id": "consulting_advisory",
        "name": "Consulting & Advisory",
        "icon": "🧭",
        "description": "Konsultasi strategis TI: IT Master Plan (ITMP), Enterprise Architecture, IT Governance (COBIT), IT Audit, Compliance Advisory, dan Digital Transformation Strategy Roadmap.",
        "search_queries": [
            "rencana strategis TI roadmap transformasi digital tata kelola IT governance IT Master Plan audit sistem kepatuhan standar",
            "kebijakan teknologi pedoman manajemen risiko TI efektivitas organisasi teknologi informasi"
        ]
    },
    {
        "id": "cloud_services",
        "name": "Cloud Services",
        "icon": "☁️",
        "description": "Solusi komputasi awan: Cloud Migration, Multi-Cloud Management (AWS, Azure, GCP, Alibaba Cloud), Cloud Cost Optimization (FinOps), dan DevOps CI/CD Automation.",
        "search_queries": [
            "migrasi cloud komputasi awan skalabilitas server cloud hosting biaya infrastruktur fleksibilitas beban kerja cloud DevOps",
            "modernisasi aplikasi cloud native redundansi data ketersediaan tinggi high availability"
        ]
    },
    {
        "id": "bootcamp",
        "name": "Bootcamp",
        "icon": "🎓",
        "description": "Program peningkatan kapasitas SDM TI: Pelatihan IT korporat, Tech Talent Upskilling (Data, Cloud, Security, AI), Sertifikasi Profesional TI, dan Program Talent Incubation.",
        "search_queries": [
            "kompetensi SDM TI pelatihan karyawan literasi digital keahlian teknologi talent gap keterbatasan tenaga ahli TI sertifikasi",
            "pengembangan sumber daya manusia peningkatan keterampilan teknis budaya digital perusahaan"
        ]
    }
]

PILLAR_DICT = {p["id"]: p for p in NASHTA_PILLARS}
