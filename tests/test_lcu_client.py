"""Tests for LCUClient lockfile parsing and basic auth headers."""

from pathlib import Path

import pytest

from temvision.lol.lcu_client import LCUClient, Lockfile


def test_read_lockfile_valid(tmp_path: Path, monkeypatch):
    lock = tmp_path / "lockfile"
    lock.write_text("LeagueClient:1234:2999:password:https", encoding="utf-8")
    client = LCUClient(lockfile_path=str(lock))
    lf = client._read_lockfile()
    assert isinstance(lf, Lockfile)
    assert lf.port == 2999
    assert lf.password == "password"
    assert lf.protocol == "https"


def test_read_lockfile_invalid(tmp_path: Path):
    lock = tmp_path / "lockfile"
    lock.write_text("broken:data", encoding="utf-8")
    client = LCUClient(lockfile_path=str(lock))
    assert client._read_lockfile() is None


def test_is_running_false(tmp_path: Path):
    client = LCUClient(lockfile_path=str(tmp_path / "missing"))
    assert client.is_running() is False


def test_is_running_true(tmp_path: Path):
    lock = tmp_path / "lockfile"
    lock.write_text("LeagueClient:1:2999:pw:https", encoding="utf-8")
    client = LCUClient(lockfile_path=str(lock))
    assert client.is_running() is True
