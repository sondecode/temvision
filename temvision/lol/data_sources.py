"""Data source layer for LoL live/pre-game/post-game pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Optional, Protocol, TypeVar

from temvision.lol.client_api import LiveClientAPI
from temvision.lol.match_history import MatchHistory
from temvision.lol.models import GameData, PostGameStats
from temvision.lol.post_game import PostGameAnalyzer
from temvision.lol.pre_game import PreGameAnalyzer, PreGameInfo

T = TypeVar("T")


class IDataProvider(Protocol, Generic[T]):
    """Generic provider contract for game data sources."""

    def is_enabled(self) -> bool:
        """Return whether this provider is enabled by configuration."""

    def fetch(self) -> Optional[T]:
        """Fetch the latest snapshot from the provider."""


@dataclass
class LiveGameDataProvider(IDataProvider[dict]):
    """Provider for in-game snapshots via Live Client API."""

    api: LiveClientAPI
    enabled: bool = True

    def is_enabled(self) -> bool:
        return self.enabled

    def fetch(self) -> Optional[dict]:
        if not self.enabled:
            return None
        return self.api.get_all_game_data()


@dataclass
class PreGameDataProvider(IDataProvider[PreGameInfo]):
    """Provider for champion-select / pre-game insights."""

    analyzer: PreGameAnalyzer
    enabled: bool = True

    def is_enabled(self) -> bool:
        return self.enabled

    def fetch(self) -> Optional[PreGameInfo]:
        if not self.enabled:
            return None
        return self.analyzer.fetch()


@dataclass
class PostGameDataProvider:
    """Provider for post-game analysis and optional persistence."""

    analyzer: PostGameAnalyzer
    history: MatchHistory
    enabled: bool = True

    def is_enabled(self) -> bool:
        return self.enabled

    def analyze(self, game_data: GameData) -> Optional[PostGameStats]:
        if not self.enabled:
            return None
        return self.analyzer.analyze(game_data)

    def persist(self, stats: PostGameStats) -> int:
        if not self.enabled:
            return 0
        return self.history.save(stats)
