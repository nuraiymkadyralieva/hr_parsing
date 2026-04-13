"""Helpers for selecting text related to HR leadership."""

from __future__ import annotations

HR_KEYWORDS: list[str] = [
    "hr",
    "\u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b",
    "\u0434\u0438\u0440\u0435\u043a\u0442\u043e\u0440 \u043f\u043e \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u0443",
    "hr-\u0434\u0438\u0440\u0435\u043a\u0442\u043e\u0440",
    "\u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u043e\u043c",
    "\u0440\u0443\u043a\u043e\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u044c \u043f\u043e \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u0443",
    "hr director",
    "head of hr",
    "director of hr",
    "people director",
    "human resources",
]


def has_hr_keywords(text: str) -> bool:
    """Check whether the text contains any HR-related keyword."""
    normalized_text = text.lower()
    return any(keyword in normalized_text for keyword in HR_KEYWORDS)


def extract_relevant_chunk(text: str, max_length: int = 3000) -> str:
    """Return a bounded text chunk around the first HR keyword occurrence."""
    if max_length <= 0:
        return ""

    normalized_text = text.lower()
    first_index: int | None = None

    for keyword in HR_KEYWORDS:
        index = normalized_text.find(keyword)
        if index == -1:
            continue
        if first_index is None or index < first_index:
            first_index = index

    if first_index is None:
        return text[:max_length]

    half_window = max_length // 2
    start = max(first_index - half_window, 0)
    end = start + max_length

    if end > len(text):
        end = len(text)
        start = max(end - max_length, 0)

    return text[start:end]
