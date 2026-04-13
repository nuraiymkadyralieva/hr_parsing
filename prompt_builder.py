"""Prompt construction helpers for DeepSeek extraction."""

from __future__ import annotations

PROMPT_TEMPLATE = """Find one HR leader for the company based only on the page text below.

Allowed roles:
- директор по персоналу
- HR-директор
- руководитель по персоналу
- директор по управлению персоналом
- директор департамента по управлению персоналом
- HR Director
- Head of HR
- Director of HR
- People Director
- Chief People Officer

Rules:
- Use only the provided page text
- Do not guess outside the text
- Return JSON only
- Do not explain anything
- If nothing relevant is found, return {{"results": []}}
- If several candidates exist, return the best matching HR leader
- Preserve the person's name exactly as written in the page text
- If the page contains a Russian full name with patronymic, prefer including the patronymic in person_fio
- If patronymic is not present in the page text, still return the best available full name from the page text
- If only first name and patronymic are present in the text, return them exactly as found
- Do not shorten the name to initials

Company: {company_name}

Return format:
{{
  "results": [
    {{
      "company_name": "",
      "position": "",
      "person_fio": ""
    }}
  ]
}}

Page text:
{page_text}
"""


def build_extraction_prompt(company_name: str, page_text: str) -> str:
    """Build the extraction prompt for the DeepSeek API."""
    return PROMPT_TEMPLATE.format(company_name=company_name, page_text=page_text)
