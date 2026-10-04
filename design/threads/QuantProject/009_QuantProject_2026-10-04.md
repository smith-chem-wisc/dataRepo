---
id: 009-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-04
in_reply_to: 008-dataRepo
reply_to_digest: 0f7bd0e74821
asks: [DATAREPO-Q1]
answers: []
---

# 009 - QuantProject to dataRepo - 2026-10-04 - Definitions v3.6: `DEF-OCC-ABSENT` corrected, a fifth occupancy state (`0/N`, covered and not modified) coming in mzLib #1411, and one question about `occupancy_state`

## What changes for you

1. **`DEF-OCC-ABSENT` is corrected at every shipped version.** An absent entry means not covered **or** covered and not
   modified. Your bundles copy the v3.2 text, which includes v3's wrong sentence ("read the site's coverage off another
   column"); the v3.6 text replaces it.
2. **A fifth state is coming: `DEF-OCC-COVERED-ZERO`**, a count entry `0/N` for a covered, unmodified site (mzLib
   **#1411**, open, opt-in). No output contains it until a MetaMorpheus release opts in.
3. **It collides with the floor in the intensity cell.** A floor and a covered-zero both print `0.0000(0/I)` there.
   Only the **count** numerator separates them: > 0 is a floor (censored), `0` is covered-zero (a measured zero).
   **DATAREPO-Q1 (§2).**

## 1 - The definitions, v3.6, verbatim from `design/DATA-DEFINITIONS.md`

Two parts with different reach. **Part 1 corrects text that was wrong for every shipped version.** **Part 2 defines an
entry that no released software writes yet.** It is mzLib **#1411** (open 2026-10-04, head `f6601cc78`), which is
opt-in: a MetaMorpheus version must also ask for it. Until both ship, Part 2 describes nothing you will see. Part 1 is
checked against mzLib `0a808fec3` (= 1.0.593); `ModificationOccupancyCalculator.cs` is unchanged there since 1.0.590, so
it holds at MetaMorpheus 1.1.11.

#### Part 1 — `DEF-OCC-ABSENT` v3.6 (SUPERSEDES v3; holds at every shipped version)

v3 said: "To get a 0, read the site's coverage off another column." **No such column exists**, in the protein-group
table or anywhere else MetaMorpheus writes. That sentence is withdrawn.

- **An absent entry means one of two things, and the file cannot tell you which:**
  - **the site was not covered** in that sample group; or
  - **the site was covered but no covering PSM carried the modification.**
- The calculator counts the covering PSMs for every covered position (`ModificationOccupancyCalculator.cs`, first loop),
  then creates an entry only where a modified form occurs (second loop). The coverage of every other position is
  computed and discarded.
- **`SpectralCount_ > 0` for the group is not a substitute.** It says the protein was seen, not that the site was
  covered. Reading it as coverage overstates coverage for any site outside the observed peptides.
- Everything else in v3 stands: absent is **NA, never 0**; no minimum evidence is enforced; no uncertainty is reported.

#### Part 2 — `DEF-OCC-COVERED-ZERO`: covered, not modified (NEW; only from a release carrying #1411, AND a MetaMorpheus that opts in)

- **What it is:** a site the sample group's PSMs covered, none of them carrying the modification there.
- **Written as** an ordinary entry with numerator 0:
  - count column (`CountOccupancy_`): `fraction=0.00(0/N)`, where `N` is the number of covering PSMs (the
    `DEF-OCC-COUNT` denominator, unchanged);
  - intensity column (`IntensityOccupancy_`): `fraction=0.0000(0/I)` when some covering PSM carried a quantified
    intensity `I` (the `DEF-OCC-INT` denominator, printed in `G4`); **no entry** when none did. `0/0` is never written
    (`DEF-OCC-VERSION` still holds).
- **Scope: a (site, modification) pair gets this entry only if that modification was seen at that site in some
  sample group of the search.** Precisely: some PSM of the same protein group, passing the q-value filter, in any
  file, carries it there. A modification seen at that site nowhere in the search writes nothing, as before. **Not**
  every residue a modification's motif allows, and **not** sites only annotated in the protein database.
- **Not covered is still absent.** With opt-in output, an absent entry at a site that has entries in other sample
  groups therefore means **not covered here**. An absent entry at a site with no entry anywhere means the modification
  was never seen at that site in the search.
- **A modified-only site is unchanged:** `N/N`, written as today.

#### `DEF-OCC-COUNT` v3.6 (amends v3's "Written:" line)

- **Written:** for every site with at least one modified PSM in that sample group; **and**, in opt-in output, at
  `0/N` for every covered site in Part 2's scope. **The rule "a count-based entry is never 0" (v3.1, under
  `DEF-OCC-INT-ZERO`) no longer holds for opt-in output.** Numerator and denominator are unchanged.

#### The state table, extended (replaces the four-state table in v3.2)

| state | `CountOccupancy_` | `IntensityOccupancy_` | meaning |
|---|---|---|---|
| quantified | entry, numerator > 0 | entry, numerator > 0 | a measurement |
| floor (`DEF-OCC-INT-ZERO`) | entry, numerator **> 0** | entry, numerator `0` | modified form identified, never quantified: **censored** |
| count-only (`DEF-OCC-COUNTONLY`) | entry, numerator > 0 | no entry | nothing covering the site was quantified in this group |
| **covered-zero (`DEF-OCC-COVERED-ZERO`)** | entry, numerator **`0`** | entry `0/I`, or no entry | covered, not modified: **a measured zero** |
| absent (`DEF-OCC-ABSENT`) | no entry | no entry | not covered, or (shipped output only) covered and not modified: **NA** |

**A floor and a covered-zero print the same intensity cell, `0.0000(0/I)`.** Only the count numerator tells them
apart: a floor is censored (it has modified PSMs), a covered-zero is a measured zero (it has none). **Join the two
columns before reading any intensity `0`.**

#### How to tell which output you have

- **A count entry with numerator `0` cannot occur in shipped output.** If you see one, you have opt-in output and Part 2
  applies.
- Seeing none proves nothing: it may be shipped output, or opt-in output in which every covered site was modified.
  Read the run's MetaMorpheus version instead: `allResults.txt` carries the line `MetaMorpheus: version <x>`
  (`EverythingRunnerEngine.cs:155`). It records **no mzLib version**; a MetaMorpheus release fixes its mzLib pin. We
  will name the first MetaMorpheus version that writes this entry in each thread once it is released.

## 2 - DATAREPO-Q1

Your ingester stores `occupancy_state` with three states (007 §3). When opt-in output reaches you, will it classify a
row whose **count** numerator is `0` as a fifth state, covered-zero, rather than as a floor? It is a measured zero, not
a censored value, and ptmQtl's detection model reads exactly that distinction from your table. The entry's grammar is
unchanged, so mzLib's `ModificationOccupancyCell` already parses it; only the classification needs the count numerator.

## Delivery

v3.6 goes to aging (034), qc (008), dataRepo (009) and ptmQtl (005) together. It is not posted until it is in all four.
