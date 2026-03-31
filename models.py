from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Bookmark:
    url: str
    title: str
    add_date: int = 0
    icon: str = ""
    folder_path: list[str] = field(default_factory=list)
    new_category: str = ""
    is_duplicate: bool = False
    link_status: int = 0  # HTTP status code; 0 = unchecked
    link_error: str = ""

    @property
    def normalized_url(self) -> str:
        """Lazy accessor – actual normalization lives in dedup module."""
        from dedup import normalize_url

        return normalize_url(self.url)

    @property
    def original_folder(self) -> str:
        return "/".join(self.folder_path) if self.folder_path else ""
