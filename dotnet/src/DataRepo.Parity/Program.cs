using DataRepo.Bundle;
using DataRepo.Ingest;

// Parity tooling for the C# port (design/CSHARP_PORT.md). Not the product CLI, which is phase 5.
//
//   roundtrip <store> --out <scratch> [--latest] [accession ...]
//       Phase 1: read stored bundles written by the Python ingester and rewrite every table through the C#
//       writer; report anything that is not identical. <store> is read only.
//   ingest <manifest> <accession> --store <scratch> [--mm-settings <dir>] [--overwrite]
//       Phase 2: run the C# ingester on one dataset into a scratch store.
//   compare <expected bundle dir> <actual bundle dir>
//       Phase 2: every table of two bundles, row by row (Python's and C#'s ingest of the same inputs).
if (args.Length == 0)
{
    Console.Error.WriteLine("usage: roundtrip | ingest | compare (see Program.cs)");
    return 2;
}
return args[0] switch
{
    "roundtrip" => RoundTripVerb(args),
    "ingest" => IngestVerb(args),
    "compare" => CompareVerb(args),
    _ => Usage(),
};

static int Usage()
{
    Console.Error.WriteLine("usage: roundtrip | ingest | compare (see Program.cs)");
    return 2;
}

static string? Option(string[] args, string name)
{
    var i = Array.IndexOf(args, name);
    return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
}

static int IngestVerb(string[] args)
{
    if (args.Length < 3) return Usage();
    var store = Option(args, "--store");
    if (store is null)
    {
        Console.Error.WriteLine("--store <scratch> is required: the parity tool never writes into an operator's store");
        return 2;
    }
    var started = DateTime.UtcNow;
    var result = Ingester.Ingest(args[1], args[2], store, Option(args, "--mm-settings"), args.Contains("--overwrite"));
    Console.WriteLine($"  bundle   {result.BundlePath}{(result.Skipped ? " (unchanged, not rewritten)" : "")}");
    Console.WriteLine($"  tables   {string.Join(", ", result.RowCounts.Select(kv => $"{kv.Key} {kv.Value}"))}");
    foreach (var check in result.Mismatches)
        Console.WriteLine($"  MISMATCH {check["name"]}: bundle {check["observed"]} vs producer {check["expected"]}");
    Console.WriteLine($"  seconds  {(DateTime.UtcNow - started).TotalSeconds:F1}");
    return 0;
}

static int CompareVerb(string[] args)
{
    if (args.Length < 3) return Usage();
    var differences = RoundTrip.CompareBundles(args[1], args[2]);
    foreach (var d in differences) Console.WriteLine($"  DIFF  {d}");
    Console.WriteLine(differences.Count == 0 ? "  identical: every table, every row" : $"  {differences.Count} table(s) differ");
    return differences.Count == 0 ? 0 : 1;
}

static int RoundTripVerb(string[] args)
{
    if (args.Length < 2) return Usage();
    var store = args[1];
    var scratch = Option(args, "--out");
    if (scratch is null)
    {
        Console.Error.WriteLine("--out <scratch> is required; nothing is ever written under the store");
        return 2;
    }
    var latest = args.Contains("--latest");
    var only = new HashSet<string>(StringComparer.Ordinal);
    for (var i = 2; i < args.Length; i++)
    {
        if (args[i] == "--out") { i++; continue; }
        if (!args[i].StartsWith("--")) only.Add(args[i]);
    }
    if (Path.GetFullPath(scratch).StartsWith(Path.GetFullPath(store), StringComparison.OrdinalIgnoreCase))
    {
        Console.Error.WriteLine("--out must not be inside the store");
        return 2;
    }

    int passed = 0, failed = 0, skipped = 0;
    long rows = 0;
    foreach (var datasetDir in Directory.GetDirectories(store).OrderBy(d => d, StringComparer.Ordinal))
    {
        var dataset = Path.GetFileName(datasetDir);
        if (dataset.StartsWith('_') || (only.Count > 0 && !only.Contains(dataset))) continue;
        var bundles = Directory.GetDirectories(datasetDir)
            .Where(d => File.Exists(Path.Combine(d, BundleWriter.ManifestName)))
            .Select(d => (Dir: d, Written: File.GetLastWriteTimeUtc(Path.Combine(d, BundleWriter.ManifestName))))
            .OrderBy(b => b.Written)
            .ToList();
        if (latest && bundles.Count > 0) bundles = [bundles[^1]];
        foreach (var (dir, _) in bundles)
        {
            var schema = System.Text.Json.JsonDocument.Parse(File.ReadAllText(Path.Combine(dir, BundleWriter.ManifestName)))
                .RootElement.GetProperty("schema_version").GetString();
            if (schema != Tables.SchemaVersion)
            {
                skipped++;
                continue;
            }
            var id = Path.GetFileName(dir);
            var result = RoundTrip.Verify(dir, Path.Combine(scratch, dataset, id));
            rows += result.Tables.Sum(t => t.Rows);
            if (result.Passed)
            {
                passed++;
                Console.WriteLine($"ok    {dataset}/{id}  {result.Tables.Count} tables, {result.Tables.Sum(t => t.Rows):N0} rows");
                continue;
            }
            failed++;
            Console.WriteLine($"FAIL  {dataset}/{id}");
            if (result.StoredId != result.RecomputedId)
                Console.WriteLine($"      bundle id recomputes as {result.RecomputedId}");
            foreach (var t in result.Tables.Where(t => !(t.SchemaMatchesSpec && t.SchemaMatchesOriginal && t.RowsIdentical)))
                Console.WriteLine($"      {t.Table}: spec={t.SchemaMatchesSpec} original={t.SchemaMatchesOriginal} rows={t.RowsIdentical} {t.FirstDifference}");
            foreach (var p in result.IntegrityProblems) Console.WriteLine($"      integrity: {p}");
            foreach (var u in result.UnknownTables) Console.WriteLine($"      unknown table: {u}");
        }
    }
    Console.WriteLine($"\n{passed} passed, {failed} failed, {skipped} skipped (other schema version); {rows:N0} rows compared");
    return failed == 0 ? 0 : 1;
}
