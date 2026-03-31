"""Generate a Markdown analysis report."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from models import Bookmark


def _ts_to_date(ts: int) -> str:
    if ts <= 0:
        return "N/A"
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    except (OSError, OverflowError):
        return "N/A"


def generate_report(
    bookmarks: list[Bookmark],
    duplicate_groups: dict[str, list[Bookmark]],
    output_path: str | Path,
) -> None:
    total = len(bookmarks)
    dup_count = sum(1 for bm in bookmarks if bm.is_duplicate)
    checked = [bm for bm in bookmarks if bm.link_status != 0 or bm.link_error]
    broken = [bm for bm in checked if bm.link_status >= 400 or (bm.link_status == 0 and bm.link_error)]
    unique = [bm for bm in bookmarks if not bm.is_duplicate]

    cat_counter: Counter[str] = Counter()
    for bm in unique:
        cat_counter[bm.new_category] += 1

    lines: list[str] = []
    w = lines.append

    # ── Summary ──────────────────────────────────────────────────────────
    w("# Bookmark Organizer Report\n")
    w(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    w("## Summary\n")
    w(f"| Metric | Value |")
    w(f"|--------|-------|")
    w(f"| Total bookmarks | {total} |")
    w(f"| Unique bookmarks | {total - dup_count} |")
    w(f"| Duplicates removed | {dup_count} |")
    w(f"| Links checked | {len(checked)} |")
    w(f"| Broken links | {len(broken)} |")
    w(f"| Categories | {len(cat_counter)} |")
    w("")

    # ── Category Distribution ────────────────────────────────────────────
    w("## Category Distribution\n")
    w("| Category | Count |")
    w("|----------|-------|")
    for cat, cnt in cat_counter.most_common():
        w(f"| {cat} | {cnt} |")
    w("")

    # ── Duplicate Bookmarks ──────────────────────────────────────────────
    if duplicate_groups:
        w("## Duplicate Bookmarks\n")
        for norm_url, group in sorted(duplicate_groups.items()):
            kept = group[0]
            w(f"### {kept.title}\n")
            w(f"Canonical URL: {kept.url}\n")
            w("| Title | Original Folder | Date Added | Kept |")
            w("|-------|-----------------|------------|------|")
            for bm in group:
                kept_mark = "**Yes**" if not bm.is_duplicate else "No"
                w(f"| {bm.title} | {bm.original_folder} | {_ts_to_date(bm.add_date)} | {kept_mark} |")
            w("")

    # ── Broken Links ─────────────────────────────────────────────────────
    if broken:
        w("## Broken Links\n")
        w("| Title | URL | Status | Error | Original Folder |")
        w("|-------|-----|--------|-------|-----------------|")
        for bm in broken:
            status = str(bm.link_status) if bm.link_status else "-"
            error = bm.link_error or ""
            w(f"| {bm.title} | {bm.url} | {status} | {error} | {bm.original_folder} |")
        w("")

    # ── Category Changes ─────────────────────────────────────────────────
    w("## Category Mapping (Original Folder -> New Category)\n")
    w("| Title | Original Folder | New Category |")
    w("|-------|-----------------|--------------|")
    for bm in unique:
        if bm.original_folder != bm.new_category:
            w(f"| {bm.title} | {bm.original_folder} | {bm.new_category} |")
    w("")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
