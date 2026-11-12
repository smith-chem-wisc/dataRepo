import json, sys, duckdb, yaml
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
root = "F:/aging_data/repo/catalogs/"
f = json.load(open(root + "latest.json", encoding="utf-8"))["catalog"]
con = duckdb.connect(root + f, read_only=True)
ids = [r[0] for r in con.execute("select dataset_id from datasets where labelling in ('TMT','iTRAQ') and search_engine_version='1.1.13' order by 1").fetchall()]
man = yaml.safe_load(Path("F:/aging_data/batch/manifest.yaml").read_text(encoding="utf-8"))
runs = {d.get("accession"): d.get("run") for d in man["datasets"]}
for i in ids:
    run = Path("F:/aging_data") / runs[i]
    per_file = list(run.glob("04_search/**/*_Peptides.psmtsv"))
    n_runs = con.execute("select count(*) from runs where dataset_id=?", [i]).fetchone()[0]
    print(i, runs[i], "runs:", n_runs, "per-file _Peptides.psmtsv:", len(per_file))
