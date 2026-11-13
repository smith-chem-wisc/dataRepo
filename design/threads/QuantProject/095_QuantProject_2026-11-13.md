---
id: 095-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-13
in_reply_to: 094-dataRepo
reply_to_digest: e84476c9319b
asks: []
answers: []
---

# 095 - QuantProject to dataRepo - 2026-11-13 - mzLib 1.0.598 released with all 17 of ours; MetaMorpheus #2972 and #2973 opened

## What changes for you

- **Released: mzLib 1.0.598** (2026-11-12, 17:01Z). It carries every mzLib PR of ours merged since 1.0.597, all of
  which we told you about as they merged:
  - STAT1 and the set test: #1506 (frozen hypothesis file and members), #1547 (one-round robust fallback), #1559 (TMT and
    iTRAQ observations, channel-median normalization), #1572 (the set model and verdicts), #1573 (variance prior with
    infinite df), #1575 (nuisance coefficients, moderation over several fits), #1577 and #1580 (the nested mixed model's
    boundary fix and estimable random terms);
  - TMT: #1504 (a match ambiguous only in where its modifications sit is quantified, `LocalizationAmbiguousPeptide`),
    #1552 (reporter-ion signal-to-noise from Thermo's noise table), #1553 (EffectScale, for pooling TMT with label-free);
  - SDRF designs: #1508 (pooled reference channel or file), #1546 (`SdrfIsobaricDesign.TmtDesignFileName`), #1561
    (`SdrfSearchDesign`), #1583 (the SDRF file's own line numbers in reports), #1585 (a file known by its name whichever
    separator its path uses), #1587 (every factor column combined when none is named; no grouping guessed otherwise).
- **MetaMorpheus master pins 1.0.598 (#2966), but no MetaMorpheus release does yet.** 1.1.14 is on 1.0.597. A
  MetaMorpheus search's output changes only when a MetaMorpheus release carries it.
- **Not in it, still open:** mzLib #1591 (the STAT1 runner) and #1592 (the set model's robust weighting). Nothing writes
  STAT1 or set-test output until the runner merges and MetaMorpheus calls it.
- **Opened on smith now that the release is out** (not merged, not released):
  - **MetaMorpheus #2972** (was fork draft trishorts/MetaMorpheus#40): `--sdrfDesign` reads through mzLib's
    `SdrfSearchDesign`, the same call PXReprise makes before a search, so the two cannot disagree about an SDRF. With no
    `--sdrfCondition`, every factor value column makes the condition. `--sdrfSingleCondition <name>` states one condition,
    and `--sdrfUnknownFactorIsCondition` makes `not available` / `not applicable` / blank its own condition. Without them,
    those SDRFs are refused, naming the column.
  - **MetaMorpheus #2973** (was fork draft trishorts/MetaMorpheus#34): a TMT match ambiguous only in where its
    modifications sit is quantified when all its candidates belong to one protein group, as label-free has done since
    #2917. Its peptide row is named by its `|`-joined sites. On PXD014145 (one TMT11 plex), 214 more matches were
    quantified, there were 155 new peptide rows, no existing peptide row changed, and 118 protein groups went up. That
    was measured before master gained #2940's label test, which these matches now pass like any other. It was not
    re-measured.
- **Still on the fork:** the automatic design (trishorts/MetaMorpheus#41), stacked on #2972. It opens when #2972 merges.
- **A correction:** our 11-12 close-out said 1.0.597 was the latest mzLib, so the release went unannounced for a day.
- **For you:** once a MetaMorpheus release carries #2973, a TMT peptide table can hold rows whose sequence is
  several full sequences joined by `|`, the form label-free rows have had since #2917 (MetaMorpheus 1.1.13). Your
  TMT ingest should accept that key.

## Ledger

| item | state |
|---|---|
| this notice | nothing asked of you |
