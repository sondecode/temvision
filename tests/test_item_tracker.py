"""Tests for item active cooldown tracker."""

import pytest

from temvision.lol.item_tracker import (
    ITEM_COOLDOWNS,
    ItemCooldownState,
    ItemTracker,
    PlayerItems,
)


class TestItemCooldownState:
    """Test ItemCooldownState dataclass."""

    def test_defaults(self):
        s = ItemCooldownState()
        assert s.item_name == ""
        assert s.base_cooldown == 0.0
        assert s.used_at_game_time == -1.0
        assert s.available is True
        assert s.consumed is False

    def test_remaining_when_available(self):
        s = ItemCooldownState(item_name="Zhonya's Hourglass", base_cooldown=120.0)
        assert s.remaining(100.0) == 0.0

    def test_remaining_when_on_cooldown(self):
        s = ItemCooldownState(
            item_name="Zhonya's Hourglass",
            base_cooldown=120.0,
            used_at_game_time=100.0,
            available=False,
        )
        assert s.remaining(150.0) == 70.0
        assert s.remaining(220.0) == 0.0
        assert s.remaining(300.0) == 0.0

    def test_remaining_when_consumed(self):
        s = ItemCooldownState(
            item_name="Stopwatch",
            base_cooldown=0.0,
            consumed=True,
        )
        assert s.remaining(999.0) == 0.0

    def test_remaining_never_used(self):
        s = ItemCooldownState(
            item_name="Zhonya's Hourglass",
            base_cooldown=120.0,
            used_at_game_time=-1.0,
            available=False,
        )
        assert s.remaining(100.0) == 0.0

    def test_update_comes_off_cooldown(self):
        s = ItemCooldownState(
            item_name="Zhonya's Hourglass",
            base_cooldown=120.0,
            used_at_game_time=100.0,
            available=False,
        )
        s.update(150.0)
        assert s.available is False  # still 70s left

        s.update(220.0)
        assert s.available is True  # cooldown expired

    def test_update_consumed_stays_consumed(self):
        s = ItemCooldownState(
            item_name="Stopwatch",
            base_cooldown=0.0,
            consumed=True,
            available=False,
        )
        s.update(999.0)
        assert s.consumed is True
        assert s.available is False


class TestPlayerItems:
    """Test PlayerItems overlay output."""

    def test_empty_actives(self):
        pi = PlayerItems(champion_name="Jinx")
        assert pi.to_overlay_line(100.0) == ""

    def test_available_item_line(self):
        pi = PlayerItems(
            champion_name="Jinx",
            actives=[
                ItemCooldownState(
                    item_name="Zhonya's Hourglass",
                    base_cooldown=120.0,
                    available=True,
                )
            ],
        )
        line = pi.to_overlay_line(100.0)
        assert "Jinx" in line
        assert "✅" in line
        assert "Zhonya's Hourglass" in line

    def test_on_cooldown_item_line(self):
        pi = PlayerItems(
            champion_name="Jinx",
            actives=[
                ItemCooldownState(
                    item_name="Zhonya's Hourglass",
                    base_cooldown=120.0,
                    used_at_game_time=100.0,
                    available=False,
                )
            ],
        )
        line = pi.to_overlay_line(150.0)
        assert "⏳" in line
        assert "70s" in line

    def test_consumed_item_line(self):
        pi = PlayerItems(
            champion_name="Jinx",
            actives=[
                ItemCooldownState(
                    item_name="Stopwatch",
                    base_cooldown=0.0,
                    consumed=True,
                )
            ],
        )
        line = pi.to_overlay_line(100.0)
        assert "❌" in line
        assert "Stopwatch" in line


class TestItemTracker:
    """Test ItemTracker main logic."""

    def test_refresh_items_detects_active(self):
        tracker = ItemTracker()
        tracker.refresh_items("Jinx", [
            {"displayName": "Berserker's Greaves"},
            {"displayName": "Zhonya's Hourglass"},
        ])
        lines = tracker.get_enemy_lines(["Jinx"], 100.0)
        assert len(lines) == 1
        assert "Zhonya's Hourglass" in lines[0]

    def test_refresh_items_ignores_non_active(self):
        tracker = ItemTracker()
        tracker.refresh_items("Jinx", [
            {"displayName": "Berserker's Greaves"},
            {"displayName": "Infinity Edge"},
        ])
        lines = tracker.get_enemy_lines(["Jinx"], 100.0)
        assert lines == []

    def test_mark_used_sets_cooldown(self):
        tracker = ItemTracker()
        tracker.refresh_items("Zed", [{"displayName": "Zhonya's Hourglass"}])
        tracker.mark_used("Zed", "Zhonya's Hourglass", 200.0)
        lines = tracker.get_enemy_lines(["Zed"], 210.0)
        assert "⏳" in lines[0]

    def test_mark_used_one_time_consumes(self):
        tracker = ItemTracker()
        tracker.refresh_items("Zed", [{"displayName": "Stopwatch"}])
        tracker.mark_used("Zed", "Stopwatch", 200.0)
        lines = tracker.get_enemy_lines(["Zed"], 210.0)
        assert "❌" in lines[0]

    def test_mark_used_unknown_champion_noop(self):
        tracker = ItemTracker()
        tracker.mark_used("Nonexistent", "Zhonya's Hourglass", 100.0)
        # No error raised

    def test_update_ticks_cooldowns(self):
        tracker = ItemTracker()
        tracker.refresh_items("Zed", [{"displayName": "Zhonya's Hourglass"}])
        tracker.mark_used("Zed", "Zhonya's Hourglass", 100.0)
        tracker.update(100.0)
        lines = tracker.get_enemy_lines(["Zed"], 100.0)
        assert "⏳" in lines[0]

        tracker.update(220.0)
        lines = tracker.get_enemy_lines(["Zed"], 220.0)
        assert "✅" in lines[0]

    def test_reset_clears_all(self):
        tracker = ItemTracker()
        tracker.refresh_items("Zed", [{"displayName": "Zhonya's Hourglass"}])
        tracker.reset()
        lines = tracker.get_enemy_lines(["Zed"], 100.0)
        assert lines == []

    def test_refresh_preserves_existing_state(self):
        tracker = ItemTracker()
        tracker.refresh_items("Zed", [{"displayName": "Zhonya's Hourglass"}])
        tracker.mark_used("Zed", "Zhonya's Hourglass", 100.0)

        # Refresh with same + new item
        tracker.refresh_items("Zed", [
            {"displayName": "Zhonya's Hourglass"},
            {"displayName": "Guardian Angel"},
        ])
        lines = tracker.get_enemy_lines(["Zed"], 110.0)
        joined = " ".join(lines)
        assert "⏳" in joined  # Zhonya's still on CD
        assert "Guardian Angel" in joined

    def test_get_enemy_lines_filters_champions(self):
        tracker = ItemTracker()
        tracker.refresh_items("Zed", [{"displayName": "Zhonya's Hourglass"}])
        tracker.refresh_items("Jinx", [{"displayName": "Galeforce"}])

        lines = tracker.get_enemy_lines(["Zed"], 100.0)
        assert len(lines) == 1
        assert "Zed" in lines[0]

    def test_item_cooldowns_dict_populated(self):
        assert len(ITEM_COOLDOWNS) > 10
        assert "Zhonya's Hourglass" in ITEM_COOLDOWNS
        assert "Stopwatch" in ITEM_COOLDOWNS
        assert ITEM_COOLDOWNS["Stopwatch"] == 0.0
