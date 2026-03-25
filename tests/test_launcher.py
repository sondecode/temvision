"""Tests for desktop launcher and hotkey manager."""

import pytest
from unittest.mock import patch, MagicMock

from temvision.lol.launcher import HotkeyManager, Launcher


class TestHotkeyManager:
    """Test HotkeyManager registration and lifecycle."""

    def test_create(self):
        hm = HotkeyManager()
        assert hm._active is False
        assert hm._bindings == {}

    def test_register(self):
        hm = HotkeyManager()
        cb = lambda: None
        hm.register("ctrl+shift+o", cb)
        assert "ctrl+shift+o" in hm._bindings
        assert hm._bindings["ctrl+shift+o"] is cb

    def test_start_without_keyboard_package(self):
        """Start is a no-op when keyboard package is not installed."""
        hm = HotkeyManager()
        hm.register("ctrl+o", lambda: None)
        with patch("temvision.lol.launcher._HAS_KEYBOARD", False):
            hm.start()
            assert hm._active is False

    def test_stop_without_active(self):
        hm = HotkeyManager()
        hm.stop()  # no error
        assert hm._active is False


class TestLauncher:
    """Test Launcher configuration and control flow."""

    def test_create_defaults(self):
        launcher = Launcher()
        assert launcher._poll_interval == 5.0
        assert launcher._use_gui is False
        assert launcher._hotkey_toggle == "ctrl+shift+o"
        assert launcher._hotkey_quit == "ctrl+shift+q"
        assert launcher._running is False
        assert launcher._overlay_running is False

    def test_create_custom(self):
        launcher = Launcher(
            poll_interval=2.0,
            use_gui=True,
            hotkey_toggle="ctrl+t",
            hotkey_quit="ctrl+q",
        )
        assert launcher._poll_interval == 2.0
        assert launcher._use_gui is True
        assert launcher._hotkey_toggle == "ctrl+t"
        assert launcher._hotkey_quit == "ctrl+q"

    def test_stop_sets_running_false(self):
        launcher = Launcher()
        launcher._running = True
        launcher.stop()
        assert launcher._running is False

    def test_should_start_overlay_when_already_running(self):
        launcher = Launcher()
        launcher._overlay_running = True
        assert launcher._should_start_overlay() is False

    @patch("temvision.lol.launcher.GameDetector" if False else
           "temvision.lol.game_detector.GameDetector")
    def test_should_start_overlay_no_game(self, mock_cls):
        """When no game detected, should_start_overlay returns False."""
        mock_cls.return_value.is_game_running.return_value = False
        launcher = Launcher()
        launcher._overlay_running = False
        result = launcher._should_start_overlay()
        assert result is False

    def test_toggle_overlay_starts_when_not_running(self):
        launcher = Launcher()
        launcher._overlay_running = False
        with patch.object(launcher, '_start_overlay') as mock_start:
            launcher._toggle_overlay()
            mock_start.assert_called_once()

    def test_toggle_overlay_stops_when_running(self):
        launcher = Launcher()
        launcher._overlay_running = True
        with patch.object(launcher, '_stop_overlay') as mock_stop:
            launcher._toggle_overlay()
            mock_stop.assert_called_once()

    def test_stop_overlay_joins_thread(self):
        launcher = Launcher()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        launcher._overlay_thread = mock_thread
        launcher._stop_overlay()
        mock_thread.join.assert_called_once_with(timeout=3.0)

    def test_stop_overlay_no_thread(self):
        launcher = Launcher()
        launcher._overlay_thread = None
        launcher._stop_overlay()  # no error

    def test_start_overlay_noop_if_already_running(self):
        launcher = Launcher()
        launcher._overlay_running = True
        launcher._start_overlay()
        assert launcher._overlay_thread is None  # didn't create new thread
