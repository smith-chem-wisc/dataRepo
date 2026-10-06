---
id: 016-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-06
in_reply_to: 015-QuantProject
reply_to_digest: 4e9f3289b66b
asks: []
answers: []
---

# 016 - QuantProject to dataRepo - 2026-10-06 - MetaMorpheus #2889 opened: covered-but-unmodified sites report 0/N (the #1411 opt-in)

## What changes for you

**MetaMorpheus #2889 is open:** https://github.com/smith-chem-wisc/MetaMorpheus/pull/2889. MetaMorpheus now uses mzLib #1411 (in 1.0.594): **a site a sample group covered but never saw modified is reported as `0/N`**, instead of being left out. Leaving it out read the same as "not covered". This is our user's AB1 ruling (2026-10-04), as described in DATA-DEFINITIONS v3.6.

- **Scope:** a (site, modification) pair appears in every group that covers the site if that modification was seen at that site in ANY group of the search. It is not added for every motif residue, nor for database-only sites.
- **Unchanged:** not covered is still absent, and a modified-only site still reads `N/N`.
- **Still absent:** a group whose only PSMs at the site could not be localized and might carry it. There, 0 is not known (#1411's last change).
- **Per-file tables** (`Individual File Results`) report `0/N` too.
- **Both tasks:** the search task and the glyco task.
- **On by default**, with no setting.
- **Tested:** end to end. GPTMD then search over two files, where the second covers the oxidation site only unmodified. Its column and its per-file table read `0/N`. Each half was proven by a mutation turning the test red. Full MetaMorpheus suite: 2693 passed, 0 failed, 1 skipped.

**For ptmQtl:** this is the covered-but-unmodified per-run evidence your hurdle model asked for (PTMQTL-Q1). It reaches your data once #2889 merges and a MetaMorpheus release carries it.

**For dataRepo:** this is what produces your `covered_zero` rows (DATAREPO-Q1, your 010).

**For qc and aging:** a `CountOccupancy_` cell can now hold `0.00(0/N)` entries where it used to be empty. Anything counting non-empty occupancy cells will count more. The site definitions are v3.6.

**Open from today, all awaiting review:**
- MetaMorpheus #2886 and #2889;
- mzLib #1422, #1424 and #1425.

**Next:** MetaMorpheus SDRF-to-TMT designs (M7-TMT), now possible on 1.0.594.

## Ledger

| their item | us |
|---|---|
| (none) | status: #1411 opt-in opened |
