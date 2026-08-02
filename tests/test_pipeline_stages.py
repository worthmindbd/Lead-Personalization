"""Direct tests for the pipeline stages the earlier fixes leaned on.

``stage_verify`` decides whether to spend Reoon credits, and ``verify_complete``
downstream of it is what the report and the reconcile short-circuit trust.
``merge_into_cumulative`` is where a list's per-batch output becomes the
enriched CSV that ``compute_delta`` and the contacted index read back. All three
were exercised only end-to-end, through a run that talks to Drive and a paid
API — which is to say, not at all.
"""

from __future__ import annotations

import csv
import json
import sys
from argparse import Namespace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pipeline"))

import run_pipeline as rp  # noqa: E402


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = fieldnames or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=names)
        writer.writeheader()
        writer.writerows(rows)
    return path


def emails_csv(path: Path, emails: list[str]) -> Path:
    return write_csv(
        path,
        [{"primary_email": e, "company": f"Co {i}"} for i, e in enumerate(emails)],
        ["primary_email", "company"],
    )


# ---------------------------------------------------------------------------
# merge_into_cumulative
# ---------------------------------------------------------------------------


def test_batches_append_into_an_empty_cumulative(tmp_path):
    a = emails_csv(tmp_path / "a.csv", ["one@x.com", "two@x.com"])
    b = emails_csv(tmp_path / "b.csv", ["three@x.com"])
    cumulative = tmp_path / "out" / "cumulative.csv"

    added, total = rp.merge_into_cumulative([a, b], cumulative)

    assert (added, total) == (3, 3)
    _, rows = rp.load_rows(cumulative)
    assert [rp.row_email(r) for r in rows] == ["one@x.com", "two@x.com", "three@x.com"]


def test_a_second_merge_adds_only_what_is_new(tmp_path):
    cumulative = tmp_path / "cumulative.csv"
    rp.merge_into_cumulative([emails_csv(tmp_path / "a.csv", ["one@x.com"])], cumulative)

    added, total = rp.merge_into_cumulative(
        [emails_csv(tmp_path / "b.csv", ["one@x.com", "two@x.com"])], cumulative
    )

    assert (added, total) == (1, 2)


def test_the_existing_rows_survive_a_rerun(tmp_path):
    """Idempotence is what makes a re-run safe: merging the same batch twice
    must not truncate the file it already wrote."""
    cumulative = tmp_path / "cumulative.csv"
    batch = emails_csv(tmp_path / "a.csv", ["one@x.com", "two@x.com"])
    rp.merge_into_cumulative([batch], cumulative)

    added, total = rp.merge_into_cumulative([batch], cumulative)

    assert (added, total) == (0, 2)
    _, rows = rp.load_rows(cumulative)
    assert len(rows) == 2


def test_a_new_batch_column_widens_the_header(tmp_path):
    """Batches gain columns over time (a new copy field, a new signal). The
    older rows keep their values; the header grows to fit the newcomer."""
    cumulative = tmp_path / "cumulative.csv"
    rp.merge_into_cumulative([emails_csv(tmp_path / "a.csv", ["one@x.com"])], cumulative)

    wider = write_csv(
        tmp_path / "b.csv",
        [{"primary_email": "two@x.com", "company": "Co", "copy_variant": "v2"}],
    )
    rp.merge_into_cumulative([wider], cumulative)

    fieldnames, rows = rp.load_rows(cumulative)
    assert fieldnames == ["primary_email", "company", "copy_variant"]
    assert rows[0]["copy_variant"] == ""
    assert rows[1]["copy_variant"] == "v2"


def test_rows_without_an_address_are_dropped(tmp_path):
    batch = write_csv(
        tmp_path / "a.csv",
        [{"primary_email": "", "company": "No contact"},
         {"primary_email": "one@x.com", "company": "Co"}],
    )

    added, total = rp.merge_into_cumulative([batch], tmp_path / "cumulative.csv")

    assert (added, total) == (1, 1)


def test_no_partial_file_is_left_when_the_write_fails(tmp_path, monkeypatch):
    """The write goes via a .tmp + replace. If it dies mid-way, the previous
    cumulative list must still be the one on disk — a half-written enriched CSV
    would silently shrink the contacted index on the next backfill."""
    cumulative = tmp_path / "cumulative.csv"
    rp.merge_into_cumulative([emails_csv(tmp_path / "a.csv", ["one@x.com"])], cumulative)
    before = cumulative.read_text(encoding="utf-8")

    class Boom(Exception):
        pass

    def explode(self, *args, **kwargs):
        raise Boom

    monkeypatch.setattr(Path, "replace", explode)
    with pytest.raises(Boom):
        rp.merge_into_cumulative([emails_csv(tmp_path / "b.csv", ["two@x.com"])], cumulative)

    assert cumulative.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# compute_delta — the parts the contacted-index tests do not reach
# ---------------------------------------------------------------------------


def test_delta_carries_the_source_fieldnames(tmp_path):
    """The caller writes the delta CSV with these names; losing one loses a
    column of research the personalizer needs."""
    verified = write_csv(
        tmp_path / "v.csv",
        [{"primary_email": "a@x.com", "company": "Co", "Status": "safe"}],
    )

    fieldnames, delta, _ = rp.compute_delta(verified, tmp_path / "missing.csv")

    assert fieldnames == ["primary_email", "company", "Status"]
    assert delta[0]["Status"] == "safe"


def test_rows_with_no_address_never_reach_the_delta(tmp_path):
    verified = write_csv(
        tmp_path / "v.csv",
        [{"primary_email": "", "company": "No contact"},
         {"primary_email": "not-an-email", "company": "Junk"},
         {"primary_email": "a@x.com", "company": "Co"}],
    )

    _, delta, _ = rp.compute_delta(verified, tmp_path / "missing.csv")

    assert [rp.row_email(r) for r in delta] == ["a@x.com"]


def test_an_empty_verified_list_yields_an_empty_delta(tmp_path):
    verified = write_csv(tmp_path / "v.csv", [], ["primary_email", "company"])

    fieldnames, delta, suppressed = rp.compute_delta(verified, tmp_path / "missing.csv")

    assert fieldnames == ["primary_email", "company"]
    assert delta == [] and suppressed == 0


# ---------------------------------------------------------------------------
# stage_verify
# ---------------------------------------------------------------------------


@pytest.fixture
def verify_env(tmp_path, monkeypatch):
    """A list ready to verify, with the cache and Drive-free paths pinned."""
    monkeypatch.setattr(rp, "ROOT", tmp_path)
    monkeypatch.setattr(rp, "WORK_ROOT", tmp_path / "leads" / "pipeline")
    monkeypatch.setattr(rp, "REOON_CACHE_FILE", tmp_path / ".reoon" / "verified_cache.json")
    monkeypatch.setattr(rp, "REOON_REJECTED_FILE", tmp_path / ".reoon" / "rejected.json")
    monkeypatch.setenv("REOON_API_KEY", "test-key")

    workdir = tmp_path / "leads" / "pipeline" / "july-1"
    cleaned = emails_csv(workdir / "july-1-cleaned.csv", ["a@x.com", "b@x.com", "c@x.com"])
    entry = rp.new_entry("July 1")
    entry["slug"] = "july-1"
    entry["cleaned_csv"] = str(cleaned.relative_to(tmp_path))
    return entry, workdir


def no_subprocess(monkeypatch):
    """Fail loudly if the stage shells out to the verifier."""
    def guard(*args, **kwargs):
        raise AssertionError("stage_verify spent Reoon credits when it should not have")

    monkeypatch.setattr(rp.subprocess, "run", guard)


def fake_verifier(monkeypatch, workdir: Path, results: dict[str, str], returncode: int = 0):
    """Stand in for verify_emails_reoon.py: cache what it checked, write the
    rows it kept. Returns the list of commands it was invoked with."""
    calls: list[list[str]] = []

    def run(cmd, **kwargs):
        calls.append(cmd)
        cache = rp.load_json(rp.REOON_CACHE_FILE, {})
        cache.update({e: {"status": s} for e, s in results.items()})
        rp.save_json_atomic(rp.REOON_CACHE_FILE, cache)
        kept = [e for e, s in results.items() if s == "safe"]
        emails_csv(workdir / "july-1-verified.csv", kept)
        return Namespace(returncode=returncode)

    monkeypatch.setattr(rp.subprocess, "run", run)
    return calls


def args_for(**overrides) -> Namespace:
    return Namespace(**{"no_verify": False, "verify_limit": 500, **overrides})


def test_no_verify_records_the_backlog_without_spending(verify_env, monkeypatch, capsys):
    entry, _ = verify_env
    no_subprocess(monkeypatch)

    rp.stage_verify("July 1", entry, args_for(no_verify=True))

    assert entry["pending_verification"] == 3
    assert entry["verify_complete"] is False
    assert "skipped (--no-verify)" in capsys.readouterr().out


def test_a_missing_api_key_defers_rather_than_failing(verify_env, monkeypatch, capsys):
    entry, _ = verify_env
    monkeypatch.delenv("REOON_API_KEY")
    no_subprocess(monkeypatch)

    rp.stage_verify("July 1", entry, args_for())

    assert entry["pending_verification"] == 3
    assert "REOON_API_KEY not configured" in capsys.readouterr().out


def test_a_placeholder_api_key_counts_as_missing(verify_env, monkeypatch):
    entry, _ = verify_env
    monkeypatch.setenv("REOON_API_KEY", "your_api_key_here")
    no_subprocess(monkeypatch)

    rp.stage_verify("July 1", entry, args_for())

    assert entry["pending_verification"] == 3


def test_a_fully_cached_list_is_not_re_sent(verify_env, monkeypatch, capsys):
    """Every address answered and a verified list on disk: nothing to buy."""
    entry, workdir = verify_env
    rp.save_json_atomic(
        rp.REOON_CACHE_FILE,
        {"a@x.com": {"status": "safe"}, "b@x.com": {"status": "invalid"},
         "c@x.com": {"status": "safe"}},
    )
    emails_csv(workdir / "july-1-verified.csv", ["a@x.com", "c@x.com"])
    no_subprocess(monkeypatch)

    rp.stage_verify("July 1", entry, args_for())

    assert entry["pending_verification"] == 0
    assert entry["verify_complete"] is True
    assert "cache hit, skip" in capsys.readouterr().out


def test_a_tombstoned_address_is_not_pending(verify_env, monkeypatch):
    """The Step 3 tombstones exist precisely so a rejected address stops
    looking unchecked. If they did not count here, a reset would re-buy them."""
    entry, workdir = verify_env
    rp.save_json_atomic(rp.REOON_CACHE_FILE, {"a@x.com": {"status": "safe"}})
    rp.save_rejected({"b@x.com": {"status": "inferred_rejected"},
                      "c@x.com": {"status": "inferred_rejected"}})
    emails_csv(workdir / "july-1-verified.csv", ["a@x.com"])
    no_subprocess(monkeypatch)

    rp.stage_verify("July 1", entry, args_for())

    assert entry["pending_verification"] == 0
    assert entry["verify_complete"] is True


def test_a_cached_list_with_no_verified_file_is_rebuilt(verify_env, monkeypatch):
    """Zero pending but the verified CSV is gone — regenerate it from the cache
    rather than leaving the list with no output to upload."""
    entry, workdir = verify_env
    rp.save_json_atomic(
        rp.REOON_CACHE_FILE,
        {"a@x.com": {"status": "safe"}, "b@x.com": {"status": "safe"},
         "c@x.com": {"status": "safe"}},
    )
    calls = fake_verifier(monkeypatch, workdir,
                          {"a@x.com": "safe", "b@x.com": "safe", "c@x.com": "safe"})

    rp.stage_verify("July 1", entry, args_for())

    assert len(calls) == 1
    assert (workdir / "july-1-verified.csv").is_file()


def test_a_completed_run_marks_the_list_complete(verify_env, monkeypatch):
    entry, workdir = verify_env
    calls = fake_verifier(monkeypatch, workdir,
                          {"a@x.com": "safe", "b@x.com": "invalid", "c@x.com": "safe"})

    rp.stage_verify("July 1", entry, args_for())

    assert "--limit" in calls[0] and "500" in calls[0]
    assert entry["pending_verification"] == 0
    assert entry["verify_complete"] is True
    assert entry["verified_csv"] == "leads/pipeline/july-1/july-1-verified.csv"
    assert entry["stage"] == "verifying"


def test_a_capped_run_leaves_the_rest_pending(verify_env, monkeypatch, capsys):
    """The daily cap is the normal case, not an error: the stage records what
    is left so the next run resumes instead of starting over."""
    entry, workdir = verify_env
    fake_verifier(monkeypatch, workdir, {"a@x.com": "safe"})

    rp.stage_verify("July 1", entry, args_for(verify_limit=1))

    assert entry["pending_verification"] == 2
    assert entry["verify_complete"] is False
    assert "resume next run/day" in capsys.readouterr().out


def test_a_failing_verifier_does_not_abort_the_list(verify_env, monkeypatch, capsys):
    """A non-zero exit warns and continues — the addresses it did check are
    cached, and the next stage still has whatever it wrote."""
    entry, workdir = verify_env
    fake_verifier(monkeypatch, workdir, {"a@x.com": "safe"}, returncode=1)

    rp.stage_verify("July 1", entry, args_for())

    out = capsys.readouterr().out
    assert "WARNING: verify exited 1" in out
    assert entry["pending_verification"] == 2
    assert entry["verify_complete"] is False


def test_the_reported_row_count_is_the_verified_list(verify_env, monkeypatch, capsys):
    entry, workdir = verify_env
    fake_verifier(monkeypatch, workdir,
                  {"a@x.com": "safe", "b@x.com": "invalid", "c@x.com": "safe"})

    rp.stage_verify("July 1", entry, args_for())

    assert "verified list: 2 rows kept" in capsys.readouterr().out


def test_the_cache_written_by_the_run_is_reread_not_assumed(verify_env, monkeypatch):
    """Pending is recomputed after the subprocess, from the cache on disk. It is
    not inferred from the limit or from the verified row count — a row missing
    from the output is a rejection, not an unchecked address."""
    entry, workdir = verify_env
    fake_verifier(monkeypatch, workdir,
                  {"a@x.com": "invalid", "b@x.com": "invalid", "c@x.com": "invalid"})

    rp.stage_verify("July 1", entry, args_for())

    assert rp.csv_row_count(workdir / "july-1-verified.csv") == 0
    assert entry["pending_verification"] == 0
    assert entry["verify_complete"] is True


def test_state_json_survives_the_stage(verify_env, monkeypatch):
    """The entry is mutated in place; the fields the report reads must all be
    JSON-serializable when save_state writes it out."""
    entry, workdir = verify_env
    fake_verifier(monkeypatch, workdir, {"a@x.com": "safe", "b@x.com": "safe",
                                         "c@x.com": "safe"})

    rp.stage_verify("July 1", entry, args_for())

    assert json.loads(json.dumps(entry))["verify_complete"] is True
