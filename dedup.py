"""URL normalisation and duplicate detection."""

from __future__ import annotations

from collections import defaultdict
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from config import TRACKING_PARAMS
from models import Bookmark


def normalize_url(raw: str) -> str:
    """Return a canonical form of *raw* so that trivially-different URLs match.

    Rules applied:
      1. Lower-case the scheme and host.
      2. Remove default ports (80 for http, 443 for https).
      3. Strip ``www.`` prefix from the host.
      4. Unify scheme to ``https``.
      5. Remove known tracking query params (utm_*, fbclid …).
      6. Strip trailing ``/`` from the path.
      7. Sort remaining query params for determinism.
    """
    parsed = urlparse(raw)

    scheme = parsed.scheme.lower()
    host = parsed.netloc.lower()

    # strip default ports
    if host.endswith(":80") and scheme == "http":
        host = host[:-3]
    elif host.endswith(":443") and scheme == "https":
        host = host[:-4]

    # strip www.
    if host.startswith("www."):
        host = host[4:]

    # unify to https
    scheme = "https"

    # clean path
    path = parsed.path.rstrip("/") or ""

    # filter tracking params and sort
    qs = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {k: v for k, v in qs.items() if k.lower() not in TRACKING_PARAMS}
    query = urlencode(sorted(filtered.items()), doseq=True) if filtered else ""

    return urlunparse((scheme, host, path, "", query, ""))


def find_duplicates(bookmarks: list[Bookmark]) -> dict[str, list[Bookmark]]:
    """Mark duplicate bookmarks and return groups with >=2 entries.

    Within each group the bookmark with the latest ``add_date`` is kept
    (``is_duplicate`` stays *False*); all others are flagged as duplicates.
    """
    groups: dict[str, list[Bookmark]] = defaultdict(list)
    for bm in bookmarks:
        groups[normalize_url(bm.url)].append(bm)

    duplicate_groups: dict[str, list[Bookmark]] = {}
    for norm_url, group in groups.items():
        if len(group) < 2:
            continue
        # sort descending by add_date; first one wins
        group.sort(key=lambda b: b.add_date, reverse=True)
        for bm in group[1:]:
            bm.is_duplicate = True
        duplicate_groups[norm_url] = group

    return duplicate_groups
