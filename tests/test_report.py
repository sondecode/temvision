"""Tests for post-game improvement report."""

import pytest

from temvision.lol.models import PostGameStats
from temvision.lol.report import (
    BenchmarkComparison,
    ImprovementReport,
    RANK_BENCHMARKS,
    ReportGenerator,
)


class TestBenchmarkComparison:
    """Test BenchmarkComparison dataclass."""

    def test_defaults(self):
        c = BenchmarkComparison()
        assert c.metric == ""
        assert c.player_value == 0.0
        assert c.benchmark_value == 0.0
        assert c.above is False

    def test_above_flag(self):
        c = BenchmarkComparison(
            metric="CS/min",
            player_value=7.5,
            benchmark_value=6.5,
            above=True,
            diff_percent=15.4,
        )
        assert c.above is True
        assert c.diff_percent > 0


class TestImprovementReport:
    """Test ImprovementReport overlay lines."""

    def test_overlay_lines_structure(self):
        report = ImprovementReport(
            champion="Jinx",
            grade="A",
            performance_score=85.0,
            comparisons=[
                BenchmarkComparison(
                    metric="CS/min", player_value=7.0,
                    benchmark_value=6.5, tier="Gold",
                    above=True, diff_percent=7.7,
                ),
                BenchmarkComparison(
                    metric="KDA", player_value=2.0,
                    benchmark_value=3.0, tier="Gold",
                    above=False, diff_percent=-33.3,
                ),
            ],
            suggestions=["Reduce deaths: 5 deaths."],
        )
        lines = report.overlay_lines()
        joined = "\n".join(lines)
        assert "IMPROVEMENT REPORT" in joined
        assert "Jinx" in joined
        assert "CS/min" in joined
        assert "✅" in joined
        assert "❌" in joined
        assert "Focus areas" in joined
        assert "Reduce deaths" in joined

    def test_overlay_lines_with_trend(self):
        report = ImprovementReport(
            champion="Jinx",
            grade="B",
            trend_lines=["📈 Overall: 10 games, WR 60%"],
        )
        lines = report.overlay_lines()
        joined = "\n".join(lines)
        assert "📈 Overall" in joined

    def test_overlay_lines_empty_report(self):
        report = ImprovementReport()
        lines = report.overlay_lines()
        assert len(lines) >= 2  # header + separator


class TestReportGenerator:
    """Test ReportGenerator logic."""

    def _make_stats(self, **overrides) -> PostGameStats:
        defaults = dict(
            game_duration=1800.0,  # 30 min
            player_champion="Jinx",
            win=True,
            kills=8,
            deaths=3,
            assists=10,
            gold_earned=12000.0,
            cs=200,
            cs_per_min=6.67,
            kda_ratio=6.0,
            performance_score=85.0,
            grade="A",
        )
        defaults.update(overrides)
        return PostGameStats(**defaults)

    def test_generate_basic(self):
        gen = ReportGenerator(target_tier="gold")
        stats = self._make_stats()
        report = gen.generate(stats)
        assert report.champion == "Jinx"
        assert report.grade == "A"
        assert len(report.comparisons) == 3

    def test_generate_above_benchmarks(self):
        gen = ReportGenerator(target_tier="iron")
        stats = self._make_stats(cs_per_min=8.0, kda_ratio=5.0, gold_earned=15000)
        report = gen.generate(stats)
        # With iron benchmarks and high stats, all should be above
        above_count = sum(1 for c in report.comparisons if c.above)
        assert above_count == 3
        assert any("Great game" in s for s in report.suggestions)

    def test_generate_below_benchmarks(self):
        gen = ReportGenerator(target_tier="master")
        stats = self._make_stats(cs_per_min=4.0, kda_ratio=1.5, gold_earned=6000)
        report = gen.generate(stats)
        below_count = sum(1 for c in report.comparisons if not c.above)
        assert below_count >= 2
        assert len(report.suggestions) >= 2

    def test_generate_cs_suggestion(self):
        gen = ReportGenerator(target_tier="gold")
        stats = self._make_stats(cs_per_min=3.0)
        report = gen.generate(stats)
        assert any("Farm" in s or "CS" in s for s in report.suggestions)

    def test_generate_kda_suggestion(self):
        gen = ReportGenerator(target_tier="gold")
        stats = self._make_stats(kda_ratio=1.0, deaths=8)
        report = gen.generate(stats)
        assert any("death" in s.lower() for s in report.suggestions)

    def test_generate_gold_suggestion(self):
        gen = ReportGenerator(target_tier="gold")
        stats = self._make_stats(gold_earned=3000, game_duration=1800)
        report = gen.generate(stats)
        assert any("gold" in s.lower() for s in report.suggestions)

    def test_generate_with_match_history(self, tmp_path):
        from temvision.lol.match_history import MatchHistory

        db_path = str(tmp_path / "test.db")
        mh = MatchHistory(db_path=db_path)

        # Save a couple matches so trend shows
        for _ in range(3):
            mh.save(self._make_stats())

        gen = ReportGenerator(match_history=mh, target_tier="gold")
        stats = self._make_stats()
        report = gen.generate(stats)
        assert len(report.trend_lines) > 0
        assert any("Overall" in t for t in report.trend_lines)

    def test_generate_unknown_tier_falls_back_to_gold(self):
        gen = ReportGenerator(target_tier="challenger")
        stats = self._make_stats()
        report = gen.generate(stats)
        # Should use gold benchmarks fallback
        assert len(report.comparisons) == 3

    def test_compare_method(self):
        gen = ReportGenerator(target_tier="gold")
        comp = gen._compare("CS/min", 7.0, 6.5)
        assert comp.metric == "CS/min"
        assert comp.above is True
        assert comp.diff_percent > 0

    def test_compare_zero_benchmark(self):
        gen = ReportGenerator(target_tier="gold")
        comp = gen._compare("test", 5.0, 0.0)
        assert comp.diff_percent == 0.0


class TestRankBenchmarks:
    """Test the rank benchmark data."""

    def test_all_tiers_present(self):
        expected = {"iron", "bronze", "silver", "gold", "platinum", "emerald", "diamond", "master"}
        assert expected.issubset(set(RANK_BENCHMARKS.keys()))

    def test_all_tiers_have_required_keys(self):
        required = {"cs_per_min", "kda_ratio", "vision_score_per_min", "kill_participation", "gold_per_min"}
        for tier, data in RANK_BENCHMARKS.items():
            assert required.issubset(set(data.keys())), f"{tier} missing keys"

    def test_benchmarks_increase_with_rank(self):
        tiers = ["iron", "bronze", "silver", "gold", "platinum", "emerald", "diamond", "master"]
        for metric in ["cs_per_min", "kda_ratio"]:
            values = [RANK_BENCHMARKS[t][metric] for t in tiers]
            for i in range(1, len(values)):
                assert values[i] >= values[i - 1], f"{metric} should increase: {tiers[i]}"
