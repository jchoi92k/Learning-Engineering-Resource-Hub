"""Shared pytest fixtures."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


@pytest.fixture(autouse=True)
def isolate_throttle_clock(monkeypatch, tmp_path):
    """Point scrape.py's per-host throttle clock at a temp file: _throttle() runs for real
    under a mocked SESSION and would otherwise write fake hosts (x.org) into
    docs/staging/logs/last-request.json."""
    import scrape
    monkeypatch.setattr(scrape, "LAST_REQUEST_FILE", tmp_path / "last-request.json")
