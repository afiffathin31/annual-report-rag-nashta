import os
import re
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
import config

class GDriveDownloader:
    """Downloader to fetch folder structure and download PDF documents from public Google Drive."""

    def __init__(self, root_folder_id: str = config.GDRIVE_FOLDER_ID, output_dir: Path = config.RAW_PDF_DIR):
        self.root_folder_id = root_folder_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _fetch_folder_items(self, folder_id: str) -> List[Dict]:
        """Fetch items inside a Google Drive folder by scraping _DRIVE_ivd payload."""
        url = f"https://drive.google.com/drive/folders/{folder_id}"
        resp = self.session.get(url, headers=self.headers, timeout=15)
        if resp.status_code != 200:
            print(f"Failed to fetch GDrive folder {folder_id}: status {resp.status_code}")
            return []

        match = re.search(r"window\[\'_DRIVE_ivd\'\]\s*=\s*\\'([^\']+)\\'", resp.text) or re.search(r"window\[\'_DRIVE_ivd\'\]\s*=\s*\'([^\']+)\'", resp.text)
        if not match:
            return []

        raw_str = match.group(1).encode("utf-8").decode("unicode_escape")
        try:
            data = json.loads(raw_str)
        except Exception as e:
            print(f"Error parsing GDrive JSON payload: {e}")
            return []

        items = []
        def traverse(node):
            if isinstance(node, list):
                if len(node) >= 4 and isinstance(node[0], str) and isinstance(node[2], str) and isinstance(node[3], str):
                    item_id = node[0]
                    item_name = node[2]
                    mime_type = node[3]
                    if len(item_id) in (28, 33, 44):
                        items.append({
                            "id": item_id,
                            "name": item_name,
                            "mime_type": mime_type,
                            "is_folder": mime_type == "application/vnd.google-apps.folder"
                        })
                for child in node:
                    traverse(child)
            elif isinstance(node, dict):
                for v in node.values():
                    traverse(v)

        traverse(data)
        # Deduplicate items by id
        unique_items = {item["id"]: item for item in items}
        return list(unique_items.values())

    def list_emitens(self) -> List[Dict]:
        """Returns list of emiten folders in the root GDrive folder."""
        items = self._fetch_folder_items(self.root_folder_id)
        emiten_folders = [item for item in items if item["is_folder"]]
        return sorted(emiten_folders, key=lambda x: x["name"])

    def list_files_for_emiten(self, emiten_folder_id: str) -> List[Dict]:
        """Returns list of PDF files inside an emiten folder."""
        items = self._fetch_folder_items(emiten_folder_id)
        pdf_files = [item for item in items if not item["is_folder"] and item["name"].lower().endswith(".pdf")]
        return sorted(pdf_files, key=lambda x: x["name"])

    def download_file(self, file_id: str, destination: Path) -> bool:
        """Download a file directly from Google Drive."""
        if destination.exists() and destination.stat().st_size > 1000:
            print(f"File already exists: {destination.name} ({destination.stat().st_size / (1024*1024):.2f} MB)")
            return True

        destination.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
        print(f"Downloading {destination.name}...")

        try:
            resp = self.session.get(url, headers=self.headers, stream=True, timeout=60)
            if resp.status_code != 200:
                # Fallback URL
                alt_url = f"https://docs.google.com/uc?export=download&id={file_id}"
                resp = self.session.get(alt_url, headers=self.headers, stream=True, timeout=60)

            if resp.status_code == 200:
                with open(destination, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                size_mb = destination.stat().st_size / (1024 * 1024)
                print(f"Downloaded {destination.name} ({size_mb:.2f} MB)")
                return True
            else:
                print(f"Failed to download {file_id}: HTTP {resp.status_code}")
                return False
        except Exception as e:
            print(f"Exception downloading {file_id}: {e}")
            return False

    def sync_emitens(self, target_emitens: Optional[List[str]] = None, max_years_per_emiten: int = 1) -> List[Dict]:
        """
        Sync PDFs for target emitens.
        If target_emitens is None, syncs first 5 available emitens.
        """
        all_emitens = self.list_emitens()
        print(f"Found {len(all_emitens)} total emitens in Google Drive.")

        if target_emitens:
            selected_emitens = [e for e in all_emitens if e["name"].upper() in [t.upper() for t in target_emitens]]
        else:
            # Default to first 5
            selected_emitens = all_emitens[:5]

        synced_files = []
        for emiten in selected_emitens:
            emiten_name = emiten["name"].upper()
            emiten_folder_id = emiten["id"]
            print(f"\n--- Syncing Emiten: {emiten_name} ---")

            files = self.list_files_for_emiten(emiten_folder_id)
            print(f"Found {len(files)} files for {emiten_name}")

            # Sort descending to get newest annual reports first
            sorted_files = sorted(files, key=lambda x: x["name"], reverse=True)
            files_to_download = sorted_files[:max_years_per_emiten]

            for file_info in files_to_download:
                dest_filename = f"{emiten_name}_{file_info['name']}"
                dest_path = self.output_dir / dest_filename
                success = self.download_file(file_info["id"], dest_path)
                if success:
                    synced_files.append({
                        "emiten_code": emiten_name,
                        "file_name": dest_filename,
                        "file_path": str(dest_path),
                        "file_id": file_info["id"]
                    })
                time.sleep(1)

        return synced_files

if __name__ == "__main__":
    downloader = GDriveDownloader()
    emitens = downloader.list_emitens()
    print("Available Emitens:", [e["name"] for e in emitens])
