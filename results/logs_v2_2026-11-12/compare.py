"""1.5.0 item 5 with mzLib 1.0.598 (scratch, read-only on aging's store): v2 gene-resolution artefacts written by the
runner on the inputs of aging's stored v1 artefacts, compared with them. Every v1 column must be equal row for row;
ensembl_xref_agreement must pair with ensembl_xref_agrees as logs 034 says; entry counts are set beside logs 034's."""
import glob
import json
import os
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
V1 = "F:/aging_data/repo/store/_engine/logs.resolve_genes"
V2 = "F:/datarepo_scratch_150/logs_v2_store/_engine/logs.resolve_genes"
con = duckdb.connect()


def record(d):
    return json.load(open(os.path.join(d, "run.json"), encoding="utf-8"))


stored = {}
for d in glob.glob(f"{V1}/*"):
    r = record(d)
    key = (r["inputs"]["search_database"], r["inputs"]["gene_set"], r["inputs"]["xref"])
    stored.setdefault(key, []).append((d, r))

ok = True
for d in sorted(glob.glob(f"{V2}/*")):
    r2 = record(d)
    key = (r2["inputs"]["search_database"], r2["inputs"]["gene_set"], r2["inputs"]["xref"])
    db = os.path.basename(r2["input_files"]["search_database"])
    print(f"v2 artefact {os.path.basename(d)}: {db}, definition {r2['definition_id']}, release {r2['release']}")
    a2 = f"{d}/gene_resolutions.parquet"
    v1s = [(x, r) for x, r in stored.get(key, []) if r["definition_id"].endswith("v1")]
    if not v1s:
        print("  no stored v1 artefact with these inputs")
        ok = False
        continue
    for x, r1 in v1s:
        a1 = f"{x}/gene_resolutions.parquet"
        cols1 = [c[0] for c in con.execute(f"DESCRIBE SELECT * FROM '{a1}'").fetchall()]
        shared = [c for c in cols1 if c not in ("definition_id", "ensembl_xref_agreement")]
        sel = ", ".join(f'"{c}"' for c in shared)
        n1 = con.execute(f"SELECT count(*) FROM '{a1}'").fetchone()[0]
        n2 = con.execute(f"SELECT count(*) FROM '{a2}'").fetchone()[0]
        only1 = con.execute(f"SELECT count(*) FROM (SELECT {sel} FROM '{a1}' EXCEPT ALL SELECT {sel} FROM '{a2}')").fetchone()[0]
        only2 = con.execute(f"SELECT count(*) FROM (SELECT {sel} FROM '{a2}' EXCEPT ALL SELECT {sel} FROM '{a1}')").fetchone()[0]
        v1col = con.execute(f"SELECT count(*) FILTER (WHERE ensembl_xref_agreement IS NOT NULL) FROM '{a1}'").fetchone()[0] \
            if "ensembl_xref_agreement" in cols1 else "absent"
        print(f"  vs stored {os.path.basename(x)} ({r1['definition_id']}, mzLib {r1['release'].get('mzlib')}): rows {n1:,} / {n2:,}; "
              f"{len(shared)} v1 columns: {only1} rows only in v1, {only2} only in v2; v1's agreement cells filled: {v1col}")
        ok &= only1 == only2 == 0 and n1 == n2
    pairs = con.execute(f"""SELECT ensembl_xref_agrees, ensembl_xref_agreement, count(*) FROM '{a2}' GROUP BY ALL ORDER BY ALL""").fetchall()
    print("  (ensembl_xref_agrees, ensembl_xref_agreement, rows):", pairs)
    bad = con.execute(f"""SELECT count(*) FROM '{a2}' WHERE (ensembl_xref_agreement IS NULL) <> (ensembl_xref_agrees IS NULL)
                         OR (ensembl_xref_agrees AND ensembl_xref_agreement <> 'agrees')
                         OR (NOT ensembl_xref_agrees AND ensembl_xref_agreement = 'agrees')""").fetchone()[0]
    ids = con.execute(f"SELECT list(DISTINCT definition_id) FROM '{a2}'").fetchone()[0]
    entries = con.execute(f"""SELECT count(DISTINCT entry_accession) FILTER (WHERE ensembl_xref_agreement = 'agrees'),
                                     count(DISTINCT entry_accession) FILTER (WHERE ensembl_xref_agreement IN ('agrees', 'silent')),
                                     count(DISTINCT entry_accession) FILTER (WHERE ensembl_xref_agreement = 'disagrees')
                              FROM '{a2}'""").fetchone()
    print(f"  rows breaking logs 034's pairing: {bad}; definition ids on rows: {ids}")
    print(f"  entries with a row that agrees: {entries[0]:,}; agrees or silent: {entries[1]:,}; disagrees: {entries[2]:,}")
    ok &= bad == 0 and ids == ["logs:DEF-GENE-RESOLUTION v2"]
print("RESULT:", "v2 = v1 + the new column, paired as logs 034 says" if ok else "DIFFERENCES")
