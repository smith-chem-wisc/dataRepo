"""Entry point PyInstaller freezes into the `datarepo` executable (tools/build_binary.py)."""
import sys

from datarepo.cli import main

if __name__ == "__main__":
    sys.exit(main())
