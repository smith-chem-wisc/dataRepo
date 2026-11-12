# PRIDE records and shared raw files (1.5.0 build list item 12), 2026-11-12

**Built as agreed** (U20, U21; ptmQtl's DATAREPO-P35 in our 061, accepted in their 062; the user: "build it"):
`datarepo pride` keeps each deposit's PRIDE record beside the bundles, `build` reads the newest into `deposit_records`,
`deposit_contacts` and `deposit_references`, and the `shared_raw_files` view finds runs whose raw file is served more than
once, by `runs.sha256`.

**Method.** A scratch build (`F:/datarepo_scratch_150/cli_item12b`) fetched the record of every deposit in aging's serving
catalog `3bde62130d08a4c4` (194 deposits) into a scratch store, and the eight deposits of `store_598b` into that store, from
which a scratch folder catalog was built (`build.log`). `measure.py` reads the records, that catalog's three tables, and runs
the view's SQL, as the build wrote it, over the runs of aging's serving catalog (read-only). Output: `measure.out`.

**Result.**

- **All 194 fetched, none failed, all found.** Fetching the eight again wrote nothing ("unchanged"). The scratch catalog of
  eight bundles builds, 157 checks passed, with 8 records, 16 contacts and 8 papers.
- **The view finds exactly the cases our 061 reported, and only them:** PXD006815's `Z73a` and `Z74` (one file, within the
  deposit) and PXD033430's three `Control-*` files under PXD057544's names (across deposits). 8 runs of 5,838.
- **The records still show what our 061 told ptmQtl:** one lab head and one submitter on every deposit, no lab head with an
  ORCID, no lab-head contact id on two deposits, and submitter accounts shared across deposits (21). The other counts moved a
  little since 2026-11-04, because aging's catalog changed (193 -> 194 deposits) and PRIDE edits its records. Papers: 0 on 23
  deposits, 1 on 168, 2 on 3; of 174, PubMed 0 on 23, no citation line on 15, no DOI on 2. Submitter ORCID 127 of 194. The
  `PhD` last name of our 061 was on PXD028852 and PXD049018, which aging's catalog no longer serves.
- **Found by filling it: e-mail addresses in free text.** Leaving PRIDE's e-mail field out did not keep e-mail out: two
  affiliations (PXD015079, PXD021194) held an address the submitter typed in, one with a telephone number. Every kept text now
  has any e-mail address replaced by `[e-mail removed]` (`PrideRecords.WithoutEmail`); after the fix no record holds an
  address and those two hold the marker. An `@` with no dotted domain after it (`BayBioMS@MRI`, a facility's name) is kept.
  The telephone number is kept, as written; whether to remove it too is the user's.
- The first scratch fetch, before the fix, is `F:/datarepo_scratch_150/pride_store`; it holds the two addresses as PRIDE
  publishes them. The measured store is `pride_store2`.
