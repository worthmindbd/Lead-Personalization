#!/usr/bin/env python3
"""Drive one batch: research every lead, generate its copy, export the batch.

Both halves of the work live in ``lead_personalization`` now — ``research`` for
the signals, ``copywriter`` plus a versioned offer pack for the words. What is
left here is the batch driver and the things that are genuinely about *this*
environment rather than about lead personalization: where the manifest lives,
which artifacts get written, and the CLI flags.

This file used to carry a full copy of both halves — ~370 lines of copy pools
and ~320 of research — kept honest by a parity test for the first and by nothing
at all for the second.

Every lead in the batch gets a sequence. There is no fit or quality gate here,
and the docstring used to claim one ("leads with fit_score == skip are excluded
from copy entirely") that no code ever implemented.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# ROOT as well as ROOT/scripts: lead_personalization is a top-level package, and
# without this it imports only when something else has already put the repo root
# on the path — true under `python -m pytest`, not true for a direct
# `python3 scripts/personalization/run_batches.py`.
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from lead_personalization import fsutil
from lead_personalization.config import Config
from lead_personalization.copywriter import fix_sequence, generate_sequence  # noqa: E402
from lead_personalization.naming import campaign_stem  # noqa: E402
from lead_personalization.offer_pack import OfferPackError, load_offer_pack  # noqa: E402
from lead_personalization.renderers import NodePlaywrightRenderer  # noqa: E402
from lead_personalization.research import fallback_research_item, research_lead  # noqa: E402
from personalization import artifacts, linkedin_apify  # noqa: E402
from personalization.build_enriched import build_batch  # noqa: E402
from personalization.manifest_lock import update_batch_status  # noqa: E402
from personalization.merge_enriched import merge_enriched  # noqa: E402

# Runtime knobs come from the library's Config (.env aware), so there is one
# definition of each path/flag/limit instead of a per-script copy. The module
# names stay: flags and tests flip them after import.
_CONFIG = Config.from_env(root=ROOT)

# Headless-render fallback for JS-built sites (Wix, Squarespace, React).
# Disable with --no-render if node/playwright is unavailable.
RENDER_FALLBACK = _CONFIG.render_fallback
RENDER_SCRIPT = _CONFIG.render_script
RENDER_TIMEOUT_S = _CONFIG.render_timeout_s

# LinkedIn recent-post enrichment via Apify. Disable with --no-linkedin.
LINKEDIN_ENRICH = _CONFIG.linkedin_enrich
LINKEDIN_MAX_POSTS = _CONFIG.linkedin_max_posts

# The words. Swapping packs re-skins the campaign without touching this file;
# override with --offer-pack, the way --no-render overrides RENDER_FALLBACK.
OFFER_PACK_NAME = "aevora"


# ---------------------------------------------------------------------------
# Batch driver
# ---------------------------------------------------------------------------


def merged_output_path(source: Path, prefix: str | None = None) -> Path:
    """Stable single merged file per run: leads/<prefix>-enriched.csv.

    With a prefix this is one file per list. Without one it falls back to the
    old source-stem derivation, which truncates at the first digit — so
    ``july-6-delta-normalized``, ``july-7-...`` and ``july-8-...`` all resolved
    to ``leads/july-enriched.csv``. Callers that know their prefix should pass
    it; the pipeline does.
    """
    if prefix:
        return artifacts.merged_csv(prefix)
    campaign = campaign_stem(source.stem)
    return ROOT / "leads" / f"{campaign}-enriched.csv"


def can_resume_from_disk(batch: dict, research_path: Path, copy_path: Path) -> bool:
    """True when a crashed ``copy_done`` batch left both JSONs on disk.

    ``copy_done`` means the expensive half — LinkedIn, website research, copy
    generation — finished and its artifacts were written; only the export is
    missing. Re-researching would re-fetch every website for copy that cannot
    change (the engine is deterministic), and ``--all-pending`` used to skip
    the batch entirely instead, stranding it in a dead state.
    """
    return (
        batch.get("status") == "copy_done"
        and research_path.is_file()
        and copy_path.is_file()
    )


def process_batch(
    batch_id: str,
    source: Path,
    manifest_path: Path,
    campaigns_dir: Path | None = None,
    skip_build: bool = False,
    auto_merge: bool = True,
) -> dict:
    campaigns_dir = campaigns_dir or ROOT / "campaigns"
    manifest = fsutil.load_json(manifest_path, {})
    batches = manifest.get("batches", [])
    batch = next((b for b in batches if b.get("id") == batch_id), None)
    if not batch:
        raise SystemExit(f"Batch {batch_id} not found in manifest")

    # Everything this run writes is named after the manifest's prefix, so two
    # lists processing at once never touch the same file.
    prefix = artifacts.clean_prefix(
        manifest.get("prefix") or artifacts.prefix_from_manifest_name(manifest_path)
    )

    with source.open(newline="", encoding="utf-8-sig") as handle:
        all_rows = list(csv.DictReader(handle))

    # Every lead in the list gets copy — no fit-based exclusion.
    batch_rows = []
    for i in batch.get("rows", []):
        if not isinstance(i, int) or not 0 <= i < len(all_rows):
            raise SystemExit(f"Batch {batch_id} references missing row {i}")
        batch_rows.append(all_rows[i])

    research_path = artifacts.research_json(prefix, batch_id, campaigns_dir)
    copy_path = artifacts.copy_json(prefix, batch_id, campaigns_dir)

    if can_resume_from_disk(batch, research_path, copy_path):
        print(
            f"Batch {batch_id}: resuming copy_done — rebuilding export from "
            f"existing {research_path.name} / {copy_path.name}"
        )
    else:
        # Pre-scrape LinkedIn posts for every lead that has a LinkedIn URL (one
        # batched Apify call, cached per handle so re-runs never re-pay).
        li_scraped: dict = {}
        if LINKEDIN_ENRICH:
            li_urls = [
                (r.get("Linkedin_URL") or "").strip()
                for r in batch_rows
                if (r.get("Linkedin_URL") or "").strip()
            ]
            if li_urls:
                try:
                    li_scraped = linkedin_apify.scrape_profiles(
                        li_urls, max_posts=LINKEDIN_MAX_POSTS
                    )
                    found = sum(1 for v in li_scraped.values() if v)
                    print(
                        f"Batch {batch_id}: LinkedIn URLs {len(li_urls)}, "
                        f"profiles with posts {found}"
                    )
                except SystemExit as exc:
                    print(f"Batch {batch_id}: LinkedIn enrichment skipped ({exc})")
                    li_scraped = {}

        research_out = []
        copy_out = {}
        offer_pack = load_offer_pack(OFFER_PACK_NAME)
        # Built here rather than at import: --no-render flips RENDER_FALLBACK after
        # this module is already loaded.
        renderer = NodePlaywrightRenderer(RENDER_SCRIPT, ROOT, RENDER_TIMEOUT_S)

        for row_index, row in zip(batch.get("rows", []), batch_rows):
            try:
                item = research_lead(
                    row, li_scraped, renderer=renderer, render_fallback=RENDER_FALLBACK
                )
            except Exception as exc:  # noqa: BLE001 — one lead must not lose the batch
                item = fallback_research_item(row, f"{type(exc).__name__}: {exc}")
                print(
                    f"Batch {batch_id}: research failed for row "
                    f"{row_index} ({exc}); using weak-signal copy",
                    file=sys.stderr,
                )
            # The manifest index is the authoritative row key: the CSV's
            # row_index column can be absent, and research_lead would default
            # every such lead to 0.
            item["row_index"] = row_index
            seq, variant = generate_sequence(row, item, offer_pack)
            seq = fix_sequence(seq, row, item, offer_pack)
            item["copy_variant"] = variant
            research_out.append(item)
            # Keyed by row_index, not email: two rows can share an address (or have
            # none), and keying by email silently gave every duplicate the wrong
            # lead's sequence.
            copy_out[str(row_index)] = [[s, b] for s, b in seq]

        campaigns_dir.mkdir(parents=True, exist_ok=True)
        fsutil.atomic_write_json(research_path, research_out)
        fsutil.atomic_write_json(copy_path, copy_out)

        update_batch_status(manifest_path, batch_id, "copy_done")

    result = {
        "batch_id": batch_id,
        "leads": len(batch_rows),
        "research": str(research_path),
        "copy": str(copy_path),
    }

    if not batch_rows:
        update_batch_status(manifest_path, batch_id, "exported")
        result["note"] = "batch has no rows; nothing exported"
        return result

    if not skip_build:
        build_result = build_batch(source, research_path, copy_path, batch_id, prefix=prefix)
        update_batch_status(manifest_path, batch_id, "exported")
        result.update(build_result)

        if auto_merge:
            merged_path = merged_output_path(source, prefix)
            merged_rows = merge_enriched(output_path=merged_path, manifest_path=manifest_path)
            result["merged"] = str(merged_path)
            result["merged_rows"] = merged_rows

    return result


def main() -> None:
    global RENDER_FALLBACK, LINKEDIN_ENRICH, OFFER_PACK_NAME
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--source", default="leads/all-leads-with-email-normalized.csv")
    parser.add_argument("--manifest", default=str(artifacts.manifest_path().relative_to(ROOT)))
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument(
        "--offer-pack",
        default=OFFER_PACK_NAME,
        help=f"Which offer pack supplies the copy (default: {OFFER_PACK_NAME})",
    )
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Disable the headless-browser fallback for JS-rendered sites",
    )
    parser.add_argument(
        "--no-linkedin",
        action="store_true",
        help="Disable Apify LinkedIn recent-post enrichment",
    )
    args = parser.parse_args()

    if args.no_render:
        RENDER_FALLBACK = False
    if args.no_linkedin:
        LINKEDIN_ENRICH = False
    OFFER_PACK_NAME = args.offer_pack
    # Load it now rather than after the research loop: a bad pack name should
    # cost nothing, not a batch's worth of fetches and Apify credits.
    try:
        load_offer_pack(OFFER_PACK_NAME)
    except OfferPackError as exc:
        parser.error(str(exc))

    source = Path(args.source)
    manifest = Path(args.manifest)
    if not source.is_absolute():
        source = ROOT / source
    if not manifest.is_absolute():
        manifest = ROOT / manifest

    result = process_batch(args.batch_id, source, manifest, skip_build=args.skip_build)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
