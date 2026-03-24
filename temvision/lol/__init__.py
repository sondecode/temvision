"""LoL Desktop Overlay - OP.GG-style game overlay for League of Legends."""

from temvision.lol.models import PlayerData, GameData, PreGameStats
from temvision.lol.client_api import LiveClientAPI
from temvision.lol.riot_api import RiotAPI
from temvision.lol.game_detector import GameDetector
from temvision.lol.suggestion_engine import SuggestionEngine

__all__ = [
    "PlayerData",
    "GameData",
    "PreGameStats",
    "LiveClientAPI",
    "RiotAPI",
    "GameDetector",
    "SuggestionEngine",
]
