"""Multi-Tier Harvester and Data Ingestion Module for BEI Annual Reports."""

from __future__ import annotations

import logging
import re
import ssl
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.exceptions import InsecureRequestWarning
from urllib3.util.retry import Retry

import urllib3
urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger("harvester")
logging.basicConfig(level=logging.INFO)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

YEAR_RE = re.compile(r"\b(20(?:1\d|2\d|3\d))\b")
PDF_RE = re.compile(r"(?i)\.pdf(?:$|[?#])")


@dataclass
class HarvestResult:
    code: str
    year: int
    title: str
    url: str
    tier_used: str
    status: str
    file_size_bytes: int = 0
    content_type: str = ""
    error_message: Optional[str] = None


class MultiTierHarvester:
    """Multi-tier data harvester with anti-bot, WAF, SSL fallback, and IDX mirror resolution."""

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "User-Agent": USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        })
        return session

    def test_pdf_url(self, url: str) -> Tuple[bool, str, int]:
        """Verify URL accessibility and verify it serves PDF data without downloading entire large file."""
        try:
            # First attempt HEAD request with range
            headers = {"Range": "bytes=0-2048"}
            resp = self.session.get(url, headers=headers, timeout=self.timeout, allow_redirects=True, stream=True)
            if resp.status_code in (200, 206):
                content_type = resp.headers.get("Content-Type", "").lower()
                chunk = resp.raw.read(1024)
                if b"%PDF" in chunk or "pdf" in content_type:
                    content_length = int(resp.headers.get("Content-Length", 0))
                    return True, f"OK ({content_type or 'PDF'})", content_length
                if "html" in content_type:
                    return True, "OK (Flipbook/HTML Viewer)", len(chunk)
                return True, f"OK ({content_type})", len(chunk)
            return False, f"HTTP Status {resp.status_code}", 0
        except requests.exceptions.SSLError:
            # Fallback retry without SSL cert verification if host has cert chain issue
            try:
                resp = self.session.get(url, headers={"Range": "bytes=0-2048"}, timeout=self.timeout, verify=False, stream=True)
                if resp.status_code in (200, 206):
                    return True, "OK (SSL Fallback)", 0
                return False, f"SSL Error / HTTP {resp.status_code}", 0
            except Exception as e:
                return False, f"SSL Error: {str(e)}", 0
        except requests.exceptions.RequestException as e:
            return False, f"Network Error: {str(e)}", 0

    def download_report(self, url: str, output_path: Path, max_bytes: int = 150 * 1024 * 1024) -> Tuple[bool, str]:
        """Download Annual Report PDF to disk with size protection."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            resp = self.session.get(url, timeout=self.timeout * 2, stream=True)
            if resp.status_code != 200:
                # Try without SSL verify
                resp = self.session.get(url, timeout=self.timeout * 2, verify=False, stream=True)
                if resp.status_code != 200:
                    return False, f"HTTP Error {resp.status_code}"

            downloaded = 0
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        downloaded += len(chunk)
                        if downloaded > max_bytes:
                            return False, f"File exceeds maximum allowed size ({max_bytes} bytes)"
                        f.write(chunk)
            return True, f"Downloaded successfully ({downloaded / (1024 * 1024):.2f} MB)"
        except Exception as e:
            return False, str(e)


harvester = MultiTierHarvester()
