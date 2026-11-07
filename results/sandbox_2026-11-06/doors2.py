"""Can a profile overwrite bundle.json? What do the macros hold? What does the parser say about each read form?

usage: doors2.py <datarepo.exe> <work dir from doors.py>. Scratch store only.
"""
import hashlib
import json
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
EXE = sys.argv[1]
WORK = pathlib.Path(sys.argv[2]).resolve()
SCRATCH = pathlib.Path(__file__).resolve().parent.parent
assert str(WORK).startswith(str(SCRATCH)), f"{WORK} is outside the scratchpad"
BUNDLE = WORK / "store" / "PXD017944" / "3cd52dd1b39472d8"
target = BUNDLE / "bundle.json"

p = subprocess.Popen([EXE, "mcp", "--catalog", str(WORK / "catalogs")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1)
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
    return json.loads("".join(c.get("text", "") for c in rpc("tools/call", {"name": "datarepo_sql", "arguments": {"query": query}})["result"]["content"]))


rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "probe", "version": "0"}})
p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
p.stdin.flush()

print("table macros:", [r[0] for r in sql("SELECT DISTINCT function_name FROM duckdb_functions() WHERE function_type = 'table_macro' ORDER BY 1").get("rows", [])])
print("not internal:", sql("SELECT DISTINCT function_name, function_type FROM duckdb_functions() WHERE NOT internal ORDER BY 1").get("rows", []))
print("function types:", sql("SELECT function_type, count(DISTINCT function_name) FROM duckdb_functions() GROUP BY 1 ORDER BY 1").get("rows", []))

print("\nwhat json_serialize_sql says of each form that reads")
for form in ["SHOW TABLES", "SHOW metrics", "DESCRIBE metrics", "DESCRIBE SELECT 1", "SUMMARIZE metrics", "SUMMARIZE SELECT 1", "VALUES (1)", "TABLE metrics",
             "FROM metrics", "UNPIVOT metrics ON value INTO NAME n VALUE v", "PRAGMA version", "PRAGMA table_info('metrics')",
             "SELECT * FROM unnest([1])", "SELECT * FROM main.range(1)", "SELECT * FROM \"RANGE\"(1)", "SELECT write_log('x')", "SELECT 'x'.write_log()"]:
    answer = sql(f"SELECT json_serialize_sql($q${form}$q$) AS s")
    text = answer["rows"][0][0] if "rows" in answer else json.dumps(answer)
    doc = json.loads(text) if text.startswith("{") else {}
    print(f"  {form[:44]:44} error={doc.get('error')} {doc.get('error_message', '')[:60]!r} kinds={sorted(set(_ for _ in [t for t in [] ]))}")
tree = json.loads(sql("SELECT json_serialize_sql($q$SELECT * FROM main.query('SELECT 1') WHERE write_log('x') IS NULL$q$) AS s")["rows"][0][0])


def walk(node, out):
    if isinstance(node, dict):
        if node.get("type") == "TABLE_FUNCTION":
            out.append(("table function", node["function"].get("function_name"), node["function"].get("schema"), [c.get("class") for c in node["function"].get("children", [])], node["function"]["children"][0].get("value")))
        if node.get("class") == "FUNCTION":
            out.append(("function", node.get("function_name"), node.get("schema")))
        for v in node.values():
            walk(v, out)
    elif isinstance(node, list):
        for v in node:
            walk(v, out)


found = []
walk(tree, found)
print("\nwalk:", found)

print("\nbundle.json", hashlib.sha256(target.read_bytes()).hexdigest()[:16], target.stat().st_size)
print(sql(f"SELECT * FROM enable_profiling(format='json', save_location='{target.as_posix()}')").get("rows"))
print(sql("SELECT 1 AS a").get("rows"))
p.stdin.close()
p.wait(timeout=30)
print("bundle.json", hashlib.sha256(target.read_bytes()).hexdigest()[:16], target.stat().st_size)
print(target.read_text(encoding="utf-8", errors="replace")[:160].replace("\n", " "))
out = subprocess.run([EXE, "build", str(WORK / "m.yaml"), "--store", str(WORK / "store"), "--out", str(WORK / "catalogs"), "--overwrite"], capture_output=True, text=True, encoding="utf-8", errors="replace")
print("rebuild exit", out.returncode, (out.stdout + out.stderr)[-260:].replace("\n", " "))
