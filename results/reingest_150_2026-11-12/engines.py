"""Scratch (1.5.0): replay on the scratch store every engine run aging's serving catalog 75e1c0c82f8dc965 cites, with
the same fixed inputs (read from each artefact's run.json), on the deposits each run was requested for, with the
1.5.0-scratch binary. One call per engine and input set, as an operator would make it after a re-ingest. Times each
call into engines.log. Reads aging's catalog and store read-only; writes only the scratch store's _engine folder."""
import collections, json, os, subprocess, sys, time
import duckdb

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "bin", "datarepo.exe")
STORE = os.path.join(HERE, "store")
done = {d for d in os.listdir(STORE) if not d.startswith("_")}

c = duckdb.connect(r"F:/aging_data/repo/catalogs/catalog-75e1c0c82f8dc965.duckdb", read_only=True)
groups = collections.defaultdict(set)
for eng, path in c.execute("select engine, path from catalog_engine_artefacts").fetchall():
    r = json.load(open(path + "/run.json", encoding="utf-8"))
    f = dict(r["input_files"])
    if "logs_manifest" in r.get("checked_against", {}):
        f["logs_manifest"] = r["checked_against"]["logs_manifest"]
    fixed = tuple(sorted((k, v) for k, v in f.items() if not k.startswith(("annotation_database", "protein_groups", "search_database"))))
    groups[(eng, fixed)].update(x["dataset_id"] for x in r.get("requested_for", []))

order = {"logs.register_orthology": 0, "logs.resolve_genes": 1, "go.annotate_groups": 2}
log = open(os.path.join(HERE, "engines.log"), "a", encoding="utf-8")
for (eng, fixed), accs in sorted(groups.items(), key=lambda g: order[g[0][0]]):
    want = sorted(a for a in accs if a in done)
    missing = sorted(a for a in accs if a not in done)
    cmd = [EXE, "run", eng, *want, "--store", STORE, "--latest"]
    for k, v in fixed:
        cmd += ["--input", f"{k}={v}"]
    log.write(f"== {time.strftime('%H:%M:%S', time.gmtime())} {eng} {len(want)} deposits; not re-ingested: {missing}\n")
    log.flush()
    t = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    secs = time.time() - t
    log.write(p.stdout[-6000:] + ("\n-- stderr:\n" + p.stderr[-4000:] if p.stderr.strip() else "") + "\n")
    log.write(f"== done {eng} rc={p.returncode} secs={secs:.0f}\n\n")
    log.flush()
    print(eng, len(want), "rc", p.returncode, f"{secs:.0f}s", flush=True)
