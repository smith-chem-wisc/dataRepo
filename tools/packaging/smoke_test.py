"""Run the getting-started tutorial with a built `datarepo` executable, and prove it is the same program.

    python tools/packaging/smoke_test.py <path to datarepo[.exe]> [--expect-commit SHA]

A binary is verified by running it, not by building it: every step of docs/getting-started.md runs
against a fresh copy of the example instance, with a PATH that holds no Python. Then the same steps
run through `python -m datarepo.cli` from the environment that built it, and the two must produce
the SAME bundle id and catalog id. Those ids hash every row's inputs, the schema and the ingester, so
equal ids mean the executable read and wrote exactly what the Python install does.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "tests" / "data"
BARE_PATH = r"C:\Windows\System32;C:\Windows" if sys.platform == "win32" else "/usr/bin:/bin"


def run(cmd: list[str], cwd: Path, *, bare: bool, expect: int = 0) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["NO_COLOR"] = "1"
    if bare:
        env["PATH"] = BARE_PATH
    done = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=1800)
    out = done.stdout + done.stderr
    if done.returncode != expect:
        raise SystemExit(f"FAILED ({done.returncode}, expected {expect}): {' '.join(cmd)}\n{out}")
    return out


def one(pattern: str, text: str) -> str:
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f"FAILED: no match for {pattern!r} in:\n{text}")
    return m.group(1)


def tutorial(datarepo: list[str], work: Path, *, bare: bool) -> dict[str, str]:
    inst = work / "example-instance"
    shutil.copytree(EXAMPLE, inst)
    ids = {}
    out = run([*datarepo, "ingest", "manifest.yaml", "PXD999999"], inst, bare=bare)
    ids["bundle"] = one(r"PXD999999[\\/]([0-9a-f]{16})", out)
    run([*datarepo, "ingest", "manifest.yaml", "PXD000000"], inst, bare=bare, expect=1)
    out = run([*datarepo, "publish", "manifest.yaml", "--site", "site", "--title", "Example"],
              inst, bare=bare)
    ids["catalog"] = one(r"id\s+([0-9a-f]{16})", out)
    assert (inst / "site" / "index.html").is_file(), "publish wrote no index.html"
    out = run([*datarepo, "publish", "manifest.yaml", "--site", "site", "--title", "Example"],
              inst, bare=bare)
    assert "unchanged" in out, f"a second publish rebuilt an unchanged catalog:\n{out}"
    out = run([*datarepo, "query", "catalog.duckdb", "SELECT n_psms_1pct FROM dataset_overview"],
              inst, bare=bare)
    ids["psms_1pct"] = one(r"\n\s*(\d+)\s*$", out)
    out = run([*datarepo, "mcp", "--catalog", "catalog.duckdb", "--check"], inst, bare=bare)
    assert ids["catalog"] in out, out
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("exe", help="the built datarepo executable")
    ap.add_argument("--expect-commit", help="the commit the build stamp must name")
    args = ap.parse_args()
    exe = str(Path(args.exe).resolve())

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "bin").mkdir()
        (tmp / "py").mkdir()
        version = run([exe, "--version"], tmp, bare=True).strip()
        doctor = run([exe, "doctor"], tmp, bare=True)
        assert "ready" in doctor, doctor
        if args.expect_commit:
            assert f"commit {args.expect_commit[:12]}" in doctor, doctor
        print(version)
        print(doctor)
        binary = tutorial([exe], tmp / "bin", bare=True)
        python = tutorial([sys.executable, "-m", "datarepo.cli"], tmp / "py", bare=False)
    print(f"executable: {binary}")
    print(f"python:     {python}")
    if binary != python:
        raise SystemExit("FAILED: the executable and the Python install disagree")
    print("OK: the executable runs the tutorial and matches the Python install id for id")
    return 0


if __name__ == "__main__":
    sys.exit(main())
