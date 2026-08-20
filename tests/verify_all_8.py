"""Verify all 8 target issuers on live API."""

import urllib.request
import json

def main():
    req = urllib.request.urlopen("http://127.0.0.1:8000/api/issuers")
    data = json.loads(req.read().decode("utf-8"))
    print("\n=========================================================================")
    print("       STATUS LIVE 8 TARGET EMITEN PADA DASHBOARD & TRUE RAG INDEX       ")
    print("=========================================================================")
    for idx, i in enumerate(data.get("issuers", []), 1):
        print(f"\n{idx}. [{i['code']}] {i['name']}")
        print(f"   * Sektor       : {i['sector_id']} ({i.get('subsector', '')})")
        print(f"   * Skor Peluang : {i['overall_opportunity_score']} / 100")
        print(f"   * Kelemahan RAG: {i['weaknesses_count']} temuan berhalaman resmi")
        print(f"   * Pilar Utama  : {i['top_priority_pillar']}")

if __name__ == "__main__":
    main()
