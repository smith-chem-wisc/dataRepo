using System.Threading.RateLimiting;
using DataRepo.Bundle;
using DataRepo.Catalog;
using DataRepo.Mcp;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using ModelContextProtocol.Server;

namespace DataRepo.Host;

/// <summary>How one hosted server copy runs.</summary>
/// <param name="Catalog">The catalog folder (or one catalog file) to serve.</param>
/// <param name="Sessions">Where the public session record is kept; null means the served store's <c>_sessions</c>.</param>
/// <param name="Contributions">The inbox for saved results; null serves no save tool.</param>
/// <param name="ShowPrior">Show earlier work in every <c>sql</c> answer (the user's opt-in, A18).</param>
/// <param name="PermitPerMinute">Requests one client address may make a minute before it is told to slow down (HTTP 429).</param>
/// <param name="Urls">Where to listen; port 0 picks a free one.</param>
public sealed record HostSettings(
    string Catalog,
    string? Sessions = null,
    string? Contributions = null,
    bool ShowPrior = false,
    int PermitPerMinute = 120,
    string Urls = "http://127.0.0.1:0",
    string Name = "datarepo");

/// <summary>The hosted MCP server (design/AI_CONTRIBUTIONS.md S12; PXReprise's hosting plan, part B): the same three
/// tools, record and inbox as <c>datarepo mcp</c>, over Streamable HTTP, for many agents at once.</summary>
/// <remarks>
/// <para>One copy serves one catalog through one read-only sandbox, one call at a time (the catalog connection is not
/// shared between threads). It grows by running more copies behind the host's load balancer, which share nothing but the
/// store: each MCP session writes its own record file, so copies never coordinate.</para>
/// <para>A client address is limited per minute before any request reaches the catalog. The record holds no address:
/// the host's own access logs do, apart from the record and briefly (the hosting plan, section 5).</para>
/// </remarks>
public static class HostedServer
{
    /// <summary>The application, built and not started.</summary>
    /// <exception cref="CatalogException">There is no catalog, or nowhere to keep the public record.</exception>
    public static WebApplication Build(HostSettings settings)
    {
        var catalog = new CatalogServer(settings.Catalog) { ShowPrior = settings.ShowPrior };
        var catalogId = PyValues.Str(catalog.Identity.CatalogId);
        string root;
        try
        {
            root = settings.Sessions ?? Mcp.Mcp.DefaultSessionRoot(catalog)
                ?? throw new CatalogException(
                    $"{settings.Catalog} is one catalog file and names no store, so there is nowhere to keep the public record: "
                    + "pass --sessions <folder> (the store's _sessions folder, so the next catalog build loads it)");
        }
        catch
        {
            catalog.Dispose();
            throw;
        }
        // One record per MCP session: the transport is stateful, so each session has its own McpServer, and the record
        // goes with it (and is forgotten with it). The SDK does not always fill the server's SessionId, so it is not the key.
        var logs = new System.Runtime.CompilerServices.ConditionalWeakTable<McpServer, SessionLog>();
        SessionLog LogFor(McpServer server) => logs.GetValue(server, _ => SessionLog.Open(root, catalogId));

        var builder = WebApplication.CreateSlimBuilder();
        builder.WebHost.UseUrls(settings.Urls);
        builder.Services
            .AddMcpServer(options => Mcp.Mcp.Configure(options, catalog, settings.Name, LogFor, settings.Contributions))
            .WithHttpTransport(http => http.Stateless = false);
        builder.Services.AddRateLimiter(limiter =>
        {
            limiter.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
            limiter.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(context =>
                RateLimitPartition.GetFixedWindowLimiter(context.Connection.RemoteIpAddress?.ToString() ?? "unknown", _ =>
                    new FixedWindowRateLimiterOptions { PermitLimit = settings.PermitPerMinute, Window = TimeSpan.FromMinutes(1), QueueLimit = 0 }));
        });

        var app = builder.Build();
        app.UseRateLimiter();
        app.MapGet("/healthz", () => Results.Json(new Dictionary<string, object?>
        {
            ["status"] = "ok",
            ["catalog_id"] = catalogId,
            ["served_by"] = $"datarepo {BundleWriter.PackageVersion}",
            ["record"] = BundleWriter.PathText(root),
            ["save_tool"] = settings.Contributions is not null,
        }));
        app.MapMcp("/mcp");
        app.Lifetime.ApplicationStopped.Register(catalog.Dispose);
        return app;
    }

    /// <summary>The address a started application listens on (with its real port when it asked for port 0).</summary>
    public static string Address(WebApplication app) =>
        app.Services.GetRequiredService<IServer>().Features.Get<IServerAddressesFeature>()!.Addresses.First().TrimEnd('/');
}
