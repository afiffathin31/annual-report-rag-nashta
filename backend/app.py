"""FastAPI Application Server for Nashta 10-Pillars Opportunity Radar & AI Assistant (True RAG)."""

from __future__ import annotations

import logging
import os
import re
import shutil
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.catalog import catalog_manager
from backend.gdrive_ingestor import import_from_local_folder, download_from_gdrive_url
from backend.gdrive_sync import gdrive_sync_manager
from backend.harvester import harvester
from backend.pdf_processor import pdf_processor
from backend.rag_engine import rag_engine
from backend.rag_indexer import rag_indexer
from backend.scoring_engine import scoring_engine

logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Nashta 10-Pillars Opportunity Radar & AI Assistant (True RAG)",
    description="Sistem AI Assistant & Dashboard Analisis Peluang Bisnis 10 Pilar Nashta berbasis Laporan Tahunan BEI dengan Direct Google Drive Integration.",
    version="2.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class ChatRequest(BaseModel):
    query: str
    emiten_code: Optional[str] = None


class DriveSyncRequest(BaseModel):
    folder_url: str


class DriveImportRequest(BaseModel):
    folder_path: Optional[str] = None
    gdrive_url: Optional[str] = None
    emiten_code: Optional[str] = None
    year: Optional[int] = 2024


@app.get("/api/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "app": "Nashta 10-Pillars True RAG Intelligence System"}


@app.get("/api/pillars")
def get_pillars() -> Dict[str, Any]:
    return {"pillars": catalog_manager.get_pillars()}


@app.get("/api/sectors")
def get_sectors() -> Dict[str, Any]:
    return {"sectors": catalog_manager.get_sectors()}


@app.get("/api/issuers")
def get_issuers(
    sector_id: Optional[str] = Query(None, description="Filter by sector: 'bank_syariah' or 'healthcare'"),
    search: Optional[str] = Query(None, description="Search query by code, name, or keywords"),
) -> Dict[str, Any]:
    issuers = catalog_manager.get_all_issuers(sector_id=sector_id, query=search)
    enriched = []
    for i in issuers:
        analysis = scoring_engine.analyze_issuer(i["code"])
        enriched.append({
            "code": i["code"],
            "name": i["name"],
            "sector_id": i.get("sector_id"),
            "subsector": i.get("subsector"),
            "market_tier": i.get("market_tier"),
            "website": i.get("website"),
            "reports_count": len(i.get("reports", [])),
            "weaknesses_count": len(analysis.get("verified_weaknesses", [])),
            "overall_opportunity_score": analysis.get("overall_opportunity_score", 0),
            "top_priority_pillar": analysis.get("top_priority_pillars", [{}])[0].get("pillar_name", "N/A"),
        })
    return {"count": len(enriched), "issuers": enriched}


@app.get("/api/issuers/{code}")
def get_issuer_analysis(code: str) -> Dict[str, Any]:
    analysis = scoring_engine.analyze_issuer(code)
    if "error" in analysis:
        raise HTTPException(status_code=404, detail=analysis["error"])
    return analysis


@app.get("/api/overview")
def get_overview_benchmark() -> Dict[str, Any]:
    return scoring_engine.get_sector_benchmark()


@app.post("/api/chat")
def chat_ai(request: ChatRequest) -> Dict[str, Any]:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    result = rag_engine.process_chat(request.query, active_emiten=request.emiten_code)
    return result


@app.post("/api/proposal/{code}")
def generate_proposal(code: str) -> Dict[str, Any]:
    proposal_data = rag_engine.generate_proposal(code)
    return proposal_data


@app.post("/api/drive/sync-folder")
def sync_drive_folder(req: DriveSyncRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    if not req.folder_url.strip():
        raise HTTPException(status_code=400, detail="Folder URL cannot be empty")

    if gdrive_sync_manager.is_syncing:
        return {"success": False, "message": "Sinkronisasi Google Drive sedang berjalan di latar belakang."}

    # Run in background task so UI gets instant confirmation
    background_tasks.add_task(gdrive_sync_manager.sync_google_drive_folder, req.folder_url.strip())
    return {
        "success": True,
        "message": "Proses sinkronisasi Google Drive dimulai di latar belakang. Pantau progres pada status log.",
    }


@app.get("/api/drive/status")
def get_drive_status() -> Dict[str, Any]:
    return gdrive_sync_manager.get_status()


@app.post("/api/import-drive")
def import_drive(req: DriveImportRequest) -> Dict[str, Any]:
    if req.folder_path:
        path = Path(req.folder_path)
        result = import_from_local_folder(path)
        return result
    elif req.gdrive_url:
        result = download_from_gdrive_url(req.gdrive_url, output_code=req.emiten_code, output_year=req.year)
        return result
    else:
        raise HTTPException(status_code=400, detail="Must provide either folder_path or gdrive_url")


@app.post("/api/upload")
async def upload_annual_report(
    code: str = Form(...),
    year: int = Form(...),
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")

    save_path = UPLOADS_DIR / f"{code.upper()}_AR_{year}_{file.filename}"
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        indexed_chunks_count = rag_indexer.index_pdf_file(
            pdf_path=save_path,
            emiten_code=code.upper(),
            year=year,
            doc_name=file.filename
        )

        extraction_result = pdf_processor.extract_text_from_pdf(save_path, max_pages=100)

        all_keywords = []
        for p in catalog_manager.get_pillars():
            all_keywords.extend(p.get("keywords", [])[:3])
        keyword_hits = pdf_processor.search_keywords(extraction_result, all_keywords[:15])

        return {
            "success": True,
            "filename": file.filename,
            "saved_path": str(save_path),
            "code": code.upper(),
            "year": year,
            "indexed_chunks_count": indexed_chunks_count,
            "total_pages": extraction_result.get("total_pages", 0),
            "processed_pages": extraction_result.get("processed_pages", 0),
            "keyword_hits_count": len(keyword_hits),
            "sample_hits": keyword_hits[:5],
        }
    except Exception as e:
        logger.error(f"Error uploading and parsing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "documents"


@app.get("/api/documents/{code}/{year}")
def view_document_pdf(code: str, year: int) -> FileResponse:
    """Streams the authentic local PDF document directly with inline PDF disposition."""
    c_code = code.upper().strip()
    target_dir = DOCS_DIR / c_code
    if target_dir.exists():
        for pdf_file in sorted(target_dir.glob("*.pdf")):
            if str(year) in pdf_file.name:
                return FileResponse(
                    str(pdf_file),
                    media_type="application/pdf",
                    filename=pdf_file.name,
                    headers={"Content-Disposition": f"inline; filename=\"{pdf_file.name}\""}
                )

    # Check uploads directory fallback
    for upl in UPLOADS_DIR.glob("*.pdf"):
        if c_code in upl.name and str(year) in upl.name:
            return FileResponse(
                str(upl),
                media_type="application/pdf",
                filename=upl.name,
                headers={"Content-Disposition": f"inline; filename=\"{upl.name}\""}
            )

    raise HTTPException(status_code=404, detail=f"Laporan Tahunan {c_code} tahun {year} tidak ditemukan di Document Vault lokal.")


@app.get("/api/documents/{code}")
def list_local_documents(code: str) -> Dict[str, Any]:
    """Lists all authentic local PDF documents available in Document Vault for an emiten."""
    c_code = code.upper().strip()
    target_dir = DOCS_DIR / c_code
    items = []
    if target_dir.exists():
        for pdf_file in sorted(target_dir.glob("*.pdf")):
            year_matches = re.findall(r"(20(?:1[89]|2[0-6]))", pdf_file.name)
            year = int(year_matches[-1]) if year_matches else 2024
            items.append({
                "filename": pdf_file.name,
                "year": year,
                "size_mb": round(pdf_file.stat().st_size / (1024 * 1024), 2),
                "view_url": f"/api/documents/{c_code}/{year}",
                "download_url": f"/api/documents/{c_code}/{year}",
            })
    return {"code": c_code, "count": len(items), "documents": items}


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_frontend_index() -> FileResponse:
        return FileResponse(
            str(FRONTEND_DIR / "index.html"),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

