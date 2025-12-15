from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_POSTS = ROOT / "archive" / "posts"
README = ROOT / "README.md"


@dataclass
class Post:
    slug: str
    path: str
    title: str
    published_iso: str | None
    published_display: str | None

    @property
    def sort_key(self) -> tuple:
        dt = None
        if self.published_iso:
            try:
                dt = datetime.strptime(self.published_iso, "%Y-%m-%d")
            except ValueError:
                dt = None
        # Sort by date desc, then by slug desc as a stable fallback
        return ((dt is not None, dt or datetime.min), self.slug)


def iter_posts() -> List[Post]:
    posts: List[Post] = []
    if not ARCHIVE_POSTS.is_dir():
        raise SystemExit(f"Missing posts directory: {ARCHIVE_POSTS}")

    for entry in sorted(ARCHIVE_POSTS.iterdir()):
        if not entry.is_dir():
            continue
        index_md = entry / "index.md"
        if not index_md.is_file():
            continue

        post_json = entry / "post.json"
        title = entry.name
        published_iso: str | None = None
        published_display: str | None = None

        if post_json.is_file():
            try:
                data = json.loads(post_json.read_text(encoding="utf-8"))
                title = data.get("title") or title
                # Some of the metadata is already formatted; prefer front matter if present
                if "date" in data:
                    published_display = data["date"]
            except Exception:
                pass

        # Prefer front matter in index.md for canonical date fields
        try:
            with index_md.open("r", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("published:"):
                        # Example: published: '2006-03-13'
                        value = line.split(":", 1)[1].strip().strip("'\"")
                        published_iso = value or None
                    elif line.startswith("published_display:"):
                        value = line.split(":", 1)[1].strip()
                        value = value.strip("'\"")
                        if value:
                            published_display = value
                    if published_iso and published_display:
                        break
        except FileNotFoundError:
            pass

        posts.append(
            Post(
                slug=entry.name,
                path=f"archive/posts/{entry.name}/index.md",
                title=title,
                published_iso=published_iso,
                published_display=published_display,
            )
        )

    # Sort newest first based on date (descending)
    posts.sort(key=lambda p: p.sort_key, reverse=True)
    return posts


def parse_readme_links(readme_text: str) -> tuple[Dict[str, str], int, int]:
    """
    Return (path_to_text, start_idx, end_idx) for the Archived Posts bullet list.
    """
    lines = readme_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "## Archived Posts":
            start = i
            break
    if start is None:
        raise SystemExit("Could not find '## Archived Posts' section in README.md")

    # List starts after the header and any blank line
    list_start = start + 1
    while list_start < len(lines) and not lines[list_start].lstrip().startswith("- ["):
        list_start += 1

    path_to_text: Dict[str, str] = {}
    i = list_start
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if not stripped.startswith("- ["):
            break
        # Very simple markdown link parser for lines like:
        # - [Title (Date)](archive/posts/slug/index.md)
        try:
            open_bracket = stripped.index("[")
            close_bracket = stripped.index("]", open_bracket + 1)
            open_paren = stripped.index("(", close_bracket + 1)
            close_paren = stripped.index(")", open_paren + 1)
        except ValueError:
            i += 1
            continue

        text = stripped[open_bracket + 1 : close_bracket]
        path = stripped[open_paren + 1 : close_paren]
        path_to_text[path] = text
        i += 1

    list_end = i
    return path_to_text, list_start, list_end


def build_display_text(post: Post, existing_text: str | None) -> str:
    if existing_text:
        return existing_text

    # Use canonical published_display if present, else derive from ISO date.
    date_display = post.published_display
    if not date_display and post.published_iso:
        try:
            dt = datetime.strptime(post.published_iso, "%Y-%m-%d")
            # Example: Mon, 13th March 2006
            dow = dt.strftime("%a")
            day = dt.day
            if 10 <= day % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
            month = dt.strftime("%B")
            date_display = f"{dow}, {day}{suffix} {month} {dt.year}"
        except ValueError:
            date_display = None

    if date_display:
        return f"{post.title} ({date_display})"
    return post.title


def sync_readme() -> None:
    readme_text = README.read_text(encoding="utf-8")
    path_to_text, list_start, list_end = parse_readme_links(readme_text)

    posts = iter_posts()

    lines = readme_text.splitlines()
    before = lines[:list_start]
    after = lines[list_end:]

    new_list_lines: List[str] = []
    for post in posts:
        display_text = build_display_text(post, path_to_text.get(post.path))
        new_list_lines.append(f"- [{display_text}]({post.path})")

    updated_lines = before + new_list_lines + after
    README.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sync_readme()



