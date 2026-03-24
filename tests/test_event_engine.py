"""Tests for event detection engine."""

import pytest

from temvision.lol.event_engine import (
    EventEngine,
    EventThresholds,
    GameEvent,
    POWER_SPIKE_LEVELS,
)
from temvision.lol.models import PlayerData, GameData


class TestGameEvent:
    """Test GameEvent dataclass."""

    def test_default_values(self):
        e = GameEvent(event_type="test", message="Test event")
        assert e.event_type == "test"
        assert e.message == "Test event"
        assert e.priority == "normal"
        assert e.icon == ""
        assert e.metadata == {}

    def test_display_text_with_icon(self):
        e = GameEvent(event_type="test", message="Alert", icon="⚠️")
        assert e.display_text == "⚠️ Alert"

    def test_display_text_without_icon(self):
        e = GameEvent(event_type="test", message="Alert")
        assert e.display_text == "Alert"


class TestEventThresholds:
    """Test configurable event thresholds."""

    def test_default_thresholds(self):
        t = EventThresholds()
        assert t.enemy_missing_seconds == 20.0
        assert t.jungle_missing_seconds == 15.0
        assert t.hp_burst_threshold == 20.0
        assert t.combat_hp_drop_threshold == 10.0

    def test_custom_thresholds(self):
        t = EventThresholds(enemy_missing_seconds=30.0)
        assert t.enemy_missing_seconds == 30.0


class TestEventEngine:
    """Test event detection engine."""

    def setup_method(self):
        self.engine = EventEngine()

    def test_process_no_active_player(self):
        game_data = GameData()
        events = self.engine.process(game_data)
        assert events == []

    def test_detect_level_up(self):
        """Detect level-up when player level increases."""
        game_data_1 = GameData(
            game_time=100.0,
            active_player=PlayerData(
                champion_name="Jinx", level=5, hp=1000, max_hp=1000
            ),
            enemies=[],
        )
        game_data_2 = GameData(
            game_time=110.0,
            active_player=PlayerData(
                champion_name="Jinx", level=6, hp=1000, max_hp=1000
            ),
            enemies=[],
        )

        # First tick: establishes baseline
        events1 = self.engine.process(game_data_1)
        # Second tick: should detect level up
        events2 = self.engine.process(game_data_2)

        level_ups = [e for e in events2 if e.event_type == "level_up"]
        assert len(level_ups) == 1
        assert "level 6" in level_ups[0].message.lower()

    def test_detect_power_spike_level_6(self):
        """Detect power spike at level 6 (ultimate unlock)."""
        game_data_1 = GameData(
            game_time=400.0,
            active_player=PlayerData(
                champion_name="Zed", level=5, hp=800, max_hp=800
            ),
            enemies=[],
        )
        game_data_2 = GameData(
            game_time=420.0,
            active_player=PlayerData(
                champion_name="Zed", level=6, hp=850, max_hp=850
            ),
            enemies=[],
        )

        self.engine.process(game_data_1)
        events = self.engine.process(game_data_2)

        spikes = [e for e in events if e.event_type == "power_spike"]
        assert len(spikes) == 1
        assert "ultimate" in spikes[0].message.lower()
        assert spikes[0].priority == "high"

    def test_detect_power_spike_level_11(self):
        """Detect power spike at level 11."""
        game_data_1 = GameData(
            game_time=900.0,
            active_player=PlayerData(
                champion_name="Jinx", level=10, hp=1000, max_hp=1000
            ),
            enemies=[],
        )
        game_data_2 = GameData(
            game_time=920.0,
            active_player=PlayerData(
                champion_name="Jinx", level=11, hp=1000, max_hp=1000
            ),
            enemies=[],
        )

        self.engine.process(game_data_1)
        events = self.engine.process(game_data_2)

        spikes = [e for e in events if e.event_type == "power_spike"]
        assert len(spikes) == 1
        assert "11" in spikes[0].message

    def test_detect_power_spike_level_16(self):
        """Detect power spike at level 16."""
        game_data_1 = GameData(
            game_time=1500.0,
            active_player=PlayerData(
                champion_name="Jinx", level=15, hp=1500, max_hp=1500
            ),
            enemies=[],
        )
        game_data_2 = GameData(
            game_time=1520.0,
            active_player=PlayerData(
                champion_name="Jinx", level=16, hp=1500, max_hp=1500
            ),
            enemies=[],
        )

        self.engine.process(game_data_1)
        events = self.engine.process(game_data_2)

        spikes = [e for e in events if e.event_type == "power_spike"]
        assert len(spikes) == 1
        assert "16" in spikes[0].message

    def test_no_power_spike_at_normal_level(self):
        """No power spike at non-key levels."""
        game_data_1 = GameData(
            game_time=300.0,
            active_player=PlayerData(
                champion_name="Jinx", level=3, hp=700, max_hp=700
            ),
            enemies=[],
        )
        game_data_2 = GameData(
            game_time=320.0,
            active_player=PlayerData(
                champion_name="Jinx", level=4, hp=750, max_hp=750
            ),
            enemies=[],
        )

        self.engine.process(game_data_1)
        events = self.engine.process(game_data_2)

        spikes = [e for e in events if e.event_type == "power_spike"]
        assert len(spikes) == 0

    def test_detect_enemy_missing(self):
        """Detect enemy missing after threshold duration."""
        # Enemy with no stat changes for > 20 seconds
        enemy = PlayerData(
            champion_name="Zed",
            level=6,
            kills=2,
            deaths=1,
            assists=1,
            creep_score=50,
        )
        game_data_1 = GameData(
            game_time=100.0,
            active_player=PlayerData(
                champion_name="Jinx", level=6, hp=1000, max_hp=1000
            ),
            enemies=[enemy],
        )

        # First tick: establishes baseline, enemy last seen at 100.0
        self.engine.process(game_data_1)

        # Same enemy stats 25 seconds later (no changes = missing)
        enemy_same = PlayerData(
            champion_name="Zed",
            level=6,
            kills=2,
            deaths=1,
            assists=1,
            creep_score=50,
        )
        game_data_2 = GameData(
            game_time=125.0,
            active_player=PlayerData(
                champion_name="Jinx", level=6, hp=1000, max_hp=1000
            ),
            enemies=[enemy_same],
        )

        events = self.engine.process(game_data_2)
        missing = [e for e in events if e.event_type == "enemy_missing"]
        assert len(missing) == 1
        assert "Zed" in missing[0].message

    def test_enemy_not_missing_when_stats_change(self):
        """Enemy not flagged as missing when stats update."""
        enemy1 = PlayerData(
            champion_name="Zed",
            level=6,
            kills=2,
            deaths=1,
            assists=1,
            creep_score=50,
        )
        game_data_1 = GameData(
            game_time=100.0,
            active_player=PlayerData(
                champion_name="Jinx", level=6, hp=1000, max_hp=1000
            ),
            enemies=[enemy1],
        )

        self.engine.process(game_data_1)

        # Enemy CS changed (they are visible, farming)
        enemy2 = PlayerData(
            champion_name="Zed",
            level=6,
            kills=2,
            deaths=1,
            assists=1,
            creep_score=55,
        )
        game_data_2 = GameData(
            game_time=125.0,
            active_player=PlayerData(
                champion_name="Jinx", level=6, hp=1000, max_hp=1000
            ),
            enemies=[enemy2],
        )

        events = self.engine.process(game_data_2)
        missing = [e for e in events if e.event_type == "enemy_missing"]
        assert len(missing) == 0

    def test_detect_jungle_gank_risk(self):
        """Detect gank risk when enemy jungler is missing."""
        jungler = PlayerData(
            champion_name="Lee Sin",
            position="JUNGLE",
            level=5,
            kills=1,
            deaths=0,
            assists=2,
            creep_score=30,
        )
        game_data_1 = GameData(
            game_time=300.0,
            active_player=PlayerData(
                champion_name="Jinx", level=5, hp=1000, max_hp=1000
            ),
            enemies=[jungler],
        )

        self.engine.process(game_data_1)

        # Same jungler stats 20 seconds later
        jungler_same = PlayerData(
            champion_name="Lee Sin",
            position="JUNGLE",
            level=5,
            kills=1,
            deaths=0,
            assists=2,
            creep_score=30,
        )
        game_data_2 = GameData(
            game_time=320.0,
            active_player=PlayerData(
                champion_name="Jinx", level=5, hp=1000, max_hp=1000
            ),
            enemies=[jungler_same],
        )

        events = self.engine.process(game_data_2)
        gank = [e for e in events if e.event_type == "gank_risk"]
        assert len(gank) == 1
        assert "Lee Sin" in gank[0].message
        assert gank[0].priority == "critical"

    def test_detect_combat_burst(self):
        """Detect heavy damage burst (>20% HP drop)."""
        game_data_1 = GameData(
            game_time=500.0,
            active_player=PlayerData(
                champion_name="Jinx", level=8, hp=1000, max_hp=1000
            ),
            enemies=[],
        )

        self.engine.process(game_data_1)

        # HP dropped from 100% to 70% in one tick
        game_data_2 = GameData(
            game_time=500.25,
            active_player=PlayerData(
                champion_name="Jinx", level=8, hp=700, max_hp=1000
            ),
            enemies=[],
        )

        events = self.engine.process(game_data_2)
        burst = [e for e in events if e.event_type == "combat_burst"]
        assert len(burst) == 1
        assert burst[0].priority == "critical"

    def test_detect_combat(self):
        """Detect moderate combat (>10% HP drop)."""
        game_data_1 = GameData(
            game_time=500.0,
            active_player=PlayerData(
                champion_name="Jinx", level=8, hp=1000, max_hp=1000
            ),
            enemies=[],
        )

        self.engine.process(game_data_1)

        # HP dropped from 100% to 85% in one tick
        game_data_2 = GameData(
            game_time=500.25,
            active_player=PlayerData(
                champion_name="Jinx", level=8, hp=850, max_hp=1000
            ),
            enemies=[],
        )

        events = self.engine.process(game_data_2)
        combat = [e for e in events if e.event_type == "combat_detected"]
        assert len(combat) == 1
        assert combat[0].priority == "high"

    def test_reset(self):
        """Verify reset clears all tracking state."""
        game_data = GameData(
            game_time=100.0,
            active_player=PlayerData(
                champion_name="Jinx", level=5, hp=1000, max_hp=1000
            ),
            enemies=[PlayerData(champion_name="Zed", level=5)],
        )
        self.engine.process(game_data)

        self.engine.reset()

        assert self.engine._previous_game_data is None
        assert self.engine._enemy_last_seen == {}
        assert self.engine._previous_levels == {}
        assert self.engine._previous_hp == {}

    def test_enemy_power_spike_detected(self):
        """Detect enemy power spike at key levels."""
        enemy = PlayerData(
            champion_name="Zed", level=5, kills=1, deaths=0,
            assists=0, creep_score=40,
        )
        game_data_1 = GameData(
            game_time=400.0,
            active_player=PlayerData(
                champion_name="Jinx", level=5, hp=1000, max_hp=1000
            ),
            enemies=[enemy],
        )
        self.engine.process(game_data_1)

        enemy_leveled = PlayerData(
            champion_name="Zed", level=6, kills=1, deaths=0,
            assists=0, creep_score=45,
        )
        game_data_2 = GameData(
            game_time=420.0,
            active_player=PlayerData(
                champion_name="Jinx", level=5, hp=1000, max_hp=1000
            ),
            enemies=[enemy_leveled],
        )
        events = self.engine.process(game_data_2)

        enemy_spikes = [e for e in events if e.event_type == "enemy_power_spike"]
        assert len(enemy_spikes) == 1
        assert "Zed" in enemy_spikes[0].message

    def test_dead_enemy_not_missing(self):
        """Dead enemies should not trigger missing alerts."""
        enemy = PlayerData(
            champion_name="Zed", is_dead=True, level=5,
            kills=1, deaths=2, assists=0, creep_score=30,
        )
        game_data_1 = GameData(
            game_time=100.0,
            active_player=PlayerData(
                champion_name="Jinx", level=5, hp=1000, max_hp=1000
            ),
            enemies=[enemy],
        )
        self.engine.process(game_data_1)

        # 25 seconds later, enemy still dead
        enemy_still_dead = PlayerData(
            champion_name="Zed", is_dead=True, level=5,
            kills=1, deaths=2, assists=0, creep_score=30,
        )
        game_data_2 = GameData(
            game_time=125.0,
            active_player=PlayerData(
                champion_name="Jinx", level=5, hp=1000, max_hp=1000
            ),
            enemies=[enemy_still_dead],
        )
        events = self.engine.process(game_data_2)

        missing = [e for e in events if e.event_type == "enemy_missing"]
        assert len(missing) == 0

    def test_power_spike_levels_constant(self):
        """Verify the power spike levels are correct."""
        assert POWER_SPIKE_LEVELS == {6, 11, 16}
