"""How far do the SELECT doors go? Can they replace a served table? Scratch store only.

usage: doors.py <datarepo.exe> <work dir, emptied first>
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
if WORK.exists():
    shutil.rmtree(WORK)
STORE = WORK / "store"
BUNDLE = STORE / "PXD017944" / "3cd52dd1b39472d8"
shutil.copytree(SCRATCH / "split" / "store" / "PXD017944" / "3cd52dd1b39472d8", BUNDLE)
manifest = yaml.safe_load((SCRATCH / "split" / "after.yaml").read_text(encoding="utf-8"))
manifest["store"] = STORE.as_posix()
manifest["datasets"] = [d for d in manifest["datasets"] if d["accession"] == "PXD017944"]
(WORK / "m.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8", newline="\n")
built = subprocess.run([EXE, "build", str(WORK / "m.yaml"), "--store", str(STORE), "--out", str(WORK / "catalogs")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
print("build exit", built.returncode)


class Server:
    def __init__(self):
        self.p = subprocess.Popen([EXE, "mcp", "--catalog", str(WORK / "catalogs")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1)
        self.n = 0
        self.rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "probe", "version": "0"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.p.stdin.flush()

    def rpc(self, method, params):
        self.n += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line:
                return None
            reply = json.loads(line)
            if reply.get("id") == self.n:
                return reply

    def sql(self, query):
        reply = self.rpc("tools/call", {"name": "datarepo_sql", "arguments": {"query": query}})
        if reply is None:
            return {"error": "SERVER DIED", "message": ""}
        return json.loads("".join(c.get("text", "") for c in reply["result"]["content"]))

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=30)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16] if path.exists() else None


def report(server, query):
    answer = server.sql(query)
    if "error" in answer:
        print(f"  {answer['error']:13} {query[:95]!r}\n      {answer['message'][:130]!r}")
    else:
        print(f"  ANSWERED      {query[:95]!r}\n      rows={str(answer.get('rows'))[:110]}")


def files():
    return {str(p.relative_to(STORE)): sha(p) for p in STORE.rglob("*") if p.is_file()}


S = STORE.as_posix()
target = BUNDLE / "metrics.parquet"
t = target.as_posix()
print("metrics.parquet", sha(target))
start = files()

print("\n1. logging to a file with a chosen name, in a fresh server each time")
for label, query in [
    ("directory", f"SELECT * FROM enable_logging(storage='file', storage_path='{S}/d1')"),
    ("config dir", f"SELECT * FROM enable_logging(storage='file', storage_config={{'path': '{S}/d2'}})"),
    ("config file, not normalized", f"SELECT * FROM enable_logging(storage='file', storage_config={{'path': '{S}/chosen.parquet', 'normalize': false}})"),
    ("over a served table", f"SELECT * FROM enable_logging(storage='file', storage_config={{'path': '{t}', 'normalize': false}})"),
    ("over a served table, FROM-first", f"FROM enable_logging(storage='file', storage_config={{'path': '{t}', 'normalize': false}})"),
    ("EXPLAIN ANALYZE", f"EXPLAIN ANALYZE SELECT * FROM enable_logging(storage='file', storage_path='{S}/d3')"),
    ("through query()", "SELECT * FROM query('SELECT * FROM enable_logging(storage=''file'', storage_path=''" + S + "/d4'')')"),
]:
    print(f" [{label}]")
    server = Server()
    report(server, query)
    report(server, "SELECT write_log('invented text', level := 'WARN', log_type := 'probe')")
    report(server, "SELECT count(*) FROM metrics")
    server.close()
    print("     metrics.parquet", sha(target))

print("\n2. profiling output")
server = Server()
report(server, f"SELECT * FROM enable_profiling(save_location='{S}/prof1.json')")
report(server, f"SELECT * FROM enable_profiling(format='json', save_location='{S}/prof2.json')")
report(server, f"SELECT * FROM enable_profiling(save_location='{t}')")
report(server, "SELECT count(*) FROM metrics")
report(server, "SELECT 1")
server.close()
print("     metrics.parquet", sha(target))

print("\n3. executing a serialized statement")
server = Server()
serial = server.sql("SELECT json_serialize_sql('SELECT 1 AS a') AS s").get("rows", [[None]])[0][0]
print("  serialized:", str(serial)[:80])
report(server, "SELECT * FROM json_execute_serialized_sql(json_serialize_sql('SELECT 1 AS a'))")
report(server, f"PRAGMA json_execute_serialized_sql('{serial}')" if serial else "SELECT 1")
server.close()

print("\n4. other state")
server = Server()
for query in [
    "SELECT * FROM truncate_duckdb_logs()",
    "SELECT * FROM disable_logging()",
    "SELECT * FROM enable_peg_parser()",
    "SELECT 1 AS after_peg",
    "SELECT * FROM disable_peg_parser()",
    "SELECT * FROM arrow_scan(1,1,1)",
    "SELECT * FROM seq_scan()",
    "PRAGMA add_parquet_key('k','0123456789012345')",
    "PRAGMA disable_object_cache",
    "PRAGMA disable_checkpoint_on_shutdown",
    "SELECT * FROM read_duckdb('" + (WORK / "catalogs").as_posix() + "/x')",
]:
    report(server, query)
server.close()

after = files()
print("\nchanged or new files in the store:")
for name in sorted(after):
    if start.get(name) != after[name]:
        print("  ", name, start.get(name), "->", after[name], (STORE / name).stat().st_size)
print("removed:", sorted(set(start) - set(after)))
