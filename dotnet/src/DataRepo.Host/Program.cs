using System.Globalization;
using DataRepo.Bundle;
using DataRepo.Host;

// datarepo-host: the hosted MCP server (design/AI_CONTRIBUTIONS.md S12). Exit codes as the CLI's: 0 stopped, 1 refused,
// 2 usage.
//
//   datarepo-host --catalog <folder> [--sessions <folder>] [--contributions <inbox>] [--show-prior]
//                 [--urls http://0.0.0.0:8080] [--rate 120]
CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
const string Usage =
    "usage: datarepo-host --catalog CATALOG [--sessions SESSIONS] [--contributions INBOX] [--show-prior] [--urls URLS] [--rate N]";

if (args.Contains("-h") || args.Contains("--help"))
{
    Console.WriteLine(Usage + "\n\n"
        + "Serve one catalog to AI agents over MCP (Streamable HTTP, at /mcp), with a PUBLIC record of every call.\n\n"
        + "  --catalog CATALOG        the catalog folder (or one catalog file) to serve\n"
        + "  --sessions SESSIONS      where the public record is kept; default the served store's _sessions\n"
        + "  --contributions INBOX    also serve datarepo_save_result, into this inbox (datarepo contribute accept)\n"
        + "  --show-prior             show earlier work in every sql answer\n"
        + "  --urls URLS              where to listen (default http://0.0.0.0:8080)\n"
        + "  --rate N                 requests per minute per client address (default 120)\n"
        + "  GET /healthz             names the catalog served, for a load balancer");
    return 0;
}
string? Value(string name)
{
    var at = Array.IndexOf(args, name);
    return at >= 0 && at + 1 < args.Length ? args[at + 1] : null;
}
var catalog = Value("--catalog");
if (catalog is null)
{
    Console.Error.WriteLine(Usage);
    Console.Error.WriteLine("datarepo-host: error: --catalog is required");
    return 2;
}
try
{
    var settings = new HostSettings(
        catalog,
        Sessions: Value("--sessions"),
        Contributions: Value("--contributions"),
        ShowPrior: args.Contains("--show-prior"),
        PermitPerMinute: int.TryParse(Value("--rate"), NumberStyles.None, CultureInfo.InvariantCulture, out var rate) ? rate : 120,
        Urls: Value("--urls") ?? "http://0.0.0.0:8080");
    await using var app = HostedServer.Build(settings);
    await app.RunAsync();
    return 0;
}
catch (DataRepoException e)
{
    Console.Error.WriteLine($"datarepo-host: {e.Message}");
    return 1;
}
