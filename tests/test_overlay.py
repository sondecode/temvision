"""Tests for the overlay output system."""

import pytest

from temvision.output.overlay import Overlay, OverlayMessage


class TestOverlayMessage:
    def test_message_fields(self):
        msg = OverlayMessage(text="Test", priority="high", duration=5.0)
        assert msg.text == "Test"
        assert msg.priority == "high"
        assert msg.duration == 5.0

    def test_message_defaults(self):
        msg = OverlayMessage(text="Test")
        assert msg.priority == "normal"
        assert msg.duration == 3.0


class TestOverlay:
    def test_show_text(self, capsys):
        overlay = Overlay(use_gui=False)
        overlay.show_text("⚠️ Enemy missing", priority="high")
        captured = capsys.readouterr()
        assert "Enemy missing" in captured.out

    def test_message_history(self):
        overlay = Overlay(use_gui=False)
        overlay.show_text("msg1")
        overlay.show_text("msg2")
        history = overlay.get_history()
        assert len(history) == 2
        assert history[0].text == "msg1"
        assert history[1].text == "msg2"

    def test_clear_history(self):
        overlay = Overlay(use_gui=False)
        overlay.show_text("msg1")
        overlay.clear_history()
        assert overlay.get_history() == []

    def test_priority_icons(self, capsys):
        overlay = Overlay(use_gui=False)
        overlay.show_text("critical", priority="critical")
        captured = capsys.readouterr()
        assert "🔴" in captured.out

    def test_show_message_object(self, capsys):
        overlay = Overlay(use_gui=False)
        msg = OverlayMessage(text="Direct message", priority="low")
        overlay.show(msg)
        captured = capsys.readouterr()
        assert "Direct message" in captured.out
