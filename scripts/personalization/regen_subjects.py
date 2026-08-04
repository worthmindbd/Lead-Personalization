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
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from lead_personalization.copywriter import fix_sequence, generate_sequence  # noqa: E402
from lead_personalization.offer_pack import load_offer_pack  # noqa: E402
from personalization import build_enriched  # noqa: E402

STATE = ROOT / ".pipeline" / "state.json"


def _resolve_list(query: str) -> tuple[str, str, Path]:
    """Return (title, slug, workdir) for a list matched by title or slug.

    state.json's ``lists`` is keyed by the human title ("July 8,2026"); the
    entry carries ``slug`` ("july-8-2026") and the workdir is derived from it.
    """
    state = json.loads(STATE.read_text(encoding="utf-8"))
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


def _merge_into_cumulative(batch_rows: list[dict[str]], fieldnames: list[str],
                           cumulative: Path) -> tuple[int, int]:
    """Fold the rebuilt batch rows into the cumulative enriched CSV, keyed by email.

    A faithful subset of ``merge_into_cumulative``: existing rows for these
    emails are replaced (the subjects changed); rows for emails not in this run
    are kept untouched.
    """
    rebuilt_by_email = {}
    for r in batch_rows:
        em = (r.get("primary_email") or r.get("Email") or "").split("|")[0].strip().lower()
        if em:
            rebuilt_by_email[em] = r

    existing = []
    keep = []
    if cumulative.is_file():
        with cumulative.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            out_fields = list(reader.fieldnames or fieldnames)
            for row in reader:
                em = (row.get("primary_email") or row.get("Email") or "").split("|")[0].strip().lower()
                if em in rebuilt_by_email:
                    existing.append(em)
                else:
                    keep.append(row)
    else:
        out_fields = list(fieldnames)

    out_rows = keep + [rebuilt_by_email[e] for e in rebuilt_by_email]
    with cumulative.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=out_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out_rows)
    return len(rebuilt_by_email), len(out_rows)


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

    # Rebuilt enriched rows accumulated across every batch of every stamp.
    all_rebuilt: list[dict[str]] = []
    out_fieldnames: list[str] = []

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

            research_items = json.loads(rp.read_text(encoding="utf-8"))
            with source.open(newline="", encoding="utf-8") as fh:
                all_rows = list(csv.DictReader(fh))

            copy_out: dict[str, list[list[str]]] = {}
            for item in research_items:
                em = item["email"]
                src = next((r for r in all_rows
                            if (r.get("primary_email") or r.get("Email") or "").split("|")[0].strip().lower() == em.lower()),
                           None)
                if src is None:
                    raise SystemExit(f"missing normalized row for {em}")
                seq, _variant = generate_sequence(src, item, pack)
                seq = fix_sequence(seq, src, item, pack)
                copy_out[em] = [[s, b] for s, b in seq]

            copy_path.write_text(json.dumps(copy_out, indent=2), encoding="utf-8")

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
            built = Path(res["csv"])
            with built.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                if not out_fieldnames:
                    out_fieldnames = list(reader.fieldnames or [])
                all_rebuilt.extend(reader)

            print(f"  batch {batch_id}: {len(research_items)} leads -> {built.name}")

    if not all_rebuilt:
        raise SystemExit("nothing rebuilt — no batch artifacts matched")

    cumulative = workdir / f"{workdir.name}-enriched.csv"
    added, total = _merge_into_cumulative(all_rebuilt, out_fieldnames, cumulative)
    print(f"merged: replaced {added} rebuilt lead(s) -> {total} total in {cumulative.name}")


if __name__ == "__main__":
    main()
