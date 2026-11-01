"""Can each reconciliation check's explained bound (aging 122, DATAREPO-86) be derived from a bundle's STORED rows?

Scratch measurement for 1.4.1 option A (build-side, no re-ingest). Reads aging's serving catalog's bundles read-only and
compares the derived terms with aging's exact ones (results/reconciliation_2026-10-29/recon_band.tsv in aging, read
from the producer files).

PSMs: count = target, q <= 0.01, notch q <= 0.01, notch resolved (Identifications.ProducerCounts).
  lower = count - counted rows whose q or notch q is exactly 0.01 (printed 0.010000);
  upper = count + passing rows whose notch is ambiguous.
Peptides: count = the recorded ingest count (AllPeptides.psmtsv; not reproducible from stored rows).
  The terms are approximated per peptidoform from its supporting PSMs:
  amb_best = its best-scoring target PSM passes and is notch-ambiguous; amb_any = any passing supporting PSM is;
  rnd = best_q_value or best_q_value_notch exactly 0.01.
  lower = count - amb - rnd; upper = count.
"""
import csv, json, sys
from pathlib import Path
import duckdb

CATALOG = sys.argv[1]
AGING_TSV = sys.argv[2]
OUT = Path(sys.argv[3])

exact = {(r["dataset"], r["check"]): r for r in csv.DictReader(open(AGING_TSV), delimiter="\t")}
cat = duckdb.connect(CATALOG, read_only=True)
bundles = cat.sql("select dataset_id, bundle_id, path from catalog_bundles order by dataset_id").fetchall()
con = duckdb.connect()
rows = []
for ds, bid, path in bundles:
    recon = {c["name"]: c for c in json.load(open(Path(path) / "bundle.json", encoding="utf-8")).get("reconciliation", [])}
    psms = Path(path) / "psms.parquet"
    if not psms.exists():
        continue
    p = con.sql(f"""
        select count(*) filter (where not coalesce(notch_ambiguous, false)),
               count(*) filter (where coalesce(notch_ambiguous, false)),
               count(*) filter (where not coalesce(notch_ambiguous, false) and (q_value = 0.01 or q_value_notch = 0.01))
        from read_parquet('{psms.as_posix()}')
        where target_decoy = 'target' and q_value <= 0.01 and (q_value_notch is null or q_value_notch <= 0.01)""").fetchone()
    count, amb, rnd = p
    c = recon.get("psms_target_1pct", {})
    exp = c.get("expected")
    rows.append(dict(dataset=ds, bundle=bid, check="psms_target_1pct", observed=c.get("observed"), recount=count,
                     expected=exp, amb=amb, rnd=rnd, lower=count - rnd, upper=count + amb,
                     inside=None if exp is None else (count - rnd <= exp <= count + amb), ok_recorded=c.get("ok"),
                     aging_amb=exact.get((ds, "psms_target_1pct"), {}).get("ambiguous_notch_rows"),
                     aging_rnd=exact.get((ds, "psms_target_1pct"), {}).get("prints_0_010000")))
    peps = Path(path) / "peptidoforms.parquet"
    c = recon.get("peptidoforms_target_1pct", {})
    if peps.exists() and c:
        q = con.sql(f"""
            with best as (
                select peptidoform, arg_max(coalesce(notch_ambiguous, false), score) as best_amb,
                       bool_or(coalesce(notch_ambiguous, false) and q_value <= 0.01
                               and (q_value_notch is null or q_value_notch <= 0.01)) as any_amb
                from read_parquet('{psms.as_posix()}') where target_decoy = 'target' group by peptidoform)
            select count(*) filter (where b.best_amb), count(*) filter (where b.any_amb),
                   count(*) filter (where p.best_q_value = 0.01 or p.best_q_value_notch = 0.01)
            from read_parquet('{peps.as_posix()}') p left join best b using (peptidoform)
            where p.target_decoy = 'target' and p.best_q_value <= 0.01
              and (p.best_q_value_notch is null or p.best_q_value_notch <= 0.01)""").fetchone()
        amb_best, amb_any, prnd = q
        obs, exp = c.get("observed"), c.get("expected")
        rows.append(dict(dataset=ds, bundle=bid, check="peptidoforms_target_1pct", observed=obs, recount=None,
                         expected=exp, amb=amb_best, rnd=prnd, lower=None if obs is None else obs - amb_best - prnd,
                         upper=obs, inside=None if exp is None or obs is None else (obs - amb_best - prnd <= exp <= obs),
                         ok_recorded=c.get("ok"), amb_any=amb_any,
                         inside_any=None if exp is None or obs is None else (obs - amb_any - prnd <= exp <= obs),
                         aging_amb=exact.get((ds, "peptidoforms_target_1pct"), {}).get("ambiguous_notch_rows"),
                         aging_rnd=exact.get((ds, "peptidoforms_target_1pct"), {}).get("prints_0_010000")))

OUT.mkdir(parents=True, exist_ok=True)
keys = sorted({k for r in rows for k in r}, key=lambda k: list(rows[0]).index(k) if k in rows[0] else 99)
with open(OUT / "bound.tsv", "w", newline="") as f:
    w = csv.DictWriter(f, keys, delimiter="\t"); w.writeheader(); w.writerows(rows)
for check in ("psms_target_1pct", "peptidoforms_target_1pct"):
    sel = [r for r in rows if r["check"] == check]
    failed = [r for r in sel if r["ok_recorded"] is False]
    print(check, "bundles", len(sel), "recorded-failed", len(failed),
          "inside(best)", sum(1 for r in failed if r["inside"]),
          "inside(any)", sum(1 for r in failed if r.get("inside_any")) if check.startswith("pep") else "",
          "recount!=observed", sum(1 for r in sel if r["recount"] is not None and r["recount"] != r["observed"]))
    for r in failed:
        if not r["inside"]:
            print("  outside:", {k: r.get(k) for k in ("dataset", "observed", "expected", "amb", "amb_any", "rnd", "aging_amb", "aging_rnd")})
