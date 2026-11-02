import asyncio
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.config import settings
from app.knowledge.store import KnowledgeStore
from app.main import app


def test_hybrid_search_returns_source_scores_and_neighbor_context(tmp_path):
    store = KnowledgeStore(str(tmp_path / "knowledge.db"))
    first = store.add_document(
        "Project notes",
        "The observability project uses a tracing dashboard. "
        + ("Unrelated archive material. " * 45)
        + "The dashboard includes a useful latency chart.",
        "notes",
    )
    store.add_document("Cooking", "A recipe for tomato soup.", "recipes")

    results = store.search("observability dashboard", limit=10)

    assert results
    assert results[0]["document_id"] == first["id"]
    assert results[0]["retrieval_mode"] == "hybrid"
    assert results[0]["bm25_score"] > 0
    assert results[0]["vector_score"] > 0
    assert results[0]["source"] == "notes"
    assert results[0]["matched_terms"] == ["observability", "dashboard"]
    assert results[0]["context"]


def test_search_filters_by_source_and_update_time(tmp_path):
    store = KnowledgeStore(str(tmp_path / "knowledge.db"))
    store.add_document("Old note", "Findable project information.", "archive")
    store.add_document("Current note", "Findable project information.", "notes")

    results = store.search(
        "project information",
        source="notes",
        updated_after=datetime.now(timezone.utc) - timedelta(minutes=5),
        updated_before=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    assert results
    assert {item["source"] for item in results} == {"notes"}


def test_search_without_terms_uses_metadata_fallback(tmp_path):
    store = KnowledgeStore(str(tmp_path / "knowledge.db"))
    document = store.add_document("Release notes", "Version 2 is ready.", "releases")

    results = store.search("---", source="releases")

    assert results
    assert results[0]["document_id"] == document["id"]
    assert results[0]["retrieval_mode"] == "metadata_fallback"
    assert results[0]["score"] == 0


def test_agent_knowledge_search_rejects_blank_query():
    from app.tools.integration_tools import search_knowledge

    try:
        asyncio.run(search_knowledge("   "))
    except ValueError as exc:
        assert "cannot be blank" in str(exc)
    else:
        raise AssertionError("Blank knowledge queries must be rejected")


def test_search_api_exposes_filters_and_hybrid_citations(monkeypatch, tmp_path):
    import app.api.knowledge as knowledge_api

    monkeypatch.setattr(settings, "JARVIS_API_KEY", "knowledge-test-key")
    monkeypatch.setattr(knowledge_api, "store", KnowledgeStore(str(tmp_path / "knowledge.db")))
    knowledge_api.store.add_document("Design note", "The hybrid search design uses FTS.", "design")

    response = TestClient(app).get(
        "/knowledge/search",
        params={
            "q": "hybrid search",
            "source": "design",
            "updated_after": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "updated_before": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
        headers={"X-JARVIS-API-Key": "knowledge-test-key"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["source"] == "design"
    assert body["results"][0]["retrieval_mode"] == "hybrid"
    assert "TF-IDF cosine" in body["note"]


def test_knowledge_library_page_is_served_without_api_key():
    response = TestClient(app).get("/knowledge-library")

    assert response.status_code == 200
    assert "Knowledge library" in response.text
    assert "X-JARVIS-API-Key" in response.text
    assert "Search sources" in response.text


def test_agent_registry_exposes_read_only_knowledge_search():
    from app.services.tool_registry import build_agent_registry

    tool = build_agent_registry().get("knowledge.search")

    assert tool.permission == "read"
    assert tool.handler is not None
    assert tool.input_schema["required"] == ["query"]
    assert "source" in tool.input_schema["properties"]
