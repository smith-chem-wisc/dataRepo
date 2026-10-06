# NOTE from the user (via the E:\CodeReview sweep) → dataRepo, 2026-10-06

**Request (user, 2026-10-06): settle DATAREPO-Q2 by talking directly with sdrf and QuantProject.**

DATAREPO-Q2 (your 019 to QuantProject) asks which definition ids, row keys, rule and release fraction-combined
values will use. QuantProject read it but did not answer, and passed it to the user. The user doesn't want to
be the go-between: **post to both the sdrf and QuantProject threads** (`threads.py new --to sdrf`, `--to
QuantProject`), name all three parties in each message so the answers line up, and work it out with them.
Bring the user only a disagreement the three of you can't settle.

Context the others already have:
- Fraction combining is ptmQtl's mzLib #1430 (`CombineRuns` / `CombineObservations`, combines a sample's
  fractions before site occupancy).
- QuantProject owns the `DEF-*` definitions (`design/DATA-DEFINITIONS.md`); sdrf owns which SDRF rows are one
  sample. QuantProject and sdrf have both been told you will write.
