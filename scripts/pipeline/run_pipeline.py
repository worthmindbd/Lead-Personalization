#!/usr/bin/env python3
"""Drive lead pipeline orchestrator.

One command drives every lead list through:

    Raw Leads (Drive) -> download -> clean -> upload Cleaned Leads/<title>/
      -> verify (Reoon, up to 500/day) -> upload Verified Leads/<title>/
      -> personalize DELTA only (new verified emails) -> merge cumulative
      -> upload Personalized leads/<title>/

State lives in .pipeline/state.json; every run is resumable and idempotent.
Working files live in leads/pipeline/<slug>/ (slug = sanitized Drive title,
e.g. "July 25,2026" -> "july-25-2026") because the existing scripts derive
campaign names that would collide across lists (e.g. every "July ..." list
collapses to campaign "july").

Local testing without Drive:

    .venv/bin/python scripts/pipeline/run_pipeline.py \
        --local-only --raw tests/fixtures/gmb_raw_sample.csv \
        --title "July 25,2026" --no-verify --no-render --no-linkedin
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from personalization import artifacts  # noqa: E402
from personalization.clean_gmb_leads import (  # noqa: E402
    campaign_stem as clean_campaign_stem,
    clean_gmb_leads,
    count_named_path,
)
from personalization.create_batch_manifest import create_manifest  # noqa: E402
from personalization.normalize_leads import (  # noqa: E402
    normalize_leads,
    normalized_output_path,
)
from verify_emails_reoon import (  # noqa: E402
    CACHE_FILE as REOON_CACHE_FILE,
    EMAIL_COLUMNS,
    REJECTED_FILE as REOON_REJECTED_FILE,
    extract_emails_from_csv,
    load_dotenv,
)

PY = str(ROOT / ".venv" / "bin" / "python")
STATE_FILE = ROOT / ".pipeline" / "state.json"
CONTACTED_FILE = ROOT / ".pipeline" / "contacted.json"
WORK_ROOT = ROOT / "leads" / "pipeline"
ENRICHED_DIR = ROOT / "leads" / "enriched"
COPY_DIR = ROOT / "copy"

DRIVE_RAW = "Raw Leads"
DRIVE_CLEANED = "Cleaned Leads"
DRIVE_VERIFIED = "Verified Leads"
DRIVE_PERSONALIZED = "Personalized leads"
# The report sheet's name lives in report.py (DRIVE_SHEET_NAME) — the single
# owner of everything to do with publishing the report.


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "list"


def banner(text: str) -> None:
    line = "=" * max(64, len(text) + 8)
    print(f"\n{line}\n    {text}\n{line}")


def stage_line(stage: str, detail: str) -> None:
    print(f"\n-- {stage.upper()}: {detail}")


def load_json(path: Path, default):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json_atomic(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def row_email(row: dict) -> str:
    for col in EMAIL_COLUMNS:
        raw = (row.get(col) or "").strip()
        if raw:
            email = raw.replace(";", "|").split("|")[0].strip().lower()
            if "@" in email:
                return email
    return ""


def csv_row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    # Parse properly: enriched rows contain quoted multi-line email bodies,
    # so counting raw lines would overcount.
    with path.open(newline="", encoding="utf-8-sig") as f:
        return max(0, sum(1 for _ in csv.reader(f)) - 1)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def load_state() -> dict:
    state = load_json(STATE_FILE, {"version": 1, "lists": {}})
    state.setdefault("lists", {})
    return state


def save_state(state: dict) -> None:
    save_json_atomic(STATE_FILE, state)


def new_entry(title: str, mtime: str = "") -> dict:
    return {
        "slug": slugify(title),
        "discovered_at": now_iso(),
        "drive_mtime": mtime,
        "stage": "discovered",
        "raw_csv": None,
        "cleaned_csv": None,
        "verified_csv": None,
        "enriched_csv": None,
        "uploads": {"cleaned": False, "verified_rows": -1, "enriched_rows": -1},
        "verify_complete": False,
        "pending_verification": None,
        "pending_delta": None,
        "personalized_emails": 0,
        "active_delta": None,
        "last_error": None,
        "last_run": None,
    }


def workdir_for(entry: dict) -> Path:
    return WORK_ROOT / entry["slug"]


# ---------------------------------------------------------------------------
# rclone helpers (all Drive I/O goes through here)
# ---------------------------------------------------------------------------


def rclone(
    args: list[str], capture: bool = False, check: bool = True
) -> subprocess.CompletedProcess:
    cmd = ["rclone", *args]
    print(f"   $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=capture, text=True)


def drive_list_raw(remote: str) -> list[dict]:
    """List Raw Leads as processable lists.

    Accepts files by name extension OR MimeType: native CSV/XLSX uploaded to
    Drive frequently carry no extension in their Name (e.g. "July 25,2026" with
    MimeType text/csv), and Google Sheets are exported to CSV via
    --drive-export-formats. Classifying by MimeType keeps the raw file's true
    type so the downstream cleaner picks the right reader.
    """
    proc = rclone(
        ["lsjson", f"{remote}:{DRIVE_RAW}", "--drive-export-formats", "csv"],
        capture=True,
    )
    items = json.loads(proc.stdout or "[]")
    lists = []
    for item in items:
        name = item.get("Name", "")
        if item.get("IsDir"):
            continue
        low = name.lower()
        mime = (item.get("MimeType") or "").lower()
        if low.endswith(".csv"):
            ext, title = ".csv", name.rsplit(".", 1)[0]
        elif low.endswith(".xlsx"):
            ext, title = ".xlsx", name.rsplit(".", 1)[0]
        elif "csv" in mime or mime == "application/vnd.google-apps.spreadsheet":
            # Native CSV without extension, or a Google Sheet exported as CSV.
            ext, title = ".csv", name
        elif "spreadsheetml" in mime or "ms-excel" in mime:
            ext, title = ".xlsx", name
        else:
            continue
        lists.append(
            {"title": title, "leaf": name, "ext": ext, "mtime": item.get("ModTime", "")}
        )
    return lists


def drive_download(remote: str, leaf: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    rclone(
        ["copyto", f"{remote}:{DRIVE_RAW}/{leaf}", str(dest),
         "--drive-export-formats", "csv"]
    )


def drive_upload(remote: str, local: Path, folder: str, title: str) -> None:
    rclone(["copyto", str(local), f"{remote}:{folder}/{title}/{local.name}"])


def drive_folder_csvs(remote: str, folder: str, title: str) -> list[dict]:
    """CSV files inside remote:folder/title (empty list if the folder is absent)."""
    proc = rclone(
        ["lsjson", f"{remote}:{folder}/{title}"], capture=True, check=False
    )
    if proc.returncode != 0:
        return []
    try:
        items = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return []
    return [
        it
        for it in items
        if not it.get("IsDir") and str(it.get("Name", "")).lower().endswith(".csv")
    ]


def drive_download_file(remote: str, folder: str, title: str, name: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    rclone(["copyto", f"{remote}:{folder}/{title}/{name}", str(dest)])


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------


def stage_download(title: str, entry: dict, args) -> None:
    workdir = workdir_for(entry)
    raw = workdir / "raw.csv"
    if entry.get("raw_csv") and (ROOT / entry["raw_csv"]).is_file():
        stage_line("download", f"already downloaded -> {entry['raw_csv']} (skip)")
        return
    workdir.mkdir(parents=True, exist_ok=True)
    if args.local_only:
        if not entry.get("local_raw_source"):
            raise RuntimeError(
                "local-only mode: list has no local raw source registered "
                "(use --raw/--title)"
            )
        src = ROOT / entry["local_raw_source"]
        raw = workdir / ("raw" + src.suffix.lower())
        shutil.copyfile(src, raw)
        stage_line("download", f"[local-only] copied {src} -> {raw}")
    else:
        leaf = entry.get("drive_leaf") or f"{title}.csv"
        ext = entry.get("drive_ext") or (Path(leaf).suffix.lower() or ".csv")
        raw = workdir / ("raw" + ext)
        drive_download(args.remote, leaf, raw)
        stage_line("download", f"downloaded '{DRIVE_RAW}/{leaf}' -> {raw}")
    entry["raw_csv"] = str(raw.relative_to(ROOT))
    entry["stage"] = "downloaded"


def stage_clean(title: str, entry: dict) -> None:
    workdir = workdir_for(entry)
    cleaned = workdir / f"{entry['slug']}-cleaned.csv"
    if entry.get("cleaned_csv") and (ROOT / entry["cleaned_csv"]).is_file():
        stage_line(
            "clean",
            f"already cleaned -> {entry['cleaned_csv']} "
            f"({csv_row_count(ROOT / entry['cleaned_csv'])} rows, skip)",
        )
        return
    raw = ROOT / entry["raw_csv"]
    stage_line("clean", f"cleaning {raw.name} via clean_gmb_leads")
    # clean_gmb_leads renames its output to <stem>-<count>-with-email.csv, so
    # compute the produced path and move it to the stable per-list name.
    out_stub = workdir / f"{entry['slug']}.csv"
    df = clean_gmb_leads(raw, out_stub)
    produced = count_named_path(
        clean_campaign_stem(out_stub.stem), len(df), "with-email", workdir
    )
    shutil.move(str(produced), str(cleaned))
    entry["cleaned_csv"] = str(cleaned.relative_to(ROOT))
    entry["stage"] = "cleaned"
    stage_line("clean", f"{len(df)} rows with email -> {cleaned}")


def stage_upload_cleaned(title: str, entry: dict, args) -> None:
    if args.local_only:
        stage_line("upload cleaned", "[local-only] skipped")
        return
    if entry["uploads"].get("cleaned"):
        stage_line("upload cleaned", "already uploaded (skip)")
        return
    drive_upload(args.remote, ROOT / entry["cleaned_csv"], DRIVE_CLEANED, title)
    entry["uploads"]["cleaned"] = True
    stage_line("upload cleaned", f"-> '{DRIVE_CLEANED}/{title}/'")


def reoon_key_available() -> bool:
    key = os.environ.get("REOON_API_KEY", "").strip()
    return bool(key) and key != "your_api_key_here"


def load_rejected() -> dict[str, dict]:
    """Addresses known checked but with no cached result — see backfill_rejected."""
    data = load_json(REOON_REJECTED_FILE, {})
    addresses = data.get("addresses") if isinstance(data, dict) else None
    return addresses if isinstance(addresses, dict) else {}


def save_rejected(addresses: dict[str, dict]) -> None:
    save_json_atomic(REOON_REJECTED_FILE, {"updated": now_iso(), "addresses": addresses})


def pending_verification(cleaned_csv: Path) -> int:
    cache = load_json(REOON_CACHE_FILE, {})
    rejected = load_rejected()
    emails = extract_emails_from_csv(cleaned_csv)
    return sum(1 for e in emails if e not in cache and e not in rejected)


def backfill_rejected(state: dict, apply: bool = False) -> list[tuple[str, int]]:
    """Recover what a lost cache knew about rejected addresses.

    Only for lists whose verification genuinely finished: every cleaned address
    was checked, so one that is in neither the cache nor the verified CSV must
    have been checked and rejected. Those are the only ones this can infer, and
    the inference is recorded with the list it came from so it stays auditable.

    Deliberately never automatic — a list wrongly marked complete would hide
    real unverified leads for good. Returns (slug, count) per list.
    """
    addresses = load_rejected()
    cache = load_json(REOON_CACHE_FILE, {})
    found: list[tuple[str, int]] = []
    stamp = now_iso()
    for entry in state.get("lists", {}).values():
        if not entry.get("verify_complete") or not entry.get("cleaned_csv"):
            continue
        slug = entry.get("slug", "")
        try:
            cleaned = extract_emails_from_csv(ROOT / entry["cleaned_csv"])
        except (SystemExit, OSError):
            continue
        kept = set()
        rel = entry.get("verified_csv")
        if rel and (ROOT / rel).is_file():
            kept = set(extract_emails_from_csv(ROOT / rel))
        new = [e for e in cleaned if e not in cache and e not in kept and e not in addresses]
        if not new:
            continue
        found.append((slug, len(new)))
        for email in new:
            addresses[email] = {
                "status": "inferred_rejected",
                "source": "inferred_from_completed_list",
                "list": slug,
                "inferred_at": stamp,
            }
    if apply and found:
        save_rejected(addresses)
    return found


def seed_cache_from_verified(verified_csv: Path) -> int:
    """Record emails from an existing verified list as already-checked.

    The Reoon cache is the record of which addresses have been spent credits
    on. If it is lost (wiped state dir, fresh clone) while the verified CSVs
    survive on Drive, every passed email would be re-verified at full cost.
    Every address in a verified list cleared a KEEP status, so reseeding it as
    ``safe`` restores that knowledge.

    Only fills gaps — a real Reoon result already in the cache always wins.
    Addresses that were checked and *rejected* are unrecoverable this way and
    will be re-checked; that costs credits but never yields a wrong answer.

    Returns the number of entries added.
    """
    if not verified_csv.is_file():
        return 0
    try:
        emails = extract_emails_from_csv(verified_csv)
    except SystemExit:  # no recognisable email column — nothing to reseed
        return 0
    cache = load_json(REOON_CACHE_FILE, {})
    added = 0
    for email in emails:
        if email not in cache:
            cache[email] = {"status": "safe", "source": "reseeded_from_verified_csv"}
            added += 1
    if added:
        save_json_atomic(REOON_CACHE_FILE, cache)  # creates .reoon/ if needed
    return added


def stage_verify(title: str, entry: dict, args) -> None:
    cleaned = ROOT / entry["cleaned_csv"]
    workdir = workdir_for(entry)
    verified = workdir / f"{entry['slug']}-verified.csv"
    entry["verified_csv"] = str(verified.relative_to(ROOT))

    pending = pending_verification(cleaned)
    entry["pending_verification"] = pending

    if args.no_verify:
        stage_line("verify", f"skipped (--no-verify). Pending: {pending} emails")
    elif not reoon_key_available():
        stage_line(
            "verify",
            f"deferred: REOON_API_KEY not configured. Pending: {pending} emails",
        )
    elif pending == 0 and verified.is_file():
        stage_line("verify", "all emails already verified (cache hit, skip)")
    else:
        stage_line("verify", f"{pending} pending — running Reoon (cap {args.verify_limit}/day)")
        cmd = [
            PY, str(ROOT / "scripts" / "verify_emails_reoon.py"),
            str(cleaned), "-o", str(verified), "--limit", str(args.verify_limit),
        ]
        proc = subprocess.run(cmd, cwd=ROOT)
        if proc.returncode != 0:
            print(f"   WARNING: verify exited {proc.returncode}; continuing with existing verified list")

    pending = pending_verification(cleaned)
    entry["pending_verification"] = pending
    entry["verify_complete"] = pending == 0
    rows = csv_row_count(verified)
    entry["stage"] = "verifying"
    stage_line(
        "verify",
        f"verified list: {rows} rows kept | still unchecked: {pending}"
        + ("" if pending == 0 else " — resume next run/day"),
    )


def stage_upload_verified(title: str, entry: dict, args) -> None:
    verified = ROOT / entry["verified_csv"]
    if not verified.is_file():
        stage_line("upload verified", "no verified list yet (skip)")
        return
    if args.local_only:
        stage_line("upload verified", "[local-only] skipped")
        return
    rows = csv_row_count(verified)
    if rows == entry["uploads"].get("verified_rows"):
        stage_line("upload verified", f"unchanged ({rows} rows, skip)")
        return
    drive_upload(args.remote, verified, DRIVE_VERIFIED, title)
    entry["uploads"]["verified_rows"] = rows
    stage_line("upload verified", f"{rows} rows -> '{DRIVE_VERIFIED}/{title}/'")


# --- personalization delta ---------------------------------------------------


def enriched_emails(enriched_csv: Path) -> set[str]:
    if not enriched_csv.is_file():
        return set()
    _, rows = load_rows(enriched_csv)
    return {e for e in (row_email(r) for r in rows) if e}


# --- contacted index (cross-list suppression) --------------------------------
#
# Drive lists overlap: the same business turns up in more than one export, so
# deduping a delta against only its own list's enriched CSV lets the same
# person receive two sequences. The index records address -> the slug of the
# list that personalized it first, and every later list skips it.


def load_contacted() -> dict[str, str]:
    """address -> slug of the list that personalized it first."""
    data = load_json(CONTACTED_FILE, {})
    addresses = data.get("addresses") if isinstance(data, dict) else None
    return addresses if isinstance(addresses, dict) else {}


def save_contacted(addresses: dict[str, str]) -> None:
    save_json_atomic(CONTACTED_FILE, {"updated": now_iso(), "addresses": addresses})


def record_contacted(slug: str, emails) -> int:
    """Claim ``emails`` for ``slug``. First writer wins — never reattributes."""
    addresses = load_contacted()
    added = 0
    for email in emails:
        if email and email not in addresses:
            addresses[email] = slug
            added += 1
    if added:
        save_contacted(addresses)
    return added


def backfill_contacted(state: dict) -> tuple[int, int]:
    """Seed the index from every per-list enriched CSV already on disk.

    Attribution goes to the oldest list first, so the newer list is the one
    that yields and re-running the backfill is stable. Returns
    (unique addresses, addresses seen on more than one list).
    """
    entries = sorted(
        state.get("lists", {}).values(),
        key=lambda e: (e.get("drive_mtime") or e.get("discovered_at") or "", e.get("slug", "")),
    )
    addresses = load_contacted()
    duplicates = 0
    for entry in entries:
        rel = entry.get("enriched_csv")
        if not rel:
            continue
        slug = entry.get("slug", "")
        for email in sorted(enriched_emails(ROOT / rel)):
            owner = addresses.get(email)
            if owner is None:
                addresses[email] = slug
            elif owner != slug:
                duplicates += 1
    save_contacted(addresses)
    return len(addresses), duplicates


def compute_delta(
    verified_csv: Path,
    enriched_csv: Path,
    *,
    contacted: dict[str, str] | None = None,
    slug: str = "",
) -> tuple[list[str], list[dict], int]:
    """Rows to personalize, plus how many were suppressed as already contacted.

    An address attributed to *this* list is not suppressed — it is already in
    the list's own enriched CSV, and if that file were lost we would want to
    rebuild it rather than skip the lead forever.
    """
    fieldnames, rows = load_rows(verified_csv)
    done = enriched_emails(enriched_csv)
    contacted = contacted or {}
    seen: set[str] = set()
    delta = []
    suppressed = 0
    for row in rows:
        email = row_email(row)
        if not email or email in done or email in seen:
            continue
        seen.add(email)
        owner = contacted.get(email)
        if owner and owner != slug:
            suppressed += 1
            continue
        delta.append(row)
    return fieldnames, delta, suppressed


def manifest_for(entry: dict) -> Path:
    """This list's manifest: campaigns/<slug>-batch-manifest.json.

    One manifest per list, and every artifact name derives from it, so two
    lists can personalize without touching each other's files. It used to be a
    single fixed path, which is why only one list could run at a time and why
    stray batch files had to be swept out of leads/enriched/ beforehand.
    """
    return artifacts.manifest_path(entry["slug"])


def batch_artifact_paths(batch_ids: list[str], entry: dict) -> list[Path]:
    """Everything one personalization run leaves in the shared directories.

    The prefix separates lists, not runs of the same list: a second delta on
    this list renumbers from batch 001 and would overwrite the first delta's
    review and copy JSON. Archiving these into the list's workdir is what keeps
    that history.
    """
    prefix = entry["slug"]
    manifest = manifest_for(entry)
    paths: list[Path] = [manifest, manifest.with_suffix(manifest.suffix + ".lock")]
    paths.append(artifacts.normalized_json(prefix))
    paths.append(artifacts.master_review_md(prefix))
    paths.append(artifacts.merged_csv(prefix))
    for bid in batch_ids:
        paths.extend(
            [
                artifacts.research_json(prefix, bid),
                artifacts.copy_json(prefix, bid),
                artifacts.emails_json(prefix, bid),
                artifacts.review_md(prefix, bid),
                artifacts.enriched_csv(prefix, bid),
            ]
        )
    return paths


def merge_into_cumulative(batch_files: list[Path], cumulative: Path) -> tuple[int, int]:
    """Append rows from batch enriched CSVs into the cumulative list (dedup by email)."""
    fieldnames: list[str] = []
    rows: list[dict] = []
    seen: set[str] = set()
    if cumulative.is_file():
        fieldnames, rows = load_rows(cumulative)
        seen = {e for e in (row_email(r) for r in rows) if e}
    before = len(rows)
    for path in batch_files:
        fnames, batch_rows = load_rows(path)
        for name in fnames:
            if name not in fieldnames:
                fieldnames.append(name)
        for row in batch_rows:
            email = row_email(row)
            if not email or email in seen:
                continue
            seen.add(email)
            rows.append(row)
    cumulative.parent.mkdir(parents=True, exist_ok=True)
    tmp = cumulative.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(cumulative)
    return len(rows) - before, len(rows)


def write_list_review(entry: dict, batch_ids: list[str], stamp: str) -> Path | None:
    total_pass = 0
    total_emails = 0
    total_leads = 0
    sections: list[str] = []
    for bid in batch_ids:
        emails_json = artifacts.emails_json(entry["slug"], bid, COPY_DIR)
        if emails_json.is_file():
            data = json.loads(emails_json.read_text(encoding="utf-8"))
            total_leads += len(data)
            total_pass += sum(
                1 for lead in data for step in lead["sequence"] if step["qa"]["pass"]
            )
            total_emails += sum(len(lead["sequence"]) for lead in data)
        review_md = artifacts.review_md(entry["slug"], bid, COPY_DIR)
        if review_md.is_file():
            sections.append(review_md.read_text(encoding="utf-8"))
    if not sections and total_leads == 0:
        return None
    lines = [
        f"# {entry['slug']} pipeline review — {stamp}",
        f"Leads personalized this run: {total_leads}",
        f"QA pass: {total_pass}/{total_emails}",
        f"Cumulative enriched list: {entry.get('enriched_csv') or '-'}",
        "",
        "---",
        "",
    ]
    out = COPY_DIR / f"{entry['slug']}-pipeline-review-{stamp}.md"
    out.write_text("\n".join(lines) + "\n\n".join(sections), encoding="utf-8")
    return out


def stage_personalize(title: str, entry: dict, args, state: dict) -> None:
    workdir = workdir_for(entry)
    manifest_path = manifest_for(entry)
    verified = ROOT / entry["verified_csv"] if entry.get("verified_csv") else None
    cumulative = workdir / f"{entry['slug']}-enriched.csv"
    entry["enriched_csv"] = str(cumulative.relative_to(ROOT))

    if verified is None or not verified.is_file() or csv_row_count(verified) == 0:
        entry["pending_delta"] = 0
        stage_line("personalize", "no verified leads yet — nothing to personalize")
        return

    # Resume a crashed/interrupted personalization run when this list's manifest
    # still points at its active delta source.
    resume = False
    active = entry.get("active_delta")
    if active:
        normalized_rel = active.get("normalized_csv", "")
        manifest = load_json(manifest_path, None)
        if manifest and manifest.get("source") == normalized_rel and (ROOT / normalized_rel).is_file():
            resume = True
            batch_ids = [b["id"] for b in manifest["batches"]]
            pending_batches = [b["id"] for b in manifest["batches"] if b.get("status") == "pending"]
            entry["pending_delta"] = active.get("leads", 0)
            stage_line(
                "personalize",
                f"resuming interrupted run: {len(pending_batches)}/{len(batch_ids)} batches pending",
            )
        else:
            print("   WARNING: stale active_delta (manifest missing/mismatched) — recomputing delta")
            entry["active_delta"] = None

    if not resume:
        fieldnames, delta, suppressed = compute_delta(
            verified, cumulative, contacted=load_contacted(), slug=entry["slug"]
        )
        entry["pending_delta"] = len(delta)
        if suppressed:
            stage_line(
                "personalize",
                f"skipped {suppressed} address(es) already personalized on another list",
            )
        if not delta:
            stage_line("personalize", "delta: 0 new verified leads — up to date")
            return
        stage_line(
            "personalize",
            f"delta: {len(delta)} new verified leads "
            f"(verified {csv_row_count(verified)}, already enriched {csv_row_count(cumulative)})",
        )

        for old in workdir.glob("*-normalized.csv"):
            old.unlink()
        delta_csv = workdir / f"{entry['slug']}-delta.csv"
        with delta_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(delta)

        # The sidecar JSON defaults to a single campaigns/mix-leads-normalized.json
        # for every list — one more shared name two lists would overwrite, and
        # one the archive step below would never find.
        normalized_rows = normalize_leads(
            delta_csv, json_out=artifacts.normalized_json(entry["slug"])
        )
        normalized = normalized_output_path(delta_csv, len(normalized_rows))
        manifest_data = create_manifest(normalized, manifest_path, batch_size=args.batch_size)
        batch_ids = [b["id"] for b in manifest_data["batches"]]
        pending_batches = list(batch_ids)

        entry["active_delta"] = {
            "normalized_csv": str(normalized.relative_to(ROOT)),
            "delta_csv": str(delta_csv.relative_to(ROOT)),
            "started": now_iso(),
            "leads": len(delta),
        }
        save_state(state)

    if pending_batches:
        workers = min(args.workers, max(1, len(pending_batches)))
        stage_line(
            "personalize",
            f"running {len(pending_batches)} batch(es) x {args.batch_size} leads, "
            f"{workers} parallel workers",
        )
        cmd = [
            PY, str(ROOT / "scripts" / "personalization" / "run_batches.py"),
            "--all-pending", "--workers", str(workers), "--merge",
            "--manifest", str(manifest_path.relative_to(ROOT)),
        ]
        if args.no_render:
            cmd.append("--no-render")
        if args.no_linkedin:
            cmd.append("--no-linkedin")
        proc = subprocess.run(cmd, cwd=ROOT)
        if proc.returncode != 0:
            raise RuntimeError(
                f"run_batches exited {proc.returncode} — state kept, next run resumes this delta"
            )

    # Harvest: fold per-batch enriched CSVs into the stable cumulative list.
    batch_files = [
        artifacts.enriched_csv(entry["slug"], bid, ENRICHED_DIR) for bid in batch_ids
    ]
    batch_files = [p for p in batch_files if p.is_file()]
    added, total = merge_into_cumulative(batch_files, cumulative)
    stage_line(
        "personalize",
        f"merged {len(batch_files)} batch file(s): +{added} leads -> {total} total in {cumulative.name}",
    )
    claimed = record_contacted(entry["slug"], enriched_emails(cumulative))
    if claimed:
        stage_line("personalize", f"claimed {claimed} address(es) in the contacted index")

    stamp = run_stamp()
    review = write_list_review(entry, batch_ids, stamp)
    if review:
        entry.setdefault("reviews", []).append(str(review.relative_to(ROOT)))
        stage_line("personalize", f"review -> {review.relative_to(ROOT)}")

    # Archive run artifacts into the list's own workdir. Names are namespaced
    # by slug now, so this is no longer about collisions between lists — it is
    # about the *next delta on this list*, which renumbers from batch 001 and
    # would otherwise overwrite this run's review and copy JSON.
    archive = workdir / "artifacts" / stamp
    archive.mkdir(parents=True, exist_ok=True)
    moved = 0
    for path in batch_artifact_paths(batch_ids, entry):
        if path.is_file():
            shutil.move(str(path), str(archive / path.name))
            moved += 1
    for extra_name in ("delta_csv", "normalized_csv"):
        rel = entry["active_delta"].get(extra_name)
        if rel and (ROOT / rel).is_file():
            shutil.move(str(ROOT / rel), str(archive / Path(rel).name))
            moved += 1
    stage_line("personalize", f"archived {moved} run artifact(s) -> {archive.relative_to(ROOT)}")

    entry["active_delta"] = None
    entry["personalized_emails"] = total
    entry["pending_delta"] = 0
    save_state(state)


def stage_upload_personalized(title: str, entry: dict, args) -> None:
    cumulative = ROOT / entry["enriched_csv"] if entry.get("enriched_csv") else None
    if cumulative is None or not cumulative.is_file():
        stage_line("upload personalized", "no enriched list yet (skip)")
        return
    if args.local_only:
        stage_line("upload personalized", "[local-only] skipped")
        return
    rows = csv_row_count(cumulative)
    if rows == entry["uploads"].get("enriched_rows"):
        stage_line("upload personalized", f"unchanged ({rows} rows, skip)")
        return
    drive_upload(args.remote, cumulative, DRIVE_PERSONALIZED, title)
    for rel in entry.get("reviews", [])[-1:]:
        review = ROOT / rel
        if review.is_file():
            drive_upload(args.remote, review, DRIVE_PERSONALIZED, title)
    entry["uploads"]["enriched_rows"] = rows
    stage_line("upload personalized", f"{rows} rows -> '{DRIVE_PERSONALIZED}/{title}/'")


def finalize_stage(title: str, entry: dict) -> None:
    if entry.get("verify_complete") and entry.get("pending_delta") == 0:
        entry["stage"] = "done"
    elif entry.get("cleaned_csv"):
        entry["stage"] = "verifying"
    stage_line("status", f"list stage: {entry['stage']}")


# ---------------------------------------------------------------------------
# Reconcile with Drive (adopt already-completed manual/prior outputs)
# ---------------------------------------------------------------------------

# (stage key, Drive folder, state field that records the adopted local path)
STAGE_FOLDERS = [
    ("cleaned", DRIVE_CLEANED, "cleaned_csv"),
    ("verified", DRIVE_VERIFIED, "verified_csv"),
    ("enriched", DRIVE_PERSONALIZED, "enriched_csv"),
]


def adopt_authoritative_csv(
    remote: str, folder: str, title: str, csvs: list[dict], dest: Path
) -> int:
    """Download the folder's CSV with the MOST data rows into ``dest``.

    Handles arbitrary filenames (e.g. the user's ``mixed-*`` naming): when a
    folder holds several CSVs, each candidate is downloaded, its data rows
    counted with the shared csv_row_count helper (quoted multi-line bodies are
    not overcounted), and the largest is kept as the baseline.
    """
    if len(csvs) == 1:
        drive_download_file(remote, folder, title, csvs[0]["Name"], dest)
        return csv_row_count(dest)
    tmpdir = dest.parent / ".reconcile-tmp"
    tmpdir.mkdir(parents=True, exist_ok=True)
    best_path: Path | None = None
    best_rows = -1
    try:
        for it in csvs:
            tmp = tmpdir / it["Name"]
            drive_download_file(remote, folder, title, it["Name"], tmp)
            rows = csv_row_count(tmp)
            if rows > best_rows:
                best_rows, best_path = rows, tmp
        if best_path is not None:
            shutil.move(str(best_path), str(dest))
        return max(best_rows, 0)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def reconcile_list_with_drive(title: str, entry: dict, args, state: dict) -> None:
    """Adopt already-completed Drive outputs as this list's baseline.

    Inspects the Cleaned/Verified/Personalized folders for ``title`` and, for
    each that already holds a CSV, downloads the authoritative file (most data
    rows) into the working dir and derives the list's stage + counts from those
    REAL Drive rows. A list whose enriched rows already cover the verified rows
    is marked ``done`` and skipped so manual work is never redone. Idempotent:
    once a list is ``done`` this is a no-op, and adopting the enriched baseline
    keeps any future personalize delta correct.
    """
    if args.local_only or entry.get("stage") == "done":
        return
    workdir = workdir_for(entry)
    workdir.mkdir(parents=True, exist_ok=True)
    slug = entry["slug"]

    found: dict[str, int] = {}
    for key, folder, field in STAGE_FOLDERS:
        csvs = drive_folder_csvs(args.remote, folder, title)
        if not csvs:
            continue
        dest = workdir / f"{slug}-{key}.csv"
        found[key] = adopt_authoritative_csv(args.remote, folder, title, csvs, dest)
        entry[field] = str(dest.relative_to(ROOT))

    if not found:
        return  # genuinely new list — nothing on Drive yet

    cleaned_n = found.get("cleaned")
    verified_n = found.get("verified")
    enriched_n = found.get("enriched")

    # Mark stages already present in Drive as uploaded so we never push a
    # duplicate (the upload stages also guard on these row counts / flag).
    if cleaned_n is not None:
        entry["uploads"]["cleaned"] = True
    if verified_n is not None:
        entry["uploads"]["verified_rows"] = verified_n
    if enriched_n is not None:
        entry["uploads"]["enriched_rows"] = enriched_n
        entry["personalized_emails"] = enriched_n

    # pending_verification() consults the Reoon cache. If that cache was lost,
    # every already-passed email looks unchecked and would burn quota again, so
    # reseed it from the verified rows just adopted from Drive.
    if verified_n is not None:
        seed_cache_from_verified(workdir / f"{slug}-verified.csv")

    # How many cleaned emails have genuinely never been checked. This is the
    # only sound completeness test: comparing enriched against verified says
    # nothing about the cleaned emails that were never verified in the first
    # place, and treating those lists as done silently abandons the backlog.
    pending = (
        pending_verification(workdir / f"{slug}-cleaned.csv")
        if cleaned_n is not None
        else None
    )
    if pending is not None:
        entry["pending_verification"] = pending
        entry["verify_complete"] = pending == 0

    verify_done = pending == 0 if pending is not None else verified_n is not None
    personalize_done = (
        verified_n is not None and enriched_n is not None and enriched_n >= verified_n
    )

    if verify_done and personalize_done:
        entry["stage"] = "done"
        entry["verify_complete"] = True
        entry["pending_verification"] = 0
        entry["pending_delta"] = 0
        entry["active_delta"] = None
        detail = (
            f"already DONE (cleaned {cleaned_n}, verified {verified_n}, "
            f"enriched {enriched_n}) — skipping"
        )
    elif verified_n is not None:
        entry["stage"] = "verifying"
        detail = (
            f"verified baseline adopted (cleaned {cleaned_n}, verified "
            f"{verified_n}, enriched {enriched_n or 0})"
            + (
                f" — {pending} email(s) still unchecked, resuming verify"
                if pending
                else " — resume at personalize"
            )
        )
    else:
        entry["stage"] = "cleaned"
        detail = f"cleaned baseline adopted ({cleaned_n} rows) — resume at verify"

    entry["last_run"] = now_iso()
    stage_line("reconcile", f'"{title}": {detail}')
    save_state(state)


# ---------------------------------------------------------------------------
# Report (regenerate + push to Drive)
# ---------------------------------------------------------------------------


def finalize_report(args) -> None:
    """Regenerate Report.csv and sync the Drive sheet. Never fatal.

    Delegates entirely to report.py so there is one upload implementation. That
    script updates only the pipeline's own columns of the Enrichment-Reports
    Google Sheet in place, leaving any hand-maintained columns intact.
    """
    cmd = [PY, str(ROOT / "scripts" / "pipeline" / "report.py")]
    if not args.local_only:
        cmd += ["--upload", "--remote", args.remote]
    try:
        subprocess.run(cmd, cwd=ROOT, check=True)
    except Exception as exc:  # noqa: BLE001 — reporting must not fail the run
        print(f"   WARNING: could not regenerate/sync the report: {exc}")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def process_list(title: str, entry: dict, args, state: dict) -> None:
    banner(f"LIST \"{title}\"  [{entry['slug']}]  stage: {entry['stage']}")
    entry["last_run"] = now_iso()
    stage_download(title, entry, args)
    save_state(state)
    stage_clean(title, entry)
    save_state(state)
    stage_upload_cleaned(title, entry, args)
    save_state(state)
    stage_verify(title, entry, args)
    save_state(state)
    stage_upload_verified(title, entry, args)
    save_state(state)
    stage_personalize(title, entry, args, state)
    save_state(state)
    stage_upload_personalized(title, entry, args)
    finalize_stage(title, entry)
    entry["last_error"] = None
    save_state(state)


def discover(state: dict, args) -> list[str]:
    lists = state["lists"]
    if args.raw:
        raw = Path(args.raw)
        if not raw.is_absolute():
            raw = ROOT / raw
        if not raw.is_file():
            raise SystemExit(f"--raw file not found: {raw}")
        title = args.title or raw.stem
        if title not in lists:
            lists[title] = new_entry(title)
            print(f"Registered local list \"{title}\" from {raw}")
        lists[title]["local_raw_source"] = str(raw.relative_to(ROOT)) if raw.is_relative_to(ROOT) else str(raw)

    if not args.local_only:
        print(f"Discovering raw lists in '{args.remote}:{DRIVE_RAW}' ...")
        for item in drive_list_raw(args.remote):
            title = item["title"]
            if title not in lists:
                lists[title] = new_entry(title, item["mtime"])
                print(f"  new list: \"{title}\"")
            lists[title]["drive_leaf"] = item["leaf"]
            lists[title]["drive_ext"] = item.get("ext", ".csv")
            lists[title].setdefault("drive_mtime", item["mtime"])

    ordered = sorted(
        lists.keys(),
        key=lambda t: (lists[t].get("drive_mtime") or lists[t]["discovered_at"], t),
    )
    if args.list:
        if args.list not in lists:
            raise SystemExit(f"Unknown list: {args.list!r}. Known: {sorted(lists)}")
        ordered = [args.list]
    return ordered


def work_priority(entry: dict) -> int:
    """Rank a list by how much of it is already underway (lower runs first).

    Verification is capped per day and the budget is shared, so whichever list
    verifies first is the one that advances. Draining lists that are already
    part-way through therefore has to come before starting a freshly uploaded
    one, or a steady trickle of new uploads keeps the older backlog starved.
    """
    stage = entry.get("stage")
    if stage == "done":
        return 2  # nothing to do; ordering among these is immaterial
    if stage in ("discovered", "error", None) and not entry.get("cleaned_csv"):
        return 1  # never processed — a brand-new upload
    return 0  # started but unfinished


def prioritise(titles: list[str], lists: dict, args) -> list[str]:
    """Unfinished lists first, then new uploads; oldest first within each."""
    if args.list:
        return titles
    return sorted(
        titles,
        key=lambda t: (
            work_priority(lists[t]),
            lists[t].get("drive_mtime") or lists[t]["discovered_at"],
            t,
        ),
    )


def print_summary(state: dict, titles: list[str], failures: dict[str, str]) -> None:
    banner("PIPELINE SUMMARY")
    for title in titles:
        entry = state["lists"][title]
        status = f"FAILED: {failures[title]}" if title in failures else entry["stage"]
        print(
            f"  \"{title}\" [{entry['slug']}] — {status} | "
            f"verified rows: {csv_row_count(ROOT / entry['verified_csv']) if entry.get('verified_csv') else 0} | "
            f"unchecked: {entry.get('pending_verification', '?')} | "
            f"enriched: {entry.get('personalized_emails', 0)}"
        )
    if failures:
        print(f"\n{len(failures)} list(s) failed — see errors above; others completed.")


def print_status(state: dict) -> None:
    if not state["lists"]:
        print("No lists tracked yet (.pipeline/state.json empty).")
        return
    for title, entry in state["lists"].items():
        print(
            f"\"{title}\" [{entry['slug']}] stage={entry['stage']} "
            f"verify_complete={entry.get('verify_complete')} "
            f"pending_verification={entry.get('pending_verification')} "
            f"enriched={entry.get('personalized_emails', 0)} "
            f"last_run={entry.get('last_run')} "
            f"last_error={entry.get('last_error')}"
        )


def main() -> None:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Drive lead pipeline orchestrator")
    parser.add_argument("--remote", default="gdrive", help="rclone remote name (default: gdrive)")
    parser.add_argument("--local-only", action="store_true",
                        help="No Drive access: skip discovery and all uploads/downloads")
    parser.add_argument("--raw", help="Register a local raw CSV/XLSX as a list (for local-only runs)")
    parser.add_argument("--title", help="List title for --raw (default: file stem)")
    parser.add_argument("--list", help="Process only this list title")
    parser.add_argument("--no-verify", action="store_true",
                        help="Skip the Reoon verification stage entirely")
    parser.add_argument("--verify-limit", type=int,
                        default=int(os.environ.get("REOON_DAILY_LIMIT", "500")),
                        help="Daily Reoon verification cap (default: 500)")
    parser.add_argument("--workers", type=int, default=10,
                        help="Parallel personalization workers (default: 10)")
    parser.add_argument("--batch-size", type=int, default=50,
                        help="Leads per personalization batch (default: 50)")
    parser.add_argument("--no-render", action="store_true",
                        help="Pass --no-render to run_batches (skip headless browser)")
    parser.add_argument("--no-linkedin", action="store_true",
                        help="Pass --no-linkedin to run_batches (skip Apify)")
    parser.add_argument("--status", action="store_true", help="Print state and exit")
    parser.add_argument("--backfill-contacted", action="store_true",
                        help="Rebuild .pipeline/contacted.json from existing enriched CSVs and exit")
    parser.add_argument("--backfill-rejected", action="store_true",
                        help="Infer .reoon/rejected.json tombstones for lists that finished "
                             "verifying but whose cache was lost (preview unless --apply)")
    parser.add_argument("--apply", action="store_true",
                        help="Write the changes a --backfill-* preview would make")
    args = parser.parse_args()

    state = load_state()
    if args.status:
        print_status(state)
        return

    if args.backfill_rejected:
        found = backfill_rejected(state, apply=args.apply)
        total = sum(n for _, n in found)
        verb = "Tombstoned" if args.apply else "Would tombstone"
        for slug, count in found:
            print(f"  {slug}: {count} address(es) checked but not kept")
        print(f"{verb} {total} address(es) across {len(found)} completed list(s)"
              + ("" if args.apply else " — re-run with --apply to write"))
        return

    if args.backfill_contacted:
        unique, duplicates = backfill_contacted(state)
        print(f"Contacted index: {unique} unique address(es); "
              f"{duplicates} already personalized on more than one list.")
        return

    # First run after the index was introduced: claim everything already sent,
    # or the next delta would re-personalize leads from every other list.
    if not CONTACTED_FILE.is_file():
        unique, duplicates = backfill_contacted(state)
        print(f"\nSeeded contacted index from existing enriched lists: {unique} address(es) "
              f"({duplicates} found on more than one list).")

    titles = discover(state, args)
    save_state(state)
    if not titles:
        print("No lists to process.")
        return

    # Adopt already-completed Drive outputs for EVERY list before processing any
    # of them, so we never redo manual/prior work — and so the ordering below
    # can see each list's true remaining work. Non-fatal: a reconcile hiccup
    # (e.g. transient Drive error) must not block processing.
    print(f"\nReconciling {len(titles)} list(s) with Drive ...")
    for title in titles:
        try:
            reconcile_list_with_drive(title, state["lists"][title], args, state)
        except Exception as exc:  # noqa: BLE001
            print(f"   WARNING: reconcile failed for \"{title}\": {exc}")
    save_state(state)

    titles = prioritise(titles, state["lists"], args)
    print(f"\nProcessing {len(titles)} list(s), unfinished first: {titles}")
    failures: dict[str, str] = {}
    for title in titles:
        entry = state["lists"][title]
        if entry["stage"] == "done":
            banner(f"LIST \"{title}\"  [{entry['slug']}]  stage: done (skip)")
            continue
        try:
            process_list(title, entry, args, state)
        except Exception as exc:  # noqa: BLE001 — one list must not block others
            traceback.print_exc()
            entry["last_error"] = f"{type(exc).__name__}: {exc}"
            entry["stage"] = entry.get("stage") or "error"
            failures[title] = entry["last_error"]
            save_state(state)
            print(f"\n!! LIST \"{title}\" FAILED — continuing with remaining lists")

    # Refresh the local report and mirror it to Drive after every run.
    finalize_report(args)

    print_summary(state, [t for t in titles if state["lists"][t]["stage"] != "done" or t in failures] or titles, failures)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
