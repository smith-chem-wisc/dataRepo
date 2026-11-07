"""Does the MCP sandbox let a client write under a folder catalog's store? Scratch store only; never aging's.

usage: repro1.py <datarepo.exe> <work dir, emptied first>
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

import yaml

sys.stdout.reconfigure(encoding="utf-8")

EXE = sys.argv[1]
WORK = pathlib.Path(sys.argv[2]).resolve()
SCRATCH = pathlib.Path(__file__).resolve().parent.parent
assert str(WORK).startswith(str(SCRATCH)), f"{WORK} is outside the scratchpad"

SOURCE_BUNDLE = SCRATCH / "split" / "store" / "PXD017944" / "3cd52dd1b39472d8"
AFTER = SCRATCH / "split" / "after.yaml"

if WORK.exists():
    shutil.rmtree(WORK)
STORE = WORK / "store"
BUNDLE = STORE / "PXD017944" / "3cd52dd1b39472d8"
shutil.copytree(SOURCE_BUNDLE, BUNDLE)

manifest = yaml.safe_load(AFTER.read_text(encoding="utf-8"))
manifest["store"] = STORE.as_posix()
manifest["datasets"] = [d for d in manifest["datasets"] if d["accession"] == "PXD017944"]
(WORK / "m.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8", newline="\n")

out = subprocess.run([EXE, "build", str(WORK / "m.yaml"), "--store", str(STORE), "--out", str(WORK / "catalogs")],
                     capture_output=True, text=True, encoding="utf-8", errors="replace")
print("build exit", out.returncode)
if out.returncode:
    print(out.stdout[-1500:], out.stderr[-1500:])
    sys.exit(1)
latest = json.loads((WORK / "catalogs" / "latest.json").read_text(encoding="utf-8"))
print("latest", {k: latest[k] for k in latest if k in ("catalog_id", "file", "built_by")})

server = subprocess.Popen([EXE, "mcp", "--catalog", str(WORK / "catalogs")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1)
next_id = 0


def rpc(method, params=None, notify=False):
    global next_id
    message = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        message["params"] = params
    if not notify:
        next_id += 1
        message["id"] = next_id
    server.stdin.write(json.dumps(message) + "\n")
    server.stdin.flush()
    if notify:
        return None
    while True:
        line = server.stdout.readline()
        if not line:
            raise RuntimeError("server closed")
        reply = json.loads(line)
        if reply.get("id") == next_id:
            return reply


def sql(query):
    reply = rpc("tools/call", {"name": "datarepo_sql", "arguments": {"query": query}})
    result = reply.get("result", {})
    text = "".join(c.get("text", "") for c in result.get("content", []))
    return result.get("isError", False), text


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "sandbox-probe", "version": "0"}})
rpc("notifications/initialized", notify=True)
print("tools", [t["name"] for t in rpc("tools/list")["result"]["tools"]])

S = STORE.as_posix()
OUTSIDE = WORK.as_posix() + "/outside"
table = (BUNDLE / "peptidoforms.parquet").as_posix()
before = sha(BUNDLE / "peptidoforms.parquet")
listing = sorted(p.name for p in STORE.rglob("*") if p.is_file())

PROBES = [
    # the door itself, and its spellings
    ("plain COPY into the store", f"COPY (SELECT 1 AS a) TO '{S}/p_plain.parquet' (FORMAT PARQUET)", "p_plain.parquet"),
    ("EXPLAIN COPY (no analyze)", f"EXPLAIN COPY (SELECT 1 AS a) TO '{S}/p_explain.parquet' (FORMAT PARQUET)", "p_explain.parquet"),
    ("EXPLAIN ANALYZE COPY", f"EXPLAIN ANALYZE COPY (SELECT 1 AS a) TO '{S}/p_analyze.parquet' (FORMAT PARQUET)", "p_analyze.parquet"),
    ("EXPLAIN ANALYSE COPY", f"EXPLAIN ANALYSE COPY (SELECT 1 AS a) TO '{S}/p_analyse.parquet' (FORMAT PARQUET)", "p_analyse.parquet"),
    ("EXPLAIN (ANALYZE) COPY", f"EXPLAIN (ANALYZE) COPY (SELECT 1 AS a) TO '{S}/p_paren.parquet' (FORMAT PARQUET)", "p_paren.parquet"),
    ("comment between", f"EXPLAIN /* x */ ANALYZE /* y */ COPY (SELECT 1 AS a) TO '{S}/p_comment.parquet' (FORMAT PARQUET)", "p_comment.parquet"),
    ("outside the store", f"EXPLAIN ANALYZE COPY (SELECT 1 AS a) TO '{OUTSIDE}.parquet' (FORMAT PARQUET)", None),
    # other things it might execute
    ("EXPORT DATABASE", f"EXPLAIN ANALYZE EXPORT DATABASE '{S}/p_export'", "p_export"),
    ("CREATE TEMP TABLE", "EXPLAIN ANALYZE CREATE TEMP TABLE t AS SELECT 1 AS a", None),
    ("ATTACH", f"EXPLAIN ANALYZE ATTACH '{S}/p_attach.duckdb' AS p", "p_attach.duckdb"),
    ("SET", f"EXPLAIN ANALYZE SET profiling_output='{S}/p_prof.json'", None),
    ("LOAD", "EXPLAIN ANALYZE LOAD httpfs", None),
    ("CALL", "EXPLAIN ANALYZE CALL pragma_version()", None),
    # the other allowed kinds
    ("PRAGMA profiling_output", f"PRAGMA profiling_output='{S}/p_prof2.json'", None),
    ("PRAGMA enable_profiling", "PRAGMA enable_profiling='json'", None),
    ("PRAGMA log_query_path", f"PRAGMA log_query_path='{S}/p_log.txt'", None),
    ("SELECT after those", "SELECT 1 AS a", "p_prof2.json"),
    ("query() table function", f"SELECT * FROM query('COPY (SELECT 1 AS a) TO ''{S}/p_query.parquet''')", "p_query.parquet"),
    ("glob inside the store", f"SELECT count(*) AS n FROM glob('{S}/**')", None),
]
for name, query, leaves in PROBES:
    error, text = sql(query)
    wrote = None
    if leaves:
        wrote = any(p.name == leaves for p in STORE.rglob("*"))
    print(f"--- {name}\n    error={error} wrote={wrote}\n    {text[:170]!r}")

print("--- outside-store file exists:", pathlib.Path(OUTSIDE + ".parquet").exists())

# The overwrite of a served table, on this scratch copy.
error, text = sql("SELECT sequence, best_q_value FROM peptidoforms ORDER BY peptidoform_id LIMIT 1") if False else (None, None)
columns = sql(f"SELECT column_name FROM (DESCRIBE SELECT * FROM read_parquet('{table}')) WHERE column_name LIKE '%q_value%'")
print("q-value columns:", columns[1][:200])
first = sql(f"SELECT round(sum(best_q_value), 6) AS s, count(*) AS n FROM read_parquet('{table}')")
print("before:", first[1][:300])
error, text = sql(f"EXPLAIN ANALYZE COPY (SELECT * REPLACE (best_q_value / 2 AS best_q_value) FROM read_parquet('{table}')) TO '{table}' (FORMAT PARQUET)")
print("overwrite: error", error, repr(text[:170]))
after_sha = sha(BUNDLE / "peptidoforms.parquet")
print("sha256 before", before, "after", after_sha, "changed", before != after_sha)
second = sql(f"SELECT round(sum(best_q_value), 6) AS s, count(*) AS n FROM read_parquet('{table}')")
print("after:", second[1][:300])
server.stdin.close()
server.wait(timeout=30)

rebuilt = subprocess.run([EXE, "build", str(WORK / "m.yaml"), "--store", str(STORE), "--out", str(WORK / "catalogs2")],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
print("rebuild on the altered store: exit", rebuilt.returncode)
print(rebuilt.stdout[-500:])
latest2 = json.loads((WORK / "catalogs2" / "latest.json").read_text(encoding="utf-8")) if rebuilt.returncode == 0 else {}
print("catalog id", latest.get("catalog_id"), "->", latest2.get("catalog_id"))
print("new files in the store:", sorted(set(p.name for p in STORE.rglob('*') if p.is_file()) - set(listing)))
