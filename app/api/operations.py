"""Authenticated operational endpoints for audit review and local backups."""
import io
import os
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.config import settings
from app.security import require_jarvis_key
from app.security_ops.audit import AuditStore

router = APIRouter(prefix="/operations", tags=["Security & Operations"],
                   dependencies=[Depends(require_jarvis_key)])

@router.get("/audit")
async def audit_events(limit: int = Query(100, ge=1, le=200),
                       offset: int = Query(0, ge=0)):
    return {"items": AuditStore().list(limit, offset), "limit": limit, "offset": offset,
            "note": "Audit entries exclude request bodies, query strings, and authentication headers."}

@router.post("/backup")
async def create_backup():
    """Create a downloadable ZIP backup of local SQLite databases using SQLite's online backup API."""
    data_dir = Path(settings.JARVIS_DATA_DIR).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    db_files = sorted(p for p in data_dir.glob("*.db") if p.is_file())
    if not db_files:
        raise HTTPException(status_code=404, detail="No SQLite databases found to back up.")
    buffer = io.BytesIO()
    included = []
    try:
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for source in db_files:
                # Backup API yields a consistent SQLite copy while the app may be running.
                temporary = io.BytesIO()
                with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True, timeout=10) as src:
                    with sqlite3.connect(":memory:") as destination:
                        src.backup(destination)
                        destination.commit()
                        destination.backup(sqlite3.connect(":memory:")) if False else None
                        # Serialize database through a temporary file so the ZIP contains a valid .db.
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix=".db") as temp:
                            with sqlite3.connect(temp.name) as out:
                                destination.backup(out)
                            temp.seek(0)
                            archive.writestr(source.name, temp.read())
                included.append(source.name)
    except (OSError, sqlite3.Error, zipfile.BadZipFile) as exc:
        raise HTTPException(status_code=500, detail="Backup failed; check local data directory permissions.") from exc
    buffer.seek(0)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return StreamingResponse(buffer, media_type="application/zip",
                            headers={"Content-Disposition": f'attachment; filename="jarvis-backup-{stamp}.zip"',
                                     "X-JARVIS-Backup-Database-Count": str(len(included))})

@router.get("/health")
async def operational_health():
    data_dir = Path(settings.JARVIS_DATA_DIR).expanduser()
    writable = data_dir.exists() and os.access(data_dir, os.W_OK)
    return {"status": "healthy" if writable else "degraded",
            "data_directory_configured": True, "data_directory_writable": writable,
            "database_count": len(list(data_dir.glob("*.db"))) if data_dir.exists() else 0,
            "backup_mode": "download-only; restore manually after stopping JARVIS"}
