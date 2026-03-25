"""Tests for objective tracker."""

import pytest

from temvision.lol.objective_tracker import (
    ObjectiveTracker,
    ObjectiveTimers,
    ObjectiveState,
    DRAGON_RESPAWN,
    BARON_RESPAWN,
    BARON_SPAWN_TIME,
)
from temvision.lol.models import PlayerData, GameData


class TestObjectiveState:
    """Test ObjectiveState dataclass."""

    def test_default_values(self):
        s = ObjectiveState()
        assert s.name == ""
        assert s.alive is True
        assert s.last_killed_time == 0.0
        assert s.kill_count == 0

    def test_time_until_spawn_alive(self):
        s = ObjectiveState(alive=True)
        assert s.time_until_spawn == 0.0

    def test_time_until_spawn_dead(self):
        s = ObjectiveState(
            alive=False,
            last_killed_time=100.0,
            next_spawn_time=400.0,
        )
        assert s.time_until_spawn == 300.0

    def test_remaining_time_alive(self):
        s = ObjectiveState(alive=True)
        assert s.remaining_time(500.0) == 0.0

    def test_remaining_time_dead(self):
        s = ObjectiveState(
            alive=False,
            next_spawn_time=400.0,
        )
        assert s.remaining_time(300.0) == 100.0

    def test_remaining_time_past_spawn(self):
        s = ObjectiveState(
            alive=False,
            next_spawn_time=400.0,
        )
        assert s.remaining_time(500.0) == 0.0


class TestObjectiveTimers:
    """Test ObjectiveTimers dataclass."""

    def test_default_values(self):
        t = ObjectiveTimers()
        assert t.dragon.alive is True
        assert t.baron.alive is True
        assert t.herald.alive is True
        assert t.dragon_kills_ally == 0
        assert t.dragon_kills_enemy == 0
        assert t.dragon_types == []

    def test_to_dict(self):
        t = ObjectiveTimers()
        d = t.to_dict()
        assert "dragon" in d
        assert "baron" in d
        assert "herald" in d
        assert d["dragon_kills_ally"] == 0
        assert d["dragon_kills_enemy"] == 0


class TestObjectiveTracker:
    """Test objective tracker engine."""

    def setup_method(self):
        self.tracker = ObjectiveTracker()

    def test_process_no_events(self):
        game_data = GameData(
            game_time=300.0,
            active_player=PlayerData(
                champion_name="Jinx", team="ORDER"
            ),
            events=[],
        )
        timers = self.tracker.process(game_data)
        assert timers.dragon.alive is True
        assert timers.baron.alive is True

    def test_process_dragon_kill(self):
        game_data = GameData(
            game_time=360.0,
            active_player=PlayerData(
                champion_name="Jinx", team="ORDER"
            ),
            events=[
                {
                    "EventName": "DragonKill",
                    "EventTime": 350.0,
                    "KillerName": "Jinx",
                    "DragonType": "Infernal",
                    "Assisters": [],
                }
            ],
        )
        timers = self.tracker.process(game_data)
        assert timers.dragon.alive is False
        assert timers.dragon.kill_count == 1
        assert timers.dragon.next_spawn_time == 350.0 + DRAGON_RESPAWN
        assert timers.dragon_kills_ally == 1
        assert "Infernal" in timers.dragon_types

    def test_process_baron_kill(self):
        game_data = GameData(
            game_time=1250.0,
            active_player=PlayerData(
                champion_name="Jinx", team="ORDER"
            ),
            events=[
                {
                    "EventName": "BaronKill",
                    "EventTime": 1240.0,
                    "KillerName": "Jinx",
                    "Assisters": [],
                }
            ],
        )
        timers = self.tracker.process(game_data)
        assert timers.baron.alive is False
        assert timers.baron.kill_count == 1
        assert timers.baron.next_spawn_time == 1240.0 + BARON_RESPAWN

    def test_process_herald_kill(self):
        game_data = GameData(
            game_time=600.0,
            active_player=PlayerData(
                champion_name="Jinx", team="ORDER"
            ),
            events=[
                {
                    "EventName": "HeraldKill",
                    "EventTime": 580.0,
                    "KillerName": "Jinx",
                    "Assisters": [],
                }
            ],
        )
        timers = self.tracker.process(game_data)
        assert timers.herald.alive is False
        assert timers.herald.kill_count == 1

    def test_dragon_respawn(self):
        """Dragon should respawn after DRAGON_RESPAWN seconds."""
        game_data_1 = GameData(
            game_time=350.0,
            active_player=PlayerData(
                champion_name="Jinx", team="ORDER"
            ),
            events=[
                {
                    "EventName": "DragonKill",
                    "EventTime": 350.0,
                    "KillerName": "Jinx",
                    "DragonType": "Ocean",
                    "Assisters": [],
                }
            ],
        )
        self.tracker.process(game_data_1)

        # After respawn time
        game_data_2 = GameData(
            game_time=350.0 + DRAGON_RESPAWN + 1,
            active_player=PlayerData(
                champion_name="Jinx", team="ORDER"
            ),
            events=[
                {
                    "EventName": "DragonKill",
                    "EventTime": 350.0,
                    "KillerName": "Jinx",
                    "DragonType": "Ocean",
                    "Assisters": [],
                }
            ],
        )
        timers = self.tracker.process(game_data_2)
        assert timers.dragon.alive is True

    def test_no_duplicate_event_processing(self):
        """Same event should not be processed twice."""
        event = {
            "EventName": "DragonKill",
            "EventTime": 350.0,
            "KillerName": "Jinx",
            "DragonType": "Cloud",
            "Assisters": [],
        }
        game_data = GameData(
            game_time=360.0,
            active_player=PlayerData(
                champion_name="Jinx", team="ORDER"
            ),
            events=[event],
        )
        self.tracker.process(game_data)
        self.tracker.process(game_data)

        assert self.tracker.timers.dragon.kill_count == 1

    def test_reset(self):
        game_data = GameData(
            game_time=350.0,
            active_player=PlayerData(
                champion_name="Jinx", team="ORDER"
            ),
            events=[
                {
                    "EventName": "DragonKill",
                    "EventTime": 350.0,
                    "KillerName": "Jinx",
                    "DragonType": "Mountain",
                    "Assisters": [],
                }
            ],
        )
        self.tracker.process(game_data)
        self.tracker.reset()

        assert self.tracker.timers.dragon.alive is True
        assert self.tracker.timers.dragon.kill_count == 0

    def test_suggestions_dragon_spawning(self):
        """Should suggest when dragon is about to spawn."""
        game_data = GameData(
            game_time=350.0,
            active_player=PlayerData(
                champion_name="Jinx", team="ORDER"
            ),
            enemies=[PlayerData(champion_name="Caitlyn")],
            events=[
                {
                    "EventName": "DragonKill",
                    "EventTime": 350.0,
                    "KillerName": "Jinx",
                    "DragonType": "Infernal",
                    "Assisters": [],
                }
            ],
        )
        self.tracker.process(game_data)

        # 20 seconds before dragon respawns
        game_data_2 = GameData(
            game_time=350.0 + DRAGON_RESPAWN - 20.0,
            active_player=PlayerData(
                champion_name="Jinx", team="ORDER"
            ),
            enemies=[PlayerData(champion_name="Caitlyn")],
            events=[
                {
                    "EventName": "DragonKill",
                    "EventTime": 350.0,
                    "KillerName": "Jinx",
                    "DragonType": "Infernal",
                    "Assisters": [],
                }
            ],
        )
        self.tracker.process(game_data_2)

        suggestions = self.tracker.get_suggestions(game_data_2)
        dragon_suggestions = [
            s for s in suggestions if "Dragon" in s["text"] or "dragon" in s["text"]
        ]
        assert len(dragon_suggestions) >= 1

    def test_suggestions_baron_with_dead_enemies(self):
        """Should suggest baron when enemies are dead."""
        game_data = GameData(
            game_time=BARON_SPAWN_TIME + 100,
            active_player=PlayerData(
                champion_name="Jinx", team="ORDER"
            ),
            enemies=[
                PlayerData(champion_name="Zed", is_dead=True),
                PlayerData(champion_name="Ahri", is_dead=True),
                PlayerData(champion_name="Lee Sin", is_dead=False),
            ],
            events=[],
        )
        self.tracker.process(game_data)
        suggestions = self.tracker.get_suggestions(game_data)
        baron_suggestions = [
            s for s in suggestions if "Baron" in s["text"] or "baron" in s["text"]
        ]
        assert len(baron_suggestions) >= 1
