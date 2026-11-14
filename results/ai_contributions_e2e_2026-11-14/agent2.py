"""Scratch (AI contributions v2, V6): a second agent, served with --show-prior, asks a question on the same table the first
agent's saved result read, and prints the prior_work the answer carries.

usage: agent2.py <exe> <catalog folder>"""
import json, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")
exe, catalog = sys.argv[1:3]
p = subprocess.Popen([exe, "mcp", "--catalog", catalog, "--show-prior"],
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
n = 0


def send(method, params=None, notify=False):
    global n
    msg = {"jsonrpc": "2.0", "method": method, **({"params": params} if params is not None else {})}
    if not notify:
        n += 1
        msg["id"] = n
    p.stdin.write(json.dumps(msg) + "\n")
    p.stdin.flush()
    while not notify:
        reply = json.loads(p.stdout.readline())
        if reply.get("id") == n:
            return reply


send("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "e2e-agent-2", "version": "0.1"}})
send("notifications/initialized", notify=True)
r = send("tools/call", {"name": "datarepo_sql", "arguments": {"query": "SELECT count(*) AS n FROM dataset_overview"}})
s = r["result"]["structuredContent"]
d = send("tools/call", {"name": "datarepo_describe", "arguments": {}})["result"]["structuredContent"]
p.stdin.close()
p.wait(timeout=60)
print(json.dumps({"rows": s["rows"], "prior_work": s.get("prior_work"), "describe.contributions": d.get("contributions"),
                  "describe.public_sessions": d.get("public_sessions")}, indent=1))
