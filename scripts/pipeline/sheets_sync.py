#!/usr/bin/env python3
"""In-place cell updates for the ``Enrichment-Reports`` Google Sheet.

The pipeline used to publish its report by staging a CSV and letting rclone
re-import it over the sheet. That is a whole-file replace: any column a human
added to the sheet by hand was destroyed on every run.

This module talks to the Google Sheets API instead and writes *only* the
columns the pipeline owns (``A``..``J`` for the 10 columns in
``report.COLUMNS``). Two properties make that guarantee hold:

* Rows are matched by ``list_title`` in column A and **never moved**. A list
  that is already in the sheet is updated where it sits.
* A list that is new gets a row *inserted* directly above ``TOTAL``. Sheets
  shifts the manual columns down along with their row, so annotations stay
  attached to the list they describe.

Nothing here ever writes past the pipeline's own column range, and nothing here
ever deletes a row.

Credentials are reused from the existing rclone remote (``scope = drive``,
which the Sheets API accepts) so there is no second OAuth setup to maintain.
"""

from __future__ import annotations

import configparser
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
SHEETS_URL = "https://sheets.googleapis.com/v4/spreadsheets"
SHEET_MIME = "application/vnd.google-apps.spreadsheet"

TOTAL_TITLE = "TOTAL"
HTTP_TIMEOUT = 30


class SheetsSyncError(RuntimeError):
    """Any failure that should leave the remote sheet untouched."""


# ---------------------------------------------------------------------------
# Planning (pure — no I/O, unit-tested in tests/test_sheets_sync.py)
# ---------------------------------------------------------------------------


@dataclass
class Plan:
    """What ``sync`` would do, decided before any write is issued."""

    # 0-based sheet row indices at which to insert a blank row, ascending.
    inserts: list[int] = field(default_factory=list)
    # (a1_range, row_values) pairs — every range is confined to columns A..last.
    updates: list[tuple[str, list[Any]]] = field(default_factory=list)

    def describe(self) -> str:
        lines = []
        for idx in self.inserts:
            lines.append(f"  insert blank row at sheet row {idx + 1}")
        for rng, values in self.updates:
            shown = ", ".join("" if v == "" else str(v) for v in values[:3])
            lines.append(f"  write {rng:<10} {shown} ...")
        return "\n".join(lines) if lines else "  (nothing to do)"


def column_letter(index: int) -> str:
    """1-based column index -> A1 letter ('1' -> 'A', '27' -> 'AA')."""
    if index < 1:
        raise ValueError("column index is 1-based")
    letters = ""
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(ord("A") + rem) + letters
    return letters


def _row_values(row: dict, columns: Sequence[str]) -> list[Any]:
    return [row.get(col, "") for col in columns]


def plan_writes(
    column_a: Sequence[str],
    header_row: Sequence[str],
    rows: Sequence[dict],
    columns: Sequence[str],
) -> Plan:
    """Decide the exact set of inserts and A..last writes for ``rows``.

    ``column_a`` is the sheet's column A top-to-bottom (index 0 == row 1).
    ``header_row`` is the sheet's existing row 1 across the pipeline columns.

    Raises SheetsSyncError if ``rows`` carries no list rows — a report built
    from missing/empty state must not be allowed to blank out the sheet.
    """
    list_rows = [r for r in rows if r.get("list_title") != TOTAL_TITLE]
    total_rows = [r for r in rows if r.get("list_title") == TOTAL_TITLE]
    if not list_rows:
        raise SheetsSyncError(
            "report contains no list rows — refusing to update the sheet "
            "(is .pipeline/state.json missing?)"
        )

    last_col = column_letter(len(columns))
    plan = Plan()

    def write(row_number: int, values: list[Any]) -> None:
        plan.updates.append((f"A{row_number}:{last_col}{row_number}", values))

    # Trailing blanks in column A are empty grid rows, not data.
    trimmed = list(column_a)
    while trimmed and not str(trimmed[-1]).strip():
        trimmed.pop()

    if list(header_row) != list(columns):
        write(1, list(columns))

    # title -> 1-based sheet row, for data rows only.
    existing: dict[str, int] = {}
    total_row_number: int | None = None
    for offset, value in enumerate(trimmed):
        row_number = offset + 1
        if row_number == 1:
            continue  # header
        title = str(value).strip()
        if not title:
            continue
        if title == TOTAL_TITLE:
            total_row_number = row_number
        elif title not in existing:
            existing[title] = row_number

    new_rows = [r for r in list_rows if str(r["list_title"]) not in existing]

    if total_row_number is not None:
        # New lists are inserted at TOTAL's position, pushing TOTAL down. Every
        # existing list row sits above TOTAL, so their row numbers do not move.
        insert_at = total_row_number
        plan.inserts = [insert_at - 1 + i for i in range(len(new_rows))]
        shift = len(new_rows)
    else:
        # No TOTAL row: append new lists (and then TOTAL) after the last row.
        insert_at = len(trimmed) + 1
        shift = 0

    for row in list_rows:
        title = str(row["list_title"])
        if title in existing:
            row_number = existing[title]
            # Defensive: a list row sitting *below* TOTAL would be shifted too.
            if total_row_number is not None and row_number >= total_row_number:
                row_number += shift
            write(row_number, _row_values(row, columns))

    for offset, row in enumerate(new_rows):
        write(insert_at + offset, _row_values(row, columns))

    if total_rows:
        if total_row_number is not None:
            write(total_row_number + shift, _row_values(total_rows[0], columns))
        else:
            write(insert_at + len(new_rows), _row_values(total_rows[0], columns))

    plan.updates.sort(key=lambda u: int(u[0].split(":")[0][1:]))
    return plan


# ---------------------------------------------------------------------------
# Credentials (reused from the existing rclone remote)
# ---------------------------------------------------------------------------


def resolve_rclone() -> str:
    """Locate the rclone binary: $RCLONE_BIN, then ~/.local/bin, then PATH."""
    candidates = [
        os.environ.get("RCLONE_BIN"),
        str(Path.home() / ".local" / "bin" / "rclone"),
        "rclone",
    ]
    for cand in candidates:
        if not cand:
            continue
        if os.sep in cand:
            if Path(cand).is_file():
                return cand
        else:
            found = shutil.which(cand)
            if found:
                return found
    return "rclone"


def _remote_config(remote: str) -> dict[str, str]:
    """Read one rclone remote's settings.

    Prefers ``rclone config show <remote>`` so encrypted configs work; falls
    back to parsing the config file directly if the binary is unavailable.
    """
    text: str | None = None
    try:
        proc = subprocess.run(
            [resolve_rclone(), "config", "show", remote],
            capture_output=True, text=True, check=True,
        )
        text = proc.stdout
    except (OSError, subprocess.CalledProcessError):
        path = Path(
            os.environ.get("RCLONE_CONFIG")
            or Path.home() / ".config" / "rclone" / "rclone.conf"
        )
        if path.is_file():
            text = path.read_text(encoding="utf-8")

    if not text:
        raise SheetsSyncError(
            f"could not read rclone remote '{remote}' (is rclone configured?)"
        )

    parser = configparser.RawConfigParser()  # tokens may contain '%'
    try:
        parser.read_string(text)
    except configparser.Error as exc:
        raise SheetsSyncError(f"could not parse rclone config: {exc}") from exc
    if not parser.has_section(remote):
        raise SheetsSyncError(f"rclone remote '{remote}' not found")
    return dict(parser[remote])


def access_token(remote: str = "gdrive") -> str:
    """Mint a fresh access token from the remote's stored refresh token."""
    cfg = _remote_config(remote)
    try:
        token = json.loads(cfg["token"])
        payload = {
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "refresh_token": token["refresh_token"],
            "grant_type": "refresh_token",
        }
    except (KeyError, json.JSONDecodeError) as exc:
        raise SheetsSyncError(
            f"rclone remote '{remote}' has no usable OAuth token ({exc}); "
            "re-run `rclone config reconnect " + remote + ":`"
        ) from exc

    data = urllib.parse.urlencode(payload).encode()
    try:
        with urllib.request.urlopen(TOKEN_URL, data, timeout=HTTP_TIMEOUT) as resp:
            return json.load(resp)["access_token"]
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
        # Deliberately does not echo the payload — it holds the refresh token.
        raise SheetsSyncError(f"OAuth token refresh failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Sheets / Drive API
# ---------------------------------------------------------------------------


def _request(token: str, url: str, method: str = "GET", body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        raise SheetsSyncError(f"{method} {url.split('?')[0]} -> {exc.code}: {detail}") from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise SheetsSyncError(f"{method} {url.split('?')[0]} failed: {exc}") from exc


def find_sheet_id(token: str, name: str) -> str:
    """Resolve a spreadsheet by exact name. Ambiguity is an error, not a guess."""
    query = f"name='{name}' and mimeType='{SHEET_MIME}' and trashed=false"
    url = f"{DRIVE_FILES_URL}?{urllib.parse.urlencode({'q': query, 'fields': 'files(id,name)'})}"
    files = _request(token, url).get("files", [])
    if not files:
        raise SheetsSyncError(
            f"no Google Sheet named '{name}' in Drive — create it (or let an "
            "earlier run create it) before syncing"
        )
    if len(files) > 1:
        raise SheetsSyncError(
            f"{len(files)} Google Sheets named '{name}' in Drive; "
            "remove the duplicates so the report has one stable target"
        )
    return files[0]["id"]


def _first_tab_id(token: str, sheet_id: str) -> int:
    url = f"{SHEETS_URL}/{sheet_id}?fields=sheets(properties(sheetId,title))"
    sheets = _request(token, url).get("sheets", [])
    if not sheets:
        raise SheetsSyncError(f"spreadsheet {sheet_id} has no tabs")
    return int(sheets[0]["properties"]["sheetId"])


def _read_grid(token: str, sheet_id: str, last_col: str) -> tuple[list[str], list[str]]:
    """Return (column A values, row 1 across A..last_col)."""
    params = urllib.parse.urlencode(
        [("ranges", "A:A"), ("ranges", f"A1:{last_col}1"),
         ("majorDimension", "ROWS")]
    )
    payload = _request(token, f"{SHEETS_URL}/{sheet_id}/values:batchGet?{params}")
    ranges = payload.get("valueRanges", [])
    col_a_rows = ranges[0].get("values", []) if ranges else []
    header_rows = ranges[1].get("values", []) if len(ranges) > 1 else []
    column_a = [(r[0] if r else "") for r in col_a_rows]
    header = header_rows[0] if header_rows else []
    return column_a, header


def apply_plan(token: str, sheet_id: str, tab_id: int, plan: Plan) -> None:
    """Insert rows (if any), then write every planned A..last range."""
    if plan.inserts:
        requests = [
            {
                "insertDimension": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "ROWS",
                        "startIndex": idx,
                        "endIndex": idx + 1,
                    },
                    "inheritFromBefore": False,
                }
            }
            # Descending, so each insert index stays valid as rows shift down.
            for idx in sorted(plan.inserts, reverse=True)
        ]
        _request(token, f"{SHEETS_URL}/{sheet_id}:batchUpdate", "POST",
                 {"requests": requests})

    if plan.updates:
        _request(
            token, f"{SHEETS_URL}/{sheet_id}/values:batchUpdate", "POST",
            {
                "valueInputOption": "USER_ENTERED",
                "data": [{"range": rng, "values": [values]}
                         for rng, values in plan.updates],
            },
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def sync(
    rows: Sequence[dict],
    columns: Sequence[str],
    sheet_name: str,
    remote: str = "gdrive",
    dry_run: bool = False,
) -> str:
    """Update ``sheet_name`` in place from ``rows``. Returns a summary line.

    Raises SheetsSyncError on any failure; the caller should warn and leave the
    sheet as it is. There is deliberately no CSV-import fallback — that path is
    what destroyed manually-added columns in the first place.
    """
    token = access_token(remote)
    sheet_id = find_sheet_id(token, sheet_name)
    last_col = column_letter(len(columns))
    column_a, header = _read_grid(token, sheet_id, last_col)
    plan = plan_writes(column_a, header, rows, columns)

    if dry_run:
        return (f"[dry-run] {sheet_name} ({sheet_id}) — "
                f"{len(plan.inserts)} insert(s), {len(plan.updates)} write(s), "
                f"columns A:{last_col} only\n{plan.describe()}")

    apply_plan(token, sheet_id, _first_tab_id(token, sheet_id), plan)
    return (f"Synced '{sheet_name}' in place: {len(plan.updates)} row(s) written "
            f"in A:{last_col}, {len(plan.inserts)} new row(s) inserted; "
            f"columns beyond {last_col} untouched")
