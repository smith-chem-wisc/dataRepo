using DataRepo.Bundle;
using DataRepo.Catalog;

namespace DataRepo.Mcp;

/// <summary><c>datarepo contribute verify</c> (design/AI_CONTRIBUTIONS.md S11, A17): re-runs a saved result's queries
/// on the frozen catalog it was computed from, the way the server ran them, and says which reproduce.</summary>
/// <remarks>
/// <para>Each query runs through a <see cref="CatalogServer"/> on that catalog's own file, so it meets the same sandbox,
/// the same caps and the same row hash (<see cref="Mcp.RowsHash"/>) as when the server answered it. A catalog that is
/// not there is reported; nothing is ever re-run on the latest catalog in its place, which would answer a different
/// question.</para>
/// <para>A model's judgement is not re-runnable: the report checks the queries behind it and says so.</para>
/// </remarks>
public static class ContributionVerifier
{
    /// <param name="store">The store that holds the contribution.</param>
    /// <param name="catalog">The catalog folder (or one catalog file) that holds the catalog it was computed from.</param>
    /// <param name="id">The contribution's id.</param>
    /// <returns><c>contribution_id</c>, <c>catalog_id</c>, <c>queries</c> (each with its <c>outcome</c>:
    /// <c>reproduced</c>, <c>differs</c>, <c>ran_no_recorded_hash</c> or <c>failed</c>), <c>reproduced</c> (every
    /// query reproduced) and, for a judgement or a stochastic result, what cannot be re-run.</returns>
    /// <exception cref="ContributionException">No such contribution, or a catalog it names is not there.</exception>
    public static Dictionary<string, object?> Verify(string store, string catalog, string id)
    {
        var contribution = Contributions.Discover(store).FirstOrDefault(c => c.Id == id)
            ?? throw new ContributionException($"{BundleWriter.PathText(store)} holds no contribution {id}");
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
                var line = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["ordinal"] = ++ordinal,
                    ["sql"] = q.GetValueOrDefault("sql"),
                    ["observed"] = q.GetValueOrDefault("observed"),
                    ["catalog_id"] = catalogId,
                    ["recorded_rows_sha256"] = recorded,
                };
                var server = On(catalogId);
                try
                {
                    var result = server.Sql((string)q["sql"]!);
                    var hash = Mcp.RowsHash(result);
                    line["rows_sha256"] = hash;
                    line["row_count"] = result.GetValueOrDefault("row_count");
                    line["truncated"] = result.GetValueOrDefault("truncated");
                    line["outcome"] = recorded is null ? "ran_no_recorded_hash" : hash == recorded ? "reproduced" : "differs";
                }
                catch (DataRepoException e)
                {
                    line["outcome"] = "failed";
                    line["error"] = e.Message;
                }
                report.Add(line);
            }
            var reproducibility = contribution.Record.GetValueOrDefault("reproducibility") as string;
            var output = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["contribution_id"] = contribution.Id,
                ["kind"] = contribution.Kind,
                ["reproducibility"] = reproducibility,
                ["catalog_id"] = contribution.BasisCatalogId,
                ["queries"] = report,
                ["reproduced"] = report.Count > 0 && report.Cast<Dictionary<string, object?>>().All(r => (string?)r["outcome"] == "reproduced"),
            };
            if (reproducibility == "judgement")
                output["judgement"] = "The model's judgement is frozen in this record and is not re-runnable; the queries it rests on are checked above.";
            if (reproducibility == "stochastic")
                output["stochastic"] = "The computation used randomness: its queries are checked above; its own result reproduces within the tolerance it states, not bit for bit.";
            return output;
        }
        finally
        {
            foreach (var server in servers.Values) server.Dispose();
        }
    }
}
