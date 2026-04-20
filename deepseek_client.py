"""Client for calling the DeepSeek chat completions API."""

from __future__ import annotations

from typing import Any

import requests
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed


class DeepSeekAPIError(Exception):
    """Raised when the DeepSeek API request fails or returns invalid data."""


class DeepSeekClient:
    """HTTP client for DeepSeek chat completion requests."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int,
        max_retries: int,
    ) -> None:
        """Initialize the DeepSeek API client."""
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

    def ask(self, prompt: str) -> str:
        """Send a prompt to DeepSeek and return response content."""
        retrying = Retrying(
            retry=retry_if_exception_type(DeepSeekAPIError),
            stop=stop_after_attempt(self.max_retries),
            wait=wait_fixed(1),
            reraise=True,
        )

        for attempt in retrying:
            with attempt:
                return self._ask_once(prompt)

        raise DeepSeekAPIError("DeepSeek request failed after retries")

    def _ask_once(self, prompt: str) -> str:
        """Perform a single DeepSeek API request."""
        try:
            response = self.session.post(
                url=f"{self.base_url}/chat/completions",
                headers=self._build_headers(),
                json=self._build_payload(prompt),
                timeout=self.timeout,
            )
        except requests.Timeout as error:
            raise DeepSeekAPIError("DeepSeek request timed out") from error
        except requests.RequestException as error:
            raise DeepSeekAPIError("DeepSeek network error") from error

        if response.status_code != 200:
            raise DeepSeekAPIError(
                f"DeepSeek returned non-200 status code: {response.status_code}"
            )

        try:
            response_json = response.json()
        except ValueError as error:
            raise DeepSeekAPIError("DeepSeek returned invalid JSON") from error

        if not isinstance(response_json, dict):
            raise DeepSeekAPIError("DeepSeek returned unexpected response format")

        choices = response_json.get("choices")
        if not isinstance(choices, list) or not choices:
            raise DeepSeekAPIError("DeepSeek returned empty choices")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise DeepSeekAPIError("DeepSeek returned invalid choice format")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise DeepSeekAPIError("DeepSeek returned invalid message format")

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise DeepSeekAPIError("DeepSeek returned empty content")

        return content

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for the DeepSeek API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, prompt: str) -> dict[str, Any]:
        """Build the JSON payload for the DeepSeek request."""
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You extract finance directors from webpage text and return JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        }
