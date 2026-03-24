"""Detect if League of Legends is running."""

import logging
import platform
from typing import Optional

import psutil

logger = logging.getLogger(__name__)

# Process names for League of Legends on different platforms
LOL_PROCESS_NAMES = {
    "windows": ["league of legends.exe", "leagueclient.exe"],
    "darwin": ["leagueoflegends", "leagueclient"],
    "linux": ["leagueoflegends", "leagueclient"],
}


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
