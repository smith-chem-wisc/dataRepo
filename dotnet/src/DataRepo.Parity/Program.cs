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
//       Works on study bundles too (it compares the Parquet files only).
//   study <study.yaml> --store <scratch> [--overwrite]
//       Phase 3: run the C# study writer on one delivery into a scratch store.
//   site <catalog.duckdb> --out <dir> [--title T] [--base-url U] [--data-url U] [--notice T] [--about F]
//        [--purpose T] [--keyword W]...
//       Phase 5: `datarepo site` with every option, from the C# generator.
//   site-compare <expected site dir> <actual site dir>
//       Phase 5: every file of two sites, byte for byte, the generator's own version normalised (SiteParity).
//   build <manifest> [accession ...] --store <store> --out <scratch catalog> [--latest] [--bundle A=id]...
//         [--study layer=id]... [--study-latest layer]... [--overwrite]
//       Phase 3: `datarepo build` through the C# catalog builder, with the Python CLI's selection and notes,
//       so the two catalogs can be compared table by table. <store> is read only.
if (args.Length == 0)
{
    Console.Error.WriteLine("usage: roundtrip | ingest | compare | study | build | site | site-compare (see Program.cs)");
    return 2;
}
// Every verb compares against Python 0.32.0, which wrote schema 0.0.13.
using var python0320 = SchemaContract.Python0320();
return args[0] switch
{
    "roundtrip" => RoundTripVerb(args),
    "ingest" => IngestVerb(args),
    "compare" => CompareVerb(args),
    "study" => StudyVerb(args),
    "build" => BuildVerb(args),
    "site" => DataRepo.Site.SiteCommand.Run(args[1..], Console.Out, Console.Error),
    "site-compare" => SiteCompareVerb(args),
    _ => Usage(),
};

static int Usage()
{
    Console.Error.WriteLine("usage: roundtrip | ingest | compare | study | build | site | site-compare (see Program.cs)");
    return 2;
}

static int StudyVerb(string[] args)
{
    if (args.Length < 2) return Usage();
    var store = Option(args, "--store");
    if (store is null)
    {
        Console.Error.WriteLine("--store <scratch> is required: the parity tool never writes into an operator's store");
        return 2;
    }
    var manifest = DataRepo.Study.StudyWriter.LoadStudyManifest(args[1]);
    var result = DataRepo.Study.StudyWriter.WriteStudyBundle(manifest, store, args.Contains("--overwrite"));
    Console.WriteLine($"{result.Layer}  (study layer, delivery {(manifest.Delivery is null ? "unlabelled" : PyFormat.StrAny(manifest.Delivery))})");
    Console.WriteLine($"  bundle   {result.BundlePath}{(result.Skipped ? " (unchanged, not rewritten)" : "")}");
    Console.WriteLine($"  tables   {string.Join(", ", result.RowCounts.OrderBy(kv => kv.Key, StringComparer.Ordinal).Select(kv => $"{kv.Key} {kv.Value}"))}");
    return 0;
}

static string? Option(string[] args, string name)
{
    var i = Array.IndexOf(args, name);
    return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
}

static List<string> Options(string[] args, string name)
{
    var found = new List<string>();
    for (var i = 0; i + 1 < args.Length; i++)
        if (args[i] == name) found.Add(args[i + 1]);
    return found;
}

static int BuildVerb(string[] args)
{
    if (args.Length < 2) return Usage();
    var valued = new HashSet<string> { "--store", "--out", "--bundle", "--study", "--study-latest" };
    var accessions = new List<string>();
    for (var i = 2; i < args.Length; i++)
    {
        if (valued.Contains(args[i])) { i++; continue; }
        if (!args[i].StartsWith("--", StringComparison.Ordinal)) accessions.Add(args[i]);
    }
    var manifest = Manifest.Load(args[1]);
    if (accessions.Count == 0) accessions = manifest.IngestableEntries().Select(e => e.Accession).ToList();
    var store = Option(args, "--store") ?? manifest.Store;
    var output = Option(args, "--out");
    if (output is null)
    {
        Console.Error.WriteLine("--out <scratch catalog> is required: the parity tool never writes into an operator's tree");
        return 2;
    }
    static Dictionary<string, string> Pins(IEnumerable<string> values) =>
        values.Select(v => v.Split('=', 2)).ToDictionary(p => p[0], p => p[1]);
    var started = DateTime.UtcNow;
    var bundles = DataRepo.Catalog.CatalogBuilder.SelectBundles(manifest, accessions, store, Pins(Options(args, "--bundle")), args.Contains("--latest"));
    var study = DataRepo.Catalog.CatalogBuilder.SelectStudyBundles(store, Pins(Options(args, "--study")), Options(args, "--study-latest"));
    var (artefacts, engineChecks) = DataRepo.Catalog.CatalogBuilder.SelectArtefacts(store, bundles);
    var notes = new Dictionary<string, object?> { ["manifest"] = manifest.Path.Replace('/', Path.DirectorySeparatorChar) };
    if (study.Count > 0) notes["study"] = study.ToDictionary(r => r.Layer, r => (object?)r.BundleId);
    var result = DataRepo.Catalog.CatalogBuilder.BuildCatalog(bundles, output, args.Contains("--overwrite"), manifest.Instance, notes, study, artefacts, engineChecks);
    Console.WriteLine($"catalog  {result.Path}");
    Console.WriteLine($"  id       {result.CatalogId}{(result.Skipped ? " (unchanged)" : "")}");
    foreach (var r in result.Bundles) Console.WriteLine($"  dataset  {r.DatasetId,-12} bundle {r.BundleId}");
    foreach (var r in result.StudyBundles) Console.WriteLine($"  study    {r.Layer,-12} bundle {r.BundleId}  ({r.LayerVersion})");
    foreach (var r in result.Artefacts) Console.WriteLine($"  engine   {r.Engine,-20} artefact {r.ArtefactId}");
    Console.WriteLine($"  indexes  {result.Indexes}");
    Console.WriteLine($"  checks   {result.Checks.Count} run, {result.FailedChecks.Count} failed");
    Console.WriteLine($"  seconds  {(DateTime.UtcNow - started).TotalSeconds:F1}");
    return 0;
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
    // Parity rules unless --current: the point of this verb is comparing with Python 0.32.0.
    var rules = args.Contains("--current") ? IngestRules.Current : IngestRules.Python0320;
    var result = Ingester.Ingest(args[1], args[2], store, Option(args, "--mm-settings"), args.Contains("--overwrite"), rules);
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

static int SiteCompareVerb(string[] args)
{
    if (args.Length < 3) return Usage();
    var differences = DataRepo.Site.SiteParity.Compare(args[1], args[2], out var files, out var bytes);
    foreach (var d in differences) Console.WriteLine($"  DIFF  {d}");
    Console.WriteLine($"  {files} files, {bytes:N0} bytes compared; {differences.Count} difference(s)");
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
            if (schema != SchemaContract.Version)
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
