"""A batch interrupted between copy and export must resume, not strand.

``process_batch`` flips a batch ``pending -> copy_done`` once the research and
copy JSONs are on disk, and ``copy_done -> exported`` after the enriched CSV is
built. ``run_batches --all-pending`` — the resume command AGENTS.md documents —
used to select only ``pending``, so a crash in that window left the batch in a
dead state: never re-run, missing from the merge, and its leads only recovered
when a later delta paid for the same research a second time.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lead_personalization.research import fallback_research_item  # noqa: E402
from personalization import process_batch as pb  # noqa: E402
from personalization import run_batches as rb  # noqa: E402

SOURCE_ROW = {
    "row_index": "0",
    "primary_email": "a@x.com",
    "company_name": "Co A",
    "City": "Austin",
    "State": "Texas",
    "First_category": "Spa",
    "aevora_segment": "low_fit",
    "outreach_tier": "company",
    "Linkedin_URL": "https://linkedin.com/in/co-a",
}


def write_source(tmp_path: Path, rows: list[dict] | None = None) -> Path:
    rows = rows if rows is not None else [SOURCE_ROW]
    source = tmp_path / "source.csv"
    with source.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return source


def write_manifest(tmp_path: Path, batches: list[dict], prefix: str = "list") -> Path:
    path = tmp_path / f"{prefix}-batch-manifest.json"
    path.write_text(
        json.dumps({"prefix": prefix, "batches": batches}), encoding="utf-8"
    )
    return path


def write_copy_done_artifacts(campaigns: Path, prefix: str = "list", bid: str = "001"):
    """The state a crash between copy and export leaves behind."""
    campaigns.mkdir(parents=True, exist_ok=True)
    research = [dict(fallback_research_item(SOURCE_ROW, "stub"), row_index=0)]
    copy = {"0": [["s1", "Hi,\n\nb1\n\ncta1"],
                  ["s2", "Hi,\n\nb2\n\ncta2"],
                  ["s3", "Hi,\n\nb3\n\ncta3"]]}
    (campaigns / f"{prefix}-batch-{bid}-research.json").write_text(
        json.dumps(research), encoding="utf-8"
    )
    (campaigns / f"{prefix}-batch-{bid}-copy.json").write_text(
        json.dumps(copy), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Target selection
# ---------------------------------------------------------------------------


def test_all_pending_picks_up_copy_done_but_leaves_exported_alone(tmp_path, monkeypatch):
    path = write_manifest(tmp_path, [
        {"id": "001", "rows": [0], "status": "pending"},
        {"id": "002", "rows": [1], "status": "copy_done"},
        {"id": "003", "rows": [2], "status": "exported"},
    ])
    monkeypatch.setattr(rb, "MANIFEST", path)
    monkeypatch.setattr(rb, "_warm_linkedin_cache", lambda targets: None)
    monkeypatch.setattr(rb, "merge_enriched", lambda **kw: 0)
    monkeypatch.setattr(rb, "update_master_review", lambda p: None)
    ran: list[str] = []

    def run(bid, source, manifest_path, auto_merge=True):
        ran.append(bid)
        return {"qa_pass": 1, "qa_total": 3}

    monkeypatch.setattr(rb, "process_batch", run)
    rb.run_batches(all_pending=True, workers=1)

    assert ran == ["001", "002"]


# ---------------------------------------------------------------------------
# process_batch resume
# ---------------------------------------------------------------------------


def test_a_copy_done_batch_rebuilds_from_disk_without_research(tmp_path, monkeypatch):
    source = write_source(tmp_path)
    manifest = write_manifest(tmp_path, [{"id": "001", "rows": [0], "status": "copy_done"}])
    campaigns = tmp_path / "campaigns"
    write_copy_done_artifacts(campaigns)

    def no_research(*args, **kwargs):
        raise AssertionError("resume re-ran research it already had on disk")

    monkeypatch.setattr(pb, "research_lead", no_research)
    monkeypatch.setattr(pb, "LINKEDIN_ENRICH", False)
    builds: list[tuple] = []
    monkeypatch.setattr(
        pb, "build_batch",
        lambda *a, **k: builds.append(a) or {"qa_pass": 3, "qa_total": 3},
    )

    result = pb.process_batch(
        "001", source, manifest, campaigns_dir=campaigns, auto_merge=False
    )

    assert len(builds) == 1
    assert result["leads"] == 1
    assert json.loads(manifest.read_text(encoding="utf-8"))["batches"][0]["status"] == "exported"


def test_copy_done_with_missing_artifacts_reruns_the_full_path(tmp_path, monkeypatch):
    """The status alone is not trusted: a swept campaigns/ dir means the JSONs
    the resume would rebuild from are gone, so research runs again."""
    source = write_source(tmp_path)
    manifest = write_manifest(tmp_path, [{"id": "001", "rows": [0], "status": "copy_done"}])
    campaigns = tmp_path / "campaigns"  # deliberately empty

    researched: list[str] = []

    def stub_research(row, li_scraped, renderer=None, render_fallback=True):
        researched.append(row["primary_email"])
        return fallback_research_item(row, "stub")

    monkeypatch.setattr(pb, "research_lead", stub_research)
    monkeypatch.setattr(pb, "LINKEDIN_ENRICH", False)
    monkeypatch.setattr(pb, "build_batch", lambda *a, **k: {"qa_pass": 3, "qa_total": 3})

    pb.process_batch(
        "001", source, manifest, campaigns_dir=campaigns, auto_merge=False
    )

    assert researched == ["a@x.com"]
    assert (campaigns / "list-batch-001-research.json").is_file()
    assert (campaigns / "list-batch-001-copy.json").is_file()


def test_a_pending_batch_never_takes_the_resume_path(tmp_path, monkeypatch):
    """Even with stray artifacts on disk, a pending batch does fresh research —
    the resume is keyed on the status the crash left, not on file presence."""
    source = write_source(tmp_path)
    manifest = write_manifest(tmp_path, [{"id": "001", "rows": [0], "status": "pending"}])
    campaigns = tmp_path / "campaigns"
    write_copy_done_artifacts(campaigns)

    researched: list[str] = []

    def stub_research(row, li_scraped, renderer=None, render_fallback=True):
        researched.append(row["primary_email"])
        return fallback_research_item(row, "stub")

    monkeypatch.setattr(pb, "research_lead", stub_research)
    monkeypatch.setattr(pb, "LINKEDIN_ENRICH", False)
    monkeypatch.setattr(pb, "build_batch", lambda *a, **k: {"qa_pass": 3, "qa_total": 3})

    pb.process_batch(
        "001", source, manifest, campaigns_dir=campaigns, auto_merge=False
    )

    assert researched == ["a@x.com"]


# ---------------------------------------------------------------------------
# LinkedIn warm-up must not pay for batches that will not research
# ---------------------------------------------------------------------------


def test_warm_skips_batches_that_will_resume_from_disk(tmp_path, monkeypatch):
    rows = [
        dict(SOURCE_ROW, row_index="0", primary_email="a@x.com",
             Linkedin_URL="https://linkedin.com/in/resumable"),
        dict(SOURCE_ROW, row_index="1", primary_email="b@x.com",
             Linkedin_URL="https://linkedin.com/in/fresh"),
    ]
    source = write_source(tmp_path, rows)
    manifest = write_manifest(tmp_path, [
        {"id": "001", "rows": [0], "status": "copy_done"},
        {"id": "002", "rows": [1], "status": "pending"},
    ])
    write_copy_done_artifacts(tmp_path / "campaigns")

    monkeypatch.setattr(rb, "MANIFEST", manifest)
    monkeypatch.setattr(rb, "SOURCE", source)
    monkeypatch.setattr(rb, "ROOT", tmp_path)
    monkeypatch.setattr(pb, "LINKEDIN_ENRICH", True)
    scraped: list[list[str]] = []
    monkeypatch.setattr(
        pb.linkedin_apify, "scrape_profiles",
        lambda urls, max_posts=2: scraped.append(list(urls)) or {},
    )

    rb._warm_linkedin_cache(["001", "002"])

    assert scraped == [["https://linkedin.com/in/fresh"]]
