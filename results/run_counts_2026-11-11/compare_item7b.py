"""1.5.0 item 7, second half: what reading PXReprise's QC payload and relabelling results.txt's per-run rows changed.

For each deposit with a bundle in both scratch stores, every table is compared row for row (order-free); for each
deposit, the per-run counts are listed by name, source and definition, the payload stage read, and the findings item 7
writes. Read-only; the stores are scratch."""
import json
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
OLD = Path(sys.argv[1] if len(sys.argv) > 1 else "F:/datarepo_scratch_150/store_item7")
NEW = Path(sys.argv[2] if len(sys.argv) > 2 else "F:/datarepo_scratch_150/store_item7b")
CODES = ("run_counts_missing", "qc_payload_not_read", "qc_payload_definition_unknown", "qc_payload_files_unplaced", "qc_payload_counts_not_whole")


def bundle(store, ds):
    dirs = sorted((store / ds).glob("*/bundle.json"), key=lambda p: p.stat().st_mtime) if (store / ds).exists() else []
    return dirs[-1].parent if dirs else None


con = duckdb.connect()
for ds_dir in sorted(p for p in NEW.iterdir() if p.is_dir()):
    ds = ds_dir.name
    new = bundle(NEW, ds)
    old = bundle(OLD, ds)
    print(f"== {ds}  new {new.name}" + (f"  old {old.name}" if old else "  (no item-7 bundle to compare)"))
    if old:
        tables = sorted({p.name for p in new.glob("*.parquet")} | {p.name for p in old.glob("*.parquet")})
        for t in tables:
            a, b = old / t, new / t
            if not a.exists() or not b.exists():
                print(f"   {t}: only in {'new' if b.exists() else 'old'}")
                continue
            only_old = con.sql(f"SELECT count(*) FROM (SELECT * FROM '{a.as_posix()}' EXCEPT ALL SELECT * FROM '{b.as_posix()}')").fetchone()[0]
            only_new = con.sql(f"SELECT count(*) FROM (SELECT * FROM '{b.as_posix()}' EXCEPT ALL SELECT * FROM '{a.as_posix()}')").fetchone()[0]
            if only_old or only_new:
                print(f"   {t}: {only_old} row(s) only in old, {only_new} only in new")
        old_sources = {s["role"] for s in json.load(open(old / "bundle.json", encoding="utf-8"))["sources"]}
        new_sources = {s["role"] for s in json.load(open(new / "bundle.json", encoding="utf-8"))["sources"]}
        print(f"   sources added: {sorted(new_sources - old_sources)}, removed: {sorted(old_sources - new_sources)}")
    m = (new / "metrics.parquet").as_posix()
    for row in con.sql(f"""
        SELECT name, source, definition_id, count(*) AS runs, sum(value)::BIGINT AS total
        FROM '{m}' WHERE scope = 'run' AND name IN ('psms_1pct','peptides','protein_groups','precursors','ms2_scans','ms2',
          'psms_1pct_whole_search','peptides_1pct_whole_search','protein_groups_1pct_whole_search')
        GROUP BY ALL ORDER BY source, name""").fetchall():
        print("   run", *row)
    for row in con.sql(f"SELECT name, value, definition_id FROM '{m}' WHERE scope = 'dataset' AND source = 'results.txt' ORDER BY name").fetchall():
        print("   dataset", *row)
    sources = [s for s in json.load(open(new / "bundle.json", encoding="utf-8"))["sources"] if s["role"] in ("qc_payload",) or s["role"].startswith("provenance:05")]
    for s in sources:
        print(f"   source {s['role']} {s.get('bundle_path')} {s['sha256'][:12]}")
    f = (new / "findings.parquet").as_posix()
    for code, severity, message in con.sql(f"SELECT code, severity, message FROM '{f}' WHERE code IN {CODES} ORDER BY code").fetchall():
        print(f"   finding {code} ({severity}): {message}")
