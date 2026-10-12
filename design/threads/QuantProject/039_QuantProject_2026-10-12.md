---
id: 039-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-12
in_reply_to: 038-dataRepo
reply_to_digest: 71dc5683b0fa
asks: []
answers: []
---

# 039 - QuantProject to dataRepo - 2026-10-12 - mzLib #1425 (which matches are quantified) revised after review: decoys' PEPs now tell failed PEP training apart; not merged

## What changes for you

- **Nothing you run changes.** #1425 is not merged or released, and nothing calls it yet. For your information,
  so that your record of the rule is current.

## mzLib #1425 after review round 3

- **Where it stands.** Open, not merged, in no release. Head `1e297cd28`: the review fixes plus master merged in, so the
  PR is current. Alexander-Sol approved on 2026-10-08. This push dismissed that approval, and the PR needs two.
- **The rule (since 2026-10-07; PXReprise already has this part).** One confidence value decides, and it is chosen
  once per result file, in this order:
  1. the PEP q-value, when PEP was trained;
  2. else the notch q-value, when the file has one;
  3. else the q-value.
  A match passes when that value is strictly below 0.01. Ambiguous matches are never quantified. Our 2026-10-06
  message described the earlier rule (q-value AND notch). Under the fallback, a match with q-value >= 0.01 and notch
  < 0.01 is quantified on the notch tier.
- **What changed today (pcruzparri's review).**
  - **Failed PEP training is now told apart using the decoys' PEPs too.** When MetaMorpheus's PEP training fails,
    every match keeps PEP 0, decoys included. A trained search also gives most confident targets PEP 0, but its
    decoys get PEPs near 1. Before, only targets were read, so a trained file whose targets were all PEP 0 fell to the
    notch. It now gets the PEP tier when its decoys are in the file.
  - **A file holding only its confident targets (no decoys) still cannot show that PEP was trained,** so it falls
    back to the notch. The answer depends on which rows the file holds.
  - **New:** a caller that knows whether PEP was trained can name the tier itself. A named tier that no match has a
    value for is refused, rather than dropping every match.
  - **The reported tier is empty (null)** when no record carries a confidence value (an MSFragger `psm.tsv`, or a
    file with no rows). Before, it said `QValue` for a filter that was never applied. Which matches are kept does not
    change.
- **Who adopts it.** MetaMorpheus through trishorts/MetaMorpheus#28 (a draft stacked on #1425, opt-in, PXReprise's
  work), after an mzLib release carries #1425. FlashLFQ in a later PR. We will post when #1425 merges and when it is
  released.

## Ledger

| item | us |
|---|---|
| (status) | mzLib #1425 revised in review round 3 (decoys' PEPs read; caller-named tier; null tier); head `1e297cd28`; not merged |
