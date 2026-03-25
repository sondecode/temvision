"""Tests for summoner spell cooldown tracker."""

import pytest

from temvision.lol.spell_tracker import (
    SpellTracker,
    SpellState,
    PlayerSpells,
    SPELL_COOLDOWNS,
)


class TestSpellState:
    """Test SpellState dataclass."""

    def test_remaining_available(self):
        s = SpellState(spell_name="Flash", base_cooldown=300.0, available=True)
        assert s.remaining(100.0) == 0.0

    def test_remaining_on_cooldown(self):
        s = SpellState(
            spell_name="Flash", base_cooldown=300.0,
            used_at_game_time=100.0, available=False,
        )
        assert s.remaining(200.0) == 200.0
        assert s.remaining(400.0) == 0.0

    def test_update_becomes_available(self):
        s = SpellState(
            spell_name="Ignite", base_cooldown=180.0,
            used_at_game_time=10.0, available=False,
        )
        s.update(100.0)  # 90s elapsed, still on CD
        assert not s.available
        s.update(191.0)  # 181s elapsed, now available
        assert s.available


class TestPlayerSpells:
    """Test PlayerSpells formatting."""

    def test_overlay_line_all_available(self):
        ps = PlayerSpells(
            summoner_name="P1",
            champion_name="Jinx",
            spell1=SpellState(spell_name="Flash", base_cooldown=300.0, available=True),
            spell2=SpellState(spell_name="Heal", base_cooldown=240.0, available=True),
        )
        line = ps.to_overlay_line(0.0)
        assert "Jinx" in line
        assert "✅ Flash" in line
        assert "✅ Heal" in line

    def test_overlay_line_on_cd(self):
        ps = PlayerSpells(
            summoner_name="P1",
            champion_name="Caitlyn",
            spell1=SpellState(
                spell_name="Flash", base_cooldown=300.0,
                used_at_game_time=0.0, available=False,
            ),
            spell2=SpellState(spell_name="Heal", base_cooldown=240.0, available=True),
        )
        line = ps.to_overlay_line(60.0)
        assert "⏳ Flash" in line
        assert "✅ Heal" in line


class TestSpellTracker:
    """Test full spell tracker lifecycle."""

    def setup_method(self):
        self.tracker = SpellTracker()

    def test_register_and_get_lines(self):
        self.tracker.register_player("Jinx", "P1", "Flash", "Heal")
        lines = self.tracker.get_enemy_lines(["Jinx"], 0.0)
        assert len(lines) == 1
        assert "✅ Flash" in lines[0]

    def test_mark_used(self):
        self.tracker.register_player("Jinx", "P1", "Flash", "Heal")
        self.tracker.mark_used("Jinx", "Flash", 100.0)
        lines = self.tracker.get_enemy_lines(["Jinx"], 150.0)
        assert "⏳ Flash" in lines[0]

    def test_cd_expires(self):
        self.tracker.register_player("Jinx", "P1", "Ignite", "Flash")
        self.tracker.mark_used("Jinx", "Ignite", 0.0)
        # Ignite CD = 180s
        lines = self.tracker.get_enemy_lines(["Jinx"], 200.0)
        assert "✅ Ignite" in lines[0]

    def test_get_all_on_cd(self):
        self.tracker.register_player("Jinx", "P1", "Flash", "Heal")
        self.tracker.mark_used("Jinx", "Flash", 10.0)
        cds = self.tracker.get_all_on_cd(50.0)
        assert len(cds) == 1
        assert cds[0]["spell"] == "Flash"
        assert cds[0]["remaining"] > 0

    def test_reset(self):
        self.tracker.register_player("Jinx", "P1", "Flash", "Heal")
        self.tracker.reset()
        lines = self.tracker.get_enemy_lines(["Jinx"], 0.0)
        assert lines == []

    def test_mark_used_unknown_champion(self):
        # Should not raise
        self.tracker.mark_used("Unknown", "Flash", 0.0)

    def test_multiple_players(self):
        self.tracker.register_player("Jinx", "P1", "Flash", "Heal")
        self.tracker.register_player("Caitlyn", "P2", "Flash", "Barrier")
        self.tracker.mark_used("Caitlyn", "Flash", 0.0)
        lines = self.tracker.get_enemy_lines(["Jinx", "Caitlyn"], 10.0)
        assert len(lines) == 2
        assert "✅ Flash" in lines[0]   # Jinx flash available
        assert "⏳ Flash" in lines[1]   # Caitlyn flash on CD
