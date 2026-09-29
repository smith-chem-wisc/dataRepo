"""Every relative link in the README and docs/ resolves: the file exists, and so does the heading.

Documentation rots first at its links: a page is renamed, a heading reworded, and the link that
pointed at it still renders as a link. Anchors follow GitHub's rule for heading ids: lower-case,
punctuation other than hyphens and underscores dropped, spaces to hyphens.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", *sorted((ROOT / "docs").rglob("*.md"))]
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^(```|~~~)")


def _slug(heading: str) -> str:
    text = re.sub(r"[`*_]|<[^>]+>", "", heading).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def _anchors(page: Path) -> set[str]:
    anchors, seen, fenced = set(), {}, False
    for line in page.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line.strip()):
            fenced = not fenced
            continue
        if fenced or not line.startswith("#"):
            continue
        slug = _slug(line.lstrip("#"))
        n = seen.get(slug, 0)
        anchors.add(slug if n == 0 else f"{slug}-{n}")
        seen[slug] = n + 1
    return anchors


def _links(page: Path):
    fenced = False
    for line in page.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line.strip()):
            fenced = not fenced
            continue
        if not fenced:
            yield from LINK.findall(line)


@pytest.mark.parametrize("page", PAGES, ids=lambda p: str(p.relative_to(ROOT)))
def test_every_relative_link_resolves(page):
    broken = []
    for target in _links(page):
        if re.match(r"^[a-z]+:", target) or target.startswith("//"):
            continue  # http(s), mailto: checked by nobody here, on purpose
        path, _, anchor = target.partition("#")
        dest = (page.parent / path).resolve() if path else page
        if not dest.exists():
            broken.append(f"{target} (no such file)")
        elif anchor and dest.suffix == ".md" and anchor not in _anchors(dest):
            broken.append(f"{target} (no such heading)")
    assert not broken, broken
