using System.Net;
using System.Text;
using System.Text.Json;
using DataRepo.Bundle;
using DataRepo.Catalog;
using DataRepo.Host;
using DataRepo.Ingest;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;

namespace DataRepo.Tests;

/// <summary>S12 of design/AI_CONTRIBUTIONS.md: the hosted server (<c>DataRepo.Host</c>), MCP over HTTP, as the hosting
/// plan's part B proposes (PXReprise design/hosting/PXReprise_hosting_plan_2026-10-28.pdf).</summary>
/// <remarks>Many agents reach one server copy at once. Each MCP session gets its own public record (A18); a client
/// sending too much is told to slow down (HTTP 429) before it reaches the catalog; a health check names the catalog
/// served, for the host's load balancer.</remarks>
[NonParallelizable]
public class HostTests
{
    private static string RepoRoot()
    {
        for (var dir = new DirectoryInfo(TestContext.CurrentContext.TestDirectory); dir is not null; dir = dir.Parent)
            if (File.Exists(Path.Combine(dir.FullName, "schema", "datarepo.yaml"))) return dir.FullName;
        throw new DirectoryNotFoundException("repository root");
    }

    private string _root = "";
    private string Store => Path.Combine(_root, "store");
    private string Folder => Path.Combine(_root, "catalogs");
    private string _catalogId = "";

    [SetUp]
    public void MakeScratch()
    {
        _root = Path.Combine(Path.GetTempPath(), "datarepo-host-" + Guid.NewGuid().ToString("N"));
        var from = Path.Combine(RepoRoot(), "tests", "data");
        var to = Path.Combine(_root, "data");
        foreach (var dir in Directory.EnumerateDirectories(from, "*", SearchOption.AllDirectories))
            Directory.CreateDirectory(Path.Combine(to, Path.GetRelativePath(from, dir)));
        foreach (var file in Directory.EnumerateFiles(from, "*", SearchOption.AllDirectories))
            File.Copy(file, Path.Combine(to, Path.GetRelativePath(from, file)));
        var manifestPath = Path.Combine(to, "manifest.yaml");
        Ingester.Ingest(manifestPath, "PXD999999", Store, rules: IngestRules.Current);
        var manifest = Manifest.Load(manifestPath);
        _catalogId = CatalogBuilder.BuildCatalog(CatalogBuilder.SelectBundles(manifest, ["PXD999999"], Store), Folder,
            instance: manifest.Instance, manifest: manifest).CatalogId;
    }

    [TearDown]
    public void RemoveScratch()
    {
        if (Directory.Exists(_root)) Directory.Delete(_root, true);
    }

    private static async Task<McpClient> Connect(string address, string name) =>
        await McpClient.CreateAsync(
            new HttpClientTransport(new HttpClientTransportOptions { Endpoint = new Uri(address + "/mcp") }),
            new McpClientOptions { ClientInfo = new Implementation { Name = name, Version = "1.0" } });

    [Test]
    public async Task EveryAgentReachesTheToolsOverHttpAndEachSessionHasItsOwnPublicRecord()
    {
        await using (var app = HostedServer.Build(new HostSettings(Folder)))
        {
            await app.StartAsync();
            var address = HostedServer.Address(app);
            await using (var first = await Connect(address, "agent-one"))
            await using (var second = await Connect(address, "agent-two"))
            {
                Assert.That(first.ServerInstructions, Does.Contain("PUBLIC"), "every client is told at initialize");
                Assert.That((await first.ListToolsAsync()).Select(t => t.Name), Is.EqualTo(DataRepo.Mcp.Mcp.ToolSpecs.Select(s => s.Name)));
                var answer = await first.CallToolAsync("datarepo_sql", new Dictionary<string, object?> { ["query"] = "SELECT 1 AS x" });
                Assert.That(answer.IsError, Is.Not.True);
                Assert.That(answer.StructuredContent!.Value.GetProperty("session_call").GetProperty("record").GetString(), Is.EqualTo("public"));
                await second.CallToolAsync("datarepo_sql", new Dictionary<string, object?> { ["query"] = "SELECT 2 AS y" });
            }
            await app.StopAsync();
        }
        var sessions = Sessions.Read(Store);
        Assert.That(sessions, Has.Count.EqualTo(2), "one record per MCP session");
        Assert.That(sessions.All(s => s.ChainOk), Is.True);
        Assert.That(sessions.Select(s => s.Entries.Single(e => (string?)e["type"] == "client")["name"]).Order(),
            Is.EqualTo(new[] { "agent-one", "agent-two" }));
        Assert.That(sessions.All(s => (string?)s.Entries[0]["catalog_id"] == _catalogId), Is.True);
    }

    [Test]
    public async Task TheSaveToolIsServedOnlyWithAnInbox()
    {
        await using var app = HostedServer.Build(new HostSettings(Folder, Contributions: Path.Combine(_root, "inbox")));
        await app.StartAsync();
        await using (var client = await Connect(HostedServer.Address(app), "agent"))
            Assert.That((await client.ListToolsAsync()).Select(t => t.Name), Does.Contain(DataRepo.Mcp.Mcp.SaveTool));
        await app.StopAsync();
    }

    [Test]
    public async Task TheHealthCheckNamesTheCatalogServed()
    {
        await using var app = HostedServer.Build(new HostSettings(Folder));
        await app.StartAsync();
        using var http = new HttpClient();
        var response = await http.GetAsync(HostedServer.Address(app) + "/healthz");
        Assert.That(response.StatusCode, Is.EqualTo(HttpStatusCode.OK));
        using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        Assert.That(doc.RootElement.GetProperty("catalog_id").GetString(), Is.EqualTo(_catalogId));
        await app.StopAsync();
    }

    [Test]
    public async Task AClientSendingTooMuchIsToldToSlowDown()
    {
        await using var app = HostedServer.Build(new HostSettings(Folder, PermitPerMinute: 3));
        await app.StartAsync();
        using var http = new HttpClient();
        var codes = new List<HttpStatusCode>();
        for (var i = 0; i < 5; i++)
            codes.Add((await http.PostAsync(HostedServer.Address(app) + "/mcp",
                new StringContent("{}", Encoding.UTF8, "application/json"))).StatusCode);
        Assert.That(codes.Skip(3), Is.All.EqualTo(HttpStatusCode.TooManyRequests));
        Assert.That(codes.Take(3), Has.None.EqualTo(HttpStatusCode.TooManyRequests));
        await app.StopAsync();
    }

    /// <summary>The MCP spec: a server MUST validate the Origin header of every HTTP connection (DNS rebinding). An agent
    /// sends none; a web page's browser always does, and only the origins the operator names are served.</summary>
    [Test]
    public async Task AWebPageFromAnOriginNotNamedIsRefused()
    {
        await using var app = HostedServer.Build(new HostSettings(Folder, AllowedOrigins: ["https://catalog.example.org"]));
        await app.StartAsync();
        using var http = new HttpClient();
        async Task<HttpStatusCode> Post(string? origin)
        {
            using var request = new HttpRequestMessage(HttpMethod.Post, HostedServer.Address(app) + "/mcp")
            {
                Content = new StringContent("{}", Encoding.UTF8, "application/json"),
            };
            if (origin is not null) request.Headers.Add("Origin", origin);
            return (await http.SendAsync(request)).StatusCode;
        }
        Assert.That(await Post("https://evil.example.com"), Is.EqualTo(HttpStatusCode.Forbidden));
        Assert.That(await Post("https://catalog.example.org"), Is.Not.EqualTo(HttpStatusCode.Forbidden));
        Assert.That(await Post(null), Is.Not.EqualTo(HttpStatusCode.Forbidden), "an agent sends no Origin");
        await app.StopAsync();
    }

    [Test]
    public void AOneFileCatalogMustNameWhereTheRecordIsKept()
    {
        var file = Path.Combine(_root, "one.duckdb");
        var manifest = Manifest.Load(Path.Combine(_root, "data", "manifest.yaml"));
        CatalogBuilder.BuildCatalog(CatalogBuilder.SelectBundles(manifest, ["PXD999999"], Store), file, instance: manifest.Instance, manifest: manifest);
        Assert.That(() => HostedServer.Build(new HostSettings(file)), Throws.TypeOf<CatalogException>().With.Message.Contains("--sessions"));
    }
}
