"""Pure helpers for wake phrase matching and transcript cleanup."""
from __future__ import annotations

import re


def normalize_speech(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def extract_command_after_wake_phrase(text: str, wake_phrase: str = "jarvis") -> str | None:
    """Return command text following the wake phrase, or None if it is absent.

    Matching is word-boundary based to avoid waking on words such as 'jarvis-like'.
    """
    normalized = normalize_speech(text)
    phrase = normalize_speech(wake_phrase)
    if not phrase:
        return None
    pattern = r"(?<![\w-])" + re.escape(phrase) + r"(?![\w-])"
    match = re.search(pattern, normalized)
    if not match:
        return None
    return normalized[match.end():].strip(" ,.!?;:-")


def is_wake_phrase_only(text: str, wake_phrase: str = "jarvis") -> bool:
    return extract_command_after_wake_phrase(text, wake_phrase) == ""
