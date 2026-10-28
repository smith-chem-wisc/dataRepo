using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using DataRepo.Bundle;

namespace DataRepo.Catalog;

/// <summary>A contribution was refused: what it says is incomplete, unverifiable, or would overwrite another.</summary>
public class ContributionException(string message) : CatalogException(message);

/// <summary>What <see cref="Contributions.Save"/> did.</summary>
/// <param name="Id">The folder name and the id a catalog shows: the first 16 hex of <paramref name="Sha256"/>.</param>
/// <param name="Sha256">The full content hash, stored and compared (64 bits is too short for content outsiders send).</param>
/// <param name="Path">The contribution's directory.</param>
/// <param name="AlreadySaved">The same contribution was in the store already; nothing was written.</param>
public sealed record ContributionSaved(string Id, string Sha256, string Path, bool AlreadySaved);

/// <summary>One saved contribution, as <c>build</c> reads it.</summary>
/// <param name="Path">The contribution's directory.</param>
/// <param name="Record">The parsed <c>contribution.json</c>: the submission plus what the save added.</param>
public sealed record ContributionRef(string Path, IReadOnlyDictionary<string, object?> Record)
{
    public string Sha256 => (string)Record["contribution_sha256"]!;

    public string Id => Sha256[..16];

    public string Kind => (string)Record["kind"]!;

    public IReadOnlyDictionary<string, object?> Basis => (IReadOnlyDictionary<string, object?>)Record["basis"]!;

    public string BasisCatalogId => (string)Basis["catalog_id"]!;

    /// <summary>The <c>(dataset, bundle)</c> pairs the contribution was computed from.</summary>
    public IReadOnlyList<(string DatasetId, string BundleId)> BasisBundles =>
        ((IEnumerable<object?>)Basis["bundles"]!).Cast<IReadOnlyDictionary<string, object?>>()
            .Select(b => ((string)b["dataset_id"]!, (string)b["bundle_id"]!)).ToList();

    /// <summary>The contributions this one builds on.</summary>
    public IReadOnlyList<string> BuildsOn =>
        Basis.TryGetValue("contributions", out var ids) && ids is IEnumerable<object?> list ? list.Cast<string>().ToList() : [];

    public string? Target => Record.TryGetValue("target", out var v) ? v as string : null;

    public string? Supersedes => Record.TryGetValue("supersedes", out var v) ? v as string : null;

    /// <summary>The submission exactly as it was hashed: the record without what the save added.</summary>
    public IReadOnlyDictionary<string, object?> Submission =>
        Record.Where(kv => !Contributions.Written.Contains(kv.Key)).ToDictionary(kv => kv.Key, kv => kv.Value, StringComparer.Ordinal);
}

/// <summary>Results an AI model (or a person) computed from a catalog, saved back into the store and carried into every
/// later catalog: design/AI_CONTRIBUTIONS.md.</summary>
/// <remarks>
/// <para>Stored beside the bundles, never in one (A1): <c>&lt;store&gt;/_contributions/&lt;id&gt;/contribution.json</c>, outside
/// <c>_engine/</c>, so none of the engine-artefact selection rules (which drop an artefact whose bundle was re-searched,
/// or whose schema version differs) can ever drop one. The id hashes exactly what the submitter stated and nothing
/// else (A2): not the time, the install, or a schema or runner version, so it is the same in every later release.</para>
/// <para>Nothing is ever deleted (A12): a retraction or a supersession is another contribution.</para>
/// </remarks>
public static class Contributions
{
    /// <summary>Where contributions live in the store. The underscore keeps it out of the dataset namespace, as
    /// <c>_study/</c> and <c>_engine/</c> do.</summary>
    public const string Dir = "_contributions";

    public const string RecordFile = "contribution.json";

    /// <summary>The submission format this build reads and writes.</summary>
    public const string SubmissionVersion = "1";

    /// <summary>What kind of result a contribution is. A retraction withdraws another contribution.</summary>
    public static readonly IReadOnlyList<string> Kinds = ["site_list", "protein_list", "relation_graph", "table", "finding", "retraction"];

    /// <summary>The catalog's own licence (D3), or a public-domain dedication.</summary>
    public static readonly IReadOnlyList<string> Licences = ["CC-BY-4.0", "CC0-1.0"];

    /// <summary>A17: <c>query</c> and <c>code</c> re-run exactly; <c>stochastic</c> within a stated tolerance;
    /// <c>judgement</c> (a model's verdict) is frozen, not re-runnable.</summary>
    public static readonly IReadOnlyList<string> Reproducibility = ["query", "code", "stochastic", "judgement"];

    /// <summary>Who stated the model's identity (A5): the server can only see the client application, never the model.</summary>
    public static readonly IReadOnlyList<string> StatedBy = ["client", "operator"];

    /// <summary>The fields the save adds. A submitter may not send them: the store, not the client, says when and what.</summary>
    internal static readonly HashSet<string> Written =
        new(["contribution_sha256", "contribution_id", "submitted_utc", "datarepo_version", "record_version"], StringComparer.Ordinal);

    public const int MaxRows = 100_000;
    public const int MaxSqlChars = 65_536;
    public const int MaxQueries = 1_000;

    /// <summary>The catalog tables a build creates when the store holds at least one contribution (A9).</summary>
    public static readonly IReadOnlyList<string> Tables =
        ["contributions", "contribution_basis", "contribution_builds_on", "contribution_items", "contribution_edges", "contribution_queries", "contributions_current"];

    /// <summary>What each contribution table holds, for a reader and an agent.</summary>
    public static readonly IReadOnlyDictionary<string, string> TableDocs = new Dictionary<string, string>(StringComparer.Ordinal)
    {
        ["contributions"] = "One row per result an AI model or a person computed from a catalog and saved back into the store, "
            + "with which model made it (as STATED by the client or the operator: no server can observe a model), who is "
            + "accountable for it, its licence, and the catalog it was computed from (`basis_catalog_id`). These rows are "
            + "claims made from the data, not measurements: read `reproducibility` and `status` before building on one.",
        ["contribution_basis"] = "The exact (dataset, bundle) pairs each contribution was computed from. `in_this_catalog` is "
            + "false when this catalog serves another bundle of that dataset (it was searched again); `catalog_bundle_id` "
            + "is the bundle served now. The contribution still names the frozen catalog it used.",
        ["contribution_builds_on"] = "Which earlier contributions each one builds on.",
        ["contribution_items"] = "The rows of a list result (sites, proteins, a table), in the submitter's order.",
        ["contribution_edges"] = "The edges of a relation graph (for example, how cell types relate).",
        ["contribution_queries"] = "The SQL each contribution recorded. `observed` is true only for a query the MCP server "
            + "itself ran and hashed (`result_sha256`, on `catalog_id`); a stated query is what the submitter says it ran.",
        ["contributions_current"] = "Contributions that are neither retracted nor superseded, and are not themselves retractions.",
    };

    private static readonly Regex Hex16 = new("^[0-9a-f]{16}$", RegexOptions.CultureInvariant);
    private static readonly Regex Hex64 = new("^[0-9a-f]{64}$", RegexOptions.CultureInvariant);
    private static readonly Regex Orcid = new(@"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", RegexOptions.CultureInvariant);

    // --- the submission ---------------------------------------------------------------------------------

    /// <summary>JSON text as plain values: objects, lists, strings, longs, doubles, booleans and nulls.</summary>
    /// <exception cref="ContributionException">Not JSON, not an object, or a key appears twice.</exception>
    public static Dictionary<string, object?> Parse(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            return Plain(doc.RootElement, "") as Dictionary<string, object?>
                ?? throw new ContributionException("a contribution is a JSON object");
        }
        catch (JsonException e)
        {
            throw new ContributionException($"a contribution must be JSON: {e.Message}");
        }
    }

    private static object? Plain(JsonElement e, string path) => e.ValueKind switch
    {
        JsonValueKind.Object => PlainObject(e, path),
        JsonValueKind.Array => e.EnumerateArray().Select((x, i) => Plain(x, $"{path}[{i}]")).ToList(),
        JsonValueKind.String => e.GetString(),
        // Boxed apart: `? l : e.GetDouble()` would make every integer a double, and a stored record would hash differently.
        JsonValueKind.Number => e.TryGetInt64(out var l) ? (object)l : e.GetDouble(),
        JsonValueKind.True => true,
        JsonValueKind.False => false,
        _ => null,
    };

    private static Dictionary<string, object?> PlainObject(JsonElement e, string path)
    {
        var map = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var p in e.EnumerateObject())
        {
            var at = path.Length == 0 ? p.Name : $"{path}.{p.Name}";
            if (map.ContainsKey(p.Name)) throw new ContributionException($"{at} appears twice");
            map[p.Name] = Plain(p.Value, at);
        }
        return map;
    }

    /// <summary>Checks a submission and returns it normalised: line ends LF, numbers typed, basis bundles sorted.</summary>
    /// <exception cref="ContributionException">A field is missing, unknown, or holds the wrong thing; the message names it.</exception>
    public static Dictionary<string, object?> Validate(IReadOnlyDictionary<string, object?> submission)
    {
        foreach (var key in submission.Keys.Where(Written.Contains))
            throw new ContributionException($"{key} is written by the store when it saves a contribution, never sent by the submitter");
        var top = Fields(submission, "",
            ["contribution_version", "kind", "title", "model", "submitted_by", "licence", "reproducibility", "basis", "method"],
            ["summary", "client", "items", "edges", "target", "supersedes", "reason"]);
        var n = new Dictionary<string, object?>(StringComparer.Ordinal);
        var version = Text(top["contribution_version"], "contribution_version");
        if (version != SubmissionVersion)
            throw new ContributionException($"contribution_version must be \"{SubmissionVersion}\", got \"{version}\"");
        n["contribution_version"] = version;
        var kind = OneOf(top["kind"], "kind", Kinds);
        n["kind"] = kind;
        n["title"] = Text(top["title"], "title", max: 300);
        if (top.TryGetValue("summary", out var summary)) n["summary"] = Text(summary, "summary");
        n["model"] = Model(top["model"]);
        if (top.TryGetValue("client", out var client))
        {
            var c = Fields(client, "client", ["name"], ["version"]);
            var observed = new Dictionary<string, object?>(StringComparer.Ordinal) { ["name"] = Text(c["name"], "client.name") };
            if (c.TryGetValue("version", out var v)) observed["version"] = Text(v, "client.version");
            n["client"] = observed;
        }
        var person = Fields(top["submitted_by"], "submitted_by", ["name"], ["orcid"]);
        var by = new Dictionary<string, object?>(StringComparer.Ordinal) { ["name"] = Text(person["name"], "submitted_by.name") };
        if (person.TryGetValue("orcid", out var orcid))
        {
            var o = Text(orcid, "submitted_by.orcid");
            if (!Orcid.IsMatch(o)) throw new ContributionException($"submitted_by.orcid must look like 0000-0002-1825-0097, got \"{o}\"");
            by["orcid"] = o;
        }
        n["submitted_by"] = by;
        n["licence"] = OneOf(top["licence"], "licence", Licences);
        n["reproducibility"] = OneOf(top["reproducibility"], "reproducibility", Reproducibility);
        n["basis"] = Basis(top["basis"]);
        n["method"] = Method(top["method"]);

        var hasItems = top.ContainsKey("items");
        var hasEdges = top.ContainsKey("edges");
        if (hasItems) n["items"] = Rows(top["items"], "items", Item);
        if (hasEdges) n["edges"] = Rows(top["edges"], "edges", Edge);
        var rows = (hasItems ? ((List<object?>)n["items"]!).Count : 0) + (hasEdges ? ((List<object?>)n["edges"]!).Count : 0);
        if (rows > MaxRows) throw new ContributionException($"items and edges hold {rows} rows; a contribution holds at most {MaxRows}");

        if (kind == "retraction")
        {
            if (!top.ContainsKey("target")) throw new ContributionException("a retraction names its target: the id of the contribution it withdraws");
            if (!top.ContainsKey("reason")) throw new ContributionException("a retraction gives its reason");
            foreach (var forbidden in new[] { "items", "edges", "supersedes" })
                if (top.ContainsKey(forbidden)) throw new ContributionException($"a retraction carries no result: remove {forbidden}");
            n["target"] = Id(top["target"], "target");
            n["reason"] = Text(top["reason"], "reason");
        }
        else
        {
            foreach (var forbidden in new[] { "target", "reason" })
                if (top.ContainsKey(forbidden)) throw new ContributionException($"{forbidden} belongs to a retraction, and this is a {kind}");
            if (top.TryGetValue("supersedes", out var supersedes)) n["supersedes"] = Id(supersedes, "supersedes");
            switch (kind)
            {
                case "site_list" or "protein_list" or "table" when !hasItems || ((List<object?>)n["items"]!).Count == 0:
                    throw new ContributionException($"a {kind} holds its rows in items, and it has none");
                case "relation_graph" when !hasEdges || ((List<object?>)n["edges"]!).Count == 0:
                    throw new ContributionException("a relation_graph holds its edges in edges, and it has none");
                case "finding" when !top.ContainsKey("summary"):
                    throw new ContributionException("a finding states itself in summary, and it has none");
            }
        }
        return n;
    }

    private static Dictionary<string, object?> Model(object? value)
    {
        var m = Fields(value, "model", ["provider", "id", "stated_by"], ["evidence"]);
        var id = Text(m["id"], "model.id", max: 200);
        if (id.EndsWith("latest", StringComparison.OrdinalIgnoreCase))
            throw new ContributionException($"model.id \"{id}\" is an alias that names a different model over time; give the exact model id");
        var model = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["provider"] = Text(m["provider"], "model.provider", max: 200),
            ["id"] = id,
            ["stated_by"] = OneOf(m["stated_by"], "model.stated_by", StatedBy),
        };
        if (m.TryGetValue("evidence", out var evidence)) model["evidence"] = Text(evidence, "model.evidence");
        return model;
    }

    private static Dictionary<string, object?> Basis(object? value)
    {
        var b = Fields(value, "basis", ["catalog_id", "bundles"], ["contributions"]);
        var basis = new Dictionary<string, object?>(StringComparer.Ordinal) { ["catalog_id"] = Id(b["catalog_id"], "basis.catalog_id") };
        var bundles = List(b["bundles"], "basis.bundles").Select((x, i) =>
        {
            var at = $"basis.bundles[{i}]";
            var f = Fields(x, at, ["dataset_id", "bundle_id"], []);
            return (Dataset: Text(f["dataset_id"], $"{at}.dataset_id", max: 100), Bundle: Id(f["bundle_id"], $"{at}.bundle_id"));
        }).Distinct().OrderBy(x => x.Dataset, StringComparer.Ordinal).ThenBy(x => x.Bundle, StringComparer.Ordinal).ToList();
        if (bundles.Count == 0) throw new ContributionException("basis.bundles names no bundle: say which data the result was computed from");
        basis["bundles"] = bundles.Select(x => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["dataset_id"] = x.Dataset,
            ["bundle_id"] = x.Bundle,
        }).ToList();
        if (b.TryGetValue("contributions", out var on))
            basis["contributions"] = List(on, "basis.contributions").Select((x, i) => Id(x, $"basis.contributions[{i}]"))
                .Distinct().Order(StringComparer.Ordinal).Cast<object?>().ToList();
        return basis;
    }

    private static Dictionary<string, object?> Method(object? value)
    {
        var m = Fields(value, "method", ["description", "queries"], ["code", "parameters"]);
        var method = new Dictionary<string, object?>(StringComparer.Ordinal) { ["description"] = Text(m["description"], "method.description") };
        var queries = List(m["queries"], "method.queries");
        if (queries.Count > MaxQueries) throw new ContributionException($"method.queries holds {queries.Count}; at most {MaxQueries}");
        method["queries"] = queries.Select((x, i) => (object?)Query(x, $"method.queries[{i}]")).ToList();
        if (m.TryGetValue("code", out var code))
            method["code"] = List(code, "method.code").Select((x, i) =>
            {
                var at = $"method.code[{i}]";
                var f = Fields(x, at, ["name", "sha256"], []);
                return (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["name"] = Text(f["name"], $"{at}.name"),
                    ["sha256"] = Sha(f["sha256"], $"{at}.sha256"),
                };
            }).ToList();
        if (m.TryGetValue("parameters", out var parameters))
            method["parameters"] = parameters as IReadOnlyDictionary<string, object?>
                ?? throw new ContributionException("method.parameters must be an object");
        return method;
    }

    private static Dictionary<string, object?> Query(object? value, string at)
    {
        var f = Fields(value, at, ["sql", "observed"], ["catalog_id", "result_sha256", "row_count", "truncated"]);
        var q = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["sql"] = Text(f["sql"], $"{at}.sql", max: MaxSqlChars),
            ["observed"] = Bool(f["observed"], $"{at}.observed"),
        };
        if (f.TryGetValue("catalog_id", out var c)) q["catalog_id"] = Id(c, $"{at}.catalog_id");
        if (f.TryGetValue("result_sha256", out var h)) q["result_sha256"] = Sha(h, $"{at}.result_sha256");
        if (f.TryGetValue("row_count", out var r))
        {
            var count = Integer(r, $"{at}.row_count");
            if (count < 0) throw new ContributionException($"{at}.row_count cannot be negative");
            q["row_count"] = count;
        }
        if (f.TryGetValue("truncated", out var t)) q["truncated"] = Bool(t, $"{at}.truncated");
        if ((bool)q["observed"]! && (!q.ContainsKey("catalog_id") || !q.ContainsKey("result_sha256")))
            throw new ContributionException($"{at} is marked observed, so it carries the catalog_id it ran on and its result_sha256");
        return q;
    }

    private static Dictionary<string, object?> Item(object? value, string at)
    {
        var f = Fields(value, at, ["subject_type", "subject_id"], ["value", "rank", "label", "attributes"]);
        var item = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["subject_type"] = Text(f["subject_type"], $"{at}.subject_type", max: 100),
            ["subject_id"] = Text(f["subject_id"], $"{at}.subject_id", max: 500),
        };
        if (f.TryGetValue("value", out var v) && v is not null) item["value"] = Number(v, $"{at}.value");
        if (f.TryGetValue("rank", out var r) && r is not null) item["rank"] = Integer(r, $"{at}.rank");
        if (f.TryGetValue("label", out var l) && l is not null) item["label"] = Text(l, $"{at}.label");
        if (f.TryGetValue("attributes", out var a) && a is not null)
            item["attributes"] = a as IReadOnlyDictionary<string, object?> ?? throw new ContributionException($"{at}.attributes must be an object");
        return item;
    }

    private static Dictionary<string, object?> Edge(object? value, string at)
    {
        var f = Fields(value, at, ["source_type", "source_id", "target_type", "target_id"], ["weight", "label"]);
        var edge = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["source_type"] = Text(f["source_type"], $"{at}.source_type", max: 100),
            ["source_id"] = Text(f["source_id"], $"{at}.source_id", max: 500),
            ["target_type"] = Text(f["target_type"], $"{at}.target_type", max: 100),
            ["target_id"] = Text(f["target_id"], $"{at}.target_id", max: 500),
        };
        if (f.TryGetValue("weight", out var w) && w is not null) edge["weight"] = Number(w, $"{at}.weight");
        if (f.TryGetValue("label", out var l) && l is not null) edge["label"] = Text(l, $"{at}.label");
        return edge;
    }

    private static List<object?> Rows(object? value, string at, Func<object?, string, Dictionary<string, object?>> row) =>
        List(value, at).Select((x, i) => (object?)row(x, $"{at}[{i}]")).ToList();

    /// <summary>An object's fields: every required one present, none unknown.</summary>
    private static IReadOnlyDictionary<string, object?> Fields(object? value, string at, string[] required, string[] optional)
    {
        var name = at.Length == 0 ? "the contribution" : at;
        if (value is not IReadOnlyDictionary<string, object?> map) throw new ContributionException($"{name} must be an object");
        var missing = required.Where(k => !map.ContainsKey(k)).ToList();
        if (missing.Count > 0)
            throw new ContributionException($"{name} is missing {string.Join(", ", missing.Select(k => at.Length == 0 ? k : $"{at}.{k}"))}");
        var known = required.Concat(optional).ToHashSet(StringComparer.Ordinal);
        var unknown = map.Keys.Where(k => !known.Contains(k)).Order(StringComparer.Ordinal).ToList();
        if (unknown.Count > 0)
            throw new ContributionException(
                $"{name} has unknown field(s) {string.Join(", ", unknown.Select(k => at.Length == 0 ? k : $"{at}.{k}"))}: "
                + $"refused, not ignored. Known: {string.Join(", ", known.Order(StringComparer.Ordinal))}");
        return map;
    }

    private static List<object?> List(object? value, string at) =>
        value is IEnumerable<object?> list ? list.ToList() : throw new ContributionException($"{at} must be a list");

    /// <summary>A non-empty string, line ends normalised to LF (they are hashed).</summary>
    private static string Text(object? value, string at, int? max = null)
    {
        if (value is not string s) throw new ContributionException($"{at} must be a string");
        s = s.Replace("\r\n", "\n", StringComparison.Ordinal).Replace('\r', '\n');
        if (s.Trim().Length == 0) throw new ContributionException($"{at} is empty");
        if (max is not null && s.Length > max) throw new ContributionException($"{at} is {s.Length} characters; at most {max}");
        return s;
    }

    private static string OneOf(object? value, string at, IReadOnlyList<string> allowed)
    {
        var s = value as string;
        if (s is null || !allowed.Contains(s))
            throw new ContributionException($"{at} must be one of {string.Join(", ", allowed)}; got {PyFormat.Json(value)}");
        return s;
    }

    private static string Id(object? value, string at)
    {
        if (value is not string s || !Hex16.IsMatch(s))
            throw new ContributionException($"{at} must be a 16-character lowercase hex id; got {PyFormat.Json(value)}");
        return s;
    }

    private static string Sha(object? value, string at)
    {
        if (value is not string s || !Hex64.IsMatch(s))
            throw new ContributionException($"{at} must be a 64-character lowercase hex sha256; got {PyFormat.Json(value)}");
        return s;
    }

    private static bool Bool(object? value, string at) => value as bool? ?? throw new ContributionException($"{at} must be true or false");

    private static long Integer(object? value, string at) =>
        value as long? ?? throw new ContributionException($"{at} must be a whole number");

    private static double Number(object? value, string at) => value switch
    {
        long l => l,
        double d when double.IsFinite(d) => d,
        _ => throw new ContributionException($"{at} must be a finite number"),
    };

    // --- the id ----------------------------------------------------------------------------------------

    /// <summary>The text the id hashes: the normalised submission as JSON, keys sorted, ASCII only.</summary>
    public static string Canonical(IReadOnlyDictionary<string, object?> normalised) => PyFormat.Json(normalised, sortKeys: true, ensureAscii: true);

    /// <summary>The full content hash of a normalised submission (A2).</summary>
    public static string Sha256Of(IReadOnlyDictionary<string, object?> normalised) =>
        Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(Canonical(normalised))));

    // --- the store -------------------------------------------------------------------------------------

    /// <summary>Saves one contribution beside the bundles of <paramref name="store"/>, after checking that what it says
    /// it was computed from is real.</summary>
    /// <param name="store">The store that holds the bundles.</param>
    /// <param name="catalog">A catalog folder (it holds <c>catalog-&lt;id&gt;.duckdb</c> files) or one catalog file:
    /// where the cited catalog is looked up. The catalog is known by the id it holds, never by its file name.</param>
    /// <param name="submission">The submission, as plain values.</param>
    /// <param name="allowObserved">Only the MCP server that ran a query and hashed its answer may mark it observed (A16).</param>
    /// <exception cref="ContributionException">The submission is invalid, the cited catalog or a bundle, contribution or
    /// target is not there, the target is already retracted, or another contribution holds the id's folder.</exception>
    public static ContributionSaved Save(string store, string catalog, IReadOnlyDictionary<string, object?> submission, bool allowObserved = false)
    {
        var normalised = Validate(submission);
        var method = (Dictionary<string, object?>)normalised["method"]!;
        if (!allowObserved && ((List<object?>)method["queries"]!).Cast<Dictionary<string, object?>>().Any(q => (bool)q["observed"]!))
            throw new ContributionException(
                "a query is marked observed, and only the MCP server that ran it may say so: mark it observed: false (stated), "
                + "or save through the server");
        var sha = Sha256Of(normalised);
        var id = sha[..16];
        var final = System.IO.Path.Combine(store, Dir, id);
        if (Directory.Exists(final))
        {
            var existing = Load(final);
            if (existing.Sha256 == sha) return new ContributionSaved(id, sha, BundleWriter.PathText(final), true);
            throw new ContributionException($"{BundleWriter.PathText(final)} holds contribution {existing.Sha256}, whose id begins as this one's ({sha}) does; nothing was written");
        }

        var basis = (Dictionary<string, object?>)normalised["basis"]!;
        CheckBasis(catalog, (string)basis["catalog_id"]!, (List<object?>)basis["bundles"]!);
        var saved = Discover(store).ToDictionary(c => c.Id, StringComparer.Ordinal);
        foreach (var on in basis.TryGetValue("contributions", out var ids) ? ((List<object?>)ids!).Cast<string>() : [])
            if (!saved.ContainsKey(on)) throw new ContributionException($"basis.contributions names {on}, which this store does not hold");
        if (normalised.TryGetValue("supersedes", out var supersedes) && !saved.ContainsKey((string)supersedes!))
            throw new ContributionException($"supersedes names {supersedes}, which this store does not hold");
        if (normalised.TryGetValue("target", out var target))
        {
            if (!saved.ContainsKey((string)target!)) throw new ContributionException($"target {target} is not a contribution this store holds");
            var prior = saved.Values.FirstOrDefault(c => c.Kind == "retraction" && c.Target == (string)target);
            if (prior is not null) throw new ContributionException($"{target} was already retracted by {prior.Id}; a contribution is retracted once");
        }

        var record = new SortedDictionary<string, object?>(StringComparer.Ordinal);
        foreach (var (k, v) in normalised) record[k] = v;
        record["contribution_sha256"] = sha;
        record["contribution_id"] = id;
        record["record_version"] = SubmissionVersion;
        record["datarepo_version"] = BundleWriter.PackageVersion;
        record["submitted_utc"] = DateTime.UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture);

        // Written into a staging directory, then renamed: a failure leaves nothing a build would read (EngineRunner).
        var staging = System.IO.Path.Combine(store, Dir, $".{id}.writing");
        if (Directory.Exists(staging)) Directory.Delete(staging, true);
        Directory.CreateDirectory(staging);
        try
        {
            File.WriteAllText(System.IO.Path.Combine(staging, RecordFile), PyFormat.JsonIndented(SortKeys(record), 1) + "\n", new UTF8Encoding(false));
            Directory.Move(staging, final);
        }
        catch
        {
            if (Directory.Exists(staging)) Directory.Delete(staging, true);
            throw;
        }
        return new ContributionSaved(id, sha, BundleWriter.PathText(final), false);
    }

    /// <summary>The cited catalog exists and holds every bundle the contribution names (A4).</summary>
    private static void CheckBasis(string catalog, string catalogId, List<object?> bundles)
    {
        var file = Directory.Exists(catalog) ? System.IO.Path.Combine(catalog, CatalogPointer.FileOf(catalogId)) : catalog;
        if (!File.Exists(file))
            throw new ContributionException(
                $"basis.catalog_id {catalogId} is not a catalog in {BundleWriter.PathText(catalog)}: a contribution names the catalog "
                + "it was computed from, and that catalog must exist");
        var held = CatalogBuilder.ReadCatalogId(file);
        if (held != catalogId)
            throw new ContributionException($"{BundleWriter.PathText(file)} holds catalog {held ?? "(none)"}, not {catalogId}");
        var served = ((IEnumerable<Dictionary<string, object?>>)CatalogBuilder.DescribeCatalog(file)["bundles"]!)
            .Select(b => ((string)b["dataset_id"]!, (string)b["bundle_id"]!)).ToHashSet();
        foreach (var b in bundles.Cast<Dictionary<string, object?>>())
        {
            var pair = ((string)b["dataset_id"]!, (string)b["bundle_id"]!);
            if (!served.Contains(pair))
                throw new ContributionException($"catalog {catalogId} does not hold {pair.Item1} bundle {pair.Item2}");
        }
    }

    /// <summary>Every contribution in <paramref name="store"/>, ordered by id. A staging directory (a save in progress or
    /// a failed one) is not a contribution.</summary>
    /// <exception cref="ContributionException">A record was changed after it was saved.</exception>
    public static List<ContributionRef> Discover(string store)
    {
        var root = System.IO.Path.Combine(store, Dir);
        if (!Directory.Exists(root)) return [];
        return Directory.EnumerateDirectories(root)
            .Where(d => !System.IO.Path.GetFileName(d).StartsWith('.') && File.Exists(System.IO.Path.Combine(d, RecordFile)))
            .Select(Load)
            .OrderBy(c => c.Id, StringComparer.Ordinal)
            .ToList();
    }

    /// <summary>One saved contribution, its hash checked against its content and its folder name.</summary>
    /// <remarks>The hash is recomputed over the stored submission as it stands, never re-validated: a rule added later
    /// must never make an earlier contribution unreadable, or it would drop out of the next release.</remarks>
    /// <exception cref="ContributionException">The record was changed after it was saved, or sits in the wrong folder.</exception>
    public static ContributionRef Load(string directory)
    {
        var path = System.IO.Path.Combine(directory, RecordFile);
        var record = Parse(File.ReadAllText(path, Encoding.UTF8));
        var shown = BundleWriter.PathText(directory);
        if (record.GetValueOrDefault("contribution_sha256") is not string sha || !Hex64.IsMatch(sha))
            throw new ContributionException($"{shown} has no contribution_sha256, so it is not a saved contribution");
        var c = new ContributionRef(BundleWriter.PathText(directory), record);
        var now = Sha256Of(c.Submission);
        if (now != sha)
            throw new ContributionException(
                $"contribution {c.Id} ({shown}) was changed after it was saved: its content hashes to {now}, and it was saved as "
                + $"{sha}. A contribution is never edited; save a new one that supersedes it.");
        if (System.IO.Path.GetFileName(directory) != c.Id)
            throw new ContributionException($"{shown} holds contribution {c.Id}, so it is in the wrong folder");
        return c;
    }

    private static object? SortKeys(object? value) => value switch
    {
        IReadOnlyDictionary<string, object?> d => new SortedDictionary<string, object?>(
            d.ToDictionary(kv => kv.Key, kv => SortKeys(kv.Value)), StringComparer.Ordinal),
        string s => s,
        System.Collections.IEnumerable e => e.Cast<object?>().Select(SortKeys).ToList(),
        _ => value,
    };
}
