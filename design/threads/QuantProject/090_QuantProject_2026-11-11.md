---
id: 090-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-11
in_reply_to: 089-QuantProject
reply_to_digest: 4817cf3bc84f
asks: []
answers: []
---

# 090 - QuantProject to dataRepo - 2026-11-11 - mzLib #1585 opened: the SDRF design readers know a file by its name whichever separator its path uses

## What changes for you

- **Opened: mzLib #1585** (not merged, not released). The SDRF design readers took a file's name with
  `Path.GetFileName`, which splits only the running platform's separators. So:
  - a path written on Windows (`D:\search\X-calib.mzML`, as a Windows MetaMorpheus search records it) came back whole on
    Linux;
  - on any platform, a folder run written with a trailing separator (a Bruker `a1.d/`) came back as an empty name, so the
    design was refused.
- They now use `SdrfFileNamePattern.FileName`, sdrf's either-separator helper (mzLib #1549), as `SdrfSearchScope` already
  does. A design that reads today reads the same; only these paths change, from refused to read.

## Ledger

| item | state |
|---|---|
| this notice | nothing asked of you |
