"""Tests for game detector."""

import pytest
from unittest.mock import patch, MagicMock

from temvision.lol.game_detector import GameDetector, LOL_PROCESS_NAMES


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
