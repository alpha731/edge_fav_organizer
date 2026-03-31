"""Generate a Netscape Bookmark HTML file from classified bookmarks."""

from __future__ import annotations

import html
import time
from collections import defaultdict
from pathlib import Path

from models import Bookmark

_HEADER = """\
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
"""


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


def _bookmark_line(bm: Bookmark, indent: int) -> str:
    pad = "    " * indent
    parts = [f'{pad}<DT><A HREF="{_escape(bm.url)}"']
    if bm.add_date:
        parts.append(f' ADD_DATE="{bm.add_date}"')
    if bm.icon:
        parts.append(f' ICON="{bm.icon}"')
    parts.append(f">{_escape(bm.title)}</A>")
    return "".join(parts)


def generate_html(
    bookmarks: list[Bookmark],
    output_path: str | Path,
    *,
    exclude_duplicates: bool = True,
    exclude_broken: bool = False,
) -> None:
    """Write a browser-importable Netscape Bookmark HTML file.

    Bookmarks are organised into folders according to ``new_category``.
    Categories containing ``/`` produce nested folders
    (e.g. ``Programming/C++`` -> ``Programming`` > ``C++``).
    """
    # Filter
    filtered = [
        bm
        for bm in bookmarks
        if (not exclude_duplicates or not bm.is_duplicate)
        and (not exclude_broken or bm.link_status == 0 or bm.link_status < 400)
    ]

    # Group by category hierarchy
    tree: dict[str, dict[str, list[Bookmark]]] = defaultdict(lambda: defaultdict(list))
    for bm in filtered:
        parts = bm.new_category.split("/", 1) if "/" in bm.new_category else [bm.new_category]
        top = parts[0]
        sub = parts[1] if len(parts) > 1 else ""
        tree[top][sub].append(bm)

    now = str(int(time.time()))
    lines: list[str] = [_HEADER, "<DL><p>"]

    # Wrap everything in a toolbar folder so Edge imports into 收藏夹栏
    lines.append(
        f'    <DT><H3 ADD_DATE="{now}" LAST_MODIFIED="{now}" '
        f'PERSONAL_TOOLBAR_FOLDER="true">收藏夹栏</H3>'
    )
    lines.append("    <DL><p>")

    for top_folder in sorted(tree):
        lines.append(f'        <DT><H3 ADD_DATE="{now}" LAST_MODIFIED="{now}">{_escape(top_folder)}</H3>')
        lines.append("        <DL><p>")

        subs = tree[top_folder]
        for sub_folder in sorted(subs):
            bms = subs[sub_folder]
            bms.sort(key=lambda b: b.add_date)

            if sub_folder:
                lines.append(f'            <DT><H3 ADD_DATE="{now}" LAST_MODIFIED="{now}">{_escape(sub_folder)}</H3>')
                lines.append("            <DL><p>")
                for bm in bms:
                    lines.append(_bookmark_line(bm, indent=4))
                lines.append("            </DL><p>")
            else:
                for bm in bms:
                    lines.append(_bookmark_line(bm, indent=3))

        lines.append("        </DL><p>")

    lines.append("    </DL><p>")
    lines.append("</DL><p>")
    lines.append("")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
