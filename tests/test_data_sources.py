"""Tests for LoL data source layer abstractions."""

from types import SimpleNamespace

from temvision.lol.data_sources import (
    LiveGameDataProvider,
    PostGameDataProvider,
    PreGameDataProvider,
)


class DummyLiveAPI:
    def __init__(self, payload=None):
        self.payload = payload if payload is not None else {"ok": True}

    def get_all_game_data(self):
        return self.payload


class DummyPreAnalyzer:
    def __init__(self, payload=None):
        self.payload = payload

    def fetch(self):
        return self.payload


class DummyPostAnalyzer:
    def __init__(self, payload=None):
        self.payload = payload

    def analyze(self, _game_data):
        return self.payload


class DummyHistory:
    def __init__(self):
        self.saved = []

    def save(self, stats):
        self.saved.append(stats)
        return len(self.saved)


def test_live_provider_enabled_fetches_payload():
    provider = LiveGameDataProvider(api=DummyLiveAPI(), enabled=True)
    assert provider.is_enabled() is True
    assert provider.fetch() == {"ok": True}


def test_live_provider_disabled_returns_none():
    provider = LiveGameDataProvider(api=DummyLiveAPI(), enabled=False)
    assert provider.is_enabled() is False
    assert provider.fetch() is None


def test_pre_game_provider_respects_flag():
    payload = SimpleNamespace(allies=["a"], enemies=["b"])
    enabled = PreGameDataProvider(analyzer=DummyPreAnalyzer(payload), enabled=True)
    disabled = PreGameDataProvider(analyzer=DummyPreAnalyzer(payload), enabled=False)

    assert enabled.fetch() is payload
    assert disabled.fetch() is None


def test_post_game_provider_analyze_and_persist():
    stats = SimpleNamespace(score=88)
    history = DummyHistory()
    provider = PostGameDataProvider(
        analyzer=DummyPostAnalyzer(stats),
        history=history,
        enabled=True,
    )

    assert provider.analyze(SimpleNamespace()) is stats
    row_id = provider.persist(stats)
    assert row_id == 1
    assert history.saved == [stats]


def test_post_game_provider_disabled_is_noop():
    stats = SimpleNamespace(score=88)
    history = DummyHistory()
    provider = PostGameDataProvider(
        analyzer=DummyPostAnalyzer(stats),
        history=history,
        enabled=False,
    )

    assert provider.analyze(SimpleNamespace()) is None
    assert provider.persist(stats) == 0
    assert history.saved == []
