# Open questions — take these to meetings

The running list of everything dataRepo needs a human answer to. I add a question the moment it
comes up. When you bring back an answer, I record it as a decision in `.project/state.yaml` and move
the row to **Answered** at the bottom.

Each question has a default. If no answer comes back, we build on the default, and any work that
depends on it is marked as such.

## For NCEMS (the operators who will run production — D1)

| ID | Question | Why it matters | Our default until answered |
|---|---|---|---|
| N1 | Do you host **public web services** (a website/API up all the time), or only compute jobs? | D1 hands production to you. If you only run batch jobs, we need a different host. | Assume yes; keep the package portable to any Linux host. |
| N2 | Can your servers run **Docker / Docker Compose**? Or only Apptainer/Singularity, as many HPC centres do? | Decides what we package. | Docker Compose; we would also test that it converts to Apptainer. |
| N3 | Will it get a **public URL with HTTPS** (a domain name, e.g. `aging.ncems.org`)? Who owns the name? | Citations, DOIs and the agents' MCP endpoint all point at this URL, so it must not change. | Placeholder URL; the address is configurable. |
| N4 | How much **disk** can the service have, and where? | We estimate a few GB of tables at ~300 datasets. Raw files are *not* hosted (PRIDE keeps them). | 50 GB, with room to grow. |
| N5 | Who runs **ingest** when aging finishes new datasets: you on a schedule, or we hand you a release? | Decides whether the server needs access to aging's output. | We build versioned releases; you deploy a release. |
| N6 | Who handles **rate limiting / abuse protection** in front of a public API (D2)? | Public and login-free means one runaway agent could swamp it. | Your reverse proxy does it; our code sets per-query limits (30 s, 1,000 rows). |
| N7 | **Backups and uptime.** What do you promise, and who do we call when it's down? | Agents and people will depend on it. | Best effort; every release can be rebuilt from its files. |
| N8 | **DOIs.** Does NCEMS mint them, or do we use Zenodo? | D2 says every release is citable. | Zenodo (free, GitHub-integrated, CC BY friendly). |
| N9 | Who is the **named operator contact** for the handover doc? | aging's D5 handover pattern needs a person. | Blank. |

## For you / the working group

| ID | Question | Our default until answered |
|---|---|---|
| U1 | D5 build order: build the table shape for DIA/TMT/rodent now, and the ingesters only when aging produces that data (**A**)? Or write the ingesters now against public example files (**B**)? | **A** (taken by default in the grill). |
| U2 | Does the working group agree to **public from day one** (D2), including age-effect results before the first paper? You decided this; this is only a check that co-leads (Schilling, Gladyshev, Mohanty) aren't surprised. | Public. |
| U5 | **How generic is "generic"?** You said to keep dataRepo "a bit more generic." My proposal: the **core** schema (dataset, sample, run, psm, peptidoform, quant, protein group, protein, provenance, finding, definition) knows nothing about aging, so any reanalysis project could use it. The aging-specific tables (`age_effect`, `organelle_age_summary`, and the age columns on `sample`) move to a pluggable **study layer** that a consumer project like aging supplies. The name, goal and first deployment stay aging's. | Core generic + aging as the first study layer. |
| U7 | **Namespacing definition IDs.** The schema's example is a bare ID (`DEF-QC-MBR`), but two registers already use overlapping codes (aging's `DEF-CONTAM-PSM` and QuantProject's `DEF-QC-9` both describe a contaminant share). The ingester writes `<owner>:<ID>`, e.g. `aging:DEF-PSM-1PCT`, `QuantProject:DEF-QC-MBR`. Is that the form the registers want to be cited by? | `<owner>:<ID>`. Numbers with no published definition use `PROVISIONAL:<NAME>` and say so in their own text. |
| U6 | D8 makes dataRepo code-only, with aging hosting the data. Does aging also **run the service** (the API/MCP server over its data, deployed by NCEMS as aging's), or does it only publish the data files and someone else runs the server? | aging owns the whole instance: the data, the releases/DOIs, and the deployed service. dataRepo ships a package that aging runs. |
| U8 | **What grain does a stored number have?** aging asked (their 014) whether per-run should be the default, after their dataset-level contaminant share of 7.0% hid a per-file spread of 2.6-18.9% structured by cell line. Our answer, now implemented and told to them in thread 018: **a number is stored at the grain at which it was measured, never coarser and never finer.** Never coarser, so a per-file measurement gets one row per file and the producer's own summaries are carried named as summaries. Never finer, because aging's per-file FDR numbers are a different calculation and must never be summed, so `psms_1pct` stays dataset-scope. And two grains of one quantity are two definitions, not one metric queried differently. Worth locking as a decision rather than leaving as a habit. | The rule above. It needs no schema change, and it only works where the producer's definition states a grain -- which is a small standing request on aging's and QuantProject's registers. |
| U9 | **Where does the modification-name → UNIMOD mapping come from?** The ingester parses mzLib's own resource files (`Mods/*.txt`, `Data/ptmlist.txt`) out of the searching MetaMorpheus install and reads the `DR Unimod;` lines itself. That is not the same as asking mzLib's loader: it never reads `Data/unimod.xml`, and it prefers `Mods.txt` where the loader prefers Unimod. Against QuantProject's `IdWithMotif-to-Unimod.1.0.591.tsv` (3,139 names, generated by running mzLib's own loader) it agrees on all 100 names that have reached `ptm_sites`, returns null for 57 more, has no entry for 2,445, and resolves **two** differently -- `Decarboxylation on D`/`on E`, a defect QuantProject is filing against mzLib. Neither has fired, so nothing shipped is wrong. The question is not which is correct -- the loader is -- but how a generated table from a third repository reaches an operator's machine and is pinned to the mzLib version that did the search. | Consume the pinned TSV as the mapping, fall back to the resource parse only when the instance's mzLib version has no table, and record in the bundle's reader log which was used. Asked of aging and QuantProject as thread 021 §5; tracked as G26. |
| U10 | **Does `catalog_id` promise more than it delivers?** It hashes `datarepo.__version__` alongside `CATALOG_VERSION`, so **0.10.0 -- which adds an MCP server and changes nothing `build` writes -- gives every catalog a new id from the same bundles.** That is the mirror of the decision that deliberately kept `__version__` OUT of the bundle hash (G29). It is not obviously wrong: a catalog is derived and disposable (D10), so the cost is a rebuild rather than a broken citation, and over-hashing can only be wrong in the safe direction. But aging is the one citing catalog ids, so whether a catalog id should move for a change that cannot reach a catalog is theirs to say. Option (b) is to drop `__version__` and make `CATALOG_VERSION` carry the builder, which would make every future `build` change a deliberate bump exactly as `INGESTER_VERSION` does. | **(a)** leave it, and document what the id does and does not promise. Tracked as G34; not changed without a thread. |
| U12 | **Where do dataRepo's public releases live, and under what name?** (PXReprise PXR-D3, 2026-09-29.) PXReprise will pin a dataRepo version in its getting-started, as it pins MetaMorpheus, and wants the release "with PXReprise". Options: (a) keep `trishorts/dataRepo` and publish releases there; (b) move or transfer the repo to `smith-chem-wisc`, beside PXReprise, where GitHub redirects the old URL. The PyPI name `datarepo` belongs to someone else, so the executables need a distinct release name. | **ANSWERED 2026-09-29 by the user:** "move it to smith-chem-wisc". PXReprise transferred the repo to `smith-chem-wisc/dataRepo` (PXReprise 003); releases there, named `datarepo-<version>-<os>`. |
| U11 | **Does D24 cover a consumer's own science?** D24 says dataRepo RUNS every engine that works on stored results. aging's abundance age-effect fits (`DEF-AGE-EFFECT`, mzLib `Statistics`) are code on stored results, so D24's letter would make them ours. aging would rather keep them, because the trait and the refusals are their science (aging 050 §2). | aging keeps them. D24 covers **generic engines** that no consumer owns; a consumer's own science stays the consumer's to run. Written into charter v0.2 §2 as a proposed reading. **CLOSED, dissolved by D27** (2026-09-24): aging accepted the operator role (aging 055, their D45) and runs its own fits and the generic engines alike. Charter v0.3 §2. |

### The runner (G64, `design/RUNNER.md`) -- ANSWERED 2026-09-24: all four defaults accepted by the user (D28)

| ID | Question | Our default until answered |
|---|---|---|
| U12 | Where does an engine's output live in an instance's store? | `<store>/_engine/<engine>/<artefact id>/`, beside the bundles and never inside one, the way `_study/` works. A search bundle is never rewritten |
| U13 | What identifies one engine run, for "already done"? | sha256 over the engine, its released version, every input's role and sha256, the definition id, `RUNNER_VERSION` and the schema version. **Not** the bundle id: logs resolves a searched database that fifteen datasets share, so one run serves all of them |
| U14 | Does the runner fetch reference inputs (Ensembl's xref dump, go.obo), or does the operator supply them? | The operator supplies every file; the runner hashes each and checks it against the engine's published manifest. Fetching would make the runner a second, unrecorded source of inputs |
| U15 | Where do logs' rows go? | A new core table `gene_resolutions`, keyed as logs keys it (`search_database_sha256, gene_set_release, accession, gene_id`), with `definition_id`. That is a schema change, taken once, together with go's per-row evidence columns |

### The C# port (D41, design/CSHARP_PORT.md), 2026-10-04

| ID | Question | Default (work proceeds on it) |
|---|---|---|
| U16 | Which GitHub repository holds the C# code? | `dotnet/` in this repository (smith-chem-wisc/dataRepo), beside `src/` until the Python is retired, so nobody repoints anything. **ANSWERED 2026-10-04 (the user): option 1, same repo.** |
| U17 | Is the schema docs generator (LinkML's Python tooling, build-time only, never touches data) acceptable as "quick work"? | **ANSWERED 2026-10-04 (the user): yes, it stays.** |
| U18 | Does the frozen Python 0.32.0 get fixes for defects that block the operator during the port? | **ANSWERED 2026-10-04 (the user): yes.** Minimal ones, each also written into the port. |
| U19 | When a search's design puts several files (fractions, technical replicates) into one sample, MetaMorpheus writes ONE protein-group intensity, spectral count and occupancy for that sample. Should the repository store those sample-level values? That needs a new place in the schema (a full re-ingest for aging) and QuantProject's definition of what the number means. (G92, PXReprise PXR-R9) | **Not stored, with a `sample_quant_not_stored` warning naming each sample** (1.3.1). They are never split onto runs. Peptide quantities stay per file and are stored. Revisit once we know how many aging deposits have such samples. |

### PRIDE deposit records (ptmQtl DATAREPO-P35; our ptmQtl 061), 2026-11-04

| ID | Question | Default (work proceeds on it) |
|---|---|---|
| U20 | ptmQtl wants each deposit's lab head, submitter and papers from PRIDE. They are kept out of the bundle, because PRIDE edits its record after deposit. Can a datarepo command fetch PRIDE's records (through mzLib's `PrideArchiveClient`) for the operator to run, given U14's rule that the runner never fetches its inputs? | **ANSWERED 2026-11-05 (the user): yes,** "operator may fetch pride" (D54). An operator command, not a runner step. Each record is stored with its sha256, fetch time and mzLib version, and `build` reads the newest per accession. E-mail addresses are never stored. |
| U21 | Which release carries P35's three catalog tables (`deposit_records`, `deposit_contacts`, `deposit_references`) and the served view of shared raw files ptmQtl asked for (their 062)? All are build-side only: no schema bump, no re-ingest. | **ANSWERED 2026-11-05 (the user): 1.5.0** (D54). |

### Fragment ions (PXR-R44, G116; `design/RELEASE_1.5.0.md`), 2026-11-05

| ID | Question | Default (work proceeds on it) |
|---|---|---|
| U22 | Where do fragment ions live: a table inside every bundle (a schema bump, every deposit re-ingested, all ids move) or a companion beside the bundle (no re-ingest, no id moves, a second thing to host)? | **ANSWERED 2026-11-05 (the user): "fragment ions in every bundle"** (D53). The agent had recommended the companion. PXD031782 loses nothing: it is already out of the catalog. |
| U23 | Which rows: every `AllPeptides.psmtsv` row or only those at 1%? | **ANSWERED 2026-11-05 (the user): 1% PEP q-value, with the q-value notch fallback for a search with no PEP** (D53), about 2 GB across the store. 1.4% to 3.0% of `peptidoforms_1pct` rows have no ions under it, since that view uses the q-value rule. (Measured on five deposits only, and moot now the view moved too: U24.) |
| U24 | The user moved `peptidoforms_1pct` to 1% PEP q-value too (2026-11-05). On 21 of 194 deposits, mostly low-resolution, that rule accepts fewer peptides than the q-value rule: 19 lose over half, and PXD057502 goes from 5,962 to 0, with no ions. The PSM level holds on 18 of the 21, so this is peptide-level `PEP_QValue`, not a failed model. What does such a search use? | **ANSWERED 2026-11-05 (the user): "priority is 1%pep q-value when it is computed. when it is not computed, we fall back to q-value notch"** (D55). So these 21 stay on PEP q-value, and only PXD058775 falls back. The agent's proposed test on a count is dropped. `design/RELEASE_1.5.0.md`, `results/pep_rule_2026-11-05/`. |

### Per-run counts (G125; `design/RELEASE_1.5.0.md`), 2026-11-06

| ID | Question | Default (work proceeds on it) |
|---|---|---|
| U25 | New searches no longer write per-file lines in results.txt (PXReprise's `label-free-dda@14` and `lowres@7`, live 2026-11-06, on the user's word to them of 2026-11-05). So bundles from them hold no run-level PSM, peptide or protein-group counts, and no run-level `ms2_scans` or `precursors` rows until PXReprise pins MetaMorpheus 1.1.14, which carries #2955. Per-run MS2 stays in every bundle from the QC report (`ms2`, equal on all 5,051 runs). The user, 2026-11-06: results.txt is not the only place for scan counts, so PXR-R51 asks PXReprise where else; precursors are the open one. Every bundle served today holds all five. Recount them per run from the whole search at 1.5.0's re-ingest, or leave the gap and state it? | **Recount at 1.5.0, for every deposit**, as our 119 told aging, under a definition from its owner, with a finding on any bundle still lacking the rows. aging reads none of these rows (its 120). Not built. |

### Split deposits (G126; `design/RELEASE_1.5.0.md`), 2026-11-06

| ID | Question | Default (work proceeds on it) |
|---|---|---|
| U26 | A split key already ingests and builds on 1.4.3, but a served split gets a wrong PRIDE link and double counts until the catalog side is built (no re-ingest needed). Which release carries it: 1.5.0, or a smaller release before it if PXReprise wants to serve a split sooner? | **ANSWERED 2026-11-09 (D58): its own release, 1.4.5.** PXReprise 105 asked for a date (PXR-R57); the user said "yes" to a catalog-only release before 1.5.0. Built on `feat/1.4.5`; released on the user's word. |

### The SDRF as the sample record (G127; `results/sdrf_route_2026-11-06/`), 2026-11-06

| ID | Question | Default (work proceeds on it) |
|---|---|---|
| U27 | The user hopes the SDRF carries all treatment conditions and sample facts into dataRepo (PXR-R52, PXR-F9). Proposed in sdrf 034: a treatment is a sample fact written as `characteristics[treatment]`, which reaches the catalog today for any project; `factor value[...]` stays out of a shared bundle. Is that the route? And should the search's own SDRF become the record for new searches, or should we keep reading the input SDRF? | **Yes to the route. Keep reading the input SDRF** until a search with `InputSdrfPath` exists to test; sdrf takes PXR-F9 to the user first. The larger gap is that 151 of 196 deposits read no SDRF at all, which sdrf's drafts could fill. |
| U30 | **How does dataRepo keep each deposit's SDRF?** Asked in chat on 2026-11-07 ("travel with the data, be the official record of sample facts, or both?"), not yet answered. Since then the user ruled elsewhere: PXReprise makes a checked SDRF for every deposit, one per group for a split (PXReprise 104, their D65); and a search with an input SDRF writes its own SDRF and design, both for dataRepo (QuantProject 080, 081; DATAREPO-D14, G130). Also: should a bundle keep a curated SDRF's factor values? Our sdrf 034 rule leaves them out, and the user's words in QuantProject 080 cover "all of the sdrf information". | **Both.** The search's own SDRF and design file go in the bundle at 1.5.0, every column verbatim, factor values included and marked as the grouping that search quantified under. PXReprise's checked SDRF and its check report sit beside the bundle, dated and hashed, so a correction never moves a bundle id. Every column is searchable in the catalog. DATAREPO-D14 is answered only after the user says. **2026-11-09, the user (not disagreeing, a clarification):** a search is calibration, GPTMD, then search and quant. Calibration writes new spectra files and GPTMD a new database, so the SDRF that belongs with the result is the one written after the last search, naming those files, with pointers back to the originals: "you do not need the original because the final contains everything. but you should verify this with the sdrf project." **Default now: keep only that final SDRF (and the design file) in the bundle at 1.5.0.** Asked sdrf as SDRF-D14 (our 036): does every input column survive, is the file name the only pointer back, should the database be named (PXD058082's output names none), and is the final SDRF rewritten when a sample fact is corrected? A copy beside the bundle is needed only if it is. **2026-11-11, PXReprise 109 (PXR-R58, their user):** a corrected sample fact is a new search and a new bundle, never an edit; the old bundle stays unchanged, and a bundle keeps only its own search's SDRFs. So no copy beside a bundle is needed. What is left is sdrf's answer: does the final SDRF hold every input column (if not, the bundle keeps the input SDRF too). |
| U31 | **Review and release mzLib #1555 and #1557 soon?** sdrf holds its drafts until then (PXReprise 103, step 1). PXReprise's plan can also go ahead with the held columns left out. Asked in chat 2026-11-07. | **The user's to merge and release.** The agent recommends soon, so checked SDRFs are ready for 1.5.0's re-ingest at no extra cost. **2026-11-11:** both merged 2026-11-09, not yet released (mzLib's latest is 1.0.597, 2026-11-03). |

### dataRepo moves into PXReprise (D62), 2026-11-12

| ID | Question | Default (work proceeds on it) |
|---|---|---|
| U33 | The user and Alex agreed on 2026-11-11 that dataRepo moves into PXReprise. The user, 2026-11-12: "I don't know how that will transpire yet." **How and when does it happen?** PXReprise's diabetes 004 gives one account: after 1.5.0 ships, preparation as PRs the user reviews, one shared store (reversing PXReprise D64), `datarepo push`/`pull` drafted on a `feat/storage-push-pull` branch that is not in our repo. | **1.5.0 ships from this repo as planned (D60).** Nothing is built, moved or renamed toward the merge until the user and Alex decide how. Repo moves are the user's. |

### The database a search read (G131; `results/searched_db_2026-11-09/`), 2026-11-09

| ID | Question | Default (work proceeds on it) |
|---|---|---|
| U32 | The user: "somehow somewhere we need to store a pointer to the database ... Might even be good to store the database somehow but that is probably unweildy. it needs to be somewhere because without it there is no hope of reproducing a result." The pointer is decided. **Should the databases themselves be kept, and by whom?** All 159 GPTMD databases are 51.7 GB as written and about 5 GB with zstd -3. The 46 distinct originals are 11.6 GB. The served bundles are 29.4 GiB. Asked PXReprise as PXR-R59 (our 108). | **OPEN, no default (the user, 2026-11-09: "i'm not prepared to make a decision on databases at the moment. leave the decision open").** Nothing is stored or built on it. PXReprise's answer to PXR-R59 is information for the user, not a decision. The agent's view, when asked: keep them compressed under their sha256. |

### A hole in the MCP sandbox (G128), 2026-11-06

| ID | Question | Default (work proceeds on it) |
|---|---|---|
| U28 | A client of `datarepo mcp` on a folder catalog can write into the store: run on 1.4.3, read from the code back to 1.3.5. The fix is built and tested on local branch `feat/1.4.4`, not pushed, because its tests show how to do it. Release it as 1.4.4 now? It moves no row and no bundle id. PXReprise and aging swap one binary and restart their servers. | **Hold until the user says:** a release is only ever on the user's word. The agent's recommendation is yes, now, ahead of 1.5.0. |

### AI contributions and hosting (G129; PXR-R37 to R39), 2026-11-06

| ID | Question | Default (work proceeds on it) |
|---|---|---|
| U29 | The review of `feat/ai-contributions` says not to take it as it stands (PXReprise, our reply to R37-R39). Four choices are the user's. (a) Which release carries contributions? (b) What may a contribution claim? Today `reproduced: true` came back for a result citing `SELECT 1`, so `observed` and `reproduced` can only mean "this call happened" and "these rows came back", and the grant wording has to match. (c) Does hosting go ahead now? D16 says hosted MCP only on evidence of demand, and PXReprise 064 says the user has chosen to host. (d) The design's four "Open for the user" items: grant wording, who may submit, contributions on a working build, who reviews before the next model is told to build on one. | **Answered in part, 2026-11-07 (D57).** (a) Not held for 1.5.0: a result keeps pointing at the data it used, and the build carries old results across a re-ingest. Which release, and whether before or after 1.5.0, is still open. (c) No host for now; the users are the user and Alex. (d) Results come in through the operator's inbox and a person reviews them, but nobody fills anything in: the server records what it can itself. **Still open, with defaults:** (b) the narrow meanings above. When hosting comes: rebuilt, last, read-only, under an account that cannot write the data, with limits and a stage-two sandbox. |

## Waiting on aging (thread `design/threads/aging/`)

| ID | Question | Status |
|---|---|---|
| DATAREPO-2 | Record organism / acquisition / quant_method / instrument_vendor, **plus enrichment and labelling** (aging's addition), explicitly in provenance. | Accepted (aging 003). aging will say in the thread when `provenance.json` carries them. Until then the ingester reads them from discover/SDRF and marks them `inferred`. |
| DATAREPO-3 | Which accession list and which PSM count are canonical? | Open on aging's side: SUSPICIOUS.md S20 (datasets; the frozen census, R1, will be canonical) and S21 (PSMs; aging will answer with a definition ID). Until then the ingester stores both PSM numbers with their source. |
| DATAREPO-5 | Confirm or replace the aging study layer (`schema/study/aging.yaml`), incl. the AgeEffect `response` vocabulary. | Posted 004, 2026-09-19. Default: build on the stub. |
| DATAREPO-6 | Route J12 (literature-claim table) and P2 (mass-shift histogram as a bundle file). | Posted 004. Default: P2 as a file; J12 treated as a definition-only trap. |
| DATAREPO-7 | Emit both PSM counts, contaminant share, and run date + instrument as definition-backed metrics. | Posted 004. Default: read what exists; run date from raw header. |
| DATAREPO-8 | Relay R7 / R16 / R7b column names to MetaMorpheus and QuantProject. | Posted 004. Default: schema's proposed names. |
| DATAREPO-9 | D8: accept the data-instance role (bundle location, releases/DOIs, CC BY 4.0, handover doc). | Posted 005, 2026-09-19. Default: accepted; bundles on `F:\aging_data\repo\<release>\`. |
| DATAREPO-10 | = U6: does aging also run the service? | Answered (aging 006): yes. aging populates and hosts the instance, including the service. |
| DATAREPO-11 | Definition IDs for the numbers the ingester now stores with `PROVISIONAL:` placeholders: FlashLFQ peptide and protein intensity, protein spectral count, peptide and protein-group counts at 1% FDR, MS2 count, run minutes, precursor count. | Posted 007, 2026-09-19. Default: keep the `PROVISIONAL:` IDs, whose text says they are not an owner's definition, and swap them when the owners publish. |
| DATAREPO-12 | pyMzLib: populate `pro_forma` on `.psmtsv` records. It is null in 0.1.x, so dataRepo translates MetaMorpheus notation itself, which is peptidoform semantics it should not own. | Posted 007. Default: keep `src/datarepo/proforma.py` and delete it when the field arrives. |
| DATAREPO-13 | pyMzLib: two readers dataRepo had to work around. `AllQuantifiedPeaks.tsv` fails with "Header with name 'MBR Score' was not found" on MetaMorpheus 1.1.11 output, and the SDRF projection joins header and cells with `;`, which SDRF values also contain, so columns cannot be recovered. The `.psmtsv` projection also omits the matched-ion summary columns and the localization score. | Posted 007. Default: dataRepo reads those three files as plain TSV, with the reason recorded in its reader log. |
| DATAREPO-14 | The exact predicate behind `aging DEF-PSM-1PCT v1`. Target plus `QValue <= 0.01` and `QValueNotch <= 0.01` reproduces the peptide (5,541) and protein-group (1,652) totals of PXD036557 exactly, but gives 26,594 PSMs against the reported 26,582. | Posted 007. Default: use that predicate, store both numbers, and raise a `count_mismatch` finding for the 12. |
| DATAREPO-20 | **The study layer is instantiated and four things about its shape are ours, not aging's.** (a) How do `age_effect` rows reach the repository at all? They are the output of a modelling stage that runs long after a search, so they cannot come from `datarepo ingest`. (b) `aging:DEF-AGE-EFFECT v1` §4 writes `feature_type = glycosite`; the core `FeatureType` enum has `glycopeptide` and no `glycosite`. (c) §6's meta key omits `feature_type`, and a dataset-scoped identifier such as a `protein_group_id` cannot be a cross-dataset key at all - so what IS a feature's cross-dataset identity? (d) `stratum` is left an open string because §5 adds `incl_censored`, which §2's table does not list. | Posted as thread 022. (a) **BUILT on the default in datarepo 0.7.0** (2026-09-21): `datarepo study` writes a separately content-addressed study bundle under `<store>/_study/<layer>/`, `build --study` loads it, and no search bundle id moves. Still reversible -- if aging wants another hand-over, only the reader changes. Defaults: (a) a separate study bundle written by a new command and loaded by `build`, so a study layer never forces a re-ingest; (b) use the core `glycopeptide` rather than forking the enum; (c) include `feature_type` and treat `feature_id` at meta grain as a protein accession for protein features; (d) leave it a string. |
| DATAREPO-27 | **Does `aging:DEF-PEPTIDE-1PCT` carry a notch condition?** We applied the PSM notch-resolution clause from their 008 to the peptidoform count as well. PXD032202 settles it against us: the producer reports 21,771 and the un-clause count is 21,771 exactly, while ours said 21,768 -- so we raised a `count_mismatch` against a dataset that matched perfectly. | Implemented on our default (no notch condition) in 0.11.0, thread 033 section 1. aging says so before re-ingesting if the definition means something else. |

## Answered

| ID | Answer | Recorded as |
|---|---|---|
| U12-U15 | The runner's shape as proposed: output beside the bundle under `_engine/`; id from engine, version and input sha256s; operator supplies inputs; one schema change adds `gene_resolutions` with go's columns | D28 (2026-09-24) |
| G2 | Prototype local; NCEMS runs production | D1 |
| G3 | Public from day one, no login | D2 |
| — | CC BY 4.0 data, MIT code | D3 |
| G6a | QPX-compatible superset | D4 |
| G6b | Human + rodent, DDA + DIA, LFQ + TMT | D5 |
| DATAREPO-1 | aging accepts DIA/TMT/rodent; build order stays human DDA LFQ first (aging 003) | D5 (unchanged) |
| DATAREPO-4 | aging owns the benchmark: `aging/design/QUESTIONS.md` v0.3, 168 questions, read from trishorts/aging master, not copied (aging 003) | G5 |
| U3 | Credit line: "NCEMS Aging Proteome Working Group" (user: "citation is fine", 2026-09-19) | CITATION.cff |
| G8 | Public GitHub repo created by the user | state.yaml github.remote |
| — | dataRepo is code only; aging hosts the data (user) | D8 |
