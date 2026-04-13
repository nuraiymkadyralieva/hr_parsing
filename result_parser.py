"""Parsing helpers for DeepSeek extraction responses."""

from __future__ import annotations

import json

from pydantic import ValidationError

from models import DeepSeekResponseModel, HRResult


POSITION_PRIORITY: dict[str, int] = {
    "директор по персоналу": 1,
    "hr-директор": 2,
    "директор по управлению персоналом": 3,
    "head of hr": 4,
    "director of hr": 5,
    "руководитель по персоналу": 6,
}


def extract_json_block(raw_text: str) -> str | None:
    """Extract the first balanced JSON object from raw text."""
    start_index = raw_text.find("{")
    if start_index == -1:
        return None

    brace_balance = 0
    for index in range(start_index, len(raw_text)):
        character = raw_text[index]
        if character == "{":
            brace_balance += 1
        elif character == "}":
            brace_balance -= 1
            if brace_balance == 0:
                return raw_text[start_index : index + 1]

    return None


def normalize_text(value: str) -> str:
    """Normalize text by trimming and collapsing whitespace."""
    cleaned_value = value.strip().strip("\"'.,;:()[]{}")
    return " ".join(cleaned_value.split())


def pick_best_result(results: list[HRResult]) -> HRResult | None:
    """Pick the best HR result based on position priority."""
    if not results:
        return None

    def sort_key(item: HRResult) -> tuple[int, str]:
        normalized_position = normalize_text(item.position).lower()
        priority = POSITION_PRIORITY.get(normalized_position, 999)
        return (priority, normalized_position)

    return min(results, key=sort_key)


def parse_hr_result(raw_text: str) -> tuple[str | None, str | None]:
    """Parse raw DeepSeek output into `(position, person_fio)`."""
    json_block = extract_json_block(raw_text)
    if json_block is None:
        return (None, None)

    try:
        parsed_data = json.loads(json_block)
        response_model = DeepSeekResponseModel.model_validate(parsed_data)
    except (json.JSONDecodeError, ValidationError):
        return (None, None)

    if not response_model.results:
        return (None, None)

    best_result = pick_best_result(response_model.results)
    if best_result is None:
        return (None, None)

    position = normalize_text(best_result.position)
    person_fio = normalize_text(best_result.person_fio)

    if not position or not person_fio:
        return (None, None)

    return (position, person_fio)
