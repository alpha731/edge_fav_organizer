"""CLI entry-point for the Edge Bookmark Organizer."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from tqdm import tqdm

from classifier import classify_bookmarks
from dedup import find_duplicates
from html_generator import generate_html
from link_checker import check_links
from parser import parse_bookmarks
from report_generator import generate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Organise, deduplicate, validate and reclassify browser bookmarks."
    )
    p.add_argument(
        "-i",
        "--input",
        type=Path,
        default=None,
        help="Input Netscape Bookmark HTML file (auto-detected if omitted).",
    )
    p.add_argument(
        "--skip-link-check",
        action="store_true",
        help="Skip HTTP link validation.",
    )
    p.add_argument(
        "--skip-classify",
        action="store_true",
        help="Skip LLM-based reclassification.",
    )
    p.add_argument(
        "--keep-broken",
        action="store_true",
        help="Keep broken links in the output HTML.",
    )
    p.add_argument(
        "--concurrency",
        type=int,
        default=20,
        help="Max concurrent HTTP connections for link checking (default: 20).",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("organized_bookmarks.html"),
        help="Output HTML file path.",
    )
    p.add_argument(
        "--report",
        type=Path,
        default=Path("report.md"),
        help="Output Markdown report path.",
    )
    p.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="DeepSeek API key (overrides DEEPSEEK_API_KEY env var / .env file).",
    )
    return p


def _auto_detect_input() -> Path:
    candidates = sorted(Path(".").glob("favorites*.html")) + sorted(
        Path(".").glob("bookmarks*.html")
    )
    if not candidates:
        log.error("No bookmark HTML file found in the current directory.")
        sys.exit(1)
    log.info("Auto-detected input: %s", candidates[0])
    return candidates[0]


async def _run(args: argparse.Namespace) -> None:
    # Override API key if provided via CLI
    if args.api_key:
        import config
        config.DEEPSEEK_API_KEY = args.api_key

    input_path = args.input or _auto_detect_input()

    # 1. Parse
    log.info("Parsing %s …", input_path)
    bookmarks = parse_bookmarks(input_path)
    log.info("Parsed %d bookmarks.", len(bookmarks))

    # 2. Deduplicate
    log.info("Finding duplicates …")
    dup_groups = find_duplicates(bookmarks)
    dup_count = sum(1 for bm in bookmarks if bm.is_duplicate)
    log.info("Found %d duplicate(s) across %d URL group(s).", dup_count, len(dup_groups))

    # 3. Link check
    if not args.skip_link_check:
        non_dup = [bm for bm in bookmarks if not bm.is_duplicate]
        log.info("Checking %d links (concurrency=%d) …", len(non_dup), args.concurrency)
        pbar = tqdm(total=len(non_dup), desc="Link check", unit="url")

        def _link_progress(done: int) -> None:
            pbar.update(1)

        await check_links(non_dup, concurrency=args.concurrency, progress_cb=_link_progress)
        pbar.close()
        broken = sum(
            1
            for bm in non_dup
            if bm.link_status >= 400 or (bm.link_status == 0 and bm.link_error)
        )
        log.info("Link check complete: %d broken.", broken)
    else:
        log.info("Skipping link check.")

    # 4. Classify
    if not args.skip_classify:
        log.info("Classifying bookmarks via DeepSeek …")

        def _cls_progress(batch_done: int, batch_total: int) -> None:
            log.info("  batch %d / %d", batch_done, batch_total)

        await classify_bookmarks(bookmarks, progress_cb=_cls_progress)
        log.info("Classification complete.")
    else:
        log.info("Skipping classification — keeping original folders as categories.")
        for bm in bookmarks:
            bm.new_category = bm.original_folder or "Other"

    # 5. Generate outputs
    log.info("Writing HTML → %s", args.output)
    generate_html(
        bookmarks,
        args.output,
        exclude_duplicates=True,
        exclude_broken=not args.keep_broken,
    )

    log.info("Writing report → %s", args.report)
    generate_report(bookmarks, dup_groups, args.report)

    log.info("Done.")


def main() -> None:
    args = _build_parser().parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
