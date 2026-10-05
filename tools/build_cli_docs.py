"""Generate docs/cli.md, the command reference, from the C# `datarepo` executable's own help.

    python tools/build_cli_docs.py                      # build the CLI, then (re)write docs/cli.md
    python tools/build_cli_docs.py --check              # exit 1 if the page is stale
    python tools/build_cli_docs.py --exe <datarepo>     # use an already-built executable

The program is the single source of truth: the page is `datarepo -h` and `datarepo <command> -h`, run
for every command, so the reference cannot describe a flag that does not exist. Without `--exe` the
CLI is built once with `dotnet build` into a temporary folder (the .NET 10 SDK is needed). CI runs
`--check` in the dotnet job, against the CLI it has just built. The help text lives in
`dotnet/src/DataRepo.Cli` (`Cli.Summaries` and each command's `Args.Spec`), with `mcp`'s and `site`'s
in `DataRepo.Mcp.McpCommand` and `DataRepo.Site.SiteCommand`.

(This is documentation tooling, so it may stay Python; the product is C#.)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "cli.md"
PROJECT = ROOT / "dotnet" / "src" / "DataRepo.Cli"

#: The order a reader meets the commands in, grouped by who runs them. Every command `datarepo -h`
#: lists must appear here exactly once; `render` refuses otherwise, so a new command cannot go
#: undocumented.
GROUPS: list[tuple[str, str, list[str]]] = [
    (
        "Check the machine",
        "Run first on a new machine.",
        ["doctor"],
    ),
    (
        "Ingest: a producer's run becomes a bundle",
        "An instance operator runs these once per dataset, after the search. See "
        "[ingest.md](ingest.md) and [study.md](study.md).",
        ["manifest", "ingest", "inspect", "study", "run"],
    ),
    (
        "Build and publish: bundles become a catalog and a site",
        "`publish` is `build` then `site` in one step. See [build.md](build.md), [site.md](site.md) "
        "and [operating.md](operating.md).",
        ["publish", "build", "site", "catalog"],
    ),
    (
        "Ask: read a catalog",
        "See [querying.md](querying.md) and [mcp.md](mcp.md).",
        ["query", "mcp"],
    ),
]

#: What the help text cannot say in one line: behaviour a calling script depends on.
NOTES: dict[str, str] = {
    "manifest": (
        "A dataset with a `run_enrichment` map is checked the way `ingest` would check it, against "
        "the run folder when it is reachable. A map `ingest` would refuse is printed as `REFUSED` and "
        "the command exits `1`, so a wrong map is found before a re-ingest."
    ),
    "ingest": (
        "With `--json`, standard output carries exactly one JSON object and nothing else; the human "
        "report goes to standard error. Its keys: `datarepo` (the version), `ok`, `exit_code`, "
        "`reasons`, and `datasets`, one per accession, each with `accession`, `status` (`ingested`, "
        "`unchanged`, `excluded`, `refused` or `error`) and `reasons`, plus for a written bundle "
        "`bundle_id`, `bundle_path`, `tables` (row counts), `checks`, `mismatches`, "
        "`unresolved_modifications`, `unmatched_runs` and `findings` (the open warning codes)."
    ),
    "run": "A development build (version `0.0.0-dev`, or no recorded commit) is refused: see "
           "[operating.md](operating.md#1-install-one-released-version).",
}


def build_cli() -> Path:
    """Build the CLI once into a temporary folder and return the executable's path."""
    out = Path(tempfile.mkdtemp(prefix="datarepo-cli-docs-"))
    subprocess.run(
        ["dotnet", "build", str(PROJECT), "-c", "Release", "-o", str(out), "-v", "quiet", "-nologo"],
        check=True, stdout=subprocess.DEVNULL,
    )
    exe = out / ("datarepo.exe" if os.name == "nt" else "datarepo")
    if not exe.exists():
        raise SystemExit(f"dotnet build wrote no {exe.name} in {out}")
    return exe


def help_text(exe: Path, *args: str) -> str:
    result = subprocess.run([str(exe), *args, "-h"], capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise SystemExit(f"`datarepo {' '.join(args)} -h` exited {result.returncode}: {result.stderr}")
    return result.stdout.replace("\r\n", "\n").rstrip("\n")


def _summaries(top: str) -> dict[str, str]:
    """The `commands:` block of `datarepo -h`: command -> one line."""
    lines = top.split("\n")
    start = lines.index("commands:") + 1
    found = {}
    for line in lines[start:]:
        if not line.startswith("  "):
            break
        name, _, summary = line.strip().partition(" ")
        found[name] = summary.strip()
    return found


def _cell(text: str) -> str:
    text = " ".join(text.split()).replace("|", "\\|")
    return text.replace("<", "&lt;").replace(">", "&gt;")


def render(exe: Path) -> str:
    summaries = _summaries(help_text(exe))
    listed = [name for _, _, names in GROUPS for name in names]
    missing = sorted(set(summaries) - set(listed))
    extra = sorted(set(listed) - set(summaries))
    if missing or extra or len(listed) != len(set(listed)):
        raise SystemExit(
            f"GROUPS in tools/build_cli_docs.py is out of step with `datarepo -h`: "
            f"undocumented {missing}, unknown {extra}"
        )

    out = [
        "<!-- GENERATED by tools/build_cli_docs.py from `datarepo <command> -h`. "
        "Do not edit by hand. -->\n\n",
        "# Command reference\n\n",
        "Every `datarepo` command, with every argument it takes. This page is generated from the "
        "program's own help, so it lists exactly what the executable accepts; "
        "`datarepo <command> -h` prints the same text.\n\n",
        "New here? Start with [getting-started.md](getting-started.md), which runs the main "
        "commands end to end on the example instance shipped in this repository.\n\n",
        "| Command | What it does |\n|---|---|\n",
    ]
    for _, _, names in GROUPS:
        for name in names:
            out.append(f"| [`{name}`](#datarepo-{name}) | {_cell(summaries[name])} |\n")
    out.append(
        "\n`datarepo --version` prints the version. A release build says its version (`datarepo X.Y.Z`); "
        "a build from source says `0.0.0-dev`.\n\n"
        "**Exit status.** `0` when the command did what it was asked, including a no-op it reports "
        "(an unchanged bundle or catalog, a delivery already written). `1` when it refused: a dataset "
        "the manifest excludes, a check that failed, a file that does not match its record. The reason "
        "is on standard error. `2` for a command line it cannot parse.\n"
    )
    for title, lede, names in GROUPS:
        out.append(f"\n## {title}\n\n{lede}\n")
        for name in names:
            summary = summaries[name]
            out.append(f"\n### `datarepo {name}`\n\n{summary[:1].upper()}{summary[1:]}.\n\n")
            out.append(f"```text\n{help_text(exe, name)}\n```\n")
            if name in NOTES:
                out.append(f"\n{NOTES[name]}\n")
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if docs/cli.md is stale")
    ap.add_argument("--exe", type=Path, help="a built datarepo executable; default: build one")
    args = ap.parse_args()
    exe = args.exe or build_cli()
    text = render(exe)
    if args.check:
        current = OUT.read_text(encoding="utf-8").replace("\r\n", "\n") if OUT.exists() else ""
        if current != text:
            print("stale, run python tools/build_cli_docs.py: docs/cli.md")
            return 1
        print("docs/cli.md is current")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
