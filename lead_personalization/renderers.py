"""Page renderers behind a small interface.

Tier 2 of the rendering chain: when a plain HTTP fetch (tier 1, in research.py)
can't read a JS-built site, a renderer produces the same signal dict. The
``PageRenderer`` protocol lets a future ``FirecrawlRenderer`` (tier 3) slot in
without touching research logic — the roadmap's Phase 2 hook.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Protocol

VIDEO_EVIDENCE = re.compile(
    r"youtube\.com/embed|youtube-nocookie\.com|player\.vimeo\.com|fast\.wistia"
    r"|<video\b|\.mp4\b|loom\.com/embed",
    re.I,
)

EMPTY_SIGNALS = {
    "title": "",
    "description": "",
    "h1": "",
    "has_video": False,
    "fetched": False,
    "error": "",
}


class PageRenderer(Protocol):
    """Anything that turns a URL into a page-signal dict."""

    def render(self, url: str) -> dict: ...


class NodePlaywrightRenderer:
    """Tier 2: headless Chromium via the bundled render_page.js subprocess."""

    def __init__(self, script_path: Path, cwd: Path, timeout_s: int = 45) -> None:
        self.script_path = Path(script_path)
        self.cwd = Path(cwd)
        self.timeout_s = timeout_s

    @property
    def available(self) -> bool:
        return self.script_path.is_file()

    def render(self, url: str) -> dict:
        result = {**EMPTY_SIGNALS, "rendered": True}
        if not url or not url.startswith("http") or not self.available:
            result["error"] = "render unavailable"
            return result
        try:
            proc = subprocess.run(
                ["node", str(self.script_path), url],
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                cwd=str(self.cwd),
            )
            if proc.returncode != 0:
                result["error"] = (
                    f"render failed (node exit {proc.returncode}): "
                    f"{proc.stderr.strip()[:100]}"
                )
                return result
            data = json.loads(proc.stdout.strip() or "{}")
            for key in ("title", "description", "h1", "has_video", "fetched", "error"):
                if key in data:
                    result[key] = data[key]
        except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError) as exc:
            result["error"] = f"render failed: {str(exc)[:100]}"
        return result
