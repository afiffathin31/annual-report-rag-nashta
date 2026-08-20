"""Test live API for Dual-Anchor output."""

import urllib.request
import json

def main():
    for code in ["BTPS", "BRIS", "KAEF"]:
        req = urllib.request.urlopen(f"http://127.0.0.1:8000/api/issuers/{code}")
        data = json.loads(req.read().decode("utf-8"))
        print(f"\n=======================================================")
        print(f"API /api/issuers/{code}")
        print(f"Issuer: {data['issuer']['name']}")
        print(f"Total Verified Weaknesses: {len(data.get('verified_weaknesses', []))}")
        print("=======================================================")
        for idx, w in enumerate(data.get("verified_weaknesses", [])[:2], 1):
            print(f"[{idx}] {w.get('title')}")
            print(f"    * Page Ref      : {w.get('page_ref')}")
            print(f"    * Printed Page  : {w.get('printed_page')}")
            print(f"    * Physical Page : {w.get('physical_page')}")
            print(f"    * Doc Name      : {w.get('doc_name')}")
            print(f"    * Quote Excerpt : \"{w.get('evidence_quote')[:120]}...\"")

if __name__ == "__main__":
    main()
