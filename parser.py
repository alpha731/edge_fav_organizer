"""Parse Netscape Bookmark HTML into a list of Bookmark objects."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

from models import Bookmark


class _BookmarkHTMLParser(HTMLParser):
    """State-machine parser for the Netscape Bookmark file format."""

    def __init__(self) -> None:
        super().__init__()
        self.bookmarks: list[Bookmark] = []
        self._folder_stack: list[str] = []
        self._current_tag: str = ""
        self._current_attrs: dict[str, str] = {}
        self._text_buf: str = ""
        self._in_h3 = False
        self._in_a = False

    # ── callbacks ────────────────────────────────────────────────────────

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_dict = {k.lower(): (v or "") for k, v in attrs}

        if tag == "h3":
            self._in_h3 = True
            self._text_buf = ""
            self._current_attrs = attr_dict

        elif tag == "a":
            self._in_a = True
            self._text_buf = ""
            self._current_attrs = attr_dict

        elif tag == "dl":
            pass  # depth tracked via <h3>

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag == "h3" and self._in_h3:
            folder_name = self._text_buf.strip()
            self._folder_stack.append(folder_name)
            self._in_h3 = False

        elif tag == "a" and self._in_a:
            title = self._text_buf.strip()
            url = self._current_attrs.get("href", "")
            add_date_str = self._current_attrs.get("add_date", "0")
            try:
                add_date = int(add_date_str)
            except ValueError:
                add_date = 0
            icon = self._current_attrs.get("icon", "")
            self.bookmarks.append(
                Bookmark(
                    url=url,
                    title=title,
                    add_date=add_date,
                    icon=icon,
                    folder_path=list(self._folder_stack),
                )
            )
            self._in_a = False

        elif tag == "dl":
            if self._folder_stack:
                self._folder_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._in_h3 or self._in_a:
            self._text_buf += data

    def handle_entityref(self, name: str) -> None:
        char = {"amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'"}.get(
            name, f"&{name};"
        )
        if self._in_h3 or self._in_a:
            self._text_buf += char

    def handle_charref(self, name: str) -> None:
        try:
            char = chr(int(name, 16) if name.startswith("x") else int(name))
        except ValueError:
            char = f"&#{name};"
        if self._in_h3 or self._in_a:
            self._text_buf += char


def parse_bookmarks(filepath: str | Path) -> list[Bookmark]:
    """Read a Netscape Bookmark HTML file and return parsed bookmarks."""
    text = Path(filepath).read_text(encoding="utf-8")
    parser = _BookmarkHTMLParser()
    parser.feed(text)
    return parser.bookmarks
