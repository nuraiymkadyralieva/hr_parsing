"""Utilities for writing finance director lookup results to a new Excel file."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from models import OutputRow

OUTPUT_HEADERS: tuple[str, str, str, str] = (
    "Company",
    "RegistrationNumber",
    "Finance_Position",
    "Finance_FullName",
)


class OutputWriter:
    """Collect and write output rows into a new Excel workbook."""

    def __init__(self, file_path: str | Path) -> None:
        """Initialize the output writer."""
        self.file_path = Path(file_path)
        self.rows: list[OutputRow] = []

    def add_row(self, row: OutputRow) -> None:
        """Add one output row to the result buffer."""
        self.rows.append(row)

    def save(self) -> None:
        """Write all buffered rows to a new workbook."""
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Results"
        worksheet.append(list(OUTPUT_HEADERS))

        for row in self.rows:
            worksheet.append(
                [
                    row.company,
                    row.registration_number,
                    row.finance_position,
                    row.finance_full_name,
                ]
            )

        workbook.save(self.file_path)
