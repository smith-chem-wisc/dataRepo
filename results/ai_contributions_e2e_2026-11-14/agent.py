"""Scratch (AI contributions v2, V6): drive the real `datarepo mcp` over stdio as an agent would. Asks two questions, then
saves a result citing both by their place in the public record, and prints what came back. Writes nothing itself: the
server writes its session record and the inbox request.

usage: agent.py <exe> <catalog folder> <inbox> <out.json>"""
import json, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")
exe, catalog, inbox, out = sys.argv[1:5]
p = subprocess.Popen([exe, "mcp", "--catalog", catalog, "--contributions", inbox],
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
seq = 0


def send(method, params=None, notify=False):
    global seq
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:
        seq += 1
        msg["id"] = seq
    p.stdin.write(json.dumps(msg) + "\n")
    p.stdin.flush()
    if notify:
        return None
    while True:
        line = p.stdout.readline()
        if not line:
            raise SystemExit("server closed: " + p.stderr.read())
        reply = json.loads(line)
        if reply.get("id") == seq:
            return reply


def call(tool, args):
    r = send("tools/call", {"name": tool, "arguments": args})
    res = r["result"]
    return res.get("structuredContent"), res.get("isError"), res["content"][0]["text"]


log = {}
init = send("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                           "clientInfo": {"name": "e2e-agent", "version": "0.1"}})
log["instructions"] = init["result"].get("instructions")
send("notifications/initialized", notify=True)
log["tools"] = [t["name"] for t in send("tools/list")["result"]["tools"]]

top, _, _ = call("datarepo_sql", {"query": "SELECT dataset_id, n_protein_groups_1pct FROM dataset_overview "
                                           "ORDER BY n_protein_groups_1pct DESC, dataset_id LIMIT 3"})
log["top"] = {"rows": top["rows"], "session_call": top["session_call"]}
ids = [r[0] for r in top["rows"]]
bundles, _, _ = call("datarepo_sql", {"query": "SELECT dataset_id, bundle_id FROM catalog_bundles WHERE dataset_id IN ("
                                               + ", ".join(f"'{i}'" for i in ids) + ") ORDER BY dataset_id"})
log["bundles"] = {"rows": bundles["rows"], "session_call": bundles["session_call"]}
catalog_id = top["provenance"]["catalog_id"] if isinstance(top.get("provenance"), dict) and "catalog_id" in top["provenance"] else None
if catalog_id is None:
    meta, _, _ = call("datarepo_sql", {"query": "SELECT catalog_id FROM catalog_meta"})
    catalog_id = meta["rows"][0][0]

result = {
    "contribution_version": "1", "kind": "table", "title": "The three deposits with the most protein groups at 1%",
    "summary": "Ranked by n_protein_groups_1pct in dataset_overview.",
    "model": {"provider": "scratch", "id": "e2e-agent-0.1", "stated_by": "client"},
    "licence": "CC-BY-4.0", "reproducibility": "query",
    "basis": {"catalog_id": catalog_id, "bundles": [{"dataset_id": d, "bundle_id": b} for d, b in bundles["rows"]]},
    "method": {"description": "Two queries: the ranking, then the bundles it rests on.", "queries": []},
    "items": [{"subject_type": "dataset", "subject_id": d, "value": n, "rank": i + 1} for i, (d, n) in enumerate(top["rows"])],
}
saved, err, text = call("datarepo_save_result", {"contribution": result,
                                                 "cites": [top["session_call"]["seq"], bundles["session_call"]["seq"]]})
log["save"] = saved or text
named = dict(result, submitted_by={"name": "Some Person"})
refused, _, _ = call("datarepo_save_result", {"contribution": named})
log["refused_named"] = refused
p.stdin.close()
p.wait(timeout=60)
log["stderr"] = p.stderr.read()
json.dump(log, open(out, "w", encoding="utf-8"), indent=1)
print(json.dumps({k: log[k] for k in ("tools", "save", "refused_named")}, indent=1))
print("stderr:", log["stderr"].strip())
