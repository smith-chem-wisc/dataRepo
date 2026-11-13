using DataRepo.Bundle;
using DataRepo.Catalog;

namespace DataRepo.Mcp;

/// <summary><c>datarepo contribute verify</c> (design/AI_CONTRIBUTIONS.md S11, A17; reworked in
/// design/AI_CONTRIBUTIONS_V2.md V5): re-runs a saved result's queries on the frozen catalog it was computed from, the way
/// the server ran them, and says which reproduce.</summary>
/// <remarks>
/// <para>Each query runs through a <see cref="CatalogServer"/> on that catalog's own file, so it meets the same sandbox,
/// the same caps and the same row hash (<see cref="Mcp.RowsHash"/>) as when the server answered it, with the row limit
/// it was run with (097 finding 3: a query run with <c>max_rows</c> was re-run without it and read "differs"). A catalog
/// that is not there is reported; nothing is ever re-run on the latest catalog in its place, which would answer a
/// different question.</para>
/// <para><b>What "reproduced" means, and only that:</b> running this query again on that catalog returns rows with the
/// same hash. It says nothing about whether the result follows from them, and a model's judgement is never called
/// reproduced (097 finding 3, A17): the report checks the queries behind it and says the judgement cannot be re-run.</para>
/// <para>A folder catalog's views read the bundles in the store, so once those are removed (after a re-ingest, say) the
/// catalog file is still there and its queries cannot run. That is reported as <c>basis_gone</c>, apart from a query
/// that fails for any other reason.</para>
/// </remarks>
public static class ContributionVerifier
{
    /// <param name="store">The store that holds the contribution.</param>
    /// <param name="catalog">The catalog folder (or one catalog file) that holds the catalog it was computed from.</param>
    /// <param name="id">The contribution's id.</param>
    /// <returns><c>contribution_id</c>, <c>catalog_id</c>, <c>queries</c> (each with its <c>outcome</c>:
    /// <c>reproduced</c>, <c>differs</c>, <c>ran_no_recorded_hash</c>, <c>basis_gone</c> or <c>failed</c>),
    /// <c>queries_reproduced</c> (every query reproduced), <c>basis_in_store</c> and the bundles missing from it, and
    /// <c>result</c>: what can be said of the result itself.</returns>
    /// <exception cref="ContributionException">No such contribution, or a catalog it names is not there.</exception>
    public static Dictionary<string, object?> Verify(string store, string catalog, string id)
    {
        var contribution = Contributions.Discover(store).FirstOrDefault(c => c.Id == id)
            ?? throw new ContributionException($"{BundleWriter.PathText(store)} holds no contribution {id}");
        var missing = contribution.BasisBundles
            .Where(b => !Directory.Exists(Path.Combine(store, b.DatasetId, b.BundleId)))
            .Select(b => (object?)$"{b.DatasetId} {b.BundleId}").ToList();
        var servers = new Dictionary<string, CatalogServer>(StringComparer.Ordinal);
        CatalogServer On(string catalogId)
        {
            if (servers.TryGetValue(catalogId, out var open)) return open;
            var file = Directory.Exists(catalog) ? Path.Combine(catalog, CatalogPointer.FileOf(catalogId)) : catalog;
            if (!File.Exists(file))
                throw new ContributionException(
                    $"catalog {catalogId}, which contribution {id} was computed from, is not in {BundleWriter.PathText(catalog)}: "
                    + "its queries are never re-run on another catalog, which would answer a different question");
            var server = new CatalogServer(file);
            if (PyValues.Str(server.Identity.CatalogId) != catalogId)
            {
                server.Dispose();
                throw new ContributionException($"{BundleWriter.PathText(file)} holds catalog {PyValues.Str(server.Identity.CatalogId)}, not {catalogId}");
            }
            return servers[catalogId] = server;
        }
        try
        {
            var method = (IReadOnlyDictionary<string, object?>)contribution.Record["method"]!;
            var queries = ((IEnumerable<object?>)method["queries"]!).Cast<IReadOnlyDictionary<string, object?>>().ToList();
            var report = new List<object?>();
            var ordinal = 0L;
            foreach (var q in queries)
            {
                var catalogId = q.GetValueOrDefault("catalog_id") as string ?? contribution.BasisCatalogId;
                var recorded = q.GetValueOrDefault("result_sha256") as string;
                var maxRows = q.GetValueOrDefault("max_rows") as long?;
                var line = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["ordinal"] = ++ordinal,
                    ["sql"] = q.GetValueOrDefault("sql"),
                    ["observed"] = q.GetValueOrDefault("observed"),
                    ["catalog_id"] = catalogId,
                    ["recorded_rows_sha256"] = recorded,
                };
                if (maxRows is not null) line["max_rows"] = maxRows;
                var server = On(catalogId);
                try
                {
                    var result = server.Sql((string)q["sql"]!, maxRows);
                    var hash = Mcp.RowsHash(result);
                    line["rows_sha256"] = hash;
                    line["row_count"] = result.GetValueOrDefault("row_count");
                    line["truncated"] = result.GetValueOrDefault("truncated");
                    line["outcome"] = recorded is null ? "ran_no_recorded_hash" : hash == recorded ? "reproduced" : "differs";
                }
                catch (DataRepoException e)
                {
                    line["outcome"] = missing.Count > 0 ? "basis_gone" : "failed";
                    line["error"] = e.Message;
                }
                report.Add(line);
            }
            var reproducibility = contribution.Record.GetValueOrDefault("reproducibility") as string;
            var queriesReproduced = report.Count > 0 && report.Cast<Dictionary<string, object?>>().All(r => (string?)r["outcome"] == "reproduced");
            var output = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["contribution_id"] = contribution.Id,
                ["kind"] = contribution.Kind,
                ["reproducibility"] = reproducibility,
                ["catalog_id"] = contribution.BasisCatalogId,
                ["basis_in_store"] = missing.Count == 0,
                ["queries"] = report,
                ["queries_reproduced"] = queriesReproduced,
                ["result"] = reproducibility switch
                {
                    "judgement" => "A model's judgement: frozen in this record, never re-runnable. Only the queries it rests on are checked above.",
                    "stochastic" => "The computation used randomness: its queries are checked above; its own result reproduces within the tolerance it states, not bit for bit.",
                    "code" => "Its queries are checked above; its code is named by sha256 and must be run again to check the result itself.",
                    _ => "Its queries are checked above: each reproduced query returned rows with the hash recorded when the result was made. "
                        + "That is all this checks; whether the result follows from those rows is not checked by anything.",
                },
            };
            if (missing.Count > 0)
            {
                output["basis_missing"] = missing;
                output["basis_note"] = "The store no longer holds bundles this result was computed from, so queries on the views over "
                    + "them cannot run. The result stays readable in every catalog; it can no longer be checked by re-running.";
            }
            return output;
        }
        finally
        {
            foreach (var server in servers.Values) server.Dispose();
        }
    }
}
