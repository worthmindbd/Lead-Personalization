"""One bad batch must not take the healthy workers down with it.

The batch code raises SystemExit for ordinary problems — a missing input file,
an unknown batch id, a bad manifest. SystemExit is a BaseException, so the
worker's ``except Exception`` never saw it: it travelled out through
``future.result()`` into the main thread and ended a ten-worker run, throwing
away the nine batches that had already succeeded.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from personalization import run_batches as rb  # noqa: E402


@pytest.fixture
def manifest(tmp_path, monkeypatch):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps({"batches": [{"id": bid, "status": "pending"}
                                for bid in ("001", "002", "003")]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(rb, "MANIFEST", path)
    monkeypatch.setattr(rb, "_warm_linkedin_cache", lambda targets: None)
    monkeypatch.setattr(rb, "merge_enriched", lambda **kw: 0)
    monkeypatch.setattr(rb, "update_master_review", lambda p: None)
    return path


def batch_runner(failing: dict[str, BaseException]):
    """process_batch stand-in: fails for the listed ids, succeeds otherwise."""
    ran: list[str] = []

    def run(bid, source, manifest_path, auto_merge=True):
        ran.append(bid)
        if bid in failing:
            raise failing[bid]
        return {"qa_pass": 3, "qa_total": 3}

    return run, ran


# ---------------------------------------------------------------------------
# The worker
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "failure",
    [SystemExit("no such batch"), RuntimeError("scrape blew up")],
    ids=["SystemExit", "Exception"],
)
def test_a_failure_comes_back_as_a_value(monkeypatch, failure):
    run, _ = batch_runner({"001": failure})
    monkeypatch.setattr(rb, "process_batch", run)

    bid, result = rb._run_one_batch("001")

    assert bid == "001"
    assert result is failure


def test_a_success_comes_back_as_its_result(monkeypatch):
    run, _ = batch_runner({})
    monkeypatch.setattr(rb, "process_batch", run)

    assert rb._run_one_batch("001") == ("001", {"qa_pass": 3, "qa_total": 3})


def test_keyboardinterrupt_is_still_allowed_out(monkeypatch):
    """Ctrl-C must stop the run, not be filed as a batch failure."""
    def run(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(rb, "process_batch", run)
    with pytest.raises(KeyboardInterrupt):
        rb._run_one_batch("001")


# ---------------------------------------------------------------------------
# The pool
# ---------------------------------------------------------------------------


def test_healthy_batches_finish_when_one_exits(manifest, monkeypatch, capsys):
    run, ran = batch_runner({"002": SystemExit("batch 002 input missing")})
    monkeypatch.setattr(rb, "process_batch", run)

    with pytest.raises(SystemExit) as exc:
        rb.run_batches(all_pending=True, workers=3)

    # The run ends by reporting the failure, not by propagating it raw.
    assert "1 batch(es) failed: 002" in str(exc.value)
    assert sorted(ran) == ["001", "002", "003"]
    assert "batch 002 FAILED: batch 002 input missing" in capsys.readouterr().out


def test_every_failure_is_reported_not_just_the_first(manifest, monkeypatch):
    run, _ = batch_runner({"001": SystemExit("a"), "003": RuntimeError("b")})
    monkeypatch.setattr(rb, "process_batch", run)

    with pytest.raises(SystemExit) as exc:
        rb.run_batches(all_pending=True, workers=3)

    assert "2 batch(es) failed" in str(exc.value)
    assert "001" in str(exc.value) and "003" in str(exc.value)


def test_a_clean_parallel_run_merges_once(manifest, monkeypatch):
    run, ran = batch_runner({})
    merged: list[dict] = []
    monkeypatch.setattr(rb, "process_batch", run)
    monkeypatch.setattr(rb, "merge_enriched", lambda **kw: merged.append(kw))

    rb.run_batches(all_pending=True, workers=3)

    assert sorted(ran) == ["001", "002", "003"]
    assert len(merged) == 1


def test_serial_runs_still_stop_at_the_first_failure(manifest, monkeypatch):
    """Unchanged: one worker means no siblings to protect, so fail fast."""
    run, ran = batch_runner({"002": SystemExit("boom")})
    monkeypatch.setattr(rb, "process_batch", run)

    with pytest.raises(SystemExit, match="boom"):
        rb.run_batches(all_pending=True, workers=1)

    assert ran == ["001", "002"]  # never reached 003
