using System.Text.Json;
using DataRepo.Bundle;
using DataRepo.Catalog;
using DataRepo.Ingest;
using DataRepo.Mcp;

namespace DataRepo.Tests;

/// <summary>S7 of design/AI_CONTRIBUTIONS.md (A18): the MCP server keeps a public record of every call itself.</summary>
/// <remarks>The user, 2026-10-28: "the server side should independently choose to keep any interaction and the users
/// be given the option to have previous interactions be exposed to them", and "this is a public repo. no question is
/// private". So the record does not depend on an agent choosing to save anything: every call (a refused or malformed
/// one too) is written by the server, as an add-only hash chain beside the bundles, and loaded by every later catalog.
/// The server never sees a prompt or the model's prose, so neither is in it.</remarks>
[NonParallelizable]
public class SessionRecordTests
{
    private static string RepoRoot()
    {
        for (var dir = new DirectoryInfo(TestContext.CurrentContext.TestDirectory); dir is not null; dir = dir.Parent)
            if (File.Exists(Path.Combine(dir.FullName, "schema", "datarepo.yaml"))) return dir.FullName;
        throw new DirectoryNotFoundException("repository root");
    }

    private string _root = "";
    private string Store => Path.Combine(_root, "store");
    private string ManifestPath => Path.Combine(_root, "data", "manifest.yaml");
    private string Folder => Path.Combine(_root, "catalogs");
    private string SessionRoot => Path.Combine(Store, Sessions.Dir);
    private CatalogResult _a = null!;

    [SetUp]
    public void MakeScratch()
    {
        _root = Path.Combine(Path.GetTempPath(), "datarepo-sessions-" + Guid.NewGuid().ToString("N"));
        var from = Path.Combine(RepoRoot(), "tests", "data");
        var to = Path.Combine(_root, "data");
        foreach (var dir in Directory.EnumerateDirectories(from, "*", SearchOption.AllDirectories))
            Directory.CreateDirectory(Path.Combine(to, Path.GetRelativePath(from, dir)));
        foreach (var file in Directory.EnumerateFiles(from, "*", SearchOption.AllDirectories))
            File.Copy(file, Path.Combine(to, Path.GetRelativePath(from, file)));
        Ingester.Ingest(ManifestPath, "PXD999999", Store, rules: IngestRules.Current);
        _a = Build();
    }

    [TearDown]
    public void RemoveScratch()
    {
        if (Directory.Exists(_root)) Directory.Delete(_root, true);
    }

    private CatalogResult Build(string? release = null)
    {
        var manifest = Manifest.Load(ManifestPath);
        var bundles = CatalogBuilder.SelectBundles(manifest, ["PXD999999"], Store, latest: true);
        var notes = release is null ? null : new Dictionary<string, object?>(StringComparer.Ordinal) { ["release"] = release };
        return CatalogBuilder.BuildCatalog(bundles, Folder, instance: manifest.Instance, notes: notes, manifest: manifest);
    }

    private static Dictionary<string, JsonElement> Args(string json) => JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(json)!;

    private static List<IReadOnlyDictionary<string, object?>> Calls(SessionRef session) =>
        session.Entries.Where(e => (string?)e["type"] == "call").ToList();

    private SessionLog Open(CatalogServer server) => SessionLog.Open(SessionRoot, (string)server.Identity.CatalogId!);

    [Test]
    public void EveryCallIsRecordedByTheServerNotByTheAgentsChoice()
    {
        using (var server = new CatalogServer(Folder))
        using (var log = Open(server))
        {
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"query": "SELECT 1 AS x"}"""), log);
            Mcp.Mcp.CallTool(server, "datarepo_describe", Args("{}"), log);
        }
        var session = Sessions.Read(Store).Single();
        var header = session.Entries[0];
        Assert.Multiple(() =>
        {
            Assert.That(header["type"], Is.EqualTo("session"));
            Assert.That(header["visibility"], Is.EqualTo("public"));
            Assert.That(header["catalog_id"], Is.EqualTo(_a.CatalogId));
            var calls = Calls(session);
            Assert.That(calls.Select(c => c["tool"]), Is.EqualTo(new[] { "datarepo_sql", "datarepo_describe" }));
            Assert.That(((IReadOnlyDictionary<string, object?>)calls[0]["arguments"]!)["query"], Is.EqualTo("SELECT 1 AS x"));
            Assert.That(calls[0]["catalog_id"], Is.EqualTo(_a.CatalogId));
            Assert.That(calls[0]["outcome"], Is.EqualTo("ok"));
            Assert.That(calls[0]["row_count"], Is.EqualTo(1L));
            Assert.That(calls[0]["rows_sha256"], Does.Match("^[0-9a-f]{64}$"));
            Assert.That(calls.Select(c => c["seq"]), Is.EqualTo(new object?[] { 1L, 2L }));
            Assert.That(session.ChainOk, Is.True);
        });
    }

    [Test]
    public void TheAnswerNamesItsPlaceInTheRecord()
    {
        using var server = new CatalogServer(Folder);
        using var log = Open(server);
        var answer = Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"query": "SELECT 1 AS x"}"""), log);
        var call = answer.StructuredContent!.Value.GetProperty("session_call");
        Assert.That(call.GetProperty("session_id").GetString(), Is.EqualTo(log.SessionId));
        Assert.That(call.GetProperty("seq").GetInt64(), Is.EqualTo(1));
        log.Dispose();
        var entry = Calls(Sessions.Read(Store).Single())[0];
        Assert.That(call.GetProperty("entry_sha256").GetString(), Is.EqualTo(entry["entry_sha256"]));
    }

    [Test]
    public void WithoutARecordTheAnswerIsWhatItWas()
    {
        using var server = new CatalogServer(Folder);
        var answer = Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"query": "SELECT 1 AS x"}"""));
        Assert.That(answer.StructuredContent!.Value.TryGetProperty("session_call", out _), Is.False,
            "the parity answers (Python 0.32.0) are byte-identical when no record is kept");
    }

    [Test]
    public void RefusedAndMalformedCallsAreRecordedToo()
    {
        using (var server = new CatalogServer(Folder))
        using (var log = Open(server))
        {
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"query": "DROP TABLE catalog_meta"}"""), log);
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"max_rows": 3}"""), log);
            Mcp.Mcp.CallTool(server, "datarepo_write", Args("{}"), log);
        }
        var calls = Calls(Sessions.Read(Store).Single());
        Assert.That(calls.Select(c => (c["tool"], c["outcome"], c.GetValueOrDefault("error"))), Is.EqualTo(new (object?, object?, object?)[]
        {
            ("datarepo_sql", "error", "QueryRefused"),
            ("datarepo_sql", "invalid", null),
            ("datarepo_write", "invalid", null),
        }));
    }

    [Test]
    public void TheRowsHashIgnoresRowOrderAndTheAnswerHashDoesNot()
    {
        using (var server = new CatalogServer(Folder))
        using (var log = Open(server))
        {
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"query": "SELECT * FROM (VALUES (1), (2)) t(x) ORDER BY x"}"""), log);
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"query": "SELECT * FROM (VALUES (1), (2)) t(x) ORDER BY x DESC"}"""), log);
        }
        var calls = Calls(Sessions.Read(Store).Single());
        Assert.That(calls[1]["rows_sha256"], Is.EqualTo(calls[0]["rows_sha256"]));
        Assert.That(calls[1]["answer_sha256"], Is.Not.EqualTo(calls[0]["answer_sha256"]));
    }

    [Test]
    public void TheRecordIsAHashChainAndAnEditShows()
    {
        using (var server = new CatalogServer(Folder))
        using (var log = Open(server))
        {
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"query": "SELECT 1 AS x"}"""), log);
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"query": "SELECT 2 AS y"}"""), log);
        }
        var file = Sessions.Read(Store).Single().Path;
        File.WriteAllText(file, File.ReadAllText(file).Replace("SELECT 1 AS x", "SELECT 3 AS x", StringComparison.Ordinal));
        var session = Sessions.Read(Store).Single();
        Assert.That(session.ChainOk, Is.False);
        Assert.That(session.BrokenAtSeq, Is.EqualTo(1L));
    }

    [Test]
    public void AHalfWrittenLastLineIsIncompleteNotTampered()
    {
        using (var server = new CatalogServer(Folder))
        using (var log = Open(server))
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"query": "SELECT 1 AS x"}"""), log);
        var file = Sessions.Read(Store).Single().Path;
        File.AppendAllText(file, "{\"type\": \"call\", \"seq\": 2");
        var session = Sessions.Read(Store).Single();
        Assert.That(session.ChainOk, Is.True);
        Assert.That(session.Incomplete, Is.True);
        Assert.That(Calls(session), Has.Count.EqualTo(1));
    }

    [Test]
    public void TheServerTellsEveryClientItsCallsArePublic()
    {
        using var server = new CatalogServer(Folder);
        using var log = Open(server);
        Assert.That(Mcp.Mcp.ServerOptions(server, log: log).ServerInstructions, Does.Contain("public").IgnoreCase);
        Assert.That(Mcp.Mcp.ServerOptions(server).ServerInstructions, Is.Null);
    }

    [Test]
    public void TheClientAppIsRecordedOnceAsObserved()
    {
        using (var server = new CatalogServer(Folder))
        using (var log = Open(server))
        {
            log.SetClient("claude-code", "2.1.309");
            log.SetClient("claude-code", "2.1.309");
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"query": "SELECT 1 AS x"}"""), log);
        }
        var clients = Sessions.Read(Store).Single().Entries.Where(e => (string?)e["type"] == "client").ToList();
        Assert.That(clients, Has.Count.EqualTo(1));
        Assert.That(clients[0]["name"], Is.EqualTo("claude-code"));
    }

    [Test]
    public void TheDefaultRecordIsBesideTheBundlesOfTheServedStore()
    {
        using var server = new CatalogServer(Folder);
        Assert.That(Path.GetFullPath(Mcp.Mcp.DefaultSessionRoot(server)!), Is.EqualTo(Path.GetFullPath(SessionRoot)));
    }

    [Test]
    public void ACatalogWithNoSessionsHasNoSessionTables()
    {
        Assert.That(CatalogBuilder.RunQuery(Folder, "SELECT count(*) FROM information_schema.tables WHERE table_name LIKE 'session%'").Rows[0][0], Is.EqualTo(0L));
    }

    [Test]
    public void SessionsAreLoadedIntoEveryLaterCatalogAndAReleaseKeepsThem()
    {
        string id;
        using (var server = new CatalogServer(Folder))
        using (var log = Open(server))
        {
            id = log.SessionId;
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args("""{"query": "SELECT 1 AS x"}"""), log);
        }
        var b = Build(release: "v1");
        Assert.That(b.CatalogId, Is.Not.EqualTo(_a.CatalogId));
        Assert.That(b.ReleaseId, Is.EqualTo(_a.ReleaseId), "the measured data did not change");
        Assert.That(CatalogBuilder.RunQuery(Folder, "SELECT session_id, visibility, n_calls, chain_ok FROM sessions").Rows,
            Is.EqualTo(new List<object?[]> { new object?[] { id, "public", 1L, true } }));
        Assert.That(CatalogBuilder.RunQuery(Folder, "SELECT tool, json_extract_string(arguments, '$.query'), outcome FROM session_calls").Rows,
            Is.EqualTo(new List<object?[]> { new object?[] { "datarepo_sql", "SELECT 1 AS x", "ok" } }));
        Assert.That((string)CatalogBuilder.RunQuery(Folder, "SELECT notes FROM catalog_meta").Rows[0][0]!, Does.Contain(id));
        File.Delete(Sessions.Read(Store).Single().Path);
        Assert.That(() => Build(), Throws.TypeOf<CatalogException>().With.Message.Contains(id).And.Message.Contains("v1"));
    }

    [Test]
    public void EverySessionTableIsDocumented()
    {
        Assert.That(Sessions.TableDocs.Keys.Order(StringComparer.Ordinal), Is.EqualTo(Sessions.Tables.Order(StringComparer.Ordinal)));
    }
}
