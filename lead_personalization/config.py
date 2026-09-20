"""Runtime configuration: paths, feature flags, and API keys.

One definition of the repo's paths, feature flags, and limits (``.env``
aware) instead of a copy per script. Scripts build a ``Config`` at startup and
derive their module-level knobs from it, so tests can still flip a flag by
patching the module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent


def _parse_bool(val: str | None, default: bool) -> bool:
    if val is None:
        return default
    return val.strip().lower() not in ("0", "false", "no", "off")


def load_dotenv(path: Path) -> None:
    """Populate os.environ from a .env file (does not overwrite existing keys)."""
    if not path.is_file():
        return
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if "#" in value and not (
            (value.startswith('"') and '"' in value[1:])
            or (value.startswith("'") and "'" in value[1:])
        ):
            value = value.split("#", 1)[0].strip()
        os.environ.setdefault(key, value.strip('"').strip("'"))


@dataclass
class Config:
    """Paths, feature flags, and secrets for one run of the pipeline."""

    root: Path = REPO_ROOT

    # Data locations (defaults mirror the original repo layout).
    leads_dir: Path = field(default=None)  # type: ignore[assignment]
    campaigns_dir: Path = field(default=None)  # type: ignore[assignment]
    copy_dir: Path = field(default=None)  # type: ignore[assignment]
    enriched_dir: Path = field(default=None)  # type: ignore[assignment]
    state_dir: Path = field(default=None)  # type: ignore[assignment]

    # Feature flags.
    render_fallback: bool = True
    render_timeout_s: int = 45
    linkedin_enrich: bool = True
    linkedin_max_posts: int = 2

    # Secrets / limits.
    apify_token: str = ""
    apify_tokens: list[str] = field(default_factory=list)
    reoon_api_key: str = ""
    reoon_daily_limit: int = 500
    firecrawl_api_key: str = ""  # reserved for a future tier-3 renderer

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        if self.leads_dir is None:
            self.leads_dir = self.root / "leads"
        if self.campaigns_dir is None:
            self.campaigns_dir = self.root / "campaigns"
        if self.copy_dir is None:
            self.copy_dir = self.root / "copy"
        if self.enriched_dir is None:
            self.enriched_dir = self.leads_dir / "enriched"
        if self.state_dir is None:
            self.state_dir = self.root
        if not self.apify_tokens and self.apify_token:
            from lead_personalization.linkedin import parse_tokens
            self.apify_tokens = parse_tokens(self.apify_token)
        elif self.apify_tokens and not self.apify_token:
            self.apify_token = ",".join(self.apify_tokens)

    @classmethod
    def from_env(cls, root: Path | None = None, **overrides) -> "Config":
        """Build a Config from environment variables (loading .env and .env.local first)."""
        base = Path(root) if root else REPO_ROOT
        load_dotenv(base / ".env")
        load_dotenv(base / ".env.local")
        env = os.environ
        try:
            reoon_daily_limit = int(env.get("REOON_DAILY_LIMIT", "500") or "500")
        except ValueError:
            reoon_daily_limit = 500

        try:
            render_timeout_s = int(env.get("RENDER_TIMEOUT_S", "45") or "45")
        except ValueError:
            render_timeout_s = 45

        try:
            linkedin_max_posts = int(env.get("LINKEDIN_MAX_POSTS", "2") or "2")
        except ValueError:
            linkedin_max_posts = 2

        raw_primary = env.get("APIFY_API_TOKEN", "").strip()
        raw_fallbacks = (
            env.get("APIFY_API_TOKENS", "").strip()
            or env.get("APIFY_FALLBACK_TOKENS", "").strip()
            or env.get("APIFY_API_FALLBACK_TOKENS", "").strip()
        )
        combined = []
        if raw_primary:
            combined.append(raw_primary)
        if raw_fallbacks:
            combined.append(raw_fallbacks)
        apify_token_val = ",".join(combined)

        kwargs = dict(
            root=base,
            render_fallback=_parse_bool(env.get("RENDER_FALLBACK"), True),
            render_timeout_s=render_timeout_s,
            linkedin_enrich=_parse_bool(env.get("LINKEDIN_ENRICH"), True),
            linkedin_max_posts=linkedin_max_posts,
            apify_token=apify_token_val,
            reoon_api_key=env.get("REOON_API_KEY", "").strip(),
            reoon_daily_limit=reoon_daily_limit,
            firecrawl_api_key=env.get("FIRECRAWL_API_KEY", "").strip(),
        )
        kwargs.update(overrides)
        return cls(**kwargs)

    @property
    def apify_cache_file(self) -> Path:
        return self.state_dir / ".apify" / "linkedin_cache.json"

    @property
    def render_script(self) -> Path:
        return PACKAGE_DIR / "render_page.js"
