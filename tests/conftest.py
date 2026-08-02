"""Keep the suite off the real runtime state.

``run_pipeline`` reads ``.reoon/`` and ``.pipeline/`` through module-level
constants. Without this, a test that calls ``pending_verification`` would read
whatever the last real pipeline run left on this machine — passing or failing
depending on the developer's Drive backlog. Individual tests still override
these with their own tmp paths; this just guarantees nothing escapes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pipeline"))

import report  # noqa: E402
import run_pipeline as rp  # noqa: E402


@pytest.fixture(autouse=True)
def isolate_runtime_state(tmp_path_factory, monkeypatch):
    scratch = tmp_path_factory.mktemp("runtime-state")
    monkeypatch.setattr(rp, "REOON_CACHE_FILE", scratch / ".reoon" / "verified_cache.json")
    monkeypatch.setattr(rp, "REOON_REJECTED_FILE", scratch / ".reoon" / "rejected.json")
    monkeypatch.setattr(rp, "CONTACTED_FILE", scratch / ".pipeline" / "contacted.json")
    monkeypatch.setattr(rp, "STATE_FILE", scratch / ".pipeline" / "state.json")
    # report.py reads the same cache and tombstones to compute pending live, and
    # writes Report.csv at the repo root — none of which a test should touch.
    monkeypatch.setattr(report, "REOON_CACHE_FILE", scratch / ".reoon" / "verified_cache.json")
    monkeypatch.setattr(report, "REOON_REJECTED_FILE", scratch / ".reoon" / "rejected.json")
    monkeypatch.setattr(report, "WORK_ROOT", scratch / "leads" / "pipeline")
    monkeypatch.setattr(report, "STATE_FILE", scratch / ".pipeline" / "state.json")
    monkeypatch.setattr(report, "REPORT_FILE", scratch / "Report.csv")
    return scratch
