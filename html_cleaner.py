"""Helpers for extracting readable text from HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

REMOVABLE_TAGS: tuple[str, ...] = (
    "script",
    "style",
    "noscript",
    "header",
    "footer",
    "nav",
)


def clean_html_to_text(html: str) -> str:
    """Convert raw HTML into normalized visible text."""
    soup = BeautifulSoup(html, "lxml")

    for tag_name in REMOVABLE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    raw_text = soup.get_text(separator="\n", strip=True)
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw_text.splitlines()]
    non_empty_lines = [line for line in lines if line]
    return "\n".join(non_empty_lines)


def truncate_text(text: str, max_length: int) -> str:
    """Trim text to the requested maximum length."""
    if max_length <= 0:
        return ""
    return text[:max_length]
