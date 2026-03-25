"""SQLite-based match history storage.

Stores post-game stats locally so the overlay can show historical
performance trends, win-rate over time, and per-champion statistics.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Optional

from temvision.lol.models import PostGameStats

logger = logging.getLogger(__name__)

_DEFAULT_DB_DIR = os.path.join(os.path.expanduser("~"), ".temvision")
_DEFAULT_DB_PATH = os.path.join(_DEFAULT_DB_DIR, "match_history.db")

_CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS matches (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   REAL    NOT NULL,
    champion    TEXT    NOT NULL,
    win         INTEGER NOT NULL DEFAULT 0,
    kills       INTEGER NOT NULL DEFAULT 0,
    deaths      INTEGER NOT NULL DEFAULT 0,
    assists     INTEGER NOT NULL DEFAULT 0,
    cs          INTEGER NOT NULL DEFAULT 0,
    cs_per_min  REAL    NOT NULL DEFAULT 0.0,
    gold_earned REAL    NOT NULL DEFAULT 0.0,
    duration    REAL    NOT NULL DEFAULT 0.0,
    kda_ratio   REAL    NOT NULL DEFAULT 0.0,
    performance REAL    NOT NULL DEFAULT 0.0,
    grade       TEXT    NOT NULL DEFAULT '',
    mvp         INTEGER NOT NULL DEFAULT 0
);
"""


@dataclass
class MatchRecord:
    """A single stored match."""

    id: int = 0
    timestamp: float = 0.0
    champion: str = ""
    win: bool = False
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    cs: int = 0
    cs_per_min: float = 0.0
    gold_earned: float = 0.0
    duration: float = 0.0
    kda_ratio: float = 0.0
    performance: float = 0.0
    grade: str = ""
    mvp: bool = False

    @property
    def kda_string(self) -> str:
        return f"{self.kills}/{self.deaths}/{self.assists}"


class MatchHistory:
    """Persistent match history backed by SQLite."""

    def __init__(self, db_path: str = _DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        self._ensure_db()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, stats: PostGameStats) -> int:
        """Persist a PostGameStats and return the new row id."""
        conn = self._connect()
        try:
            cur = conn.execute(
                "INSERT INTO matches "
                "(timestamp, champion, win, kills, deaths, assists, cs, "
                "cs_per_min, gold_earned, duration, kda_ratio, performance, "
                "grade, mvp) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    time.time(),
                    stats.player_champion,
                    int(stats.win),
                    stats.kills,
                    stats.deaths,
                    stats.assists,
                    stats.cs,
                    stats.cs_per_min,
                    stats.gold_earned,
                    stats.game_duration,
                    stats.kda_ratio,
                    stats.performance_score,
                    stats.grade,
                    int(stats.mvp),
                ),
            )
            conn.commit()
            return cur.lastrowid or 0
        finally:
            conn.close()

    def recent(self, limit: int = 20) -> list[MatchRecord]:
        """Return the most recent *limit* matches, newest first."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM matches ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._row_to_record(r) for r in rows]
        finally:
            conn.close()

    def champion_stats(self, champion: str) -> dict:
        """Aggregate stats for a specific champion.

        Returns dict with keys: games, wins, avg_kda, avg_cs, avg_perf.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*), SUM(win), AVG(kda_ratio), "
                "AVG(cs_per_min), AVG(performance) "
                "FROM matches WHERE champion = ?",
                (champion,),
            ).fetchone()
            if row is None or row[0] == 0:
                return {"games": 0, "wins": 0, "avg_kda": 0.0,
                        "avg_cs": 0.0, "avg_perf": 0.0}
            return {
                "games": row[0],
                "wins": row[1] or 0,
                "avg_kda": round(row[2] or 0.0, 2),
                "avg_cs": round(row[3] or 0.0, 1),
                "avg_perf": round(row[4] or 0.0, 1),
            }
        finally:
            conn.close()

    def overall_stats(self) -> dict:
        """Aggregate stats across all matches."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*), SUM(win), AVG(kda_ratio), "
                "AVG(cs_per_min), AVG(performance) "
                "FROM matches"
            ).fetchone()
            if row is None or row[0] == 0:
                return {"games": 0, "wins": 0, "win_rate": 0.0,
                        "avg_kda": 0.0, "avg_cs": 0.0, "avg_perf": 0.0}
            games = row[0]
            wins = row[1] or 0
            return {
                "games": games,
                "wins": wins,
                "win_rate": round(wins / games * 100, 1) if games else 0.0,
                "avg_kda": round(row[2] or 0.0, 2),
                "avg_cs": round(row[3] or 0.0, 1),
                "avg_perf": round(row[4] or 0.0, 1),
            }
        finally:
            conn.close()

    def overlay_summary(self, limit: int = 5) -> list[str]:
        """Return overlay-ready summary lines for recent matches."""
        recent = self.recent(limit)
        if not recent:
            return ["No match history yet."]
        overall = self.overall_stats()
        lines = [
            f"📊 {overall['games']} games | "
            f"WR: {overall['win_rate']}% | "
            f"Avg KDA: {overall['avg_kda']}"
        ]
        for m in recent[:3]:
            result = "✅" if m.win else "❌"
            lines.append(
                f"{result} {m.champion} {m.kda_string} "
                f"({m.grade}) {m.performance:.0f}pts"
            )
        return lines

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_db(self) -> None:
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute(_CREATE_TABLE)
            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    @staticmethod
    def _row_to_record(row: tuple) -> MatchRecord:
        return MatchRecord(
            id=row[0],
            timestamp=row[1],
            champion=row[2],
            win=bool(row[3]),
            kills=row[4],
            deaths=row[5],
            assists=row[6],
            cs=row[7],
            cs_per_min=row[8],
            gold_earned=row[9],
            duration=row[10],
            kda_ratio=row[11],
            performance=row[12],
            grade=row[13],
            mvp=bool(row[14]),
        )
