"""Serper API client for company HR-related page searches."""

from __future__ import annotations

from typing import Any

import requests
from requests import Response
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed


class SearchAPIError(Exception):
    """Raised when the Serper API request fails or returns invalid data."""


def build_search_queries(company_name: str) -> list[str]:
    """Build the fixed MVP search queries for a company."""
    normalized_name = company_name.strip()
    return [
        f'"{normalized_name}" "\u0434\u0438\u0440\u0435\u043a\u0442\u043e\u0440 \u043f\u043e \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u0443"',
        f'"{normalized_name}" "HR-\u0434\u0438\u0440\u0435\u043a\u0442\u043e\u0440"',
        f'"{normalized_name}" "\u0440\u0443\u043a\u043e\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u044c \u043f\u043e \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u0443"',
    ]


class SerperSearchClient:
    """HTTP client for Serper search requests."""

    def __init__(self, api_key: str, timeout: int, max_retries: int) -> None:
        """Initialize the Serper search client."""
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = "https://google.serper.dev/search"
        self.session = requests.Session()

    def search(self, query: str, num_results: int = 3) -> list[str]:
        """Search Serper and return URLs from the organic results list."""
        retrying = Retrying(
            retry=retry_if_exception_type(SearchAPIError),
            stop=stop_after_attempt(self.max_retries),
            wait=wait_fixed(1),
            reraise=True,
        )

        for attempt in retrying:
            with attempt:
                payload = self._perform_search(query=query, num_results=num_results)
                return self._extract_urls(payload)

        return []

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for Serper API requests."""
        return {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
        }

    def _build_payload(self, query: str, num_results: int) -> dict[str, Any]:
        """Build the JSON payload for the Serper API request."""
        return {
            "q": query,
            "num": num_results,
        }

    def _perform_search(self, query: str, num_results: int) -> dict[str, Any]:
        """Execute the Serper API request and return parsed JSON."""
        try:
            response = self.session.post(
                url=self.base_url,
                headers=self._build_headers(),
                json=self._build_payload(query=query, num_results=num_results),
                timeout=self.timeout,
            )
        except requests.Timeout as error:
            raise SearchAPIError("Serper request timed out") from error
        except requests.RequestException as error:
            raise SearchAPIError("Serper network error") from error

        self._validate_response(response)

        try:
            payload = response.json()
        except ValueError as error:
            raise SearchAPIError("Serper returned invalid JSON") from error

        if not payload:
            raise SearchAPIError("Serper returned an empty response")

        if not isinstance(payload, dict):
            raise SearchAPIError("Serper returned unexpected response format")

        return payload

    def _validate_response(self, response: Response) -> None:
        """Validate the HTTP response from Serper."""
        if response.status_code != 200:
            raise SearchAPIError(
                f"Serper returned non-200 status code: {response.status_code}"
            )

        if not response.content:
            raise SearchAPIError("Serper returned an empty HTTP body")

    def _extract_urls(self, payload: dict[str, Any]) -> list[str]:
        """Extract organic result URLs from the Serper JSON payload."""
        organic_results = payload.get("organic")

        if organic_results is None:
            return []

        if not isinstance(organic_results, list):
            raise SearchAPIError("Serper returned invalid organic results format")

        urls: list[str] = []
        for item in organic_results:
            if not isinstance(item, dict):
                continue

            link = item.get("link")
            if isinstance(link, str) and link.strip():
                urls.append(link.strip())

        return urls
