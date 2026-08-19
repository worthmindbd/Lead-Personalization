"""Day-keyed state must be keyed on UTC dates.

Reoon's free credits reset at midnight UTC. The daily-usage tracker used the
local date, so on a UTC+6 machine every run after 06:00 local was still
counted against the previous (already-reset) day. Same class of bug: the
LinkedIn cache stamp and the pipeline run stamp used local time while
everything else used UTC. These tests fail on any non-UTC machine during the
part of the day where the local date disagrees with the UTC date — which is
exactly when the bug bites.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pipeline"))

import run_pipeline as rp  # noqa: E402
import verify_emails_reoon as ver  # noqa: E402


def test_reoon_day_key_is_the_utc_date():
    assert ver.today_str() == datetime.now(timezone.utc).date().isoformat()


def test_usage_tracker_resets_with_the_utc_date():
    assert ver.daily_usage()["date"] == datetime.now(timezone.utc).date().isoformat()


def test_pipeline_run_stamp_is_utc():
    assert rp.run_stamp()[:8] == datetime.now(timezone.utc).strftime("%Y%m%d")
    assert rp.now_iso().endswith("Z")
