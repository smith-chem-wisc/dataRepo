"""docs/getting-started.md shows output it measured, and this keeps it that way.

The tutorial promises that a reader on its stated version gets the same ids it prints. A catalog id
hashes the package version, so every release silently falsified the page: 0.30.0's tutorial quoted a
0.29.0 catalog id, and a stranger running it found the mismatch before we did. This runs the
tutorial's own commands on the example instance and fails when the page and the program disagree.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from conftest import needs_pymzlib

from datarepo import __version__
from datarepo.cli import main

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "getting-started.md"


@needs_pymzlib
def test_the_tutorial_prints_what_the_program_prints(tmp_path, monkeypatch, capsys):
    text = PAGE.read_text(encoding="utf-8")
    stated = re.search(r"was run on this example with datarepo (\S+?)\.\s", text)
    assert stated and stated.group(1) == __version__, (
        f"getting-started.md says it was run with datarepo {stated and stated.group(1)}, and this is "
        f"{__version__}: rerun the tutorial and update its output"
    )

    inst = tmp_path / "example-instance"
    shutil.copytree(ROOT / "tests" / "data", inst)
    monkeypatch.chdir(inst)
    assert main(["ingest", "manifest.yaml", "PXD999999"]) == 0
    bundle = re.search(r"PXD999999[\\/]([0-9a-f]{16})", capsys.readouterr().out).group(1)
    assert main(["publish", "manifest.yaml", "--site", "site", "--title", "Example repository",
                 "--purpose", "how a tutorial fixture behaves"]) == 0
    catalog = re.search(r"id\s+([0-9a-f]{16})", capsys.readouterr().out).group(1)

    quoted_bundles = set(re.findall(r"bundle\s+(?:…/store/PXD999999/)?([0-9a-f]{16})", text))
    quoted_catalogs = set(re.findall(r"(?:id|catalog)\s+([0-9a-f]{16})", text))
    assert quoted_bundles == {bundle}, f"page quotes bundle {quoted_bundles}, program wrote {bundle}"
    assert quoted_catalogs == {catalog}, f"page quotes catalog {quoted_catalogs}, program built {catalog}"
