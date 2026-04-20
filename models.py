"""Shared models for the finance director parser project."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field


class DirectorResult(BaseModel):
    """Structured finance director record extracted from model output."""

    company_name: Optional[str] = None
    position: str
    person_fio: str


class DeepSeekResponseModel(BaseModel):
    """Container for parsed DeepSeek response results."""

    results: list[DirectorResult] = Field(default_factory=list)


@dataclass(slots=True)
class InputCompanyRow:
    """Single source workbook row with company metadata."""

    row_index: int
    company: str
    registration_number: str


@dataclass(slots=True)
class OutputRow:
    """Single output workbook row with extracted finance director data."""

    company: str
    registration_number: str
    finance_position: str
    finance_full_name: str


@dataclass(slots=True)
class ProcessingStats:
    """Processing counters collected during the pipeline run."""

    total_rows: int = 0
    processed_rows: int = 0
    found_director: int = 0
    empty_result: int = 0
    search_errors: int = 0
    fetch_errors: int = 0
    api_errors: int = 0
    parse_errors: int = 0
