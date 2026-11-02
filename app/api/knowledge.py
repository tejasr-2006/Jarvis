"""Authenticated API for importing and retrieving local knowledge documents."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from app.security import require_jarvis_key
from app.knowledge.store import KnowledgeStore

router = APIRouter(prefix="/knowledge", tags=["Knowledge Retrieval"],
                   dependencies=[Depends(require_jarvis_key)])
store = KnowledgeStore()


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=200_000)
    source: str = Field(default="manual", max_length=300)

    @field_validator("title", "content")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be blank")
        return value


@router.post("/documents", status_code=201)
def add_document(body: DocumentCreate):
    return {"status": "indexed", "document": store.add_document(body.title, body.content, body.source)}


@router.get("/documents")
def list_documents(limit: int = Query(default=100, ge=1, le=200),
                   offset: int = Query(default=0, ge=0)):
    return {"documents": store.list_documents(limit, offset), "limit": limit, "offset": offset}


@router.get("/documents/{document_id}")
def get_document(document_id: int):
    item = store.get_document(document_id)
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return {"document": item}


@router.delete("/documents/{document_id}")
def delete_document(document_id: int):
    if not store.delete_document(document_id):
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return {"status": "deleted", "id": document_id}


@router.delete("/documents")
def clear_documents():
    return {"status": "cleared", "deleted": store.clear()}


@router.get("/search")
def search_knowledge(q: str = Query(min_length=1, max_length=500),
                     limit: int = Query(default=10, ge=1, le=50),
                     source: str | None = Query(default=None, max_length=300),
                     updated_after: datetime | None = None,
                     updated_before: datetime | None = None):
    if not q.strip():
        raise HTTPException(status_code=422, detail="Search query cannot be blank")
    if updated_after is not None and updated_after.tzinfo is None:
        updated_after = updated_after.replace(tzinfo=timezone.utc)
    if updated_before is not None and updated_before.tzinfo is None:
        updated_before = updated_before.replace(tzinfo=timezone.utc)
    if updated_after is not None and updated_before is not None and updated_after > updated_before:
        raise HTTPException(
            status_code=422,
            detail="updated_after must be earlier than or equal to updated_before",
        )
    results = store.search(
        q.strip(),
        limit,
        source=source,
        updated_after=updated_after,
        updated_before=updated_before,
    )
    return {
        "query": q.strip(),
        "count": len(results),
        "results": results,
        "note": "Hybrid BM25 and TF-IDF cosine ranking with reciprocal-rank fusion. Each result includes its document source and neighboring chunk context; verify the source document for important decisions.",
    }
