"""Tests for game detector."""

import pytest
from unittest.mock import patch, MagicMock

from temvision.lol.game_detector import GameDetector, GamePhase, LOL_PROCESS_NAMES


class TestGameDetector:
    """Test game detection functionality."""

    def test_default_process_names(self):
        detector = GameDetector()
        # Should have process names based on platform
        assert isinstance(detector.process_names, list)

    def test_custom_process_names(self):
        detector = GameDetector(process_names=["MyGame.exe"])
        assert detector.process_names == ["mygame.exe"]

    def test_lol_process_names_defined(self):
        assert "windows" in LOL_PROCESS_NAMES
        assert "darwin" in LOL_PROCESS_NAMES
        assert "linux" in LOL_PROCESS_NAMES
        assert "league of legends.exe" in LOL_PROCESS_NAMES["windows"]

    @patch("psutil.process_iter")
    def test_is_game_running_found(self, mock_process_iter):
        mock_proc = MagicMock()
        mock_proc.info = {"name": "league of legends.exe"}
        mock_process_iter.return_value = [mock_proc]

        detector = GameDetector(
            process_names=["league of legends.exe"]
        )
        assert detector.is_game_running() is True

    @patch("psutil.process_iter")
    def test_is_game_running_not_found(self, mock_process_iter):
        mock_proc = MagicMock()
        mock_proc.info = {"name": "chrome.exe"}
        mock_process_iter.return_value = [mock_proc]

        detector = GameDetector(
            process_names=["league of legends.exe"]
        )
        assert detector.is_game_running() is False

    @patch("psutil.process_iter")
    def test_get_game_pid(self, mock_process_iter):
        mock_proc = MagicMock()
        mock_proc.info = {"name": "league of legends.exe", "pid": 12345}
        mock_process_iter.return_value = [mock_proc]

        detector = GameDetector(
            process_names=["league of legends.exe"]
        )
        assert detector.get_game_pid() == 12345

    @patch("psutil.process_iter")
    def test_get_game_pid_not_found(self, mock_process_iter):
        mock_proc = MagicMock()
        mock_proc.info = {"name": "chrome.exe", "pid": 99}
        mock_process_iter.return_value = [mock_proc]

        detector = GameDetector(
            process_names=["league of legends.exe"]
        )
        assert detector.get_game_pid() is None

    @patch("psutil.process_iter")
    def test_is_game_running_empty_process_list(self, mock_process_iter):
        mock_process_iter.return_value = []
        detector = GameDetector(
            process_names=["league of legends.exe"]
        )
        assert detector.is_game_running() is False


class TestGamePhase:
    """Test GamePhase enum and get_phase() logic."""

    def test_phase_closed_when_process_not_running(self):
        detector = GameDetector(process_names=["league of legends.exe"])
        with patch.object(detector, "is_game_running", return_value=False):
            phase = detector.get_phase(live_api_running=False)
        assert phase == GamePhase.CLOSED

    def test_phase_client_open_when_process_running_no_api(self):
        detector = GameDetector(process_names=["league of legends.exe"])
        with patch.object(detector, "is_game_running", return_value=True):
            phase = detector.get_phase(live_api_running=False)
        assert phase == GamePhase.CLIENT_OPEN

    def test_phase_in_game_when_live_api_responds(self):
        detector = GameDetector(process_names=["league of legends.exe"])
        phase = detector.get_phase(live_api_running=True)
        assert phase == GamePhase.IN_GAME

    def test_phase_enum_values(self):
        assert GamePhase.CLOSED.value == "closed"
        assert GamePhase.CLIENT_OPEN.value == "client_open"
        assert GamePhase.IN_GAME.value == "in_game"
