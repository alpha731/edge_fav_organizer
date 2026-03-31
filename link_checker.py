"""Async link-health checker using aiohttp."""

from __future__ import annotations

import asyncio
import ssl

import aiohttp

from config import LINK_CHECK_CONCURRENCY, LINK_CHECK_MAX_REDIRECTS, LINK_CHECK_TIMEOUT
from models import Bookmark


async def _check_one(
    bm: Bookmark,
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
) -> None:
    """Issue an HTTP GET for *bm* and populate status / error fields."""
    async with sem:
        try:
            async with session.get(
                bm.url,
                timeout=aiohttp.ClientTimeout(total=LINK_CHECK_TIMEOUT),
                max_redirects=LINK_CHECK_MAX_REDIRECTS,
                allow_redirects=True,
                ssl=False,  # ignore SSL certificate errors
            ) as resp:
                bm.link_status = resp.status
        except asyncio.TimeoutError:
            bm.link_status = 0
            bm.link_error = "Timeout"
        except aiohttp.TooManyRedirects:
            bm.link_status = 0
            bm.link_error = "TooManyRedirects"
        except aiohttp.ClientError as exc:
            bm.link_status = 0
            bm.link_error = type(exc).__name__
        except ssl.SSLError as exc:
            bm.link_status = 0
            bm.link_error = f"SSL: {exc}"
        except Exception as exc:  # noqa: BLE001
            bm.link_status = 0
            bm.link_error = str(exc)[:120]


async def check_links(
    bookmarks: list[Bookmark],
    concurrency: int = LINK_CHECK_CONCURRENCY,
    progress_cb=None,
) -> None:
    """Check every bookmark URL concurrently.

    *progress_cb*, if provided, is called after each request finishes with
    the number of completed checks so far.
    """
    sem = asyncio.Semaphore(concurrency)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"
        ),
    }
    connector = aiohttp.TCPConnector(limit=concurrency, force_close=True)

    done_count = 0

    async def _wrapped(bm: Bookmark) -> None:
        nonlocal done_count
        await _check_one(bm, session, sem)
        done_count += 1
        if progress_cb:
            progress_cb(done_count)

    async with aiohttp.ClientSession(
        headers=headers, connector=connector
    ) as session:
        tasks = [asyncio.create_task(_wrapped(bm)) for bm in bookmarks]
        await asyncio.gather(*tasks)
