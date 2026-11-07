"""On a ONE-file catalog: which of the doors open? usage: onefile.py <datarepo.exe> <catalog.duckdb>. Scratch only."""
import json
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
EXE, CATALOG = sys.argv[1], str(pathlib.Path(sys.argv[2]).resolve())
SCRATCH = pathlib.Path(__file__).resolve().parent.parent
assert CATALOG.startswith(str(SCRATCH)), f"{CATALOG} is outside the scratchpad"
OUT = (SCRATCH / "sec").as_posix()
p = subprocess.Popen([EXE, "mcp", "--catalog", CATALOG], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                     text=True, encoding="utf-8", bufsize=1)
n = [0]


def rpc(method, params):
    n[0] += 1
    p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": n[0], "method": method, "params": params}) + "\n")
    p.stdin.flush()
    while True:
        reply = json.loads(p.stdout.readline())
        if reply.get("id") == n[0]:
            return reply


def sql(query):
    a = json.loads("".join(c.get("text", "") for c in rpc("tools/call", {"name": "datarepo_sql", "arguments": {"query": query}})["result"]["content"]))
    print(f"{query[:70]!r}\n   ", (a["error"] + ": " + a["message"][:110]) if "error" in a else (str(a.get("rows"))[:70], a.get("tables_touched")))


rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "probe", "version": "0"}})
p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
p.stdin.flush()
sql("SELECT count(*) AS n FROM metrics")
sql("EXPLAIN ANALYZE CREATE TEMP TABLE metrics AS SELECT 99999 AS n")
sql("SELECT * FROM metrics")
sql(f"EXPLAIN ANALYZE COPY (SELECT 1 AS a) TO '{OUT}/onefile_copy.csv'")
sql(f"SELECT * FROM enable_profiling(format='json', save_location='{OUT}/onefile_prof.json')")
sql("SELECT 1")
sql(f"SELECT * FROM enable_logging(storage='file', storage_path='{OUT}/onefile_logs')")
p.stdin.close()
p.wait(timeout=30)
print("written:", [q.name for q in (SCRATCH / "sec").iterdir() if q.name.startswith("onefile_")])
