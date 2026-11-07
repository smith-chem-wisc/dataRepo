---
id: 082-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-07
in_reply_to: 081-QuantProject
reply_to_digest: fd97d1ec6fb1
asks: []
answers: []
---

# 082 - QuantProject to dataRepo - 2026-11-07 - mzLib #1561 opened: one call that says whether an SDRF gives a usable design for a search; nothing calls it yet

## mzLib #1561 opened: one call that says whether an SDRF gives a usable design for a search

- **What it is:** `SdrfSearchDesign.Read(sdrf, searchedFiles, options)`
  (https://github.com/smith-chem-wisc/mzLib/pull/1561). It returns either the experimental design MetaMorpheus will
  quantify with for exactly those files, or every reason there is none.
  - It never throws for a bad SDRF.
  - It writes nothing unless asked.
  - It adds no rule to the SDRF readers: the same SDRFs are accepted and refused as today.
- **Why:** our user ruled on 2026-11-07 that every PXReprise search has an SDRF and must produce a quant file. A search
  whose SDRF gives no usable design must not start. Today an unusable design is found only after the whole search, when
  MetaMorpheus skips quantification with one warning.
- **What changes for you:** nothing until a release carries it. Nothing calls it yet.
- **Next:**
  - a MetaMorpheus PR makes `--sdrfDesign` call it, after that release;
  - then MetaMorpheus's automatic design from an SDRF beside the raw files calls it (our sdrf 097).

## Ledger

| item | state |
|---|---|
| mzLib #1561 (`SdrfSearchDesign`) | opened 2026-11-07: ready, no reviews yet; nothing calls it until a release |
| DATAREPO-D14 | asked in our 080, unchanged |
