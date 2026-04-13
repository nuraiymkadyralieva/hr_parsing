"""Application settings for the HR parser project."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    serper_api_key: str
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    request_timeout: int = 30
    max_retries: int = 3
    sleep_between_requests: float = 1.0
    top_search_results: int = 3
    max_pages_per_company: int = 3
    max_text_length: int = 6000


def load_settings() -> Settings:
    """Load and validate settings from `.env` and environment variables."""
    load_dotenv()

    serper_api_key = os.getenv("SERPER_API_KEY", "").strip()
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()

    if not serper_api_key:
        raise ValueError("SERPER_API_KEY is required")

    if not deepseek_api_key:
        raise ValueError("DEEPSEEK_API_KEY is required")

    return Settings(
        serper_api_key=serper_api_key,
        deepseek_api_key=deepseek_api_key,
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip(),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip(),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        sleep_between_requests=float(os.getenv("SLEEP_BETWEEN_REQUESTS", "1.0")),
        top_search_results=int(os.getenv("TOP_SEARCH_RESULTS", "3")),
        max_pages_per_company=int(os.getenv("MAX_PAGES_PER_COMPANY", "3")),
        max_text_length=int(os.getenv("MAX_TEXT_LENGTH", "6000")),
    )
