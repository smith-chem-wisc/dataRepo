"""What else can a client's SELECT or PRAGMA do? Lists the engine's functions and tries the ones that could write.

usage: enumerate.py <datarepo.exe> <work dir from repro1>. Scratch store only.
"""
import json
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

EXE = sys.argv[1]
WORK = pathlib.Path(sys.argv[2]).resolve()
SCRATCH = pathlib.Path(__file__).resolve().parent.parent
assert str(WORK).startswith(str(SCRATCH)), f"{WORK} is outside the scratchpad"
STORE = WORK / "store"
S = STORE.as_posix()

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
    return json.loads("".join(c.get("text", "") for c in reply["result"]["content"]))


rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "sandbox-probe", "version": "0"}})
rpc("notifications/initialized", notify=True)

print(sql("SELECT version() AS v")["rows"])
for kind in ("pragma", "table"):
    answer = sql(f"SELECT DISTINCT function_name FROM duckdb_functions() WHERE function_type = '{kind}' AND NOT internal = false ORDER BY 1")
    names = [r[0] for r in answer.get("rows", [])]
    print(f"\n{kind} functions ({len(names)}, truncated={answer.get('truncated')}):")
    print("  " + ", ".join(names))
answer = sql("SELECT DISTINCT function_name FROM duckdb_functions() WHERE function_type = 'scalar' AND regexp_matches(function_name, 'write|log|export|copy|set|config|checkpoint|flush|file|persist|secret|load|install|attach') ORDER BY 1")
print("\nscalars with a suggestive name:", ", ".join(r[0] for r in answer.get("rows", [])))

files_before = {p for p in STORE.rglob("*") if p.is_file()}
PROBES = [
    f"PRAGMA enable_logging",
    f"PRAGMA enable_logging(storage='file', storage_path='{S}/l_pragma')",
    f"PRAGMA enable_logging(storage_path='{S}/l_pragma2', storage='file')",
    f"SELECT * FROM enable_logging(storage='file', storage_path='{S}/l_select')",
    f"PRAGMA disable_logging",
    f"PRAGMA truncate_duckdb_logs",
    "SELECT write_log('probe')",
    "SELECT * FROM duckdb_logs LIMIT 1",
    f"SELECT * FROM checkpoint()",
    f"SELECT * FROM force_checkpoint()",
    f"PRAGMA checkpoint",
    f"PRAGMA force_checkpoint",
    f"PRAGMA create_extension",
    f"PRAGMA install_extension('x')",
    f"SELECT * FROM duckdb_secrets()",
    f"SELECT * FROM which_secret('{S}/x','local')",
    f"SELECT getvariable('x')",
    f"SELECT set_config('threads','1')",
    f"SELECT setvar('x', 1)",
    f"PRAGMA copy_database('a','b')",
    f"PRAGMA export_database('{S}/l_export')",
    f"PRAGMA import_database('{S}/imp')",
    f"PRAGMA storage_info('metrics')",
    f"PRAGMA table_info('metrics')",
    f"PRAGMA show_tables",
    f"PRAGMA database_size",
    f"PRAGMA version",
    f"PRAGMA platform",
    f"PRAGMA threads",
    f"PRAGMA disable_optimizer",
    f"PRAGMA enable_optimizer",
    f"PRAGMA enable_verification",
    f"PRAGMA disable_verification",
    f"PRAGMA force_compression('zstd')",
    f"PRAGMA debug_checkpoint_abort",
    f"PRAGMA preserve_identifier_case",
    f"PRAGMA default_collation('nocase')",
    f"PRAGMA default_order('desc')",
    f"PRAGMA default_null_order('first')",
    f"PRAGMA memory_limit('1MB')",
    f"PRAGMA temp_directory('{S}/l_tmp')",
    f"PRAGMA home_directory('{S}/l_home')",
    f"PRAGMA extension_directory('{S}/l_ext')",
    f"PRAGMA secret_directory('{S}/l_sec')",
    f"PRAGMA log_query_path('{S}/l_q')",
    f"PRAGMA profiling_output('{S}/l_prof')",
    f"PRAGMA profile_output('{S}/l_prof2')",
    f"PRAGMA enable_profile",
    f"PRAGMA enable_profiling",
    f"PRAGMA enable_progress_bar",
    "SELECT * FROM pragma_show_tables()",
    "SELECT 1 AS after_all_of_it",
]
print()
for query in PROBES:
    answer = sql(query)
    if "error" in answer:
        print(f"{answer['error']:14} {query[:62]:62} {answer['message'][:90]!r}")
    else:
        print(f"{'ANSWERED':14} {query[:62]:62} rows={str(answer.get('rows'))[:60]}")
new = sorted(str(p.relative_to(STORE)) for p in STORE.rglob("*") if p.is_file() and p not in files_before)
print("\nnew files in the store:", new)
print("new directories:", sorted(p.name for p in STORE.iterdir() if p.is_dir() and p.name.startswith("l_")))
# Does anything that answered change what later answers mean?
print(sql("SELECT current_setting('default_order') AS o, current_setting('default_collation') AS c, current_setting('memory_limit') AS m, current_setting('threads') AS t")["rows"])
print(sql("SELECT min(a) AS lo FROM (VALUES (1),(2)) t(a)")["rows"])
print(sql("SELECT a FROM (VALUES (1),(2)) t(a) ORDER BY a")["rows"])
server.stdin.close()
server.wait(timeout=30)
