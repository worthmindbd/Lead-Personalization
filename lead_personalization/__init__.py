"""Lead personalization core library.

Deterministic B2B cold-email research + copy engine. No LLM calls: copy is
assembled from versioned offer packs (variant pools + subject templates)
selected by a stable per-lead hash, driven by research signals scraped from
websites and LinkedIn.
"""

from __future__ import annotations

__version__ = "1.0.0"

from lead_personalization.config import Config
from lead_personalization.offer_pack import OfferPack, load_offer_pack

__all__ = ["Config", "OfferPack", "load_offer_pack", "__version__"]
