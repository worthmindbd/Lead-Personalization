#!/usr/bin/env python3
"""Every filename a personalization run produces, in one place.

These names used to be spelled out wherever they were needed — seven files
repeating ``mix-leads-batch-{id}-...`` — and they were the same names for every
Drive list. Two consequences: ``merge_enriched`` globbed
``mix-leads-batch-*-enriched.csv`` and would happily fold another list's batches
into this one's output, and only one list could personalize at a time.

Now a run carries a *prefix* (the pipeline passes the list slug), recorded in
its manifest and threaded through every name below. ``july-6`` and ``july-7``
write disjoint files and glob disjoint sets.

The prefix names the *list*, not the run. A second delta on the same list
renumbers from batch 001 and will overwrite the first delta's artifacts —
archiving them into the list's workdir is what preserves that history, and is
why the pipeline still does it.
"""

from __future__ import annotations

import json
from pathlib import Path

from lead_personalization.naming import slugify

ROOT = Path(__file__).resolve().parents[2]

CAMPAIGNS_DIR = ROOT / "campaigns"
COPY_DIR = ROOT / "copy"
ENRICHED_DIR = ROOT / "leads" / "enriched"
LEADS_DIR = ROOT / "leads"

# What a run is called when nobody says otherwise: the historical name, so a
# hand-run `python3 scripts/personalization/run_batches.py` still finds the
# files it always did.
DEFAULT_PREFIX = "mix-leads"

MANIFEST_SUFFIX = "-batch-manifest.json"


def clean_prefix(raw: str) -> str:
    """A prefix safe to put in a filename and to glob with.

    List titles reach here as slugs, but a slug is only as clean as the Drive
    folder it came from. Anything that would make the name ambiguous — a path
    separator, a glob character — is collapsed to a dash. The slug regex lives
    in the library (lead_personalization.naming) so every stage derives the
    same names; only the run-specific fallback lives here.
    """
    return slugify(raw, fallback=DEFAULT_PREFIX)


def manifest_path(prefix: str = DEFAULT_PREFIX) -> Path:
    return CAMPAIGNS_DIR / f"{clean_prefix(prefix)}{MANIFEST_SUFFIX}"


def prefix_from_manifest_name(path: Path) -> str:
    """Recover the prefix from a manifest filename.

    The fallback for a manifest written before prefixes existed, whose JSON has
    no ``prefix`` key.
    """
    name = path.name
    if name.endswith(MANIFEST_SUFFIX):
        return clean_prefix(name[: -len(MANIFEST_SUFFIX)])
    return DEFAULT_PREFIX


def prefix_for(path: Path) -> str:
    """The prefix a manifest's artifacts use.

    Prefers what the manifest recorded; falls back to its filename. Reading a
    manifest that is missing or unparseable is not this function's problem —
    the caller will fail on it in a moment for a better reason — so it just
    falls back rather than raising here.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        recorded = data.get("prefix")
        if isinstance(recorded, str) and recorded.strip():
            return clean_prefix(recorded)
    except (OSError, ValueError):
        pass
    return prefix_from_manifest_name(path)


# --- per-batch artifacts -----------------------------------------------------


def research_json(prefix: str, batch_id: str, campaigns_dir: Path | None = None) -> Path:
    return (campaigns_dir or CAMPAIGNS_DIR) / f"{clean_prefix(prefix)}-batch-{batch_id}-research.json"


def copy_json(prefix: str, batch_id: str, campaigns_dir: Path | None = None) -> Path:
    return (campaigns_dir or CAMPAIGNS_DIR) / f"{clean_prefix(prefix)}-batch-{batch_id}-copy.json"


def enriched_csv(prefix: str, batch_id: str, enriched_dir: Path | None = None) -> Path:
    return (enriched_dir or ENRICHED_DIR) / f"{clean_prefix(prefix)}-batch-{batch_id}-enriched.csv"


def emails_json(prefix: str, batch_id: str, copy_dir: Path | None = None) -> Path:
    return (copy_dir or COPY_DIR) / f"{clean_prefix(prefix)}-emails-batch-{batch_id}.json"


def review_md(prefix: str, batch_id: str, copy_dir: Path | None = None) -> Path:
    return (copy_dir or COPY_DIR) / f"{clean_prefix(prefix)}-review-batch-{batch_id}.md"


# --- per-run artifacts -------------------------------------------------------


def master_review_md(prefix: str, copy_dir: Path | None = None) -> Path:
    return (copy_dir or COPY_DIR) / f"{clean_prefix(prefix)}-master-review.md"


def normalized_json(prefix: str, campaigns_dir: Path | None = None) -> Path:
    return (campaigns_dir or CAMPAIGNS_DIR) / f"{clean_prefix(prefix)}-normalized.json"


def merged_csv(prefix: str, leads_dir: Path | None = None) -> Path:
    """Where a run's batches are merged to.

    Was derived from the source CSV's stem, truncated at the first digit — so
    ``july-6-delta-normalized``, ``july-7-...`` and ``july-8-...`` all resolved
    to ``leads/july-enriched.csv``. Three lists, one file.
    """
    return (leads_dir or LEADS_DIR) / f"{clean_prefix(prefix)}-enriched.csv"


def enriched_glob(prefix: str) -> str:
    """The pattern ``merge_enriched`` folds into one file.

    Prefix-scoped, so another list's leftovers in ``leads/enriched/`` cannot be
    swept into this run's merge.
    """
    return f"{clean_prefix(prefix)}-batch-*-enriched.csv"
