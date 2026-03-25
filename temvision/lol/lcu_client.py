"""League Client (LCU) local API helper.

Reads the Riot lockfile to connect to the League Client API
(champion select, lobby data, etc.). Provides minimal champ-select
queries used for pre-game insights.
"""

from __future__ import annotations

import base64
import logging
import os
import platform
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Default lockfile paths per platform
DEFAULT_LOCKFILE_PATHS = {
    "darwin": os.path.expanduser(
        "~/Library/Application Support/League of Legends/lockfile"
    ),
    "windows": r"C:\\Riot Games\\League of Legends\\lockfile",
    "linux": os.path.expanduser("~/.local/share/leagueoflegends/lockfile"),
}


@dataclass
class Lockfile:
    app_name: str
    process_id: int
    port: int
    password: str
    protocol: str


class LCUClient:
    """Minimal League Client API wrapper using the local lockfile."""

    def __init__(self, lockfile_path: Optional[str] = None, timeout: float = 2.0):
        system = platform.system().lower()
        self.lockfile_path = lockfile_path or DEFAULT_LOCKFILE_PATHS.get(
            system, ""
        )
        self.timeout = timeout
        self._session = requests.Session()

    def _read_lockfile(self) -> Optional[Lockfile]:
        if not self.lockfile_path or not os.path.exists(self.lockfile_path):
            return None
        try:
            with open(self.lockfile_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except OSError as exc:
            logger.debug("Failed to read lockfile: %s", exc)
            return None

        # Format: app:PID:port:password:protocol
        parts = content.split(":")
        if len(parts) != 5:
            logger.debug("Invalid lockfile format: %s", content)
            return None

        try:
            return Lockfile(
                app_name=parts[0],
                process_id=int(parts[1]),
                port=int(parts[2]),
                password=parts[3],
                protocol=parts[4],
            )
        except ValueError:
            logger.debug("Invalid lockfile values: %s", content)
            return None

    def is_running(self) -> bool:
        """Return True if the LCU lockfile exists and is parseable."""
        return self._read_lockfile() is not None

    def _build_base_url(self, lock: Lockfile) -> str:
        return f"https://127.0.0.1:{lock.port}"

    def _headers(self, lock: Lockfile) -> dict[str, str]:
        token = base64.b64encode(f"riot:{lock.password}".encode()).decode()
        return {"Authorization": f"Basic {token}"}

    def get(self, path: str) -> Optional[dict]:
        """Perform a GET request to the LCU API.

        Args:
            path: API path beginning with '/'.
        """
        lock = self._read_lockfile()
        if lock is None:
            return None
        url = f"{self._build_base_url(lock)}{path}"
        try:
            resp = self._session.get(
                url,
                headers=self._headers(lock),
                timeout=self.timeout,
                verify=False,  # LCU uses self-signed cert
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            logger.debug("LCU GET %s failed: %s", path, exc)
            return None

    # --- High-level helpers -------------------------------------------------
    def get_champ_select_session(self) -> Optional[dict]:
        """Return champion select session if available."""
        return self.get("/lol-champ-select/v1/session")

    def get_current_summoner(self) -> Optional[dict]:
        """Return current logged-in summoner profile."""
        return self.get("/lol-summoner/v1/current-summoner")

    def close(self) -> None:
        self._session.close()
