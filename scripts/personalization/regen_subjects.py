#!/usr/bin/env python3
"""Re-derive email subjects for an already-personalized list, in place.

Subjects are a deterministic function of (lead row, research, offer pack) —
computed once in ``copywriter.generate_sequence`` / ``fix_sequence`` and then
copied verbatim through ``copy.json`` -> ``build_enriched`` -> merge. A fix to
``subjects.py`` therefore does NOT reach an already-merged enriched CSV by
re-running ``build_enriched`` alone: the stale subjects are baked into the
saved ``copy.json``.

This script closes that gap without spending Reoon credits or re-running LLM
copy generation (the copywriter is deterministic and network-free). For each
batch artifact set under a list's archived ``artifacts/<stamp>/``:

  1. load the cached ``*-research.json`` and the normalized delta CSV,
  2. re-run ``generate_sequence`` + ``fix_sequence`` to get fresh subjects
     (bodies come out byte-identical — only the subject can change),
  3. overwrite ``*-copy.json`` with the new [subject, body] pairs,
  4. rebuild the per-batch ``*-enriched.csv`` via ``build_batch``,
  5. fold the rebuilt batch CSVs into the list's cumulative enriched CSV.

Nothing upstream of subjects changes: no research re-fetch, no verify, no
LinkedIn, no render. Inputs are all on disk in the artifact dir.

Usage:
    regen_subjects.py --list "July 8,2026" [--stamp 20260803-125721]

If ``--stamp`` is omitted, the most recent artifact stamp for the list is used.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "pipeline"))
sys.path.insert(0, str(ROOT))

from lead_personalization import fsutil
from lead_personalization.copywriter import fix_sequence, generate_sequence  # noqa: E402
from lead_personalization.offer_pack import load_offer_pack  # noqa: E402
from personalization import build_enriched  # noqa: E402
from run_pipeline import merge_into_cumulative  # noqa: E402

STATE = ROOT / ".pipeline" / "state.json"


def index_source_rows(all_rows: list[dict]) -> tuple[dict[str, dict], dict[str, dict]]:
    """Row lookups for a normalized CSV, keyed the way ``build_enriched`` keys them.

    ``row_index`` is authoritative; the email index is only the fallback for
    artifacts written before row-keyed research JSON. Matching by email alone
    (what this script used to do) gives every row sharing an address the FIRST
    matching row's city/category/name — and two rows sharing an address is a
    scenario the main path explicitly supports and tests.
    """
    by_row_index: dict[str, dict] = {}
    by_email: dict[str, dict] = {}
    for pos, row in enumerate(all_rows):
        by_row_index[str(pos)] = row
        ri = str(row.get("row_index") or "").strip()
        if ri:
            by_row_index[ri] = row
        email = (row.get("primary_email") or row.get("Email") or "").split("|")[0].strip().lower()
        if email:
            by_email[email] = row
    return by_row_index, by_email


def source_row_for(
    item: dict, by_row_index: dict[str, dict], by_email: dict[str, dict]
) -> dict | None:
    """The normalized row a research item was generated from (None if absent)."""
    return by_row_index.get(str(item.get("row_index", ""))) or by_email.get(
        (item.get("email") or "").lower()
    )


def _resolve_list(query: str) -> tuple[str, str, Path]:
    """Return (title, slug, workdir) for a list matched by title or slug.

    state.json's ``lists`` is keyed by the human title ("July 8,2026"); the
    entry carries ``slug`` ("july-8-2026") and the workdir is derived from it.
    """
    state = fsutil.load_json(STATE, {})
    lists = state.get("lists", {})
    for title, entry in lists.items():
        slug = entry.get("slug", "")
        if query in (title, slug):
            wd_rel = entry.get("workdir") or f"leads/pipeline/{slug}"
            wd = ROOT / wd_rel
            if not wd.is_dir():
                raise SystemExit(f"workdir not found: {wd}")
            return title, slug, wd
    raise SystemExit(f"no pipeline list matches title/slug {query!r}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", required=True, help="Pipeline list title or slug")
    ap.add_argument("--stamp", action="append", default=None,
                    help="Artifact stamp to regenerate (repeatable; default: all stamps)")
    ap.add_argument("--offer-pack", default="aevora", help="Offer pack name (default: aevora)")
    args = ap.parse_args()

    title, slug, workdir = _resolve_list(args.list)
    artifacts_root = workdir / "artifacts"
    stamps = args.stamp or sorted(p.name for p in artifacts_root.iterdir() if p.is_dir())
    if not stamps:
        raise SystemExit(f"no artifact stamps under {artifacts_root}")
    run_dirs = []
    for stamp in stamps:
        run_dir = artifacts_root / stamp
        if not run_dir.is_dir():
            raise SystemExit(f"artifact stamp not found: {run_dir}")
        run_dirs.append(run_dir)

    pack = load_offer_pack(args.offer_pack)
    print(f"regen: list={title} slug={slug} stamps={[d.name for d in run_dirs]} pack={args.offer_pack}")

    # Rebuilt enriched CSVs accumulated across every batch of every stamp.
    rebuilt_files: list[Path] = []

    for run_dir in run_dirs:
        research_files = sorted(run_dir.glob("*-batch-*-research.json"))
        if not research_files:
            print(f"  (skip {run_dir.name}: no batch research JSONs)")
            continue
        normalized = next(run_dir.glob("*-normalized.csv"), None)
        if normalized is None:
            raise SystemExit(f"no normalized CSV in {run_dir}")
        print(f"== {run_dir.name}: {len(research_files)} batches, source={normalized.name}")

        for rp in research_files:
            # batch id like "001" -> derived from the filename suffix.
            batch_id = rp.stem.split("-batch-")[1].split("-")[0]
            copy_path = run_dir / rp.name.replace("-research.json", "-copy.json")
            source = normalized

            research_items = fsutil.load_json(rp, [])
            with source.open(newline="", encoding="utf-8-sig") as fh:
                all_rows = list(csv.DictReader(fh))
            by_row_index, by_email = index_source_rows(all_rows)

            copy_out: dict[str, list[list[str]]] = {}
            for item in research_items:
                if not isinstance(item, dict):
                    continue
                em = item.get("email") or ""
                src = source_row_for(item, by_row_index, by_email)
                if src is None:
                    raise SystemExit(f"missing normalized row for {em}")
                seq, _variant = generate_sequence(src, item, pack)
                seq = fix_sequence(seq, src, item, pack)
                copy_out[str(item.get("row_index", em))] = [[s, b] for s, b in seq]

            fsutil.atomic_write_json(copy_path, copy_out)

            # Rebuild this batch's enriched CSV from the refreshed copy. Write to a
            # throwaway dir so we don't disturb leads/enriched/ for other lists.
            tmp_enriched = run_dir / "_regen_enriched"
            tmp_enriched.mkdir(exist_ok=True)
            res = build_enriched.build_batch(
                source=source,
                research_path=rp,
                copy_path=copy_path,
                batch_id=batch_id,
                enriched_dir=tmp_enriched,
                copy_dir=run_dir,
                prefix=slug,
            )
            rebuilt_files.append(Path(res["csv"]))

            print(f"  batch {batch_id}: {len(research_items)} leads -> {Path(res['csv']).name}")

    if not rebuilt_files:
        raise SystemExit("nothing rebuilt — no batch artifacts matched")

    cumulative = workdir / f"{workdir.name}-enriched.csv"
    added, total = merge_into_cumulative(
        rebuilt_files, cumulative, replace_existing=True
    )
    print(f"merged: replaced/regenerated {added} lead(s) -> {total} total in {cumulative.name}")


if __name__ == "__main__":
    main()
