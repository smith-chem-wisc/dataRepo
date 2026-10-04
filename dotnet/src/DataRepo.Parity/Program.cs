using DataRepo.Bundle;

// Phase 1 parity (design/CSHARP_PORT.md): read stored bundles written by the Python ingester and
// rewrite every table through the C# writer; report anything that is not identical.
//
//   dotnet run --project dotnet/src/DataRepo.Parity -- roundtrip <store> --out <scratch> [--latest] [PXD ...]
//
// <store> is read only. Bundles on another schema version are skipped and counted, not failed: the C#
// writer speaks the current schema only, as the Python one does.
if (args.Length < 2 || args[0] != "roundtrip")
{
    Console.Error.WriteLine("usage: roundtrip <store> --out <scratch> [--latest] [accession ...]");
    return 2;
}
var store = args[1];
var outIndex = Array.IndexOf(args, "--out");
if (outIndex < 0 || outIndex + 1 >= args.Length)
{
    Console.Error.WriteLine("--out <scratch> is required; nothing is ever written under the store");
    return 2;
}
var scratch = args[outIndex + 1];
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
