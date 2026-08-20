"""Catalog and taxonomy management for Bank Syariah and Healthcare issuers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PILLARS_FILE = DATA_DIR / "nashta_pillars.json"
EMITEN_FILE = DATA_DIR / "emiten_database.json"


class CatalogManager:
    def __init__(self) -> None:
        self.reload()

    def reload(self) -> None:
        self.pillars_data: Dict[str, Any] = self._load_json(PILLARS_FILE)
        self.emiten_data: Dict[str, Any] = self._load_json(EMITEN_FILE)

    @staticmethod
    def _load_json(file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_pillars(self) -> List[Dict[str, Any]]:
        return self.pillars_data.get("pillars", [])

    def get_pillar_by_id(self, pillar_id: str) -> Optional[Dict[str, Any]]:
        for p in self.get_pillars():
            if p["id"] == pillar_id:
                return p
        return None

    def get_sectors(self) -> List[Dict[str, Any]]:
        return self.emiten_data.get("sectors", [])

    def get_all_issuers(self, sector_id: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, Any]]:
        self.reload()
        issuers = self.emiten_data.get("issuers", [])
        if sector_id and sector_id != "all":
            issuers = [i for i in issuers if i.get("sector_id") == sector_id]
        if query:
            q = query.lower().strip()
            issuers = [
                i for i in issuers
                if q in i.get("code", "").lower()
                or q in i.get("name", "").lower()
                or q in i.get("subsector", "").lower()
                or q in i.get("summary", "").lower()
            ]
        return issuers

    def get_issuer_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        self.reload()
        c = code.upper().strip()
        for i in self.emiten_data.get("issuers", []):
            if i.get("code") == c:
                return i
        return None

    def add_or_update_issuer(self, issuer_dict: Dict[str, Any]) -> None:
        c = issuer_dict.get("code", "").upper().strip()
        if not c:
            return
        issuers = self.emiten_data.get("issuers", [])
        found = False
        for idx, i in enumerate(issuers):
            if i.get("code") == c:
                issuers[idx] = issuer_dict
                found = True
                break
        if not found:
            issuers.append(issuer_dict)
        self.emiten_data["issuers"] = issuers
        self._save_json(EMITEN_FILE, self.emiten_data)

    @staticmethod
    def _save_json(file_path: Path, data: Dict[str, Any]) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


catalog_manager = CatalogManager()
