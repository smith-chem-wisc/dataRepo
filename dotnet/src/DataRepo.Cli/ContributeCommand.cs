using System.Text;
using DataRepo.Bundle;
using DataRepo.Catalog;

namespace DataRepo.Cli;

/// <summary><c>datarepo contribute save|list</c>: save a result computed from a catalog back into the store, beside
/// the bundles, and list what is saved (design/AI_CONTRIBUTIONS.md). The operator's step: the next catalog build
/// loads every saved contribution, and every later release carries it.</summary>
internal static class ContributeCommand
{
    internal const string Summary = "save a result computed from a catalog back into the store (an AI model's or a person's), or list them";

    private const string Usage = "usage: datarepo contribute [-h] --store STORE [--catalog CATALOG] [--json] {save,list} [file]";

    public static int Run(string[] argv)
    {
        var a = new Args.Spec("datarepo contribute", Cli.Summaries["contribute"])
            .Positional("action", "save: save the contribution in FILE; list: list the store's contributions")
            .Positional("file", "the contribution, as JSON (save only)", "?")
            .Option("--store", Args.Kind.Value, "the instance's bundle store", required: true)
            .Option("--catalog", Args.Kind.Value, "the catalog folder (or one catalog file) that holds the catalog the contribution cites (save only)")
            .Option("--json", Args.Kind.Flag, "print one JSON object on stdout")
            .Parse(argv);
        var store = a.Value("--store")!;
        var json = a.Flag("--json");
        switch (a.Positional("action"))
        {
            case "save":
            {
                var file = a.Positionals("file").FirstOrDefault()
                    ?? throw new Args.UsageException(Usage, "save needs the contribution's file");
                var catalog = a.Value("--catalog") ?? throw new Args.UsageException(Usage, "save needs --catalog: where the cited catalog is");
                var saved = Contributions.Save(store, catalog, Contributions.Parse(File.ReadAllText(file, Encoding.UTF8)));
                if (json)
                    Console.WriteLine(PyFormat.Json(new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["ok"] = true,
                        ["contribution_id"] = saved.Id,
                        ["contribution_sha256"] = saved.Sha256,
                        ["path"] = saved.Path,
                        ["already_saved"] = saved.AlreadySaved,
                    }));
                else
                    Console.WriteLine(saved.AlreadySaved
                        ? $"done     contribution {saved.Id} is already saved; nothing written  {saved.Path}"
                        : $"saved    contribution {saved.Id}  {saved.Path}\n  the next catalog build loads it, and every later release carries it");
                return 0;
            }
            case "list":
            {
                var all = Contributions.Discover(store);
                if (json)
                {
                    Console.WriteLine(PyFormat.Json(new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["ok"] = true,
                        ["contributions"] = all.Select(c => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["contribution_id"] = c.Id,
                            ["kind"] = c.Kind,
                            ["title"] = c.Record.GetValueOrDefault("title"),
                            ["model"] = c.Record.GetValueOrDefault("model"),
                            ["basis_catalog_id"] = c.BasisCatalogId,
                            ["submitted_utc"] = c.Record.GetValueOrDefault("submitted_utc"),
                        }).ToList(),
                    }));
                    return 0;
                }
                if (all.Count == 0) Console.WriteLine($"no contributions under {BundleWriter.PathText(Path.Combine(store, Contributions.Dir))}");
                foreach (var c in all)
                {
                    var model = c.Record.GetValueOrDefault("model") as IReadOnlyDictionary<string, object?>;
                    Console.WriteLine($"{c.Id}  {c.Kind,-14} {model?.GetValueOrDefault("id")} (stated by {model?.GetValueOrDefault("stated_by")})  "
                        + $"on catalog {c.BasisCatalogId}  {c.Record.GetValueOrDefault("title")}");
                }
                return 0;
            }
            default:
                throw new Args.UsageException(Usage, $"argument action: invalid choice: '{a.Positional("action")}' (choose from 'save', 'list')");
        }
    }
}
