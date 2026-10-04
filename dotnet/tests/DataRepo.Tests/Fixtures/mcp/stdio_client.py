"""Drive an MCP server over real stdio: list tools, call each once, dump what came back.

usage: python stdio_client.py <out.json> <command> [args...]
"""
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CALLS = [
    ("datarepo_describe", {}),
    ("datarepo_describe", {"target": "psms"}),
    ("datarepo_search", {"query": "P02768"}),
    ("datarepo_sql", {"query": "SELECT dataset_id, count(*) AS n FROM psms GROUP BY 1 ORDER BY 1"}),
    ("datarepo_sql", {"query": "DROP TABLE psms"}),
    ("datarepo_describe", {"target": "psmz"}),
    ("datarepo_search", {"query": "x", "kind": "nope"}),
]


async def main() -> None:
    out_path, command, args = sys.argv[1], sys.argv[2], sys.argv[3:]
    params = StdioServerParameters(command=command, args=args)
    record = {}
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            record["server_info"] = init.server_info.model_dump(mode="json", exclude_none=True)
            tools = await session.list_tools()
            record["tools"] = [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in tools.tools]
            record["calls"] = []
            for name, arguments in CALLS:
                result = await session.call_tool(name, arguments)
                dumped = result.model_dump(mode="json", by_alias=True, exclude_none=True)
                record["calls"].append({"name": name, "arguments": arguments, "result": dumped})
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=1, ensure_ascii=False)
    print(f"{len(record['tools'])} tools, {len(record['calls'])} calls -> {out_path}")


asyncio.run(main())
