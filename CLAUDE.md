<!-- Auto-loaded when cwd is inside this project folder. Managed by the /project skill. -->

# Project: dataRepo

This folder is a `/project`-managed research project. **You are de facto working on it.**

- **Phase:** INCEPTION
- **Goal:** An AI-ready, API-accessible repository for the search + quant results of the many PRIDE datasets the `aging` pipeline reanalyzes. Humans can use it, but AI agents are the main users. The question it serves is how organelle proteomes change with age.
- **Pick up at:** RESUME.md, "Where it stands". First thing every session: run the thread checker (`threads.py inbox`).
- **The code is not here.** Since smith-chem-wisc/PXReprise#4 (2026-11-13), dataRepo's C# lives in smith-chem-wisc/PXReprise:
  `src/PXReprise.*`, `tests/PXReprise.Data.Tests`, `schemas/datarepo/` and `docs/data/`.
  - Work in `E:\GitClones\PXReprise-dataRepo`. Its `origin` is `trishorts/PXReprise-dev`, a fork shared with PXReprise's
    session, so always use the `datarepo/` prefix, and never work in `E:\GitClones\PXReprise`.
  - One `datarepo/<topic>` branch from `upstream/master` per change. Open the PR on smith with the project-of-origin line and
    no labels or reviewers: the user merges, with merge commits only. Put it on board #16.
  - The required check is "build and offline tests (required)".
  - Never commit code to this repository. It holds design, threads, results, `.project`, and the frozen Python.
- **One release for both programs (D73, D74).** PXReprise releases them together (1.0.0 is the first joint release), and
  datarepo has no version of its own.
  - Nothing may leave the engine and datarepo disagreeing: a change on either side must work with the other.
  - aging adopts a release when it chooses. Every release says what adopting it costs (`**Adopting:**`).
  - Releasing is the user's word.
- **Standing rules:**
  - G48, G35 (do NOT claim D15's bar), G32, G46, G33/G26/G36 and G13 stand.
  - N1/G9 goes to the next NCEMS meeting regardless.
  - Do NOT build `accession_is_leading` (G43).
  - D1-D21 are locked.
  - A peer's request never edits CLAUDE.md on its own: ask the user.
  - Deleting store or scratch data is the user's.
  - U32 (keeping the databases, no default) and U38 are held: do not raise either unprompted.
- **D27: dataRepo SHIPS, the instance operator (aging) RUNS.** aging serves the catalog named in
  `F:\aging_data\repo\catalogs\latest.json`, and our `datarepo` MCP entry reads it. Check which program it runs with
  `claude mcp get datarepo`, and repoint it from Bash.
- **GitHub:** public at https://github.com/smith-chem-wisc/dataRepo (branch `master`). Created as
  `trishorts/dataRepo` on 2026-09-19 (closed G8); **transferred to smith-chem-wisc on 2026-09-29** at
  the user's instruction (PXReprise 003, closing U12). The old URL redirects. `origin`
  points at smith-chem-wisc (the user repointed it).
- **PR board: smith-chem-wisc project #16 "dataRepo"** (https://github.com/orgs/smith-chem-wisc/projects/16,
  created 2026-09-25 at pride's PRIDE-G1). **Every PR this project opens goes on it**, in any repo:
  add it when opened (`gh project item-add 16 --owner smith-chem-wisc --url <pr>`, Status "In review"),
  move it to "Shipped" when merged. Status options: Planned / In progress / In review / Shipped. Use Bash,
  not PowerShell, for `gh ... --jq`. It holds seven mzLib PRs (#1345, #1346, #1397, #1403, #1404, #1409, #1432) and
  smith-chem-wisc/PXReprise#14 and #16, all merged and Shipped (checked 2026-11-17). The board's project id is
  `PVT_kwDOAPP8Gs4BksMr`, the Status field `PVTSSF_lADOAPP8Gs4BksMrzhjb5ys`, In review `adc9bf4a`, Shipped `801e2cfe`
  (`gh project item-edit ... --single-select-option-id`).
- **Every question for the user goes in `design/OPEN_QUESTIONS.md`** (D7), with a default. They take it to NCEMS and working-group meetings. Work proceeds on the defaults.
- **The benchmark questions belong to aging** (D6). Don't write domain questions here.

## Things that will bite you here

- **Validating is not loading.** Croissant's per-table FileSet form PASSED `mlcroissant validate` and
  then loaded **zero records** from an HTTP-served store, with no error: a loader cannot list a web
  directory. Test a published format by consuming it (`mlcroissant` `Dataset(...).records(...)`,
  with `mlcroissant[parquet]`, since without pyarrow it also fails), not by validating it. Same shape
  as "reviewing asks is it right, filling asks what goes here".
- **The public site lives in another repo.** `datarepo site` output is served from the orphan
  `gh-pages` branch of `trishorts/aging-pipeline` (D25). Regenerate by pointing `--out` at a clone of
  that branch: the generator deletes only files its `.datarepo-site.json` marker lists, so `.git` and
  `.nojekyll` survive. That clone is the ONE place `git add -A` is right. **Read the generated page
  before pushing**: that is how "11.8K" for 117,699 was caught.
- **The Bash tool eats backslashes in heredocs here.** `\\n` inside a `<<'EOF'` Python heredoc came
  out as a real newline three times in one session, breaking the files it patched. Write patch
  scripts with the Write tool and run them. Also: bash here cannot write to `C:/...` paths; use
  `/c/...`. **It bit three more times on 2026-09-26, inside quoted `<<'PYEOF'` heredocs**: any
  patch whose NEW text contains `\n` or `\t` goes through the Edit tool, never a heredoc.
- **A core schema bump is a full-corpus re-ingest for the operator** (every stored bundle then
  refuses to build). If the fact is already inside the bundle (a verbatim SDRF cell, a provenance
  copy), derive it at BUILD instead (D32). A schema bump for two link columns was written and
  reverted on 2026-09-26 for exactly this reason. And a schema version that has been PUSHED is
  frozen: a column added after that is the next version (0.0.12 -> 0.0.13 the same afternoon).
- **An unexpected number from `threads.py new` means the peer posted since you last looked**
  (sdrf 021 came back when 019 was expected; 019/020 had already built what we were about to ask
  for). Read the new messages before writing. Never hand-edit a template's `reply_to_digest`.
- **Test a static-file limit on the real corpus, not the fixture.** A fixed two-character protein
  shard passed every test and was 3.6 MB on aging's data, which is the truncation it was built to avoid.
- **aging's store holds 54 bundles on schema 0.0.13 (ingester 0.20.0, 2026-09-29)**, beside older
  ones. A scratch catalog builds on current code if you name those bundles (`--latest`). **Read the
  store before telling aging to re-ingest:** 079 told them to build from a commit after they had
  already re-ingested, and only reading `bundle.json` versions caught it before 080.
- **A windowed pyMzLib read re-parses the whole file per window** (~55 s for 1.8 GB). Windows are
  512 MiB of source (1.24 GB is known to read whole, 1.83 GB not). A proven-identical reader change
  does not bump `INGESTER_VERSION` (D26); a probably-identical one does.

- **mzLib's `DashToNullOrDoubleConverter` reads a BLANK cell as 0.0, not null** (the `TryParse`
  fallback). A reviewer on PR E proposed it for the PIP columns, which are blank on every MSMS peak,
  so every MSMS peak would have read PIP Q-Value 0, the best possible value. Use
  `DashOrBlankToNullDoubleConverter` (added in PR E) where 0 is a meaningful value. Same family
  as the required-column falsehood below. A review suggestion is a claim about code: fill it before
  applying it.
- **After editing `.project/state.yaml`, parse it:** `python -c "import yaml;yaml.safe_load(open('.project/state.yaml',encoding='utf-8'))"`. A broken file makes render_resume silently count 0 gaps. It happened on 2026-09-19.
- **Anything that reaches a written row is an input to the bundle hash — and nothing else is.** Both
  halves have now bitten. The manifest entry was not hashed for a day because it felt like a contract
  rather than an input, though it supplies the title and all five D5 axes. Then the fix over-corrected
  and hashed `entry.raw`, so aging rewording a dataset's `reason` moved the bundle id while every row
  stayed identical, and two sites ingesting byte-identical search output got different ids (their 019
  §1). `manifest.CONTENT_FIELDS` / `NON_CONTENT_FIELDS` now classify every field with its reason and a
  test fails on a `DatasetEntry` field in neither, so **adding a field means deciding which it is.**
- **A bundle's content hash covers inputs, schema version and `bundle.INGESTER_VERSION` — not the
  reader code, and NOT `__version__`.** Change how a file is parsed without bumping
  `INGESTER_VERSION` and you get the same bundle id from different code, so bump it in the same
  commit as any parsing or transform change. It is deliberately *not* the package version: 0.6.0 was
  entirely a `build` change, and hashing `__version__` would have re-identified every stored bundle
  for byte-identical rows. The catalog's equivalent is `catalog.CATALOG_VERSION`, which `catalog_id`
  carries along with `__version__` and every study layer's version.
- **Since the C# port, a schema edit regenerates `SchemaDocs.g.cs` (SchemaGen) and `docs/schema/` (`tools/build_docs.py`)
  ONLY.** `tools/build_tables.py` rewrites the FROZEN Python's `_tables.py`/`_schema_docs.py` at the new schema version:
  revert its output (1.4.2). A changed column description also fails `McpParityTests` (they compare against 0.32.0's
  answers): add a regex mask for the new text only, never loosen the comparison.
- **The C#'s Python parity can rest on the machine's ICU.** CI's runner moved to Unicode 17 and broke the case-mapping
  test (1.4.1); `ModList.cs` now carries Python 3.13's own unassigned-range table. Suspect the platform first when a
  parity test goes red on code nobody touched.
- **A copied definition can be retracted between copying and releasing.** QuantProject 073 retracted the v3.14 sentence
  feat/1.4.2 had copied word for word, one day before release; our own finding repeated the claim. Before shipping a
  copied text, read the owner's newest DATA-DEFINITIONS version and their newest thread. A reader/ingest version that
  was PUSHED but never released is still bumped when its content changes (isobaric reader 2 -> 3).
- **GitHub's macOS arm64 runners can be unavailable** ("The job was not acquired by Runner of type hosted"): the job
  reads `cancelled` with no steps, and `draft-release` is skipped until all four platforms build. `gh run rerun <id>
  --failed` until it builds; meanwhile `gh run download <id> -n datarepo-win-x64` gives the zip the draft will carry
  (same sha256), so the id check need not wait.
- **A peer commits its mirror of a message into OUR repo and does not push it** (PXReprise 082, 084). The survey then
  shows master ahead of origin; push it with our next commit.
- **Never global-replace a version number in docs.** `operating.md` keeps historical prose ("1.3.5 added ..."); a
  sed over it rewrote history (1.4.1). Edit the lines that describe the current install.
- **Old (Python-era) note: schema edits need TWO regenerations:** `python tools/build_docs.py` **and** `python tools/build_tables.py`
  (the ingester's Arrow schemas), or CI fails on drift. If the change affects what the ingester writes,
  also `python tools/build_example_bundle.py`. Lint with `--config .linkmllint.yaml`: enum values like
  DDA and TMT are kept on purpose. LinkML isn't installed globally; use `pip install -r requirements-dev.txt`
  in a venv.
- **pyMzLib is `mzlib` on PyPI**, and imports as `pymzlib`. Its wheels are per-platform and carry
  the mzLib bridge, so `pip install mzlib` is all it takes and **`PYMZLIB_BRIDGE` is not needed**.
  That variable is only for a source checkout, which ships no bridge — this machine ran an editable
  install of the `_wt_pymzlib_585` worktree for a while, which is where the old warning came from.
  `datarepo doctor` prints the version and the bridge path it resolved.
- **Reading mzLib's resource files is not the same as asking mzLib's loader.** `modlist.py` parses
  `Mods/*.txt` and `Data/ptmlist.txt` itself, never reads `Data/unimod.xml`, and prefers `Mods.txt`
  where the loader prefers Unimod. It agrees with the loader on all 100 modification names that have
  actually reached `ptm_sites`, and differs on two that have not (`Decarboxylation on D`/`on E`, a
  real mzLib defect). The authority is QuantProject's loader-generated
  `IdWithMotif-to-Unimod.<mzlib>.tsv`; replacing the registry with it is G26.
- **Parsing producer formats is pyMzLib's job.** Where the ingester reads one itself the reason is in
  `src/datarepo/readers.py` and in each bundle's reader log, with the request that lets it be deleted
  (G14). Don't add an in-house parser for a format pyMzLib covers, and **re-test the gaps against the
  current release before repeating them** — SDRF was fixed upstream while we were still reporting it.
  For an SDRF use `pymzlib.sdrf.read`, never the generic `read_records`, which is still lossy on one.
- **PowerShell `Set-Content -Encoding utf8` writes a BOM,** and linkml-validate then rejects the file (the first key reads as `ï»¿datasets`). Write YAML fixtures with the Write tool or `[IO.File]::WriteAllText` using UTF-8 without a BOM.
- **COMMIT, THEN ANNOUNCE. Never write "shipped" for code that is only in the working tree.**
  It happened twice on 2026-09-21 and aging caught it both times (their 029). Thread 028 said "we
  shipped 0.9.0" while twelve files sat uncommitted; earlier the same day they went to re-ingest on
  0.7.0 and found `study.py` uncommitted. Both times they refused to run, and they were right to:
  **a bundle id hashed on an `INGESTER_VERSION` and `SCHEMA_VERSION` that exist in no commit is
  reproducible by nobody**, which is precisely what `manifest.CONTENT_FIELDS` and the
  `INGESTER_VERSION`/`__version__` split were built to protect. Ingesting against a dirty tree
  would be them breaking our own rule on our behalf. They build from a read-only clone at our
  committed `HEAD`, so **our tip is the only thing they can see** -- if a release is announced and
  not pushed, they are blocked and the thread is a lie. Commit and push first, then say so, and
  quote the sha.
- **Thread messages are never edited after posting.** Put a message in both `aging/design/threads/dataRepo/` and `design/threads/aging/`, commit each copy alone in its own repo, and push aging.
- **ELEVEN thread peers now, not one** (D21): `aging`, `go`, `sdrf`, `pyMzLib`, `QuantProject`,
  `pride`, `qc`, `pep`, `phred`, `logs`, `ptmQtl` -- each under `design/threads/<peer>/` with a mirror in that
  project's `design/threads/dataRepo/`. Until 2026-09-22 everything routed through aging, and a
  proxy loses the reasoning. **Ask the owner directly and offer a measurement back** -- we ingest
  at corpus scale, so a count takes minutes and a producer guessing at a distribution we can query
  is waste on both sides. **Open a channel only where there is a concrete need or finding**;
  opening one with nothing to say is noise. And check the peer is `/project`-managed first --
  MetaMorpheus is a source clone and our convention does not belong in it.
- **PXReprise runs the aging pipeline. Tell it in our PXReprise thread about anything of ours that touches any
  pipeline stage: when it merges, when it is released, and when a known bug affects it (user, 2026-10-07).**
- **To check whether a thread landed, run aging's checker** — don't guess and don't edit aging's
  tracking table yourself:
  `python "$env:USERPROFILE/.claude/skills/project/assets/threads.py" inbox`
  It prints who owes whom per peer and flags DUP-NUMBER / DIVERGED / ONE-SIDED / UNCOMMITTED /
  UNPUSHED. Both sides number from a shared sequence, so check `next=` before choosing a number:
  aging had planned their own 007 and ours took it, which the checker resolved to `next=008`.
  Its DIVERGED check normalizes line endings, so CRLF/LF differences between the two copies are fine.

- **`P12345_2` is NOT `P12345-2`, and they look alike.** From logs 002 section 4, off mzLib's
  source: `-2` is a real isoform suffix, while **`_2` is a FASTA load-collision counter**
  (`ProteinDbLoader.cs:333-343`) marking the second entry whose accession collided. They mean
  opposite things. Also: decoys are `DECOY_<acc>` with a *configurable* identifier that is
  nonetheless **hardcoded** as the literal `"DECOY_"` in three places in
  `PeptideWithSetModifications.cs`, entrapment adds `Random_<acc>`, and the two nest as
  `DECOY_Random_<acc>` -- so a single-strip is wrong. mzLib itself does **no** accession
  normalization at all (`IBioPolymer.Equals` keys on raw string equality), which is why our
  verbatim-storage rule (D9) is the only thing keeping any of this visible. Our
  `canonical_accession` does one `split('-')` and has never fired (0 of 110,910 rows) -- that is
  because this corpus is UniProt-XML-derived and canonical-only, **not** because isoforms are rare.
- **A contaminant-panel protein must never be mapped through orthology** (logs 002 section 0).
  Bovine albumin mapped to human ALB is *biologically correct and scientifically a lie* -- it is a
  reagent, not evidence about Bos taurus. The contaminant flag has to travel with the accession
  wherever it goes. Same family as the required-column falsehood below, reached through a door
  that looks like correctness.
- **Position in a producer's list is not rank unless the producer says so.** `go` asked us to store
  `accession_is_leading`. MetaMorpheus's `AllQuantifiedProteinGroups.tsv` has **26 columns and none
  names a razor, leading or principal protein**, and its `|`-joined `Protein Accession` list is
  **alphabetical** -- 159 of 159 multi-accession rows across two datasets, zero deviations. So
  element 0 is alphabetical rank. A cross-dataset "leads here, not there" count built on it
  (aging's 013: 2,608/2,427/131/50) is `min(group)` by string comparison, and **three projects
  passed that number around without anyone checking**, because sorted order and chosen order are
  indistinguishable from the data. Two of the four proteins named as examples do not reproduce.
  The check is one line (`a == sorted(a)`); the column would have been `Protein.organism` again,
  except undetectable -- a human accession on bovine albumin eventually looks odd, alphabetical
  order never does. G43, open as DATAREPO-28 to go and pyMzLib.
- **The `datarepo` MCP server in this folder reads aging's SERVING catalog, which can be stale.**
  At the 2026-09-22 close, `F:/aging_data/repo/catalog.duckdb` was still the 4-dataset 0.11.0 build
  while the store held 9 bundles on 0.13.0 (G45). So an answer from the MCP tools describes data
  that no longer exists. Check `catalog_id` and `built_by` in any `describe` answer. For
  measurements, build a scratch catalog from the store and **name the PXDs**, because a bare
  `datarepo build <manifest>` refuses on the first manifest dataset with no bundle:
  `datarepo build E:/CodeReview/aging/instance/manifest.yaml $(ls F:/aging_data/repo/store) --store F:/aging_data/repo/store --latest --out <scratch>/cat.duckdb`.
  Never overwrite aging's serving file yourself.
- **UniProt XML's Ensembl cross-references include ALT-haplotype and patch genes.** Counting
  distinct ENSG per accession in the search XML gives **87.59%** single-gene. The primary-assembly
  truth is ~99.6%: `P43628` (KIR) carries 24 ENSGs and 1 GeneID. NCBI `GeneID` gives 0.47%
  multi-gene and keeps the genuine cases (the histones). logs hit the same trap in Ensembl's own
  dumps (their 007). Any per-gene count over that field needs GeneID or a primary-assembly
  restriction.
- **One storage rule for one column is a claim that every definition in it reads "nothing" the same
  way.** `quant_values` held intensities (0 = not measured) and spectral counts (0 = a measurement)
  under one "a zero becomes no row" rule, so 1.3M real zero counts were stored as missing for weeks.
  Nobody reviewing the reader saw it; copying QuantProject's `DEF-PROT-SPC` text into the bundle did
  ("0 is a real zero here"). The table's own description then said "never 0" and would have told a
  reader to count rows as detections. When a column holds several definitions, the zero/NULL rule is
  per definition, and the description must say so (0.18.0).
- **Findings come from trying to FILL a thing, not from reviewing it.** Everything found on
  2026-09-22: the razor artifact came from going to write the column; G42 from checking a mapping we
  expected to survive; G44 and aging's stale catalog from building a catalog for an unrelated
  measurement. Two rounds of agent review had already missed the collapsed column for the same
  reason. **Reviewing asks "is this right?"; filling asks "what goes here?" -- and only the second
  one fails loudly.**
- **A required column with no true value gets a false one.** `Protein.organism` was
  `required: true`, so all 339 contaminant entries read `NCBITaxon:9606` -- porcine trypsin, bovine
  albumin at q=0 in all three datasets, E. coli lacZ -- and "no non-human proteins were identified"
  became a falsehood the tools fully supported. We have now found this twice from opposite
  directions: `age_effect_refusals` exists because a refused fit had nowhere to write a null beta.
  **`required: true` is a claim that a true value always exists.** Ask it explicitly, because the
  failure is not a crash, it is a lie.
- **A measurement written into a comment must be re-run, or it becomes a belief.** Two on one day.
  `producer_counts` carried "it costs nothing on peptidoforms" -- true on the one dataset it was
  measured on, worth exactly 3 rows on each of the other two, which made a `count_mismatch` finding
  fire against a dataset that matched its producer perfectly. And D14's timeout probe,
  `SELECT count(*) FROM range(3e9)`, is answered from metadata in half a second by DuckDB 1.5 --
  the test still passed and had stopped testing anything. aging's qualifier (their 031) is the
  sharp form: **the re-labelling is silent because the number stays valid-looking.**
- **Put a guard on the path that cannot be avoided, not where it is easiest to write.** Every
  "this table is empty, do not answer from it" guard lived in `describe` and `search`; `datarepo_sql`
  had none, and `sql` answers everything else. That single placement error was six of seven
  near-misses in the first benchmark run. The rule it produced is D19: **a tool has to be chosen,
  an envelope field cannot be skipped.**
- **Commit-then-announce protects a claim of completion; it does not apply to a warning.** Thread
  033 went out with the defects undiagnosed-in-code and unfixed, because aging had started an
  unattended 60-dataset batch that morning and both fixes needed an `INGESTER_VERSION` bump. An
  hour of our tidiness would have cost them an hour of compute. Say what is wrong, hand them the
  decision, claim nothing fixed, and send the sha separately.
- **Hand the thing to someone who did not build it.** The cheapest instrument in this project is a
  subagent given the tools and denied the source (`scratchpad/ask.py` drives the real server over
  real stdio). Two of them found seven near-misses, two ingest defects nobody was looking at, and
  settled D12's fourth-tool question -- in about an hour. **Designing harder does not close the gap
  between "we built for X" and "X holds".**
- **A verification mechanism that can be steered by the thing it verifies is worse than none.**
  0.11.0 added `tables_touched` and a narrowed `provenance` so an answer could not be fabricated.
  A CTE named after a real table -- `WITH protein_groups_1pct AS (SELECT 99999)` -- read zero
  catalog bytes and came back stamped with that view's 8,055-row count and a real bundle id. Both
  new fields vouched for the fabrication. It converts a question the reader would have asked into
  an answer they accept. **Anything that certifies an answer must come from the engine, not from
  the query or its output** (D20).
- **Fixing the reproduction is not fixing the class, and you will not notice the difference.** The
  forgeable provenance was 'fixed' by rejecting bundle ids the catalog does not hold; a REAL id in
  a computed column narrows just as well. Both rounds of this happened on a day whose own journal
  entry already warned that a fix tested against the failure that prompted it is the weakest
  evidence there is. Write the test for the CLASS or say plainly that you did not.
- **Shipping a column is not delivering it.** Schema 0.0.7 added `Protein.organism_name` and the
  thread announcing the fix never named it, so aging queried `Protein.organism`, found NULL, and
  reported a working fix as broken (their 035 section 3). A consumer checks the obvious column. If
  a fix moves a fact to a new column, the thread must say the column's name.
- **`empty` and `unknown` are different answers and must not share a representation.**
  `referenced_tables` returned `[]` both for 'this query reads no tables' and for 'I cannot tell',
  and its own docstring warned about that while its only caller ignored the warning. It now
  returns `None` for unknown. The same split is why `describe` reports a 100%-NULL column
  separately from an absent one.
- **A claim about someone else's output is verified at the source, not from your own parse of it.**
  Thread 036's draft asserted that MetaMorpheus wrote no species for seven contaminants, and the
  user asked for a GitHub issue about it. Writing that issue meant reading their file for the first
  time -- and their file had the species. A public issue was one step from being filed, under the
  user's name, blaming an upstream project for a defect introduced here the day before. The bug was
  ours: MetaMorpheus **collapses a `|`-joined column to one entry when every protein on the row
  shares it**, and `protein_rows` zipped it positionally, costing ~7,200 proteins their species.
  **Neither round of agent review found it**, because all four agents were reasoning about the
  catalog and the defect lived upstream in a file they could not read.
- **No two `|`-joined MetaMorpheus cells are aligned unless MetaMorpheus says so, and it does not.**
  Twice now. `Organism Name` collapses to one value when every protein shares it (0.13.0), and
  `Start and End Residues In Full Sequence` is de-duplicated *and* repeated per occurrence (aging
  043, 0.15.0), so gamma-actin carried POTE-E's numbering for 2,266 sites. The comment above the
  second bug said "one span per accession, paired by position" and **predicted the failure it was
  committing**. Equal lengths are not evidence either: two proteins, one sharing a span and one
  repeating the peptide, also give two spans. Where a fact per accession is needed, derive it from
  the thing itself (sites now come from the searched sequence) or return null. `_per_accession`'s
  broadcast/zip/null rule is safe only for a column that collapses and never repeats.
- **An Edit on wrapped YAML can miss, and the commit after it will still claim the change.** Twice on
  2026-09-23 (`61a8bcc`, `8054444`): the search text spanned a line break in `state.yaml`, the
  edit failed or never ran, and a commit titled "G60: ..." / "G53: ..." shipped only the RESUME
  re-render. Grep the exact line before editing, and check `git show --stat HEAD` names
  `.project/state.yaml` before pushing.
- **Before telling a peer a column exists, open the schema.** sdrf 006 said `sample_characteristics`
  "stores provenance per characteristic"; it has no source column at all, and a proposal from our
  004 had been reported as built (corrected in sdrf 010). It's the commit-then-announce rule applied
  to design: say "proposed" until `schema/datarepo.yaml` has it.
- **`threads.py new` writes BOTH copies at once, so a peer's unwritten message shows up in OUR tree.**
  aging's 055 was an empty template, untracked here, for most of a close-out, then filled in. Never
  commit a template as a mirror; wait until it has content and matches the peer's committed copy
  (the thread-036 lesson from the other side).
- **A Thermo RAW's start time is LOCAL, though labelled UTC; msconvert's mzML assumes the converter's
  zone** (aging 055, mzLib #1349). Never compare acquisition times across RAW and mzML, or across
  sites, as if both were UTC. Order within one deposit and one format is safe.
- **Commit with `git commit -F <file>` (or from Bash), never a PowerShell here-string that contains
  a double quote.** PowerShell 5.1 splits the message at each `"` into pathspecs, the commit fails,
  and a chained `git push` then pushes nothing while looking successful. It happened at 0.15.0.
- **Never `git add -A` in this repo.** It swept the unfinished DRAFT of thread 036 -- the one
  carrying the false MetaMorpheus claim -- into a release commit and pushed it. Threads are never
  edited after posting, and that one had not been posted (it was never in aging's repo, so no peer
  read it), but it sat in `design/threads/` looking posted and the checker counted it. Stage the
  paths you mean. This is the second convenience in two days that reached further than intended,
  the first being provenance inferred from a query's own output -- the same shape, a tool taking
  what is there rather than what was meant.
- **A consumer who does not state their requirements has delegated the design of their own inputs
  to someone with less information** -- and one who states them through an intermediary has
  delegated the reasoning too (D21). Opening four channels in an afternoon turned up two defects in
  our OWN schema (G39) that had sat unnoticed because aging wrote REQ-GO-2..10 on our behalf and
  nobody checked the contract against the table. Writing a first message forces you to state what
  you need, which forces you to check whether you know.
- **Re-test an upstream gap before reporting it again.** Already in this list for SDRF; it earned
  its keep again on 2026-09-22. All three pyMzLib gaps were re-run against 0.1.1 (confirmed latest
  via `pip index versions mzlib`) on real data before thread 001 went out. They still reproduce, so
  the report is dated and exact rather than inherited -- and if one had been fixed we would have
  reported a stale failure to the people who fixed it.
- **A requirement written on your behalf goes stale and you will not notice.** Our schema's own
  description cites `REQ-GO-2..10` -- which **aging** wrote for us, and which `go` had overruled in
  two later threads we were not party to. We built a table against the superseded version and only
  found out by opening the channel and being told *"trust D1-D22, not REQ-GO-2..10"*. If a
  contract in this schema names requirements somebody else authored, **check them against their
  owner's current rulings before building**, and prefer a flat current contract from the owner over
  a requirement list reconstructed from a thread.
- **FRAMEWORK.md is still partly a proposal.** Steps 1 (ingest) and 2 (build) are built and their contracts locked as D9 and D10; steps 3-6 (client/MCP, REST, deploy, auto-ingest) are not decided, so don't build on them as if they were.
- **The user is not a server or infrastructure person.** They said "out of my league" and rely on you to explain. Keep choices few and give a recommendation each time.
- **Don't re-own other projects' work.**
  - aging's rule (D1) applies here: the organelle map's content belongs to **aging** (since 2026-09-23: go D27, aging D46; `go` owns only the map's file format and GO machinery), metric definitions (`DEF-*`) to QuantProject under their own namespace, and the age normalizer to sdrf/mzLib.
  - Parse with pyMzLib typed readers where they exist.
  - dataRepo **never defines** (D24) and, since **D27** (2026-09-23), **operates nothing** either:
    it ships the software, including the runner through which an instance's OPERATOR (today aging)
    executes a released engine on stored data. D24's "dataRepo runs the engines" is superseded;
    aging accepted (055, their D45). Charter v0.2 still reads the D24 way until v0.3 is written.
    dataRepo still makes scratch runs on real data to TEST its software, never to serve. Who does
    what is in `design/CHARTER.md`, which is **not in force until all eight parties sign**.
- **`datarepo run` refuses THIS tree, by design** (editable install; aging 063). To test the runner on
  real data, call `engines.logs.run(..., install={...stand-in...})` from Python and say it is a scratch
  run, or install a clean clone at a commit into a venv. Never soften the refusal to make a test pass.
- **A fixture that does not follow the producer's grammar hides the whole path.** The test fixture's
  occupancy cells were `0.5` placeholders, so pyMzLib refused them, no occupancy test ever ran, and
  the first real one found a false label within minutes (0.21.0). Fixture cells must be in the
  producer's real format, covering each state the definition names.
- **`gh run list --commit` needs the FULL sha.** A short sha matches nothing and returns empty, so a
  watcher loop waits forever and reports nothing. Use `git rev-parse <short>`.
- **A fallback turns a producer's word into yours.** G75: a source column's own `not applicable`
  was read as empty and replaced by the row default, so 65 cells said `publication` that sdrf never
  wrote, and our sdrf 024 reported that to them as a fact about their file. Only the fix showed it.
  Any `x or default` over a producer's cell must treat a WRITTEN reserved word as written.
- **To ingest a peer's file against aging's real search, build a scratch run dir. Never write
  into `F:/aging_data`.** Junction each stage folder of `run_<date>/<PXD>`, put the file in
  `00_sdrf/metadata/`, junction `<work_root>/db` to `F:/aging_data/db`, and pass `--mm-settings
  F:/aging_data/mm_settings/1.1.11`. Without the last two, occupancy, contaminant and
  unresolved-mod findings are artefacts of the scratch setup (2026-09-27, PXD049018).
- **A PowerShell `@(@("old","new"))` is ONE flat pair, not a list of one pair.** A replace loop over it took `"/"` and
  `"o"` as the pair and turned every `/` in `docs/mcp.md` into `o` (2026-10-19, restored from git). Make text
  replacements with the Edit tool (`replace_all` for a version bump), never a hand-rolled PowerShell loop.
- **A whole DuckDB 1.5 file is exactly `12288 + total_blocks * block_size` bytes** (`pragma_database_size()`;
  measured on a fresh file and on aging's 62 GiB catalog). A file cut short still OPENS and answers until a query
  reaches the missing block. That is how aging 107 was diagnosed: the length was 4 KiB off the block grid, so the
  cut was not DuckDB's. `CatalogFile.Shortfall` checks it at build and in the MCP sandbox (1.3.3).
- **PowerShell `Set-Content -Encoding utf8` adds a BOM to .py files too** (0.28.0 version bump).
  Use `[IO.File]::WriteAllText` with `UTF8Encoding $false`, or the Edit tool.
- **A zip loses the Unix executable bit.** The first CI run of the binaries failed on Linux and both
  macOS builds with `Permission denied` on pyMzLib's `mzlib-bridge`. Unix builds ship `.tar.gz`,
  and the workflow unpacks WITHOUT chmod, so a lost bit still fails the smoke test.
- **A catalog id hashes the package version; a bundle id does not.** So every release makes a
  printed catalog id stale. `tests/test_getting_started.py` fails until the tutorial's version and
  ids are rerun; update the page, never the test.
- **Hand any user-facing page to an agent with nothing else.** The tutorial passed every review;
  a stranger with only the page and a fresh clone found a dozen faults in 2.5 minutes.
- **Repo moves and remote repoints are the user's.** The agent's `git remote set-url` was denied
  (2026-09-29); the user ran it. Publishing a release happened only on the user's explicit ask.
- **mzLib's PSM reader rewrites run names**: `SpectrumMatchFromTsv` deletes `.raw`, `.mzML`, `.mgf`,
  `.d` and the msalign extensions ANYWHERE in `File Name`. So `X.raw.thermo.raw` reads as `X.thermo`,
  and `run.day2` as `runay2`. `usi.RunNameMap` mirrors the rule (0.32.0, G80). A run-name mismatch
  is decided in mzLib's source, not by guessing strip order.
- **The auto-mode classifier refuses the agent's push and tag of a release** unless the user grants it in the
  session. For 1.3.1 (2026-10-08) the user said "you run it for me ... you have my permission", and the push, tag and
  `gh release edit --draft=false` all went through. Without that, commit locally and give the user the `!` commands
  one at a time. Either way: push master, wait for CI and dotnet-binaries to go green, tag, and publish only after the
  downloaded draft binary reproduces known bundle ids.
- **"The site doesn't show the new release" is usually the operator's pin, not our code.** Read
  `https://trishorts.github.io/aging-pipeline/.datarepo-site.json`: its `generator` names the datarepo
  that built the page. On 2026-09-30 it said 0.28.1 a day after 0.32.0 shipped, because aging's
  `publish_catalog_and_site.ps1` points at a venv that only moves when PXReprise switches (D39).
- **`threads.py new` needs `--date`** as well as `--project` and `--to`.
- **A peer can read our message while it is still the blank template.** PXReprise read our 044 between `threads.py new`
  and our writing its body, replied to an empty message, and nearly swapped to the wrong release (2026-10-19). Write the
  body to a scratch file FIRST, then allocate the number and fill both copies in the same command.
- **The .gitignore template ignores `bin/`.** Add a `!/<dir>/bin/` exception before putting code in any bin folder (G4).
- **C# port: parity is measured against what Python WROTE, never against what we expect it wrote.** Every
  port in `dotnet/` was checked by running the Python on the same inputs (scratch scripts, never shipped) and
  comparing rows, bytes or JSON. `dotnet/PORTING.md` is the convention; `DataRepo.Parity` is the tool
  (`roundtrip`, `ingest`, `compare`, `build`, `site`, `site-compare`, `study`). `IngestRules.Python0320` keeps
  0.32.0's rows reproducible forever and hashes ids from `parity-python-0.32.0`, so a parity bundle can
  never pass for a real one.
- **The ports surfaced platform-dependent Python.** pathlib sorted `Mods/*.txt` case-SENSITIVELY on Linux and
  case-insensitively on Windows, so the same search resolved modifications differently by OS (the C# pins the
  Windows order every stored bundle used). `dataset_databases.database` is `Path(p).name` of a Windows path.
  DuckDB renders TIMESTAMPTZ in the session's zone (Chicago here, UTC on CI). **CI on Linux is what finds
  these; never call a port done on a Windows-only run.**
- **`*.parquet` is gitignored repo-wide (D8).** The C# test fixtures need the `!/dotnet/tests/...` exception
  that exists; a new fixture folder elsewhere would silently not be committed and CI fails (it did, once).
- **Python `Path.write_text` writes CRLF on Windows**, which compounds the heredoc-backslash trap: a `\r\n`
  written by a Python patch script came out as CR CR LF. Patch C# with the Edit tool, or byte-level Python.
- **One version for the whole C# solution** (`dotnet/Directory.Build.props`, `0.0.0-dev` until CI stamps a
  release with `-p:Version` and `-p:SourceRevisionId`). It reaches bundle.json, `catalog_id` and the site's
  generator; three projects once read three different values. `datarepo run` refuses a `-dev` build.
- **Name no C# class after its namespace** (`DataRepo.Site.Site`): it cannot be reached by short name from
  other `DataRepo.*` namespaces. Hence `SiteGenerator`, `StudyWriter`, `CatalogBuilder`.
- **PXReprise rewrites the live `F:/aging_data/batch/manifest.yaml` non-atomically**: a reader caught it
  half-written once (2026-10-04). Retry before diagnosing a YAML error in it; tell PXReprise.
- **Moving dataRepo to mzLib 1.0.595 moves NO ingested row** (measured 2026-10-19 by datarepo-9b on
  `feat/1.4.0-ingest`: PXD022180 `6e3e74097cf82695` and PXD011740 `c56354676fd7c929` on both 1.0.593 and 1.0.595,
  every table equal). From 1.0.594, #1403 writes UniProt-named modifications as UNIMOD ids in mzLib's psmtsv
  `ProForma` field (`[UniProt:N6,N6-dimethyllysine on K]` -> `[UNIMOD:36]`), but no ingest code reads that field:
  peptidoform keys and USIs come from our own `Proforma.cs` over the full sequence (`Identifications.cs`). This bullet
  said the keys move for two weeks, and the 1.4.0 plan (PXReprise 049 item 1) repeated it: a belief, not a measurement.
  **But mzLib 1.0.597 DOES move peptidoform keys** (measured 2026-11-11, `results/mzlib597_2026-11-11/` on `feat/1.5.0`):
  #1416/#1524 link 106 UniProt modifications to Unimod in mzLib's own code, and our `Proforma.cs` asks mzLib, so a mass
  tag becomes an accession (967 of 360,551 keys in PXD034564). The bundle id does NOT move, so an mzLib bump rides an
  ingest-path bump. **The psmtsv canary passed and saw none of it:** measure every bump by ingesting real deposits on both
  versions and comparing every table.
- **A pre-release mzLib makes the go engine refuse, by design** (GO-A1: go files from an unreleased writer are never
  stored). On a branch built against a locally packed mzLib, the go tests fail for that reason alone.
- **MetaMorpheus modification names can hold brackets** (`[Metal:Cu[I] on D]`). Parse full sequences by bracket depth
  (`PtmQtlCore.ModificationNames`), never with a flat `\[...\]` pattern. ptmQtl's own tooling had the flat one.
- **In the Bash tool, a `cat > file` with no heredoc and no input blocks until the 2-minute timeout**, and nothing
  after it in the command runs. Write files with the Write tool.
- **"Biological" is mzLib's category, not a table of ours** (D45). Never add an IdWithMotif-to-class map. Read the
  category off MetaMorpheus's names.
- **With a design, protein-group columns are SAMPLES, not runs** (PXR-R9, 1.3.1). MetaMorpheus labels
  `Intensity_`/`SpectralCount_`/`*Occupancy_` columns `{Condition}_{Biorep}` whenever a condition or fraction is
  defined (mzLib `SampleGroupBuilder`), and sums each sample's files. The peptide and peak tables stay per file. Every
  aging batch search has a design since 2026-10-07. Anything that maps a protein-group label to a run goes through
  `SampleColumns`, never `RunNameMap` alone. PXReprise's pre-fix trial provenance also keyed contamination by sample
  label.
- **A PSM `count_mismatch` is the norm, not a signal** (G93). 62 of 94 stored bundles miss results.txt by up to
  ~1,300 PSMs. Measure the store before calling one new; a draft once claimed 1.1.11 "matched exactly".
- **A peer can reproduce our bundle id exactly, which makes it the best cross-check.** The id hashes each source's role
  and sha256, never its path, and the manifest entry's content fields, never `work_root`. PXReprise 030 matched both
  predicted ids. A scratch copy of a manifest with a relative `work_root` (the trial's `../runs`) must make it
  absolute.
- **`RealRunFoldersMatchPython` (RealData) fails while PXReprise re-searches a deposit**: its `04_search` folder
  vanishes mid-search (PXD008934, 2026-10-08). That is environmental. Run CI-equivalent with
  `--filter "TestCategory!=RealData"`.
- **On Windows a file another process holds open can be DELETED (DuckDB allows it) but not REPLACED.** 1.3.0/1.3.1's
  `File.Move(overwrite)` crashed aging's builds whenever anything read the catalog; Python had deleted first, then
  renamed. Row parity could never see it. aging's 098 "measured" that an MCP server does not block by deleting the file:
  a delete test is not a replace test. Test the operation you ship (fixed in 1.3.2).
- **DuckLake takes ownership of every file registered with `ducklake_add_data_files`.** One default `CHECKPOINT`
  merged registered bundle files and scheduled the originals for deletion, even outside DATA_PATH (re-run
  independently, 2026-10-11). Never register the store itself.
- **A view over Parquet in the MCP sandbox needs `allowed_directories` set BEFORE `enable_external_access=false`**, set
  as SET statements (not a connect option), and only absolute paths pass. A relative path resolved through
  `file_search_path` is refused (`results/public_data_2026-10-11/sandbox_allowed.py`).
- **Large real ingests need time and RAM.** PXD012307's 6.2 GB psmtsv took 17 min and ~30 GB; PXD051715's 3.3 GB
  took 9 min. Run them in the background, and the small ones in parallel (512 GB here).
- **Key a reference annotation by the TARGET SET, never by one database file** (D50, kegg 004). aging's proteome XMLs
  hold no isoform entries. Every isoform is in an overlay file loaded beside them, and 173 of 178 datasets load two to
  four target files. A per-file key cuts an isoform from its entry, which breaks go's D37 inheritance. Our kegg 003
  shipped that mistake and patched over it with a view rule. go's review caught it, not ours.
- **The auto-mode classifier refuses the agent's delete of store files, even with the user's order** (2026-10-25,
  "Irreversible Local Destruction"). Hand the user the command. **The `!` prefix runs bash here, not PowerShell**: give
  `find ... -delete` rather than `Get-ChildItem | Remove-Item`. Record what is deleted (path, size, the hash run.json
  keeps) first, and verify with a scratch build after. **On 2026-11-05 a `!` line and a pasted `Remove-Item` both arrived as chat
  text and ran nothing,** and the refusal also covered the agent's own scratch folder and said not to re-issue the delete through
  another shell. Ask the user to paste the command into a separate PowerShell window.
- **A raw file's name is not its identity; `runs.sha256` is.** 193 deposits passed PXReprise's duplicate check (between
  deposits only, name + size), yet PXD006815 holds one run under two animals' names and two deposits share three renamed
  runs. `SELECT sha256, list(DISTINCT dataset_id), list(file_name) FROM runs GROUP BY sha256 HAVING count(*) > 1` finds
  them. With a design, MetaMorpheus has already summed a copy into that sample's pooled values, so dropping the run
  after the search does not undo it.
- **PRIDE's contact fields do not identify people** (measured on 193 records, ptmQtl 061). A lab head's contact id is a
  fresh copy per deposit, no lab head has an ORCID, a submitter account can be a core facility across labs, the named
  lab head can be the MS collaborator, and `last_name` can read `PhD`. PRIDE also edits its records after deposit, so
  they stay out of bundles.
- **`PYTHONIOENCODING` is ignored under `python -I`,** and `-I` is required for scripts reading downloaded data, so a
  PRIDE name crashes the print on cp1252. Call `sys.stdout.reconfigure(encoding="utf-8")` in the script.
- **A bundle in the store is not a bundle in the catalog.** PXReprise 084 counted PXD031782 as served by reading the store,
  and we repeated it to the user as a cost of a schema bump. Its only bundle is schema 0.0.15, so 1.4.0 had already excluded it.
  Ask `catalog_bundles`, not the folder.
- **A search that trained no PEP still has numbers in `PEP_QValue`.** PXD058775's `PEP` column holds one value, and 229 target
  rows read `PEP_QValue` at or below 1%. Whether PEP trained is decided per search, from results.txt's PEP block (pep 007), never
  from the row.
- **A bundle id proves nothing about a reader change.** It hashes inputs, never code, so the same id comes back from different
  rows. Compare the tables' bytes with the served bundle. For a reader, keep the old one in the test as the oracle.
- **The Write tool can turn `\u` escapes into raw characters.** A raw U+2028 in a C# string broke the build (2026-11-05). Grep a
  new test file for non-ASCII bytes before building.
- **`RunNameMap.Resolve` has a side effect:** it counts every unmatched name. Cache only names that matched.
- **A deposit's search folder is not under one date.** Read `run:` in `F:\aging_data\batch\manifest.yaml`
  (`run_2026-09-21/<PXD>`). `F:\aging_data\batch\state.json` keys its entries under `datasets`.
- **Five deposits are not the store.** "1.4% to 3.0% of rows have no ions" came from five deposits, none low-resolution, and reached two
  peers before a count of every served `AllPeptides.psmtsv` showed 21 deposits collapsing. That count takes 5 min at five at a time
  (`results/pep_rule_2026-11-05/rule_uncomputed.py`). Run it before quoting a peer anything about a rule.
- **`LogLoss: Infinity` does not mean PEP failed.** 64 deposits read it and 44 of them gain rows under 1% `PEP_QValue`. No line of the training
  report separates the deposits that lose rows. And the loss is at peptide level only: 18 of those 21 gain PSMs.
- **A `PEP_QValue` above 1 does not mean "not computed".** The unset value is exactly 2. PXD020462 holds 57,407 target rows above 1, mostly real
  numbers such as 1.0212. Whether PEP was computed is decided per search (mzLib's `QuantifiedPsmRule`).
- **PowerShell 5.1 drops an empty-string argument to a native program.** `script.py a "" b` arrives as two arguments, so a positional value silently shifts. It recorded PXR-R51 as
  answered instead of asked in our 091 (2026-11-06), caught before the commit. Use named flags.
- **The auto-mode classifier also refuses the agent's `git push origin --delete`, even on the user's order** (2026-11-06, "Git Destructive"). Hand the user the command, for a separate
  PowerShell window. Do not route around it with `gh api`.
- **"Only source" is a claim about every peer's outputs.** We told the user results.txt was the only source of per-run scan counts. It was the only source of those `metrics` rows, while the QC
  report held the same MS2 count on all 5,051 runs, in a table we already store. The user caught it. Say which rows a source fills, and ask the producer before saying nothing else holds a fact.
- **A statement's kind does not say it only reads, and `allowed_directories` allows writing as well as reading** (2026-11-06, G128; the statements are in `results/sandbox_2026-11-06/` on `feat/1.4.4`, kept off
  master until the release). So what a statement may call is an allow-list, and a test makes each function a new DuckDB adds a decision. `json_serialize_sql` reports a failure as a document, not an error: check its
  `error` field, or a walk over it finds nothing to object to.
- **A review's reproduction is one door.** The review named one statement, and a fix for that alone passed all 718 tests and still wrote into the store. Listing everything the engine offers and trying what
  could write found the rest in minutes, including a forgery the review missed. Sweep the class before calling a hole closed.
- **Master is public whenever anyone pushes it, so a recipe for a hole in released binaries does not go in its notes or journal.** I wrote the statements into both and took them out before the push (2026-11-06).
- **Never send a write probe through our own `datarepo` MCP tool.** It serves aging's real store. Build a scratch folder catalog and drive `datarepo mcp` over stdio (`results/sandbox_2026-11-06/` on `feat/1.4.4`).
- **`ci.yml` runs on a push to ANY branch, using that branch's own workflow, so an old branch can go red for old reasons.**
  `wip/d37-g81-python` (run 42147234119, 2026-11-06) predates master's `duckdb<2` pin, so pip took DuckDB 2.0.0 and its tests stop on
  `ResourceInUseException`. That says nothing about master. The branch's tests were never run and it is not to be merged, so leave it red.
- **`[skip ci]` on the HEAD commit of a push skips CI for the whole push,** release merge included. A notes commit on top of an unpushed release merge must not carry it
  (2026-11-07, D57's commit, caught before the push).
- **A folder catalog's id hashes the folder its views point at** (`data_root`, `derived_root`), so the same store built into another `--out` gets another id, on 1.4.3 too.
  Compare `release_id` across folders, and rebuild into the same folder to see an id hold (2026-11-07, probing the release).
- **Run `claude mcp add` from Bash, not PowerShell.** PowerShell 5.1 drops the `--` before the server's command line, so the add fails ("unknown option '--catalog'")
  after the `remove` has already gone through, leaving no entry (2026-11-07).
- **The user rules on our matters in other projects' sessions.** The SDRF's maker (PXReprise D65) and the search's own SDRF (QuantProject 080) were both decided there
  while we were asking. Read the inbox before putting a question to the user again.
- **`dataset_databases`, `datasets.search_database` and `bundle.json`'s `protein_databases` name the database GPTMD STARTED from, not the one the
  search read.** With a GPTMD task the search reads `*GPTMD.xml` (results.txt "Databases loaded"), which is recorded only in the bundle's
  `sources/provenance_04_search.json` `outputs[]` (G131). Never answer "which database was searched" from those tables.
- **A listing that does not recurse will tell you a file is gone.** GPTMD's databases sit in a task subfolder of `04_search`; a wildcard
  `Get-ChildItem` on the search folder found none, and a draft to PXReprise said ten searches' databases were deleted (2026-11-09, caught before
  sending). Use `-Recurse` or a `**` glob before claiming anything is missing.
- **aging's `latest.json` moves while you work.** A comparison of a scratch rebuild against "the serving catalog" first read an older 204-bundle catalog
  (2026-11-09). Read the catalog id `latest.json` names when you start, and compare against that id, not the file name.
- **Re-run every engine on every deposit after a re-ingest, and read the build's `note` lines.** Replaying each old gene artefact for the
  deposits it was first requested for left two databases unresolved and six deposits with almost no gene names (PXD005035 21,791 -> 70),
  and the build passed all 3,979 checks; only a `logs.resolve_genes coverage ... 39 of 41` note said so (2026-11-13).
- **A build refuses a study bundle of another layer version, and aging's publish names one (`--study-latest aging`).** At a layer bump
  aging must run `datarepo study` with the new binary before its first publish.
- **DuckDB refuses a file pattern that matches nothing, in every form** (a list of patterns, a table macro, a subquery as the argument;
  1.5.5). A view over files that may not exist yet must be created only when one does. A half-written last NDJSON line reads as a null
  row under `ignore_errors = true`.
- **A `--release` build of a catalog already in the folder returned "unchanged" and recorded nothing**, so the file was never marked a
  release and `--keep` could prune it. Fixed on `feat/ai-contributions-v2` (`647a2b7`); 1.5.0 still has it.
- **A required schema field breaks CI's `schema` job, not the C# tests:** `examples/minimal_bundle.yaml` takes it by hand and
  `examples/ingested_bundle.yaml` is exported from a C# ingest with `tools/build_example_bundle.py --bundle`. It was red for a day
  unnoticed (1.5.0, `7f4fca5`). A new CLI command must also be listed in `tools/build_cli_docs.py`'s `GROUPS`.
- **Send a thread message with `.project/tools/send_thread.py`, not a helper rebuilt in the scratchpad** (one died with its session
  and took `--asks NONE` literally). Write the body to a file, then `python -I .project/tools/send_thread.py --project dataRepo
  --to <peer> --date <YYYY-MM-DD> --body <file> [--asks A,B] [--answers C,D]` allocates the number and fills both copies at once.
  Read the front matter, then commit each copy alone in its own repo.
- **Read the peer's repository log just before committing a thread message.** PXReprise released engine 0.4.50 while our 121 was
  being drafted, and one sentence went stale; it was caught only because both copies were still uncommitted. A number from
  `threads.py new` catches a peer's new message, not a peer's release.
- **A peer's design choice inside a merge is not the user's ruling.** PXReprise's #4 built two release lines (`datarepo-v*` beside
  `v*`) that nobody put to the user; asked, the user ruled one release (D73). When a peer's PR settles something that is the
  user's (versions, releases, what ships), name it to the user before building on it.
- **The engine and datarepo meet in four places:** the manifest, the search output folder, datarepo's command line and JSON reply,
  and the shared `PXReprise.Storage` code. A change to any of them changes both programs. No test crosses them yet (G139), and they
  had already drifted once (engine 0.4.48 writes `split_reason: tissue`; datarepo 1.4.5 refuses it).
- **On smith-chem-wisc/PXReprise, green CI is not a release check.** The required check builds everything and runs both test
  projects (all but `Category=ExternalService`). But the 18 `RealData` tests skip themselves on GitHub, a release tag runs no test
  suite (one end-to-end run per platform), and `datarepo-binaries.yml` runs on no pull request. Run the RealData tests on this
  machine before a release.
- **A recursive `grep` over `E:\GitClones\PXReprise-dataRepo\tests` in Bash ran past two minutes** (build output under `bin/` and
  `obj/`). Use the Grep tool with `glob: *.cs`.

**Sibling project: `E:\CodeReview\aging`** (the NCEMS pipeline). aging *produces* results under
`F:\aging_data\<run>\<PXD>\` with `provenance.json` (schema `aging-provenance/2`). dataRepo *ingests and serves*
them and never re-runs a search. Requests between the two go through aging's thread convention
(`aging/design/threads/`).

**Raw data never goes on E:** (aging D3). **D8: no data in this repo.** aging hosts the data instance (bundles, releases, DOIs, the deployed service); the software ships from smith-chem-wisc/PXReprise (D74), and this repo is the project's record.

**At the start of a session (your first response in this folder), render the standard `/project brief`
once.** Format and derivation are in the `project` skill's `references/session-brief.md`. State lives in
`.project/state.yaml`. `RESUME.md` is rendered fresh by `/project`, so do not hand-edit its generated block.

Layout: `design/` `lit/` `code/` (worktrees, gitignored) `data/` (+PROVENANCE) `results/`
`manuscript/` `submission/`. Conventions and dispatch live in the `project` skill.
