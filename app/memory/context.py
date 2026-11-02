"""Retrieve a small relevant memory context without storing new data."""
import re
from app.memory.store import MemoryStore

_STOP_WORDS = {
    "a","an","and","are","about","can","could","do","does","for","from","give",
    "help","how","i","in","is","it","me","my","of","on","please","show","tell",
    "that","the","this","to","what","when","where","which","who","why","with",
    "would","you","your","jarvis","remember","saved","memory","memories"
}

def relevant_memory_context(command: str, store: MemoryStore | None = None,
                            max_items: int = 5, max_chars: int = 2500) -> str:
    store = store or MemoryStore()
    tokens = []
    for token in re.findall(r"[A-Za-z0-9_-]{3,}", command.lower()):
        if token not in _STOP_WORDS and token not in tokens:
            tokens.append(token)
    found = {}
    for token in tokens[:8]:
        try:
            for item in store.search_facts(token, limit=max_items):
                found[item["id"]] = item
        except Exception:
            return ""
        if len(found) >= max_items:
            break
    lines, used = [], 0
    for item in list(found.values())[:max_items]:
        line = f"- {item['title']}: {item['content']} (category: {item['category']})"
        if used + len(line) > max_chars:
            break
        lines.append(line)
        used += len(line)
    return "\n".join(lines)
