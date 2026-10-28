using System.Text.Json;
using DataRepo.Bundle;
using DataRepo.Catalog;
using DataRepo.Ingest;
using DataRepo.Mcp;
using static DataRepo.Tests.ContributionSubmissionTests;

namespace DataRepo.Tests;

/// <summary>S8 of design/AI_CONTRIBUTIONS.md: an AI saves a result through the MCP server, into an inbox, citing its
/// own queries by their place in the public session record; the operator accepts it into the store.</summary>
/// <remarks>The save tool exists only when the server is started with an inbox (A15), so a read-only server lists
/// exactly the tools it did. A cited query is copied from the record by the server, never taken from the agent, and
/// <c>accept</c> checks it against the record on disk again (A16): an inbox file is only a request.</remarks>
[NonParallelizable]
public class ContributionMcpTests
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
    private string Inbox => Path.Combine(_root, "inbox");
    private CatalogResult _a = null!;
    private string _bundle = "";

    [SetUp]
    public void MakeScratch()
    {
        _root = Path.Combine(Path.GetTempPath(), "datarepo-contrib-mcp-" + Guid.NewGuid().ToString("N"));
        var from = Path.Combine(RepoRoot(), "tests", "data");
        var to = Path.Combine(_root, "data");
        foreach (var dir in Directory.EnumerateDirectories(from, "*", SearchOption.AllDirectories))
            Directory.CreateDirectory(Path.Combine(to, Path.GetRelativePath(from, dir)));
        foreach (var file in Directory.EnumerateFiles(from, "*", SearchOption.AllDirectories))
            File.Copy(file, Path.Combine(to, Path.GetRelativePath(from, file)));
        _bundle = BundleRef.Load(Ingester.Ingest(ManifestPath, "PXD999999", Store, rules: IngestRules.Current).BundlePath).BundleId;
        _a = Build();
    }

    [TearDown]
    public void RemoveScratch()
    {
        if (Directory.Exists(_root)) Directory.Delete(_root, true);
    }

    private CatalogResult Build()
    {
        var manifest = Manifest.Load(ManifestPath);
        var bundles = CatalogBuilder.SelectBundles(manifest, ["PXD999999"], Store, latest: true);
        return CatalogBuilder.BuildCatalog(bundles, Folder, instance: manifest.Instance, manifest: manifest);
    }

    private static Dictionary<string, JsonElement> Args(object value) =>
        JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(JsonSerializer.Serialize(value))!;

    /// <summary>A result with no queries of its own: the server fills them from what it cites.</summary>
    private Dictionary<string, object?> Result()
    {
        var submission = Submission(_a.CatalogId, "PXD999999", _bundle);
        ((Dictionary<string, object?>)submission["method"]!)["queries"] = new List<object?>();
        return submission;
    }

    private static JsonElement Structured(ModelContextProtocol.Protocol.CallToolResult answer) => answer.StructuredContent!.Value;

    private (CatalogServer Server, SessionLog Log) Serve()
    {
        var server = new CatalogServer(Folder);
        return (server, SessionLog.Open(Path.Combine(Store, Sessions.Dir), _a.CatalogId));
    }

    [Test]
    public void WithoutAnInboxThereIsNoSaveTool()
    {
        var (server, log) = Serve();
        using (server)
        using (log)
        {
            Assert.That(Mcp.Mcp.ServerOptions(server, log: log).Handlers.ListToolsHandler, Is.Not.Null);
            Assert.That(Mcp.Mcp.ToolNames(inbox: null), Is.EqualTo(Mcp.Mcp.ToolSpecs.Select(s => s.Name)));
            Assert.That(Mcp.Mcp.ToolNames(inbox: Inbox), Does.Contain(Mcp.Mcp.SaveTool));
            var answer = Mcp.Mcp.CallTool(server, Mcp.Mcp.SaveTool, Args(new { contribution = Result() }), log);
            Assert.That(answer.IsError, Is.True, "an unknown tool on a server started without an inbox");
        }
        Assert.That(Directory.Exists(Inbox), Is.False);
    }

    [Test]
    public void ASavedResultGoesToTheInboxWithItsCitedQueriesObserved()
    {
        var (server, log) = Serve();
        string id;
        using (server)
        using (log)
        {
            var sql = Structured(Mcp.Mcp.CallTool(server, "datarepo_sql", Args(new { query = "SELECT dataset_id FROM catalog_bundles" }), log));
            var seq = sql.GetProperty("session_call").GetProperty("seq").GetInt64();
            var saved = Structured(Mcp.Mcp.CallTool(server, Mcp.Mcp.SaveTool, Args(new { contribution = Result(), cites = new[] { seq } }), log, Inbox));
            Assert.That(saved.TryGetProperty("error", out var error), Is.False, error.ToString());
            Assert.That(saved.GetProperty("status").GetString(), Is.EqualTo("pending_review"));
            id = saved.GetProperty("contribution_id").GetString()!;
        }
        Assert.That(Directory.Exists(Path.Combine(Store, Contributions.Dir)), Is.False, "nothing reaches the store before the operator accepts it");
        var pending = Contributions.Pending(Inbox).Single();
        Assert.That(pending.Id, Is.EqualTo(id));
        var query = ((List<object?>)((Dictionary<string, object?>)pending.Submission["method"]!)["queries"]!).Cast<Dictionary<string, object?>>().Single();
        Assert.Multiple(() =>
        {
            Assert.That(query["sql"], Is.EqualTo("SELECT dataset_id FROM catalog_bundles"));
            Assert.That(query["observed"], Is.True);
            Assert.That(query["catalog_id"], Is.EqualTo(_a.CatalogId));
            Assert.That(query["row_count"], Is.EqualTo(1L));
            Assert.That(query["seq"], Is.EqualTo(1L));
        });
        var calls = Sessions.Read(Store).Single().Entries.Where(e => (string?)e["type"] == "call").Select(e => e["tool"]).ToList();
        Assert.That(calls, Is.EqualTo(new[] { "datarepo_sql", Mcp.Mcp.SaveTool }), "the save is in the public record too");
    }

    [Test]
    public void OnlyASuccessfulQueryOfThisSessionCanBeCited()
    {
        var (server, log) = Serve();
        using (server)
        using (log)
        {
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args(new { query = "DROP TABLE catalog_meta" }), log);
            Mcp.Mcp.CallTool(server, "datarepo_describe", Args(new { }), log);
            foreach (var seq in new long[] { 1, 2, 9 })
            {
                var saved = Structured(Mcp.Mcp.CallTool(server, Mcp.Mcp.SaveTool, Args(new { contribution = Result(), cites = new[] { seq } }), log, Inbox));
                Assert.That(saved.GetProperty("error").GetString(), Is.EqualTo("ToolError"), $"seq {seq}");
            }
        }
        Assert.That(Contributions.Pending(Inbox), Is.Empty);
    }

    [Test]
    public void AnAgentCannotStateAQueryObservedOrNameItsOwnClient()
    {
        var (server, log) = Serve();
        using (server)
        using (log)
        {
            var observed = Result();
            ((Dictionary<string, object?>)observed["method"]!)["queries"] = new List<object?>
            {
                Map(("sql", "SELECT 1"), ("observed", true), ("catalog_id", _a.CatalogId), ("result_sha256", new string('a', 64))),
            };
            var client = Result();
            client["client"] = Map(("name", "trusted-client"));
            foreach (var submission in new[] { observed, client })
                Assert.That(Structured(Mcp.Mcp.CallTool(server, Mcp.Mcp.SaveTool, Args(new { contribution = submission }), log, Inbox))
                    .GetProperty("error").GetString(), Is.EqualTo("ToolError"));
        }
    }

    [Test]
    public void ABasisOutsideTheServedCatalogIsRefused()
    {
        var (server, log) = Serve();
        using (server)
        using (log)
        {
            var other = Submission("1111111111111111", "PXD999999", _bundle);
            var saved = Structured(Mcp.Mcp.CallTool(server, Mcp.Mcp.SaveTool, Args(new { contribution = other }), log, Inbox));
            Assert.That(saved.GetProperty("message").GetString(), Does.Contain("1111111111111111"));
        }
    }

    [Test]
    public void AcceptingPutsItInTheStoreAndTheCatalogShowsItsQueriesObserved()
    {
        var (server, log) = Serve();
        string id;
        using (server)
        using (log)
        {
            var seq = Structured(Mcp.Mcp.CallTool(server, "datarepo_sql", Args(new { query = "SELECT 1 AS x" }), log))
                .GetProperty("session_call").GetProperty("seq").GetInt64();
            id = Structured(Mcp.Mcp.CallTool(server, Mcp.Mcp.SaveTool, Args(new { contribution = Result(), cites = new[] { seq } }), log, Inbox))
                .GetProperty("contribution_id").GetString()!;
        }
        var accepted = Contributions.Accept(Inbox, id, Store, Folder);
        Assert.That(accepted.Id, Is.EqualTo(id));
        Assert.That(Contributions.Pending(Inbox), Is.Empty, "an accepted file leaves the pending list");
        Build();
        Assert.That(CatalogBuilder.RunQuery(Folder, "SELECT sql, observed, seq IS NOT NULL FROM contribution_queries").Rows,
            Is.EqualTo(new List<object?[]> { new object?[] { "SELECT 1 AS x", true, true } }));
    }

    [Test]
    public void AnObservedQueryTheRecordDoesNotHoldIsRefusedAtAccept()
    {
        var (server, log) = Serve();
        string id;
        using (server)
        using (log)
        {
            var seq = Structured(Mcp.Mcp.CallTool(server, "datarepo_sql", Args(new { query = "SELECT 1 AS x" }), log))
                .GetProperty("session_call").GetProperty("seq").GetInt64();
            id = Structured(Mcp.Mcp.CallTool(server, Mcp.Mcp.SaveTool, Args(new { contribution = Result(), cites = new[] { seq } }), log, Inbox))
                .GetProperty("contribution_id").GetString()!;
        }
        var file = Contributions.Pending(Inbox).Single().Path;
        File.WriteAllText(file, File.ReadAllText(file).Replace("SELECT 1 AS x", "SELECT 2 AS x", StringComparison.Ordinal));
        Assert.That(() => Contributions.Accept(Inbox, id, Store, Folder),
            Throws.TypeOf<ContributionException>().With.Message.Contains("public session record"));
        Assert.That(Directory.Exists(Path.Combine(Store, Contributions.Dir)), Is.False);
    }

    // --- S9: the next researcher or model finds earlier work -------------------------------------------

    /// <summary>One session that queried protein_groups and saved a result from it, accepted and built into a catalog.</summary>
    private string EarlierWork()
    {
        var (server, log) = Serve();
        string id;
        using (server)
        using (log)
        {
            var seq = Structured(Mcp.Mcp.CallTool(server, "datarepo_sql", Args(new { query = "SELECT count(*) AS n FROM protein_groups" }), log))
                .GetProperty("session_call").GetProperty("seq").GetInt64();
            id = Structured(Mcp.Mcp.CallTool(server, Mcp.Mcp.SaveTool, Args(new { contribution = Result(), cites = new[] { seq } }), log, Inbox))
                .GetProperty("contribution_id").GetString()!;
        }
        Contributions.Accept(Inbox, id, Store, Folder);
        Build();
        return id;
    }

    [Test]
    public void TheRecordNotesWhichTablesEachQueryTouched()
    {
        var (server, log) = Serve();
        using (server)
        using (log)
            Mcp.Mcp.CallTool(server, "datarepo_sql", Args(new { query = "SELECT count(*) AS n FROM protein_groups" }), log);
        var call = Sessions.Read(Store).Single().Entries.Single(e => (string?)e["type"] == "call");
        Assert.That(((List<object?>)call["tables_touched"]!).Cast<string>(), Does.Contain("protein_groups"));
    }

    [Test]
    public void DescribeTellsTheNextModelThatEarlierWorkExists()
    {
        using (var before = new CatalogServer(Folder))
        {
            var overview = before.Describe();
            Assert.That(overview.ContainsKey("contributions") || overview.ContainsKey("public_sessions"), Is.False,
                "a catalog without them describes itself exactly as before");
        }
        EarlierWork();
        using var after = new CatalogServer(Folder);
        var described = after.Describe();
        var contributions = (Dictionary<string, object?>)described["contributions"]!;
        Assert.That(contributions["active"], Is.EqualTo(1L));
        Assert.That(((Dictionary<string, object?>)described["public_sessions"]!)["calls"], Is.EqualTo(2L));
    }

    [Test]
    public void AUserWhoAsksIsShownEarlierWorkOnTheSameTables()
    {
        var id = EarlierWork();
        using var server = new CatalogServer(Folder);
        var plain = server.Sql("SELECT count(*) AS n FROM protein_groups");
        Assert.That(plain.ContainsKey("prior_work"), Is.False, "shown only to a user who opted in");
        server.ShowPrior = true;
        var shown = server.Sql("SELECT count(*) AS n FROM protein_groups");
        var prior = (Dictionary<string, object?>)shown["prior_work"]!;
        Assert.That(prior["calls"], Is.EqualTo(1L));
        Assert.That(((List<object?>)prior["contributions"]!).Cast<Dictionary<string, object?>>().Select(c => c["contribution_id"]),
            Is.EqualTo(new[] { id }));
        var elsewhere = server.Sql("SELECT count(*) AS n FROM catalog_meta");
        Assert.That(elsewhere.ContainsKey("prior_work"), Is.False, "no earlier work touched that table");
    }

    // --- S11: a saved result's queries re-run on the frozen catalog they were computed from --------------

    /// <summary>A result whose one query names the catalog it ran on, so its answer differs on any other catalog.</summary>
    private string ResultOnA()
    {
        var (server, log) = Serve();
        string id;
        using (server)
        using (log)
        {
            var seq = Structured(Mcp.Mcp.CallTool(server, "datarepo_sql", Args(new { query = "SELECT catalog_id FROM catalog_meta" }), log))
                .GetProperty("session_call").GetProperty("seq").GetInt64();
            id = Structured(Mcp.Mcp.CallTool(server, Mcp.Mcp.SaveTool, Args(new { contribution = Result(), cites = new[] { seq } }), log, Inbox))
                .GetProperty("contribution_id").GetString()!;
        }
        Contributions.Accept(Inbox, id, Store, Folder);
        return id;
    }

    [Test]
    public void ASavedResultsQueriesReproduceOnTheCatalogItWasComputedFromNotTheLatest()
    {
        var id = ResultOnA();
        var b = Build();
        Assert.That(b.CatalogId, Is.Not.EqualTo(_a.CatalogId), "the latest catalog is another one, and answers that query differently");
        var report = ContributionVerifier.Verify(Store, Folder, id);
        Assert.Multiple(() =>
        {
            Assert.That(report["catalog_id"], Is.EqualTo(_a.CatalogId));
            Assert.That(report["reproduced"], Is.True);
            var query = ((List<object?>)report["queries"]!).Cast<Dictionary<string, object?>>().Single();
            Assert.That(query["outcome"], Is.EqualTo("reproduced"));
            Assert.That(query["rows_sha256"], Is.EqualTo(query["recorded_rows_sha256"]));
        });
    }

    [Test]
    public void AMissingCatalogIsReportedNeverRunOnTheLatest()
    {
        var id = ResultOnA();
        Build();
        File.Delete(Path.Combine(Folder, CatalogPointer.FileOf(_a.CatalogId)));
        Assert.That(() => ContributionVerifier.Verify(Store, Folder, id),
            Throws.TypeOf<ContributionException>().With.Message.Contains(_a.CatalogId).And.Message.Contains("not"));
    }

    [Test]
    public void AStatedQueryRunsButCannotBeCheckedAndAJudgementSaysItCannotBeRerun()
    {
        var submission = Submission(_a.CatalogId, "PXD999999", _bundle);
        submission["reproducibility"] = "judgement";
        var saved = Contributions.Save(Store, Folder, submission);
        var report = ContributionVerifier.Verify(Store, Folder, saved.Id);
        var query = ((List<object?>)report["queries"]!).Cast<Dictionary<string, object?>>().Single();
        Assert.That(query["outcome"], Is.EqualTo("ran_no_recorded_hash"));
        Assert.That(report["reproduced"], Is.False, "nothing recorded to compare against is not a reproduction");
        Assert.That((string)report["judgement"]!, Does.Contain("not re-runnable"));
    }

    [Test]
    public void RejectingKeepsTheRequestAndSaysWhy()
    {
        var (server, log) = Serve();
        string id;
        using (server)
        using (log)
            id = Structured(Mcp.Mcp.CallTool(server, Mcp.Mcp.SaveTool, Args(new { contribution = Result() }), log, Inbox))
                .GetProperty("contribution_id").GetString()!;
        Contributions.Reject(Inbox, id, "duplicates an earlier result");
        Assert.That(Contributions.Pending(Inbox), Is.Empty);
        var kept = Path.Combine(Inbox, "rejected", $"{id}.json");
        Assert.That(File.Exists(kept), Is.True);
        Assert.That(File.ReadAllText(Path.Combine(Inbox, "rejected", $"{id}.reason.txt")), Does.Contain("duplicates"));
    }
}
