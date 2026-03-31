"""Centralised configuration for the bookmark organizer."""

import os
from pathlib import Path

# Load .env file if present (lightweight, no dependency)
_env_file = Path(__file__).with_name(".env")
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))

# ── DeepSeek API ────────────────────────────────────────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
CLASSIFIER_BATCH_SIZE = 20  # bookmarks per API call

# ── Link checker ────────────────────────────────────────────────────────────
LINK_CHECK_TIMEOUT = 15  # seconds per request
LINK_CHECK_CONCURRENCY = 20
LINK_CHECK_MAX_REDIRECTS = 5

# ── URL normalisation params to strip ───────────────────────────────────────
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
    "source",
}

# ── Predefined categories for LLM classification ───────────────────────────
CATEGORIES = [
    "Programming/C++",
    "Programming/Go",
    "Programming/Python",
    "Programming/Web",
    "Programming/General",
    "AI/MachineLearning",
    "AI/ComputerVision",
    "AI/NLP",
    "AI/Tools",
    "DevTools",
    "Algorithms/DataStructures",
    "Academic/Research",
    "Finance/Investing",
    "Career/Jobs",
    "News/Media",
    "Utilities/OnlineTools",
    "Other",
]
