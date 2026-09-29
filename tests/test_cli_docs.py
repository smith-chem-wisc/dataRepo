"""docs/cli.md is generated from the argument parser, and must match it.

The command reference is only worth reading if it cannot describe a flag that does not exist. It is
rendered from `datarepo.cli.build_parser()` by `tools/build_cli_docs.py`; this test is the CI check,
here rather than in the schema job because rendering needs the package installed.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tool():
    spec = importlib.util.spec_from_file_location("build_cli_docs", ROOT / "tools" / "build_cli_docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_command_reference_matches_the_parser():
    tool = _tool()
    assert tool.OUT.read_text(encoding="utf-8") == tool.render(), (
        "docs/cli.md is stale: run python tools/build_cli_docs.py"
    )


def test_every_command_is_documented_in_a_group():
    # render() refuses a command missing from GROUPS; calling it is the assertion.
    assert "### `datarepo publish`" in _tool().render()
