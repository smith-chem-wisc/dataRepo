using System.Security.Cryptography;
using System.Text;
using DataRepo.Bundle;
using DuckDB.NET.Data;

namespace DataRepo.Catalog;

/// <summary>Contributions in a catalog build (design/AI_CONTRIBUTIONS.md, A9-A14).</summary>
public static partial class CatalogBuilder
{
    /// <summary>Every contribution in the stores <paramref name="bundles"/> come from (A9): never a selection, so no build
    /// can leave one out. None in a Python 0.32.0 parity scope, whose catalogs had none.</summary>
    public static List<ContributionRef> ContributionsFor(IReadOnlyList<BundleRef> bundles)
    {
        if (SchemaContract.IsPython0320) return [];
        return bundles
            .Select(b => System.IO.Path.GetDirectoryName(System.IO.Path.GetDirectoryName(System.IO.Path.GetFullPath(b.Path))!)!)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .SelectMany(Contributions.Discover)
            .GroupBy(c => c.Sha256, StringComparer.Ordinal).Select(g => g.First())
            .OrderBy(c => c.Id, StringComparer.Ordinal)
            .ToList();
    }

    /// <summary>The catalog id's line for its contributions, or null when there are none, so a store without any keeps
    /// the catalog id it had (the census rule, A10).</summary>
    private static string? ContributionLine(IReadOnlyList<ContributionRef> contributions)
    {
        if (contributions.Count == 0) return null;
        var set = string.Concat(contributions.Select(c => c.Sha256 + "\n").Order(StringComparer.Ordinal));
        return $"contributions/{Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(set)))[..16]}\n";
    }

    /// <summary>A13: a build into <paramref name="folder"/> refuses if a contribution an earlier release in that folder
    /// carried is no longer in the store. A release is frozen once published; this is what keeps that true of its
    /// contributions in every release after it.</summary>
    /// <exception cref="CatalogException">One is missing.</exception>
    private static void CheckReleasedContributionsKept(string folder, IReadOnlyList<ContributionRef> contributions, IReadOnlyList<SessionRef> sessions)
    {
        if (!Directory.Exists(folder)) return;
        var have = contributions.Select(c => c.Id).ToHashSet(StringComparer.Ordinal);
        var records = sessions.GroupBy(s => s.SessionId, StringComparer.Ordinal).ToDictionary(g => g.Key, g => g.First(), StringComparer.Ordinal);
        var lost = new List<string>();
        var changed = new List<string>();
        foreach (var file in Directory.EnumerateFiles(folder, "catalog-*.duckdb").Order(StringComparer.Ordinal))
        {
            var (release, carried, anchors) = ReleasedContributions(file);
            if (release is null) continue;
            var where = $"release {release}, {System.IO.Path.GetFileName(file)}";
            lost.AddRange(carried.Where(id => !have.Contains(id)).Select(id => $"{id} ({where})"));
            foreach (var (id, lines, head) in anchors)
            {
                if (!records.TryGetValue(id, out var s)) changed.Add($"{id} is gone ({where})");
                else if (s.Entries.Count < lines || s.Entries[(int)lines - 1].GetValueOrDefault("entry_sha256") as string != head
                         || (!s.ChainOk && s.BrokenAtSeq is { } at && at < lines))
                    changed.Add($"{id} ({s.Path}) no longer holds the {lines} line(s) the release recorded ({where})");
            }
        }
        if (lost.Count > 0)
            throw new CatalogException(
                "the store no longer holds contribution(s) an earlier release carried, so nothing was built: "
                + string.Join(", ", lost) + ". A released contribution is carried into every later catalog; restore its "
                + $"folder under {Contributions.Dir}/ (it is retracted by a new contribution, never deleted).");
        if (changed.Count > 0)
            throw new CatalogException(
                "the public session record an earlier release carried has changed, so nothing was built: " + string.Join("; ", changed)
                + $". A released session is never edited, re-chained or removed; restore the file under {Sessions.Dir}/.");
    }

    /// <summary>The release a catalog file was built for, the contribution ids it recorded, and each session it carried
    /// as (id, how many lines, the last line's hash).</summary>
    private static (string? Release, List<string> Contributions, List<(string Id, long Lines, string Head)> Sessions) ReleasedContributions(string path)
    {
        try
        {
            using var con = Open(path, readOnly: true);
            if (Query(con, "SELECT notes FROM catalog_meta").SingleOrDefault()?[0] is not string notes) return (null, [], []);
            using var doc = System.Text.Json.JsonDocument.Parse(notes);
            var root = doc.RootElement;
            if (root.ValueKind != System.Text.Json.JsonValueKind.Object
                || !root.TryGetProperty("release", out var release) || release.ValueKind != System.Text.Json.JsonValueKind.String)
                return (null, [], []);
            var ids = root.TryGetProperty("contributions", out var list) && list.ValueKind == System.Text.Json.JsonValueKind.Array
                ? list.EnumerateArray().Where(e => e.ValueKind == System.Text.Json.JsonValueKind.String).Select(e => e.GetString()!).ToList()
                : [];
            var anchors = new List<(string, long, string)>();
            if (root.TryGetProperty("sessions", out var held) && held.ValueKind == System.Text.Json.JsonValueKind.Array)
                foreach (var s in held.EnumerateArray())
                    if (s.ValueKind == System.Text.Json.JsonValueKind.Object
                        && s.TryGetProperty("session_id", out var id) && id.ValueKind == System.Text.Json.JsonValueKind.String
                        && s.TryGetProperty("lines", out var n) && n.TryGetInt64(out var lines) && lines > 0
                        && s.TryGetProperty("head_sha256", out var h) && h.ValueKind == System.Text.Json.JsonValueKind.String)
                        anchors.Add((id.GetString()!, lines, h.GetString()!));
            return (release.GetString(), ids, anchors);
        }
        catch (Exception e) when (e is DuckDBException or IOException or System.Text.Json.JsonException)
        {
            return (null, [], []);
        }
    }

    /// <summary>The stores <paramref name="bundles"/> come from.</summary>
    private static List<string> StoresOf(IReadOnlyList<BundleRef> bundles) =>
        bundles.Select(b => System.IO.Path.GetDirectoryName(System.IO.Path.GetDirectoryName(System.IO.Path.GetFullPath(b.Path))!)!)
            .Distinct(StringComparer.OrdinalIgnoreCase).ToList();

    /// <summary>Every public session record in the stores <paramref name="bundles"/> come from (A18). None in a Python
    /// 0.32.0 parity scope.</summary>
    public static List<SessionRef> SessionsFor(IReadOnlyList<BundleRef> bundles) =>
        SchemaContract.IsPython0320 ? [] : StoresOf(bundles).SelectMany(Sessions.Read).ToList();

    /// <summary>Whether <paramref name="store"/> holds a session record file where the views read them
    /// (<c>_sessions/&lt;date&gt;/&lt;id&gt;.jsonl</c>).</summary>
    private static bool HasSessionRecord(string store)
    {
        var root = System.IO.Path.Combine(store, Sessions.Dir);
        return Directory.Exists(root) && Directory.EnumerateDirectories(root).Any(d => Directory.EnumerateFiles(d, "*.jsonl").Any());
    }

    /// <summary>Whether any of <paramref name="stores"/> holds a session record, so a folder catalog serves the views.</summary>
    private static bool HasSessionRecords(IReadOnlyList<string> stores) => stores.Any(HasSessionRecord);

    /// <summary>What a release records of each session it carries: its id, how many lines it then held, and the last
    /// line's hash. A later build holds the record to that (097 finding 8: re-chained lines used to build as intact).</summary>
    private static List<object?> SessionAnchors(IReadOnlyList<SessionRef> sessions) =>
        sessions.Where(s => s.Entries.Count > 0).OrderBy(s => s.SessionId, StringComparer.Ordinal).Select(s => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["session_id"] = s.SessionId,
            ["lines"] = (long)s.Entries.Count,
            ["head_sha256"] = s.Entries[^1].GetValueOrDefault("entry_sha256") as string,
        }).ToList();

    /// <summary>The views <c>sessions</c> and <c>session_calls</c> over the record files of a folder catalog's stores
    /// (A18, design/AI_CONTRIBUTIONS_V2.md V3).</summary>
    /// <remarks>Views, read when they are queried, and not in the catalog id (097 finding 5): a store whose server
    /// answered a question still rebuilds as unchanged, and a catalog shows every session up to the moment it is read.
    /// Made only when a store holds at least one record file, since DuckDB refuses a file pattern that matches nothing;
    /// a server writes its record's first line when it starts, so any agent asking through one has a file to read. A
    /// half-written last line (a server stopped mid-write) is left out. Whether each record's hash chain holds is checked
    /// in C# (<see cref="Sessions.Read"/>), and a release holds the record to what it carried.</remarks>
    private static void CreateSessionViews(DuckDBConnection con, IReadOnlyList<string> stores)
    {
        var patterns = stores.Where(HasSessionRecord)
            .Select(s => $"'{AsPosix(System.IO.Path.Combine(s, Sessions.Dir)).Replace("'", "''", StringComparison.Ordinal)}/*/*.jsonl'")
            .ToList();
        if (patterns.Count == 0) return;
        var lines = $@"read_json([{string.Join(", ", patterns)}], format = 'newline_delimited', ignore_errors = true, filename = true, columns = {{
            'type': 'VARCHAR', 'seq': 'BIGINT', 'session_id': 'VARCHAR', 'started_utc': 'VARCHAR', 'datarepo_version': 'VARCHAR',
            'catalog_id': 'VARCHAR', 'visibility': 'VARCHAR', 'utc': 'VARCHAR', 'name': 'VARCHAR', 'version': 'VARCHAR',
            'tool': 'VARCHAR', 'arguments': 'JSON', 'outcome': 'VARCHAR', 'error': 'VARCHAR', 'row_count': 'BIGINT',
            'truncated': 'BOOLEAN', 'answer_sha256': 'VARCHAR', 'rows_sha256': 'VARCHAR', 'tables_touched': 'JSON',
            'prev_sha256': 'VARCHAR', 'entry_sha256': 'VARCHAR'}})";
        // The session id of a call line is its file's name, as the server writes it.
        var line = $"SELECT *, regexp_extract(filename, '([0-9a-f]{{16}})\\.jsonl$', 1) AS record_id FROM {lines} WHERE type IS NOT NULL";
        Exec(con, $@"
        CREATE VIEW sessions AS
        WITH l AS ({line})
        SELECT s.record_id AS session_id, s.started_utc, s.datarepo_version, s.catalog_id, s.visibility,
               c.name AS client_name, c.version AS client_version,
               (SELECT count(*) FROM l x WHERE x.record_id = s.record_id AND x.type = 'call') AS n_calls
        FROM l s LEFT JOIN l c ON c.record_id = s.record_id AND c.type = 'client'
        WHERE s.type = 'session'");
        Exec(con, $@"
        CREATE VIEW session_calls AS
        SELECT record_id AS session_id, seq, utc, tool, arguments, catalog_id, outcome, error, row_count, truncated,
               answer_sha256, rows_sha256, tables_touched, prev_sha256, entry_sha256
        FROM ({line}) WHERE type = 'call'");
    }

    /// <summary>The catalog ids contributions were computed from: <c>--keep</c> never prunes those files (A14).</summary>
    private static HashSet<string> CitedCatalogs(IReadOnlyList<ContributionRef> contributions) =>
        contributions.Select(c => c.BasisCatalogId).ToHashSet(StringComparer.Ordinal);

    /// <summary>The contribution tables (A9, A11, A12), with how many rows each holds. Only called when there is at least one.</summary>
    /// <exception cref="ContributionException">A supersession cycle.</exception>
    private static Dictionary<string, long> CreateContributionTables(DuckDBConnection con, IReadOnlyList<ContributionRef> contributions,
        IReadOnlyList<BundleRef> bundles)
    {
        var byId = contributions.ToDictionary(c => c.Id, StringComparer.Ordinal);
        var retractedBy = contributions.Where(c => c.Kind == "retraction" && c.Target is not null)
            .GroupBy(c => c.Target!, StringComparer.Ordinal).ToDictionary(g => g.Key, g => g.Select(c => c.Id).Min(StringComparer.Ordinal)!, StringComparer.Ordinal);
        var supersededBy = contributions.Where(c => c.Supersedes is not null)
            .GroupBy(c => c.Supersedes!, StringComparer.Ordinal).ToDictionary(g => g.Key, g => g.Select(c => c.Id).Min(StringComparer.Ordinal)!, StringComparer.Ordinal);
        foreach (var c in contributions)
        {
            var seen = new HashSet<string>(StringComparer.Ordinal) { c.Id };
            for (var at = c.Supersedes; at is not null; at = byId.TryGetValue(at, out var next) ? next.Supersedes : null)
                if (!seen.Add(at))
                    throw new ContributionException($"contributions {string.Join(" -> ", seen)} supersede one another in a cycle; nothing was built");
        }
        var served = bundles.ToDictionary(b => b.DatasetId, b => b.BundleId, StringComparer.Ordinal);
        var stores = bundles.Select(b => System.IO.Path.GetDirectoryName(System.IO.Path.GetDirectoryName(System.IO.Path.GetFullPath(b.Path))!)!).Distinct().ToList();

        Exec(con, @"
        CREATE TABLE contributions (
            contribution_id VARCHAR, contribution_sha256 VARCHAR, kind VARCHAR, title VARCHAR, summary VARCHAR,
            model_provider VARCHAR, model_id VARCHAR, model_stated_by VARCHAR, model_evidence VARCHAR,
            client_name VARCHAR, client_version VARCHAR, submitted_by VARCHAR, submitted_by_orcid VARCHAR,
            licence VARCHAR, reproducibility VARCHAR, basis_catalog_id VARCHAR, supersedes VARCHAR, target VARCHAR,
            reason VARCHAR, status VARCHAR, superseded_by VARCHAR, retracted_by VARCHAR,
            submitted_utc VARCHAR, datarepo_version VARCHAR, accepted_utc VARCHAR, accepted_by VARCHAR, path VARCHAR, record JSON
        )");
        Exec(con, "CREATE TABLE contribution_basis (contribution_id VARCHAR, dataset_id VARCHAR, bundle_id VARCHAR, in_this_catalog BOOLEAN, catalog_bundle_id VARCHAR, bundle_in_store BOOLEAN)");
        Exec(con, "CREATE TABLE contribution_builds_on (contribution_id VARCHAR, builds_on_id VARCHAR)");
        Exec(con, "CREATE TABLE contribution_items (contribution_id VARCHAR, ordinal BIGINT, subject_type VARCHAR, subject_id VARCHAR, value DOUBLE, rank BIGINT, label VARCHAR, attributes JSON)");
        Exec(con, "CREATE TABLE contribution_edges (contribution_id VARCHAR, ordinal BIGINT, source_type VARCHAR, source_id VARCHAR, target_type VARCHAR, target_id VARCHAR, weight DOUBLE, label VARCHAR)");
        Exec(con, "CREATE TABLE contribution_queries (contribution_id VARCHAR, ordinal BIGINT, sql VARCHAR, observed BOOLEAN, catalog_id VARCHAR, result_sha256 VARCHAR, row_count BIGINT, truncated BOOLEAN, session_id VARCHAR, seq BIGINT)");

        static object? Get(IReadOnlyDictionary<string, object?>? map, string key) => map is not null && map.TryGetValue(key, out var v) ? v : null;
        static IReadOnlyDictionary<string, object?>? Sub(IReadOnlyDictionary<string, object?> map, string key) =>
            Get(map, key) as IReadOnlyDictionary<string, object?>;
        static IEnumerable<IReadOnlyDictionary<string, object?>> Each(IReadOnlyDictionary<string, object?>? map, string key) =>
            Get(map, key) is IEnumerable<object?> list ? list.Cast<IReadOnlyDictionary<string, object?>>() : [];

        long items = 0, edges = 0, queries = 0, basisRows = 0, buildsOn = 0;
        using (var contributionRows = con.CreateAppender("contributions"))
        using (var basisAppender = con.CreateAppender("contribution_basis"))
        using (var onAppender = con.CreateAppender("contribution_builds_on"))
        using (var itemAppender = con.CreateAppender("contribution_items"))
        using (var edgeAppender = con.CreateAppender("contribution_edges"))
        using (var queryAppender = con.CreateAppender("contribution_queries"))
        {
            foreach (var c in contributions)
            {
                var r = c.Record;
                var model = Sub(r, "model");
                var client = Sub(r, "client");
                var by = Sub(r, "submitted_by");
                var status = retractedBy.ContainsKey(c.Id) ? "retracted" : supersededBy.ContainsKey(c.Id) ? "superseded" : "active";
                contributionRows.CreateRow()
                    .AppendValue(c.Id).AppendValue(c.Sha256).AppendValue(c.Kind).AppendValue((string?)Get(r, "title")).AppendValue((string?)Get(r, "summary"))
                    .AppendValue((string?)Get(model, "provider")).AppendValue((string?)Get(model, "id")).AppendValue((string?)Get(model, "stated_by"))
                    .AppendValue((string?)Get(model, "evidence"))
                    .AppendValue((string?)Get(client, "name")).AppendValue((string?)Get(client, "version"))
                    .AppendValue((string?)Get(by, "name")).AppendValue((string?)Get(by, "orcid"))
                    .AppendValue((string?)Get(r, "licence")).AppendValue((string?)Get(r, "reproducibility")).AppendValue(c.BasisCatalogId)
                    .AppendValue(c.Supersedes).AppendValue(c.Target).AppendValue((string?)Get(r, "reason"))
                    .AppendValue(status).AppendValue(supersededBy.GetValueOrDefault(c.Id)).AppendValue(retractedBy.GetValueOrDefault(c.Id))
                    .AppendValue((string?)Get(r, "submitted_utc")).AppendValue((string?)Get(r, "datarepo_version"))
                    .AppendValue((string?)Get(r, "accepted_utc")).AppendValue((string?)Get(r, "accepted_by"))
                    .AppendValue(AsPosix(c.Path)).AppendValue(PyFormat.Json(r, sortKeys: true, ensureAscii: true))
                    .EndRow();
                foreach (var (dataset, bundle) in c.BasisBundles)
                {
                    var now = served.GetValueOrDefault(dataset);
                    var inStore = stores.Any(s => Directory.Exists(System.IO.Path.Combine(s, dataset, bundle)));
                    basisAppender.CreateRow().AppendValue(c.Id).AppendValue(dataset).AppendValue(bundle)
                        .AppendValue(now == bundle).AppendValue(now).AppendValue(inStore).EndRow();
                    basisRows++;
                }
                foreach (var on in c.BuildsOn)
                {
                    onAppender.CreateRow().AppendValue(c.Id).AppendValue(on).EndRow();
                    buildsOn++;
                }
                long ordinal = 0;
                foreach (var item in Each(r, "items"))
                {
                    itemAppender.CreateRow().AppendValue(c.Id).AppendValue(++ordinal)
                        .AppendValue((string?)Get(item, "subject_type")).AppendValue((string?)Get(item, "subject_id"))
                        .AppendValue(Get(item, "value") is { } v ? Convert.ToDouble(v, System.Globalization.CultureInfo.InvariantCulture) : (double?)null)
                        .AppendValue(Get(item, "rank") as long?).AppendValue((string?)Get(item, "label"))
                        .AppendValue(Get(item, "attributes") is { } a ? PyFormat.Json(a, sortKeys: true, ensureAscii: true) : null)
                        .EndRow();
                    items++;
                }
                ordinal = 0;
                foreach (var edge in Each(r, "edges"))
                {
                    edgeAppender.CreateRow().AppendValue(c.Id).AppendValue(++ordinal)
                        .AppendValue((string?)Get(edge, "source_type")).AppendValue((string?)Get(edge, "source_id"))
                        .AppendValue((string?)Get(edge, "target_type")).AppendValue((string?)Get(edge, "target_id"))
                        .AppendValue(Get(edge, "weight") is { } w ? Convert.ToDouble(w, System.Globalization.CultureInfo.InvariantCulture) : (double?)null)
                        .AppendValue((string?)Get(edge, "label"))
                        .EndRow();
                    edges++;
                }
                ordinal = 0;
                foreach (var query in Each(Sub(r, "method"), "queries"))
                {
                    queryAppender.CreateRow().AppendValue(c.Id).AppendValue(++ordinal)
                        .AppendValue((string?)Get(query, "sql")).AppendValue(Get(query, "observed") as bool?)
                        .AppendValue((string?)Get(query, "catalog_id")).AppendValue((string?)Get(query, "result_sha256"))
                        .AppendValue(Get(query, "row_count") as long?).AppendValue(Get(query, "truncated") as bool?)
                        .AppendValue((string?)Get(query, "session_id")).AppendValue(Get(query, "seq") as long?)
                        .EndRow();
                    queries++;
                }
            }
        }
        Exec(con, "CREATE VIEW contributions_current AS SELECT * FROM contributions WHERE status = 'active' AND kind <> 'retraction'");
        return new Dictionary<string, long>(StringComparer.Ordinal)
        {
            ["contributions"] = contributions.Count,
            ["contribution_basis"] = basisRows,
            ["contribution_builds_on"] = buildsOn,
            ["contribution_items"] = items,
            ["contribution_edges"] = edges,
            ["contribution_queries"] = queries,
            ["contributions_current"] = contributions.LongCount(c => c.Kind != "retraction" && !retractedBy.ContainsKey(c.Id) && !supersededBy.ContainsKey(c.Id)),
        };
    }
}
