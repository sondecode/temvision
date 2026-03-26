"""Riot Games API client for pre-game analysis.

Provides player rank, match history, and champion winrate data.
Requires a valid Riot API key set in the RIOT_API_KEY environment variable.

Reference: https://developer.riotgames.com/apis
"""

import logging
import os
from typing import Optional

import requests

from temvision.lol.http_client import HttpClient
from temvision.lol.models import PreGameStats

logger = logging.getLogger(__name__)

RIOT_API_BASE = "https://{region}.api.riotgames.com"

REGIONS = {
    "na": "na1",
    "euw": "euw1",
    "eune": "eun1",
    "kr": "kr",
    "jp": "jp1",
    "br": "br1",
    "lan": "la1",
    "las": "la2",
    "oce": "oc1",
    "tr": "tr1",
    "ru": "ru",
    "vn": "vn2",
    "tw": "tw2",
    "th": "th2",
    "sg": "sg2",
    "ph": "ph2",
}

ROUTING_REGIONS = {
    "na": "americas",
    "br": "americas",
    "lan": "americas",
    "las": "americas",
    "oce": "americas",
    "euw": "europe",
    "eune": "europe",
    "tr": "europe",
    "ru": "europe",
    "kr": "asia",
    "jp": "asia",
    "vn": "sea",
    "tw": "sea",
    "th": "sea",
    "sg": "sea",
    "ph": "sea",
}


class RiotAPI:
    """Client for the Riot Games API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        region: str = "na",
        timeout: float = 5.0,
    ):
        # Falls back to RIOT_API_KEY env var. An empty string means
        # no key is configured; all API calls will return None gracefully.
        self.api_key = api_key or os.environ.get("RIOT_API_KEY", "")
        self.region = region
        self.platform = REGIONS.get(region, "na1")
        self.routing = ROUTING_REGIONS.get(region, "americas")
        self.timeout = timeout
        self._session = requests.Session()
        if self.api_key:
            self._session.headers["X-Riot-Token"] = self.api_key
        self._http = HttpClient(
            timeout=timeout,
            verify=True,
            retries=2,
            backoff_seconds=0.25,
            session=self._session,
        )

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def get_summoner_by_name(
        self, game_name: str, tag_line: str = "NA1"
    ) -> Optional[dict]:
        """Fetch summoner account by Riot ID.

        Args:
            game_name: The player's game name.
            tag_line: The player's tag line (e.g., NA1).

        Returns:
            Account data dict or None on failure.
        """
        if not self.is_available():
            logger.warning("Riot API key not configured")
            return None

        url = (
            f"https://{self.routing}.api.riotgames.com"
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
        resp = self._http.request("GET", url)
        if resp is None:
            return None
        return resp.json()

    def get_ranked_stats(self, summoner_id: str) -> Optional[list]:
        """Fetch ranked stats for a summoner.

        Args:
            summoner_id: Encrypted summoner ID.

        Returns:
            List of ranked queue entries or None.
        """
        if not self.is_available():
            return None

        url = (
            f"https://{self.platform}.api.riotgames.com"
            f"/lol/league/v4/entries/by-summoner/{summoner_id}"
        )
        resp = self._http.request("GET", url)
        if resp is None:
            return None
        return resp.json()

    def get_match_history(
        self, puuid: str, count: int = 10
    ) -> Optional[list]:
        """Fetch recent match IDs for a player.

        Args:
            puuid: Player's PUUID.
            count: Number of matches to fetch (max 100).

        Returns:
            List of match IDs or None.
        """
        if not self.is_available():
            return None

        url = (
            f"https://{self.routing}.api.riotgames.com"
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        )
        resp = self._http.request(
            "GET", url, params={"count": count}
        )
        if resp is None:
            return None
        return resp.json()

    def get_match_detail(self, match_id: str) -> Optional[dict]:
        """Fetch details for a specific match.

        Args:
            match_id: The match ID string.

        Returns:
            Match data dict or None.
        """
        if not self.is_available():
            return None

        url = (
            f"https://{self.routing}.api.riotgames.com"
            f"/lol/match/v5/matches/{match_id}"
        )
        resp = self._http.request("GET", url)
        if resp is None:
            return None
        return resp.json()

    def build_pre_game_stats(
        self, summoner_name: str, ranked_data: list, matches: list
    ) -> PreGameStats:
        """Build pre-game analysis from Riot API data.

        Args:
            summoner_name: Player's summoner name.
            ranked_data: Ranked entries from the API.
            matches: List of match detail dicts.

        Returns:
            Populated PreGameStats object.
        """
        stats = PreGameStats(summoner_name=summoner_name)

        # Parse ranked data (Solo/Duo queue)
        for entry in ranked_data or []:
            if entry.get("queueType") == "RANKED_SOLO_5x5":
                stats.tier = entry.get("tier", "")
                stats.rank = entry.get("rank", "")
                stats.lp = entry.get("leaguePoints", 0)
                wins = entry.get("wins", 0)
                losses = entry.get("losses", 0)
                stats.total_games = wins + losses
                if stats.total_games > 0:
                    stats.win_rate = (wins / stats.total_games) * 100.0
                break

        # Parse match history for KDA and recent results
        total_kills = 0
        total_deaths = 0
        total_assists = 0
        match_count = 0

        for match in matches or []:
            info = match.get("info", {})
            participants = info.get("participants", [])
            for p in participants:
                p_name = p.get(
                    "riotIdGameName", p.get("summonerName", "")
                )
                if p_name == summoner_name:
                    total_kills += p.get("kills", 0)
                    total_deaths += p.get("deaths", 0)
                    total_assists += p.get("assists", 0)
                    match_count += 1
                    stats.recent_matches.append(
                        {
                            "champion": p.get("championName", ""),
                            "win": p.get("win", False),
                            "kills": p.get("kills", 0),
                            "deaths": p.get("deaths", 0),
                            "assists": p.get("assists", 0),
                        }
                    )
                    break

        if match_count > 0:
            if total_deaths > 0:
                stats.avg_kda = (total_kills + total_assists) / total_deaths
            else:
                stats.avg_kda = float(total_kills + total_assists)

        return stats

    def close(self):
        """Close the HTTP session."""
        self._http.close()
