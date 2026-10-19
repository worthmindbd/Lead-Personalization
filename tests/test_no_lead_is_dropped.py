"""A lead with a mailable address is never dropped for being a poor fit.

This replaces ``tests/test_fit_score.py``, whose premise was wrong. It asserted
that ``process_batch`` excludes leads scoring ``fit_score == "skip"`` — the
docstring, the README and the skill docs all said so — but the selection was
always ``[all_rows[i] for i in batch["rows"]]``, with no filter, in every commit
back to ``a676e35``. The real output agrees: July 6 personalized 2,381 of 2,381
verified, July 7 2,142 of 2,142, July 25 102 of 102.

So ``fit_score`` scored leads that nothing ever excluded. It is gone, and these
tests are the guard that no equivalent gate comes back: the exclusion that was
documented for months would have passed unnoticed precisely because no test
covered how many rows come out of a batch.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lead_personalization import pipeline as lp_pipeline  # noqa: E402
from lead_personalization import segments as lp_segments  # noqa: E402
from lead_personalization.pipeline import DERIVED_FIELDS, normalize_row  # noqa: E402
from personalization import process_batch as pb  # noqa: E402
from personalization.clean_gmb_leads import CLOSED_STATUSES, clean_gmb_leads  # noqa: E402

# The categories the deleted fit rule scored "skip" — the competition. They are
# also the four commonest on the real july-20-2026 list (228 + 53 + 48 + 34 of
# the 740 rows it would have labelled skip).
FORMER_SKIP_CATEGORIES = [
    "Film production company",
    "Recording studio",
    "Animation studio",
    "Video editing service",
]


def row(category: str, email: str = "hello@lakeview.com") -> dict:
    return {
        "Name": "Lakeview Custom Homes LLC",
        "Email": email,
        "Website": "https://lakeview.com",
        "First_category": category,
        "City": "Austin",
        "State": "Texas",
    }


# ---------------------------------------------------------------------------
# The column is gone
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("category", FORMER_SKIP_CATEGORIES + ["Custom home builder", ""])
def test_normalize_row_emits_no_fit_score(category: str) -> None:
    assert "fit_score" not in normalize_row(0, row(category))


def test_fit_score_is_not_in_the_declared_schema() -> None:
    """In DERIVED_FIELDS but not on the row (or the reverse) is how the column
    silently reappears in every enriched export."""
    assert "fit_score" not in DERIVED_FIELDS


def test_nothing_still_scores_leads_for_fit() -> None:
    assert not hasattr(lp_segments, "fit_score_for")
    assert not hasattr(lp_pipeline, "fit_score_for")


@pytest.mark.parametrize("category", FORMER_SKIP_CATEGORIES)
def test_a_former_skip_category_still_gets_a_segment(category: str) -> None:
    """Segments choose the copy angle; the general pool is a full pool with its
    own subject templates, not a demotion. Losing fit_score must not lose this."""
    assert normalize_row(0, row(category))["aevora_segment"] == "general"


# ---------------------------------------------------------------------------
# The batch keeps every row
# ---------------------------------------------------------------------------


def _stub_research(row_: dict, li_scraped, renderer=None, render_fallback=True) -> dict:
    """research_lead's shape, without touching the network or a browser."""
    return {
        "email": row_["primary_email"],
        "company": row_.get("company_name", ""),
        "first_name": "",
        "last_name": "",
        "title": "",
        "outreach_tier": "company",
        "aevora_segment": row_.get("aevora_segment", "low_fit"),
        "research_signal": "video on site: no; Austin, Texas",
        "research_notes": "",
        "signal_strength": "weak",
        "evidence": "weak",
        "snippet": "",
        "social_channel": "",
        "linkedin_topic": "",
        "linkedin_posts_count": 0,
        "linkedin_last_post": "",
        "website": row_.get("Website", ""),
        "linkedin": "",
        "twitter": "",
        "facebook": "",
    }


def _batch_of(tmp_path: Path, categories: list[str], monkeypatch) -> dict:
    """Normalize one row per category, run them through process_batch."""
    rows = [
        normalize_row(i, row(cat, f"lead{i}@example-biz.com"))
        for i, cat in enumerate(categories)
    ]
    source = tmp_path / "source.csv"
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    manifest_path = tmp_path / "list-batch-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "prefix": "list",
                "batches": [
                    {"id": "001", "rows": list(range(len(rows))), "status": "pending"}
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(pb, "research_lead", _stub_research)
    monkeypatch.setattr(pb, "LINKEDIN_ENRICH", False)
    result = pb.process_batch(
        "001",
        source,
        manifest_path,
        campaigns_dir=tmp_path / "campaigns",
        skip_build=True,
    )
    return {"result": result, "sent": len(rows)}


def test_every_row_in_the_batch_gets_copy(tmp_path, monkeypatch) -> None:
    """The regression guard the suite never had: count rows out, not just that
    the batch ran. A fit filter reappearing would drop 4 of these 6 silently."""
    categories = FORMER_SKIP_CATEGORIES + ["Custom home builder", "Dentist"]
    out = _batch_of(tmp_path, categories, monkeypatch)

    assert out["result"]["leads"] == out["sent"] == 6

    research = json.loads(Path(out["result"]["research"]).read_text(encoding="utf-8"))
    copy = json.loads(Path(out["result"]["copy"]).read_text(encoding="utf-8"))
    assert len(research) == 6
    assert len(copy) == 6
    # Every address that went in has a full 3-email sequence coming out, keyed
    # by row_index (emails can be duplicated or missing across rows).
    assert {item["email"] for item in research} == {
        f"lead{i}@example-biz.com" for i in range(6)
    }
    for seq in copy.values():
        assert len(seq) == 3


def test_a_competitor_alone_in_a_batch_still_gets_copy(tmp_path, monkeypatch) -> None:
    """A batch of nothing but former-skip leads must not come out empty."""
    out = _batch_of(tmp_path, FORMER_SKIP_CATEGORIES, monkeypatch)
    assert out["result"]["leads"] == 4
    assert len(json.loads(Path(out["result"]["copy"]).read_text(encoding="utf-8"))) == 4


# ---------------------------------------------------------------------------
# The cleaner keeps every mailable address
# ---------------------------------------------------------------------------


def _raw_export(tmp_path: Path, rows: list[dict]) -> Path:
    source = tmp_path / "raw.csv"
    pd.DataFrame(rows).to_csv(source, index=False)
    return source


def _gmb_row(email: str, status: str = "Operational", **extra) -> dict:
    base = {
        "Name": "Lakeview Custom Homes",
        "Email_From_WEBSITE": email,
        "Website": "https://lakeview.com",
        "Business_Status": status,
        "First_category": "Custom home builder",
        "City": "Austin",
        "State": "Texas",
        "Country": "United States",
    }
    base.update(extra)
    return base


# Parametrized over the real CLOSED_STATUSES rather than invented spellings: a
# status the filter never matched would pass this test with the filter back in.
@pytest.mark.parametrize("status", sorted(CLOSED_STATUSES))
def test_a_closed_business_with_a_real_email_survives_cleaning(tmp_path, status) -> None:
    """Closed on Google Maps, working inbox. The listing is stale; the person
    is not. This filter was on by default and removed them."""
    source = _raw_export(tmp_path, [_gmb_row("owner@lakeview.com", status)])
    out = clean_gmb_leads(source, tmp_path / "out.csv")
    assert list(out["Email"]) == ["owner@lakeview.com"]


def test_cleaning_still_drops_what_cannot_be_mailed(tmp_path) -> None:
    """Keeping every fit is not keeping every row — an address that cannot
    receive mail is still worthless."""
    source = _raw_export(
        tmp_path,
        [
            _gmb_row("real@lakeview.com"),
            _gmb_row(""),
            _gmb_row("someone@example.com"),
            _gmb_row("real@lakeview.com", Name="Duplicate listing"),
        ],
    )
    out = clean_gmb_leads(source, tmp_path / "out.csv")
    assert list(out["Email"]) == ["real@lakeview.com"]


def test_info_at_survives_cleaning(tmp_path) -> None:
    """info@ is many small businesses' primary inbox — the owner reads it
    directly.  It stays while other departmental prefixes are removed."""
    source = _raw_export(
        tmp_path,
        [_gmb_row("info@lakeview.com")],
    )
    out = clean_gmb_leads(source, tmp_path / "out.csv")
    assert list(out["Email"]) == ["info@lakeview.com"]


def test_noreply_at_is_removed(tmp_path) -> None:
    """noreply@ is an outbound-only mailbox — incoming mail is rejected or
    silently discarded.  Sending cold email to it is a guaranteed waste."""
    source = _raw_export(
        tmp_path,
        [_gmb_row("noreply@othersite.com"), _gmb_row("owner@lakeview.com")],
    )
    out = clean_gmb_leads(source, tmp_path / "out.csv")
    assert list(out["Email"]) == ["owner@lakeview.com"]


@pytest.mark.parametrize("prefix", [
    "support", "help", "ticket", "admin", "sales", "contact",
    "marketing", "hr", "jobs", "careers", "team", "office",
    "noreply",
])
def test_departmental_emails_are_removed(tmp_path, prefix: str) -> None:
    """Shared-queue inboxes route cold email to a triage queue or discard it.
    Each departmental prefix is removed independently so a regression in one
    cannot hide behind another passing."""
    source = _raw_export(
        tmp_path,
        [_gmb_row(f"{prefix}@lakeview.com"), _gmb_row("owner@lakeview.com")],
    )
    out = clean_gmb_leads(source, tmp_path / "out.csv")
    assert list(out["Email"]) == ["owner@lakeview.com"]


def test_info_at_is_not_treated_as_departmental(tmp_path) -> None:
    """info@ is many small businesses' primary inbox — the owner reads it
    directly.  It was deliberately excluded from the departmental blocklist."""
    source = _raw_export(tmp_path, [_gmb_row("info@lakeview.com")])
    out = clean_gmb_leads(source, tmp_path / "out.csv")
    assert list(out["Email"]) == ["info@lakeview.com"]


def test_departmental_prefix_with_digits_is_still_removed(tmp_path) -> None:
    """sales2@ and support1@ are the same shared queue with a numbered alias."""
    source = _raw_export(
        tmp_path,
        [_gmb_row("sales2@lakeview.com"), _gmb_row("owner@lakeview.com")],
    )
    out = clean_gmb_leads(source, tmp_path / "out.csv")
    assert list(out["Email"]) == ["owner@lakeview.com"]


def test_real_names_starting_with_departmental_prefixes_survive(tmp_path) -> None:
    """salesperson@ and helpful@ are real personal addresses that happen to
    start with a blocked prefix — the digit-suffix guard must not catch them."""
    source = _raw_export(
        tmp_path,
        [_gmb_row("salesperson@lakeview.com"), _gmb_row("helpful@lakeview.com")],
    )
    out = clean_gmb_leads(source, tmp_path / "out.csv")
    assert set(out["Email"]) == {"salesperson@lakeview.com", "helpful@lakeview.com"}


def test_the_per_domain_cap_is_still_enforced(tmp_path) -> None:
    """Kept deliberately: five people at one firm receiving the same sequence
    reads as a blast, not as outreach."""
    source = _raw_export(
        tmp_path,
        [_gmb_row(f"person{i}@onefirm.com") for i in range(5)],
    )
    out = clean_gmb_leads(source, tmp_path / "out.csv")
    assert len(out) == 2


def test_a_plain_email_column_still_cleans(tmp_path) -> None:
    """Not every raw export uses the GMB scraper's Email_From_WEBSITE header.
    A list carrying a plain Email column used to KeyError and fail its whole
    Drive list — again on every run — instead of cleaning."""
    source = _raw_export(
        tmp_path,
        [{"Name": "Lakeview Custom Homes",
          "Email": "owner@lakeview.com;info@lakeview.com",
          "Website": "https://lakeview.com",
          "First_category": "Custom home builder",
          "City": "Austin"}],
    )
    out = clean_gmb_leads(source, tmp_path / "out.csv")
    assert list(out["Email"]) == ["owner@lakeview.com"]


def test_a_source_with_no_email_column_fails_with_guidance(tmp_path) -> None:
    """The failure must name what was expected and what the file has — a bare
    KeyError in a daily run's state entry is not actionable."""
    source = _raw_export(tmp_path, [{"Name": "Something", "Website": "https://x.com"}])
    with pytest.raises(SystemExit, match="No email column"):
        clean_gmb_leads(source, tmp_path / "out.csv")


def test_two_rows_sharing_an_email_each_get_their_own_sequence(
    tmp_path, monkeypatch
) -> None:
    """Copy used to be keyed by email: duplicates silently received the second
    lead's sequence and the first lead's copy was lost."""
    rows = [
        normalize_row(0, row("Custom home builder", "same@example-biz.com")),
        normalize_row(1, row("Dentist", "same@example-biz.com")),
    ]
    source = tmp_path / "source.csv"
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = tmp_path / "list-batch-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {"prefix": "list",
             "batches": [{"id": "001", "rows": [0, 1], "status": "pending"}]}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(pb, "research_lead", _stub_research)
    monkeypatch.setattr(pb, "LINKEDIN_ENRICH", False)

    result = pb.process_batch(
        "001", source, manifest_path,
        campaigns_dir=tmp_path / "campaigns", skip_build=True,
    )

    copy = json.loads(Path(result["copy"]).read_text(encoding="utf-8"))
    assert sorted(copy) == ["0", "1"]
    # The two leads map to different segments, so distinct variant selection
    # must have been possible per row.
    research = json.loads(Path(result["research"]).read_text(encoding="utf-8"))
    assert [r["aevora_segment"] for r in research] != []


def test_one_lead_research_crashing_does_not_lose_the_batch(
    tmp_path, monkeypatch
) -> None:
    """A renderer crash on lead 3 of 50 used to discard every completed fetch
    in the batch. Research failures degrade to honest weak-signal copy instead."""
    from lead_personalization.research import fallback_research_item

    calls = {"n": 0}

    def flaky_research(row_, li_scraped, renderer=None, render_fallback=True):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("renderer exploded")
        return _stub_research(row_, li_scraped, renderer, render_fallback)

    rows = [normalize_row(i, row("Custom home builder", f"lead{i}@example-biz.com"))
            for i in range(3)]
    source = tmp_path / "source.csv"
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = tmp_path / "list-batch-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {"prefix": "list",
             "batches": [{"id": "001", "rows": [0, 1, 2], "status": "pending"}]}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(pb, "research_lead", flaky_research)
    monkeypatch.setattr(pb, "LINKEDIN_ENRICH", False)

    result = pb.process_batch(
        "001", source, manifest_path,
        campaigns_dir=tmp_path / "campaigns", skip_build=True,
    )

    assert result["leads"] == 3
    research = json.loads(Path(result["research"]).read_text(encoding="utf-8"))
    assert len(research) == 3
    assert research[1]["signal_strength"] == "weak"
    assert "renderer exploded" in research[1]["research_notes"]
    # The fallback item is a full research_lead shape.
    expected = set(fallback_research_item(rows[1], "x"))
    assert expected <= set(research[1])
