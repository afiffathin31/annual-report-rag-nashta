"""Verify Dual-Anchor RAG citations for BTPS, BRIS, KAEF, and BANK."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.evidence_engine import evidence_engine
from backend.scoring_engine import scoring_engine

def main():
    evidence_engine.clear_cache()
    scoring_engine.clear_cache()

    for code in ["BTPS", "BRIS", "KAEF", "BANK"]:
        analysis = scoring_engine.analyze_issuer(code)
        ev = analysis.get("verified_weaknesses", [])
        overall_score = analysis.get("overall_opportunity_score")
        print(f"\n=========================================================================")
        print(f"EMITEN: {code} | Skor Peluang: {overall_score}/100 | Total Kelemahan: {len(ev)}")
        print("=========================================================================")
        for idx, w in enumerate(ev[:3], 1):
            print(f"\n[{idx}] {w.get('title')} ({w.get('severity')})")
            print(f"    * Referensi Halaman : {w.get('page_ref')}")
            print(f"    * Printed Page      : {w.get('printed_page')}")
            print(f"    * Physical PDF Page : {w.get('physical_page')}")
            print(f"    * Dokumen Sumber    : {w.get('doc_name')}")
            print(f"    * Kutipan Eksak Dokumen Asli:")
            print(f"      \"{w.get('evidence_quote')}\"")
            print(f"    * Peluang Solusi Nashta: {w.get('nashta_opportunity')}")

if __name__ == "__main__":
    main()
