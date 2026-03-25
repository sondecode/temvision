"""Pre-game analysis for champ select using LCU + Riot API.

- Reads champion select session from the local League Client (LCU).
- Enriches player data with ranked info via Riot API (if configured).
- Produces lightweight overlay lines to show during CLIENT_OPEN phase.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from temvision.lol.champions import ChampionMapper
from temvision.lol.lcu_client import LCUClient
from temvision.lol.riot_api import RiotAPI, PreGameStats

logger = logging.getLogger(__name__)


@dataclass
class PreGamePlayer:
    summoner_name: str = ""
    champion_id: int = 0
    champion_name: str = ""
    position: str = ""
    team: str = ""  # ally/enemy
    rank_text: str = ""  # e.g., "G2 60LP (52%)"


@dataclass
class PreGameInfo:
    allies: list[PreGamePlayer] = field(default_factory=list)
    enemies: list[PreGamePlayer] = field(default_factory=list)
    fetched_rank: bool = False

    def overlay_lines(self) -> list[str]:
        lines: list[str] = []
        if self.allies or self.enemies:
            ally_champs = ", ".join(
                f"{p.position or '?'}:{p.champion_name or p.champion_id or '?'}" for p in self.allies
            )
            enemy_champs = ", ".join(
                f"{p.position or '?'}:{p.champion_name or p.champion_id or '?'}" for p in self.enemies
            )
            lines.append(f"Champ Select — Ally: {ally_champs} | Enemy: {enemy_champs}")
        if self.fetched_rank:
            ranked = [
                f"{p.summoner_name}: {p.rank_text}" for p in self.allies + self.enemies if p.rank_text
            ]
            if ranked:
                lines.extend(ranked)
        return lines


class PreGameAnalyzer:
    """Fetch champ select data and enrich with ranked info."""

    def __init__(
        self,
        lcu_client: Optional[LCUClient] = None,
        riot_api: Optional[RiotAPI] = None,
        champion_mapper: Optional[ChampionMapper] = None,
    ) -> None:
        self._lcu = lcu_client or LCUClient()
        self._riot = riot_api or RiotAPI()
        self._champs = champion_mapper or ChampionMapper()

    def fetch(self) -> Optional[PreGameInfo]:
        session = self._lcu.get_champ_select_session()
        if not session:
            return None

        info = PreGameInfo()

        def _map_team(raw_team: list, team_name: str) -> None:
            for entry in raw_team or []:
                info_list = info.allies if team_name == "ally" else info.enemies
                info_list.append(
                    PreGamePlayer(
                        summoner_name=entry.get("summonerName", ""),
                        champion_id=entry.get("championId", 0),
                        position=entry.get("assignedPosition", ""),
                        team=team_name,
                    )
                )

        _map_team(session.get("myTeam", []), "ally")
        _map_team(session.get("theirTeam", []), "enemy")

        # Map champion IDs to names
        for player in info.allies + info.enemies:
            if player.champion_id:
                player.champion_name = self._champs.name(player.champion_id)

        # Enrich with ranked info if Riot API key is available
        if self._riot.is_available():
            # Build a mapping summonerName -> summonerId if present
            name_to_id: dict[str, str] = {}
            for entry in session.get("myTeam", []) + session.get("theirTeam", []):
                name = entry.get("summonerName")
                summ_id = entry.get("summonerId")
                if name and summ_id:
                    name_to_id[name] = summ_id

            for player in info.allies + info.enemies:
                summoner_id = name_to_id.get(player.summoner_name)
                if not summoner_id:
                    continue
                ranked = self._riot.get_ranked_stats(summoner_id)
                stats = self._riot.build_pre_game_stats(
                    player.summoner_name, ranked, matches=[]
                )
                player.rank_text = _format_rank(stats)
                info.fetched_rank = True
        return info


def _format_rank(stats: PreGameStats) -> str:
    if not stats.tier:
        return ""
    rank = f"{stats.tier.title()} {stats.rank} {stats.lp}LP"
    if stats.win_rate > 0:
        return f"{rank} ({stats.win_rate:.0f}% WR)"
    return rank
