"""Build the self-contained `datarepo` executable for this platform (D36, PXReprise PXR-D1).

    python tools/build_binary.py                 # dist/datarepo-<version>-<platform>.zip (.tar.gz off Windows)
    python tools/build_binary.py --allow-dirty   # a local test build, stamped with NO commit

A user of the result needs no Python: the zip holds `datarepo/datarepo[.exe]` with the interpreter,
duckdb, pyarrow, pyMzLib and its mzLib bridge inside it. Run it from the environment you want frozen
(`pip install ".[readers,mcp]" pyinstaller`), on each platform you ship: PyInstaller does not
cross-compile, which is why `.github/workflows/binaries.yml` runs one job per OS.

**The build stamp is the binary's identity.** A frozen program has no pip record, so
`runner.install_identity` reads `datarepo/_build_info.json` instead: the commit, version and platform.
From a tree with uncommitted changes the commit is left out rather than written, because a commit
that does not describe the code would be a false identity; `datarepo run` then refuses the binary,
and `datarepo doctor` says it is unidentified. That is the point of `--allow-dirty`: a test build you
can run, which cannot pass for a release.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "tools" / "packaging" / "entry.py"


def platform_tag() -> str:
    system = {"win32": "windows", "darwin": "macos"}.get(sys.platform, sys.platform)
    machine = platform.machine().lower()
    machine = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64"}.get(machine, machine)
    return f"{system}-{machine}"


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-dirty", action="store_true",
                    help="build from uncommitted changes; the binary is stamped with no commit")
    ap.add_argument("--out", default=str(ROOT / "dist"), help="where the zip goes")
    args = ap.parse_args()

    sys.path.insert(0, str(ROOT / "src"))
    from datarepo import __version__  # noqa: PLC0415

    dirty = bool(git("status", "--porcelain"))
    if dirty and not args.allow_dirty:
        print("refused: the working tree has uncommitted changes, so no commit describes this "
              "build. Commit first, or pass --allow-dirty for an unidentified test build.")
        return 1
    tag = platform_tag()
    stamp = {
        "version": __version__,
        "commit": None if dirty else git("rev-parse", "HEAD"),
        "platform": tag,
        "python": platform.python_version(),
    }

    work = ROOT / "build" / "binary"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    info = work / "_build_info.json"
    info.write_text(json.dumps(stamp, indent=2) + "\n", encoding="utf-8")

    sep = ";" if sys.platform == "win32" else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller", str(ENTRY),
        "--name", "datarepo", "--onedir", "--noconfirm", "--clean", "--console",
        "--distpath", str(work / "dist"), "--workpath", str(work / "pyi"), "--specpath", str(work),
        "--add-data", f"{info}{sep}datarepo",
        # The whole package, since modules are imported lazily by subcommand.
        "--collect-submodules", "datarepo",
        # pyMzLib's bridge executable and its .NET payload are package data.
        "--collect-all", "pymzlib",
        # The MCP SDK's server side, which is all `datarepo mcp` imports. Not `--collect-all mcp`:
        # that also pulls the SDK's optional CLI, which needs `typer`, which is not installed.
        "--collect-submodules", "mcp.server", "--collect-submodules", "mcp.shared",
        "--collect-submodules", "mcp.types", "--collect-data", "mcp", "--copy-metadata", "mcp",
        # importlib.metadata must still answer for these: `doctor`, `--version` and the runner ask it.
        "--copy-metadata", "datarepo", "--copy-metadata", "mzlib",
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    folder = work / "dist" / "datarepo"
    # A zip on Windows, a .tar.gz elsewhere. Zip tools disagree about restoring Unix permissions
    # (Python's zipfile never does), and an unpacked mzLib bridge that is not executable fails every
    # ingest with "Permission denied": the first CI run of the smoke test, on all three Unix builds.
    if sys.platform == "win32":
        archive = out / f"datarepo-{__version__}-{tag}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(folder.rglob("*")):
                z.write(path, Path("datarepo") / path.relative_to(folder))
    else:
        archive = out / f"datarepo-{__version__}-{tag}.tar.gz"
        with tarfile.open(archive, "w:gz") as t:
            t.add(folder, arcname="datarepo")
    print(f"wrote {archive} ({archive.stat().st_size / 1e6:.0f} MB), commit {stamp['commit'] or 'NONE (dirty)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
