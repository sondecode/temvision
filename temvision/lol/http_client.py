"""Shared HTTP client utilities for LoL integrations.

Provides a minimal retry/backoff wrapper so Riot API, Live Client API,
and LCU API follow the same networking behavior and logging conventions.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class HttpClient:
    """Small requests.Session wrapper with retry/backoff support."""

    def __init__(
        self,
        timeout: float = 2.0,
        verify: bool = True,
        retries: int = 2,
        backoff_seconds: float = 0.2,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.timeout = timeout
        self.verify = verify
        self.retries = max(0, retries)
        self.backoff_seconds = max(0.0, backoff_seconds)
        self.session = session or requests.Session()

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> Optional[requests.Response]:
        """Issue an HTTP request with simple bounded retries."""
        attempts = self.retries + 1
        last_exc: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                resp = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    timeout=self.timeout,
                    verify=self.verify,
                )
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < attempts:
                    sleep_for = self.backoff_seconds * attempt
                    logger.debug(
                        "HTTP %s %s failed (attempt %d/%d): %s; retrying in %.2fs",
                        method,
                        url,
                        attempt,
                        attempts,
                        exc,
                        sleep_for,
                    )
                    time.sleep(sleep_for)
                else:
                    logger.debug(
                        "HTTP %s %s failed after %d attempts: %s",
                        method,
                        url,
                        attempts,
                        exc,
                    )

        _ = last_exc
        return None

    def close(self) -> None:
        self.session.close()
