"""One list's personalization run must not touch another's files.

Every artifact used to be called ``mix-leads-batch-{id}-...`` regardless of
which Drive list produced it. ``merge_enriched`` globbed
``mix-leads-batch-*-enriched.csv``, so a leftover batch from another list would
be folded into this list's merged output — the pipeline swept the directory
before every run to stop it — and only one list could personalize at a time.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "pipeline"))

import run_pipeline as rp  # noqa: E402
from personalization import artifacts  # noqa: E402
from personalization.create_batch_manifest import create_manifest  # noqa: E402
from personalization.merge_enriched import merge_enriched  # noqa: E402
from personalization.process_batch import merged_output_path  # noqa: E402


def batch_csv(directory: Path, name: str, emails: list[str]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["primary_email", "company"])
        writer.writeheader()
        for email in emails:
            writer.writerow({"primary_email": email, "company": email.split("@")[0]})
    return path


# ---------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------


BUILDERS = [
    artifacts.research_json,
    artifacts.copy_json,
    artifacts.enriched_csv,
    artifacts.emails_json,
    artifacts.review_md,
]


@pytest.mark.parametrize("builder", BUILDERS, ids=lambda b: b.__name__)
def test_two_lists_never_share_a_per_batch_name(builder):
    """Same batch id, different list: different file."""
    assert builder("july-6", "001") != builder("july-7", "001")


def test_two_lists_never_share_a_per_run_name():
    for build in (artifacts.manifest_path, artifacts.master_review_md,
                  artifacts.normalized_json, artifacts.merged_csv):
        assert build("july-6") != build("july-7"), build.__name__


def test_a_prefix_is_not_a_prefix_of_another_lists_glob():
    """``july`` must not sweep up ``july-6``'s batches.

    The literal ``-batch-`` after the prefix is what keeps the two apart; drop
    it and the shorter name would match the longer one's files.
    """
    from fnmatch import fnmatch

    long_name = artifacts.enriched_csv("july-6", "001").name
    assert not fnmatch(long_name, artifacts.enriched_glob("july"))
    assert fnmatch(long_name, artifacts.enriched_glob("july-6"))


def test_a_slug_survives_unchanged():
    """run_pipeline.slugify and clean_prefix must agree, or the pipeline would
    write files under one name and look for them under another."""
    for title in ("July 6,2026", "July 31,2026", "Leads / Batch #2"):
        slug = rp.slugify(title)
        assert artifacts.clean_prefix(slug) == slug


def test_a_hostile_prefix_cannot_escape_its_directory():
    path = artifacts.enriched_csv("../../etc/pass wd", "001")
    assert path.parent == artifacts.ENRICHED_DIR
    assert "*" not in path.name and ".." not in path.name


def test_an_empty_prefix_falls_back_to_the_default():
    assert artifacts.clean_prefix("") == artifacts.DEFAULT_PREFIX
    assert artifacts.manifest_path().name.startswith(artifacts.DEFAULT_PREFIX)


# ---------------------------------------------------------------------------
# The manifest carries the prefix
# ---------------------------------------------------------------------------


def test_create_manifest_records_the_prefix(tmp_path, monkeypatch):
    from personalization import create_batch_manifest as cbm

    monkeypatch.setattr(cbm, "ROOT", tmp_path)
    source = batch_csv(tmp_path, "july-6-delta-normalized.csv", ["a@x.com", "b@x.com"])
    manifest_path = tmp_path / "july-6-batch-manifest.json"

    create_manifest(source, manifest_path, batch_size=1)

    assert json.loads(manifest_path.read_text())["prefix"] == "july-6"
    assert artifacts.prefix_for(manifest_path) == "july-6"


def test_the_manifest_cli_takes_a_destination(tmp_path, monkeypatch):
    """Without a second argument there is no way to build a manifest anywhere
    but the shared mix-leads path — so the manual flow could not run two lists
    side by side even though run_batches.py accepts --manifest."""
    from personalization import create_batch_manifest as cbm

    monkeypatch.setattr(cbm, "ROOT", tmp_path)
    source = batch_csv(tmp_path, "src.csv", ["a@x.com"])
    dest = tmp_path / "july-9-batch-manifest.json"
    monkeypatch.setattr(sys, "argv", ["create_batch_manifest.py", str(source), str(dest)])

    cbm.main()

    assert json.loads(dest.read_text())["prefix"] == "july-9"


def test_a_manifest_without_a_prefix_falls_back_to_its_filename(tmp_path):
    """Written before prefixes existed — still names its own artifacts."""
    path = tmp_path / "july-7-batch-manifest.json"
    path.write_text(json.dumps({"batches": []}), encoding="utf-8")

    assert artifacts.prefix_for(path) == "july-7"


def test_an_unreadable_manifest_does_not_raise_here(tmp_path):
    """The caller is about to fail on it for a much better reason."""
    path = tmp_path / "july-8-batch-manifest.json"
    path.write_text("{not json", encoding="utf-8")

    assert artifacts.prefix_for(path) == "july-8"
    assert artifacts.prefix_for(tmp_path / "gone.json") == artifacts.DEFAULT_PREFIX


# ---------------------------------------------------------------------------
# The merge
# ---------------------------------------------------------------------------


@pytest.fixture
def two_lists_enriched(tmp_path):
    """leads/enriched/ holding batches from two lists at once."""
    enriched = tmp_path / "enriched"
    batch_csv(enriched, "july-6-batch-001-enriched.csv", ["six-a@x.com", "six-b@x.com"])
    batch_csv(enriched, "july-6-batch-002-enriched.csv", ["six-c@x.com"])
    batch_csv(enriched, "july-7-batch-001-enriched.csv", ["seven-a@x.com"])
    return enriched


def test_a_merge_sees_only_its_own_lists_batches(two_lists_enriched, tmp_path):
    out = tmp_path / "july-6-enriched.csv"

    rows = merge_enriched(two_lists_enriched, out, tmp_path / "absent.json", prefix="july-6")

    assert rows == 3
    with out.open(newline="", encoding="utf-8") as f:
        assert [r["primary_email"] for r in csv.DictReader(f)] == [
            "six-a@x.com", "six-b@x.com", "six-c@x.com"
        ]


def test_the_other_list_merges_independently(two_lists_enriched, tmp_path):
    out = tmp_path / "july-7-enriched.csv"

    assert merge_enriched(two_lists_enriched, out, tmp_path / "absent.json", prefix="july-7") == 1


def test_a_merge_with_no_batches_of_its_own_is_an_error(two_lists_enriched, tmp_path):
    """Not a silent empty file: july-8 has nothing here, and merging the other
    lists' batches into its output is exactly the bug being fixed."""
    with pytest.raises(SystemExit, match="july-8-batch-"):
        merge_enriched(two_lists_enriched, tmp_path / "out.csv",
                       tmp_path / "absent.json", prefix="july-8")


def test_the_merge_takes_its_prefix_from_the_manifest(two_lists_enriched, tmp_path, monkeypatch):
    """No prefix argument: read it from the manifest the run is working on."""
    from personalization import merge_enriched as me

    monkeypatch.setattr(me, "ROOT", tmp_path)
    manifest = tmp_path / "july-7-batch-manifest.json"
    manifest.write_text(json.dumps({"prefix": "july-7", "batches": []}), encoding="utf-8")

    assert merge_enriched(two_lists_enriched, tmp_path / "out.csv", manifest) == 1
    assert json.loads(manifest.read_text())["merged_row_count"] == 1


# ---------------------------------------------------------------------------
# The merged output path
# ---------------------------------------------------------------------------


def test_three_july_lists_used_to_share_one_merged_file():
    """The old derivation truncates the source stem at the first digit."""
    sources = [Path(f"leads/pipeline/july-{d}/july-{d}-delta-normalized-100.csv")
               for d in (6, 7, 8)]

    assert len({merged_output_path(s) for s in sources}) == 1
    assert len({merged_output_path(s, f"july-{d}") for s, d in zip(sources, (6, 7, 8))}) == 3


# ---------------------------------------------------------------------------
# The archive list
# ---------------------------------------------------------------------------


def test_the_archive_covers_every_file_a_run_writes():
    """A new artifact that nobody adds here is left behind in a shared
    directory, where the list's next delta silently overwrites it."""
    entry = {"slug": "july-6"}
    batch_ids = ["001", "002"]
    archived = set(rp.batch_artifact_paths(batch_ids, entry))

    expected = {
        artifacts.manifest_path("july-6"),
        artifacts.normalized_json("july-6"),
        artifacts.master_review_md("july-6"),
        artifacts.merged_csv("july-6"),
    }
    for bid in batch_ids:
        expected |= {b("july-6", bid) for b in BUILDERS}

    assert expected <= archived


def test_the_pipeline_names_the_normalized_sidecar_per_list(tmp_path, monkeypatch):
    """``normalize_leads`` defaults its sidecar JSON to a single
    campaigns/mix-leads-normalized.json. Left at the default it is one more name
    two lists overwrite, and the archive step above would look for a file that
    was never written."""
    monkeypatch.setattr(rp, "ROOT", tmp_path)
    workdir = tmp_path / "leads" / "pipeline" / "july-6"
    verified = batch_csv(workdir, "july-6-verified.csv", ["a@x.com"])
    monkeypatch.setattr(rp, "workdir_for", lambda entry: workdir)
    monkeypatch.setattr(rp, "load_contacted", dict)

    seen = {}

    class Stop(Exception):
        pass

    def capture(source, **kwargs):
        seen.update(kwargs)
        raise Stop

    monkeypatch.setattr(rp, "normalize_leads", capture)

    entry = {"slug": "july-6", "verified_csv": str(verified.relative_to(tmp_path))}
    with pytest.raises(Stop):
        rp.stage_personalize("July 6,2026", entry, object(), {})

    assert seen["json_out"] == artifacts.normalized_json("july-6")


def test_the_archive_names_this_lists_manifest_lock():
    paths = rp.batch_artifact_paths([], {"slug": "july-6"})
    assert any(p.name == "july-6-batch-manifest.json.lock" for p in paths)


def test_two_lists_archive_disjoint_files():
    six = set(rp.batch_artifact_paths(["001"], {"slug": "july-6"}))
    seven = set(rp.batch_artifact_paths(["001"], {"slug": "july-7"}))
    assert not (six & seven)


# ---------------------------------------------------------------------------
# run_batches switching lists
# ---------------------------------------------------------------------------


def test_use_manifest_rebinds_the_source_too(tmp_path, monkeypatch):
    """SOURCE is derived from the manifest. Rebinding only MANIFEST would leave
    the worker reading the previous list's CSV against the new list's batches."""
    from personalization import run_batches as rb

    source = batch_csv(tmp_path, "july-7-normalized.csv", ["a@x.com"])
    manifest = tmp_path / "july-7-batch-manifest.json"
    manifest.write_text(
        json.dumps({"prefix": "july-7", "source": str(source), "batches": []}),
        encoding="utf-8",
    )
    monkeypatch.setattr(rb, "MANIFEST", REPO_ROOT / "campaigns" / "other.json")
    monkeypatch.setattr(rb, "SOURCE", REPO_ROOT / "leads" / "other.csv")

    rb.use_manifest(manifest)

    assert rb.MANIFEST == manifest
    assert rb.SOURCE.name == "july-7-normalized.csv"
