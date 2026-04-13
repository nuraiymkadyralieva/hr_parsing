"""HTTP fetch helpers for downloading web pages."""

from __future__ import annotations

import requests
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed


MAX_RESPONSE_BYTES = 2_000_000
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class FetchError(Exception):
    """Internal fetch error used for retry handling."""


class PageFetcher:
    """Download page HTML with bounded response size and retries."""

    def __init__(self, timeout: int, max_retries: int) -> None:
        """Initialize the page fetcher."""
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

    def fetch(self, url: str) -> str | None:
        """Download a single page and return text or `None` on failure."""
        retrying = Retrying(
            retry=retry_if_exception_type(FetchError),
            stop=stop_after_attempt(self.max_retries),
            wait=wait_fixed(1),
            reraise=True,
        )

        try:
            for attempt in retrying:
                with attempt:
                    return self._fetch_once(url)
        except FetchError:
            return None

        return None

    def _fetch_once(self, url: str) -> str | None:
        """Perform a single HTTP GET request."""
        try:
            response = self.session.get(
                url,
                headers={"User-Agent": DEFAULT_USER_AGENT},
                timeout=self.timeout,
                allow_redirects=True,
            )
        except requests.Timeout as error:
            raise FetchError("Request timed out") from error
        except requests.TooManyRedirects:
            return None
        except requests.RequestException as error:
            raise FetchError("Network error during page fetch") from error

        if not response.ok:
            return None

        return self._response_to_text(response)

    def _response_to_text(self, response: requests.Response) -> str | None:
        """Convert an HTTP response into a bounded text payload."""
        content = response.content[:MAX_RESPONSE_BYTES]
        if not content:
            return None

        encoding = response.encoding or response.apparent_encoding or "utf-8"
        text = content.decode(encoding, errors="ignore").strip()
        return text or None
