"""Browser entry point for the local knowledge library."""
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter(tags=["Interface"])


@router.get("/knowledge-library", include_in_schema=False)
def knowledge_library_page():
    page = Path(__file__).resolve().parents[1] / "static" / "knowledge.html"
    return FileResponse(page, headers={"Cache-Control": "no-store"})
