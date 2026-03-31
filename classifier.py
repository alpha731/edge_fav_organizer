"""Classify bookmarks into categories using the DeepSeek API (OpenAI-compatible)."""

from __future__ import annotations

import json
import logging
import textwrap

from openai import OpenAI

import config
from models import Bookmark

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = textwrap.dedent("""\
    You are a bookmark classification assistant.
    Given a list of bookmarks (each with an index, title, and URL), assign
    each bookmark to EXACTLY ONE category from the allowed list.

    Allowed categories:
    {categories}

    Reply with a JSON array of objects, each containing:
      {{ "idx": <int>, "category": "<category>" }}
    Nothing else — no markdown fences, no explanation.
""")


def _build_user_prompt(batch: list[tuple[int, Bookmark]]) -> str:
    lines = []
    for idx, bm in batch:
        lines.append(f'{idx}. [{bm.title}]({bm.url})')
    return "\n".join(lines)


def _parse_response(text: str, batch: list[tuple[int, Bookmark]]) -> None:
    """Parse the LLM JSON response and assign categories."""
    # Strip possible markdown code fences
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_nl = cleaned.index("\n")
        last_fence = cleaned.rfind("```")
        cleaned = cleaned[first_nl + 1 : last_fence].strip()

    try:
        items = json.loads(cleaned)
    except json.JSONDecodeError:
        log.warning("Failed to parse LLM response as JSON: %.200s", cleaned)
        return

    idx_map = {idx: bm for idx, bm in batch}
    for item in items:
        idx = item.get("idx")
        cat = item.get("category", "Other")
        if idx in idx_map:
            if cat in config.CATEGORIES:
                idx_map[idx].new_category = cat
            else:
                idx_map[idx].new_category = "Other"


async def classify_bookmarks(
    bookmarks: list[Bookmark],
    progress_cb=None,
) -> None:
    """Classify all bookmarks via DeepSeek in batches."""
    client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)

    indexed: list[tuple[int, Bookmark]] = [
        (i, bm) for i, bm in enumerate(bookmarks) if not bm.is_duplicate
    ]

    batch_size = config.CLASSIFIER_BATCH_SIZE
    total_batches = (len(indexed) + batch_size - 1) // batch_size
    system_msg = _SYSTEM_PROMPT.format(
        categories="\n".join(f"  - {c}" for c in config.CATEGORIES)
    )

    for batch_no in range(total_batches):
        start = batch_no * batch_size
        batch = indexed[start : start + batch_size]
        user_msg = _build_user_prompt(batch)

        try:
            resp = client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.0,
                max_tokens=2048,
            )
            content = resp.choices[0].message.content or ""
            _parse_response(content, batch)
        except Exception as exc:  # noqa: BLE001
            log.warning("DeepSeek API error on batch %d: %s", batch_no, exc)
            for _, bm in batch:
                if not bm.new_category:
                    bm.new_category = "Other"

        if progress_cb:
            progress_cb(batch_no + 1, total_batches)

    # Duplicates inherit the category of their canonical bookmark
    from dedup import normalize_url

    cat_map: dict[str, str] = {}
    for bm in bookmarks:
        if not bm.is_duplicate and bm.new_category:
            cat_map[normalize_url(bm.url)] = bm.new_category
    for bm in bookmarks:
        if bm.is_duplicate:
            bm.new_category = cat_map.get(normalize_url(bm.url), "Other")

    # Fallback
    for bm in bookmarks:
        if not bm.new_category:
            bm.new_category = "Other"
