"""Verify RAG evidence and scoring for BRIS & BTPS trial."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.evidence_engine import evidence_engine
from backend.scoring_engine import scoring_engine

def main():
    evidence_engine.clear_cache()
    scoring_engine.clear_cache()

    for code in ["BRIS", "BTPS"]:
        analysis = scoring_engine.analyze_issuer(code)
        ev = analysis.get("verified_weaknesses", [])
        overall_score = analysis.get("overall_score")
        print(f"\n=======================================================")
        print(f"EMITEN: {code} | Overall Score: {overall_score}/100")
        print(f"Total Authentic Weaknesses Found in PDF: {len(ev)}")
        print("=======================================================")
        for idx, w in enumerate(ev[:5], 1):
            print(f"\n[{idx}] Pilar: {w.get('pillar_id')} | Severity: {w.get('severity')}")
            print(f"    Judul: {w.get('title')}")
            print(f"    Sumber: Tahun {w.get('report_year')} (Ref: {w.get('page_ref')})")
            print(f"    Kutipan Kalimat Dokumen Asli:")
            print(f"    \"{w.get('evidence_quote')}\"")
            print(f"    Peluang Solusi Nashta: {w.get('nashta_opportunity')}")

if __name__ == "__main__":
    main()
