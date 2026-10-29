"""Scratch: check the two biggest attributions exactly.
G101: in a deposit whose ptm_sites shrank, only O76011 and P19013 lose site rows (per protein, old vs new).
PXR-R23: the rows quant_values and ptm_stoichiometry gained are exactly the rows on design_sample assays."""
import csv, os, duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
OLD = r"F:\aging_data\repo\store"
rows = {r["accession"]: r for r in csv.DictReader(open(os.path.join(HERE, "compare_deposits.tsv"), encoding="utf-8"), delimiter="\t")}
exp = {r["accession"]: r["causes"].split() for r in csv.DictReader(open(os.path.join(HERE, "explained.tsv"), encoding="utf-8"), delimiter="\t")}
c = duckdb.connect()
P = lambda d, t: os.path.join(d, t + ".parquet").replace("\\", "/")
bad = []
for acc, causes in sorted(exp.items()):
    r = rows[acc]
    if not r["new_bundle"]:
        continue
    old, new = os.path.join(OLD, acc, r["old_bundle"]), os.path.join(HERE, "store", acc, r["new_bundle"])
    if "G101" in causes:
        diff = c.sql(f"""
            WITH o AS (SELECT protein_accession p, count(*) n FROM '{P(old, "ptm_sites")}' GROUP BY 1),
                 n AS (SELECT protein_accession p, count(*) n FROM '{P(new, "ptm_sites")}' GROUP BY 1)
            SELECT coalesce(o.p, n.p), coalesce(o.n, 0), coalesce(n.n, 0) FROM o FULL JOIN n USING (p)
            WHERE coalesce(o.n, 0) <> coalesce(n.n, 0)""").fetchall()
        others = [d for d in diff if d[0] not in ("O76011", "P19013")]
        if others: bad.append((acc, "G101: other proteins' sites differ", others[:5]))
    if "PXR-R23" in causes:
        for table in ("quant_values", "ptm_stoichiometry"):
            if not os.path.exists(P(new, table)):
                continue
            n_old = c.sql(f"SELECT count(*) FROM '{P(old, table)}'").fetchone()[0] if os.path.exists(P(old, table)) else 0
            n_new, pooled = c.sql(f"""SELECT count(*), count(*) FILTER (WHERE a.assay_kind = 'design_sample')
                FROM '{P(new, table)}' t LEFT JOIN '{P(new, "assays")}' a USING (assay_id)""").fetchone()
            if n_new - n_old != pooled:
                bad.append((acc, f"PXR-R23 {table}: gained {n_new - n_old}, pooled rows {pooled}"))
print("checked; mismatches:", len(bad))
for b in bad: print(" ", b)
