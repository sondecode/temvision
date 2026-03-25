"""Detect if League of Legends is running."""

import logging
import platform
from enum import Enum
from typing import Optional

import psutil

logger = logging.getLogger(__name__)

# Process names for League of Legends on different platforms
LOL_PROCESS_NAMES = {
    "windows": ["league of legends.exe", "leagueclient.exe"],
    "darwin": ["leagueoflegends", "leagueclient"],
    "linux": ["leagueoflegends", "leagueclient"],
}


class GamePhase(Enum):
    """Current phase of the League of Legends session."""

    CLOSED = "closed"           # LoL client not running
    CLIENT_OPEN = "client_open" # Client open (lobby / champion select)
    IN_GAME = "in_game"         # Active match in progress


class GameDetector:
    """Detects if League of Legends is running on the system."""

    def __init__(self, process_names: Optional[list] = None):
        system = platform.system().lower()
        if process_names is not None:
            self.process_names = [n.lower() for n in process_names]
        else:
            self.process_names = LOL_PROCESS_NAMES.get(system, [])

    def is_game_running(self) -> bool:
        """Check if any LoL process is currently running.

        Returns:
            True if a LoL process is found, False otherwise.
        """
        try:
            for proc in psutil.process_iter(["name"]):
                try:
                    proc_name = (proc.info.get("name") or "").lower()
                    if proc_name in self.process_names:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.debug("Error checking processes: %s", e)

        return False

    def get_game_pid(self) -> Optional[int]:
        """Get the PID of the running League of Legends game process.

        Returns:
            PID if found, None otherwise.
        """
        try:
            for proc in psutil.process_iter(["name", "pid"]):
                try:
                    proc_name = (proc.info.get("name") or "").lower()
                    if proc_name in self.process_names:
                        return proc.info.get("pid")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.debug("Error getting game PID: %s", e)

        return None

    def get_phase(self, live_api_running: bool = False) -> GamePhase:
        """Determine the current phase of the LoL session.

        Args:
            live_api_running: Whether the Live Client API at port 2999
                is responding (caller should check via LiveClientAPI).

        Returns:
            GamePhase.CLOSED         – LoL client not detected in processes.
            GamePhase.CLIENT_OPEN    – Client is open (lobby / champion select).
            GamePhase.IN_GAME        – An active match is in progress.
        """
        if live_api_running:
            return GamePhase.IN_GAME
        if self.is_game_running():
            return GamePhase.CLIENT_OPEN
        return GamePhase.CLOSED
