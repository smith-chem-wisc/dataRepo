"""After repro1: can a served table be replaced in two steps, can a temp table shadow a view, and does a rebuild notice?

usage: repro2.py <datarepo.exe> <work dir from repro1>
"""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

EXE = sys.argv[1]
WORK = pathlib.Path(sys.argv[2]).resolve()
SCRATCH = pathlib.Path(__file__).resolve().parent.parent
assert str(WORK).startswith(str(SCRATCH)), f"{WORK} is outside the scratchpad"
STORE = WORK / "store"
BUNDLE = STORE / "PXD017944" / "3cd52dd1b39472d8"

server = subprocess.Popen([EXE, "mcp", "--catalog", str(WORK / "catalogs")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1)
ids = [0]


def rpc(method, params=None, notify=False):
    message = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        message["params"] = params
    if not notify:
        ids[0] += 1
        message["id"] = ids[0]
    server.stdin.write(json.dumps(message) + "\n")
    server.stdin.flush()
    if notify:
        return None
    while True:
        reply = json.loads(server.stdout.readline())
        if reply.get("id") == ids[0]:
            return reply


def sql(query):
    reply = rpc("tools/call", {"name": "datarepo_sql", "arguments": {"query": query}})
    text = "".join(c.get("text", "") for c in reply["result"]["content"])
    return json.loads(text)


def show(label, answer):
    if "error" in answer:
        print(f"{label}: REFUSED/ERROR {answer['error']}: {answer['message'][:150]!r}")
    else:
        print(f"{label}: rows={answer.get('rows')!r:.200} tables={answer.get('tables_touched')} prov={str(answer.get('provenance'))[:120]}")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "sandbox-probe", "version": "0"}})
rpc("notifications/initialized", notify=True)

target = BUNDLE / "peptidoforms.parquet"
t = target.as_posix()
x = (STORE / "x.parquet").as_posix()
before = sha(target)
written = json.loads((BUNDLE / "bundle.json").read_text(encoding="utf-8")).get("written_utc")
print("bundle written_utc", written)
print("table mtime before", datetime.datetime.fromtimestamp(os.path.getmtime(target), datetime.timezone.utc).isoformat())

show("served sum", sql("SELECT round(sum(best_q_value),6) AS s, count(*) AS n FROM peptidoforms"))
show("step 1", sql(f"EXPLAIN ANALYZE COPY (SELECT * REPLACE (best_q_value / 2 AS best_q_value) FROM read_parquet('{t}')) TO '{x}' (FORMAT PARQUET)"))
show("step 2", sql(f"EXPLAIN ANALYZE COPY (SELECT * FROM read_parquet('{x}')) TO '{t}' (FORMAT PARQUET)"))
after = sha(target)
print("sha256", before, "->", after, "changed:", before != after)
print("table mtime after ", datetime.datetime.fromtimestamp(os.path.getmtime(target), datetime.timezone.utc).isoformat())
show("served sum again", sql("SELECT round(sum(best_q_value),6) AS s, count(*) AS n FROM peptidoforms"))
print("catalog_id in describe:", rpc("tools/call", {"name": "datarepo_describe", "arguments": {}})["result"]["content"][0]["text"][:120].replace("\n", " "))

# In-session state: a temp table named after a served view.
show("before shadow", sql("SELECT count(*) AS n FROM metrics"))
show("shadow", sql("EXPLAIN ANALYZE CREATE TEMP TABLE metrics AS SELECT 99999 AS n"))
show("after shadow", sql("SELECT * FROM metrics"))

# Other PRAGMA that expand into statements.
(STORE / "imp").mkdir(exist_ok=True)
(STORE / "imp" / "schema.sql").write_text(f"COPY (SELECT 1 AS a) TO '{(STORE / 'p_import.parquet').as_posix()}' (FORMAT PARQUET);\n", encoding="utf-8")
(STORE / "imp" / "load.sql").write_text("SELECT 1;\n", encoding="utf-8")
show("PRAGMA import_database", sql(f"PRAGMA import_database('{(STORE / 'imp').as_posix()}')"))
print("p_import written:", (STORE / "p_import.parquet").exists())
server.stdin.close()
server.wait(timeout=30)

rebuilt = subprocess.run([EXE, "build", str(WORK / "m.yaml"), "--store", str(STORE), "--out", str(WORK / "catalogs"), "--overwrite"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
print("rebuild into the same folder: exit", rebuilt.returncode)
print(rebuilt.stdout[-400:], rebuilt.stderr[-300:])
print("latest", json.loads((WORK / "catalogs" / "latest.json").read_text(encoding="utf-8")).get("catalog_id"))
