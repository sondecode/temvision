"""Post-game improvement report with rank-tier benchmarks.

Compares a player's game stats to rank-tier benchmarks and generates
actionable improvement suggestions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from temvision.lol.match_history import MatchHistory
from temvision.lol.models import PostGameStats

logger = logging.getLogger(__name__)

# Rank-tier benchmark data (approximate averages per role)
# Format: {tier: {metric: value}}
RANK_BENCHMARKS: dict[str, dict[str, float]] = {
    "iron": {
        "cs_per_min": 3.5,
        "kda_ratio": 1.5,
        "vision_score_per_min": 0.3,
        "kill_participation": 0.40,
        "gold_per_min": 280,
    },
    "bronze": {
        "cs_per_min": 4.5,
        "kda_ratio": 2.0,
        "vision_score_per_min": 0.4,
        "kill_participation": 0.45,
        "gold_per_min": 310,
    },
    "silver": {
        "cs_per_min": 5.5,
        "kda_ratio": 2.5,
        "vision_score_per_min": 0.5,
        "kill_participation": 0.50,
        "gold_per_min": 340,
    },
    "gold": {
        "cs_per_min": 6.5,
        "kda_ratio": 3.0,
        "vision_score_per_min": 0.6,
        "kill_participation": 0.55,
        "gold_per_min": 370,
    },
    "platinum": {
        "cs_per_min": 7.0,
        "kda_ratio": 3.5,
        "vision_score_per_min": 0.7,
        "kill_participation": 0.58,
        "gold_per_min": 390,
    },
    "emerald": {
        "cs_per_min": 7.5,
        "kda_ratio": 3.8,
        "vision_score_per_min": 0.8,
        "kill_participation": 0.60,
        "gold_per_min": 400,
    },
    "diamond": {
        "cs_per_min": 8.0,
        "kda_ratio": 4.0,
        "vision_score_per_min": 0.9,
        "kill_participation": 0.62,
        "gold_per_min": 420,
    },
    "master": {
        "cs_per_min": 8.5,
        "kda_ratio": 4.5,
        "vision_score_per_min": 1.0,
        "kill_participation": 0.65,
        "gold_per_min": 440,
    },
}


@dataclass
class BenchmarkComparison:
    """Comparison of a metric with a benchmark."""

    metric: str = ""
    player_value: float = 0.0
    benchmark_value: float = 0.0
    tier: str = ""
    above: bool = False
    diff_percent: float = 0.0


@dataclass
class ImprovementReport:
    """Post-game improvement report with suggestions."""

    champion: str = ""
    grade: str = ""
    performance_score: float = 0.0
    comparisons: list[BenchmarkComparison] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    trend_lines: list[str] = field(default_factory=list)

    def overlay_lines(self) -> list[str]:
        lines: list[str] = [
            "─" * 30,
            f"📋 IMPROVEMENT REPORT — {self.champion} ({self.grade})",
        ]
        # Benchmark comparisons
        for c in self.comparisons:
            icon = "✅" if c.above else "❌"
            lines.append(
                f"  {icon} {c.metric}: {c.player_value:.1f} vs "
                f"{c.tier} avg {c.benchmark_value:.1f} "
                f"({c.diff_percent:+.0f}%)"
            )
        # Suggestions
        if self.suggestions:
            lines.append("💡 Focus areas:")
            for s in self.suggestions:
                lines.append(f"  • {s}")
        # Trend
        for t in self.trend_lines:
            lines.append(t)
        lines.append("─" * 30)
        return lines


class ReportGenerator:
    """Generate post-game improvement reports.

    Compares stats to rank benchmarks and analyzes trends from
    match history.
    """

    def __init__(
        self,
        match_history: Optional[MatchHistory] = None,
        target_tier: str = "gold",
    ) -> None:
        self._history = match_history
        self._tier = target_tier.lower()

    def generate(self, stats: PostGameStats) -> ImprovementReport:
        """Generate an improvement report from post-game stats."""
        report = ImprovementReport(
            champion=stats.player_champion,
            grade=stats.grade,
            performance_score=stats.performance_score,
        )

        benchmarks = RANK_BENCHMARKS.get(self._tier, RANK_BENCHMARKS["gold"])
        duration_min = max(stats.game_duration / 60.0, 1.0)

        # CS/min comparison
        report.comparisons.append(
            self._compare("CS/min", stats.cs_per_min, benchmarks["cs_per_min"])
        )

        # KDA comparison
        report.comparisons.append(
            self._compare("KDA", stats.kda_ratio, benchmarks["kda_ratio"])
        )

        # Gold/min
        gold_per_min = stats.gold_earned / duration_min if duration_min > 0 else 0
        report.comparisons.append(
            self._compare("Gold/min", gold_per_min, benchmarks["gold_per_min"])
        )

        # Generate suggestions based on weakest areas
        weakest = sorted(
            report.comparisons, key=lambda c: c.diff_percent
        )
        for comp in weakest:
            if comp.above:
                continue
            if comp.metric == "CS/min":
                report.suggestions.append(
                    f"Farm more: {comp.player_value:.1f} CS/m is below "
                    f"{self._tier.title()} avg ({comp.benchmark_value:.1f}). "
                    f"Practice last-hitting in Practice Tool."
                )
            elif comp.metric == "KDA":
                report.suggestions.append(
                    f"Reduce deaths: {stats.deaths} deaths. "
                    f"Trade kills conservatively and track enemy cooldowns."
                )
            elif comp.metric == "Gold/min":
                report.suggestions.append(
                    f"Increase gold income: grab side-wave CS "
                    f"and jungle camps after laning phase."
                )

        if not report.suggestions:
            report.suggestions.append(
                f"Great game! All metrics at or above {self._tier.title()} level."
            )

        # Trend from match history
        if self._history is not None:
            report.trend_lines = self._build_trend(stats.player_champion)

        return report

    def _compare(
        self, metric: str, player_val: float, bench_val: float
    ) -> BenchmarkComparison:
        if bench_val == 0:
            diff = 0.0
        else:
            diff = ((player_val - bench_val) / bench_val) * 100
        return BenchmarkComparison(
            metric=metric,
            player_value=player_val,
            benchmark_value=bench_val,
            tier=self._tier.title(),
            above=player_val >= bench_val,
            diff_percent=diff,
        )

    def _build_trend(self, champion: str) -> list[str]:
        lines: list[str] = []
        overall = self._history.overall_stats()
        if overall["games"] > 1:
            lines.append(
                f"📈 Overall: {overall['games']} games, "
                f"WR {overall['win_rate']}%, "
                f"Avg KDA {overall['avg_kda']}"
            )
        champ = self._history.champion_stats(champion)
        if champ["games"] > 1:
            wr = round(champ["wins"] / champ["games"] * 100, 1) if champ["games"] else 0
            lines.append(
                f"📊 {champion}: {champ['games']} games, "
                f"WR {wr}%, "
                f"Avg Perf {champ['avg_perf']}"
            )
        return lines
