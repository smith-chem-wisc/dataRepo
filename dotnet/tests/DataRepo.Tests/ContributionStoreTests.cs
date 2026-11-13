using System.Text;
using DataRepo.Bundle;
using DataRepo.Catalog;
using DataRepo.Ingest;
using static DataRepo.Tests.ContributionSubmissionTests;

namespace DataRepo.Tests;

/// <summary>S3-S6 of design/AI_CONTRIBUTIONS.md: a contribution is saved beside the bundles, verified against the
/// catalog it cites, loaded by every later catalog build, and never lost, re-pointed or deleted.</summary>
/// <remarks>The user's question (2026-10-28) was whether AI results saved into the catalog are preserved across new
/// releases. <see cref="AReleaseRecordsItsContributionsAndALaterBuildRefusesToLoseOne"/> is the answer in code: a
/// build refuses to drop a contribution an earlier release carried (A13). Engine artefacts are the wrong precedent:
/// <c>SelectArtefacts</c> drops one whose bundle was re-searched (<c>Catalog.cs:1066-1069</c>), which
/// <see cref="AReSearchedDepositIsShownBesideTheContributionNotDroppedFromIt"/> holds the opposite of.</remarks>
public class ContributionStoreTests
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
    private string WorkRoot => Path.Combine(_root, "data", "work_root");
    private string Folder => Path.Combine(_root, "catalogs");

    /// <summary>Catalog A, built before any contribution: what every contribution in these tests cites.</summary>
    private CatalogResult _a = null!;
    private string _bundle = "";

    [SetUp]
    public void MakeScratch()
    {
        _root = Path.Combine(Path.GetTempPath(), "datarepo-contrib-" + Guid.NewGuid().ToString("N"));
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

    private CatalogResult Build(string? release = null, int? keep = null)
    {
        var manifest = Manifest.Load(ManifestPath);
        // The newest bundle of PXD999999: after ReSearch() the store holds two, as a re-searched deposit's store does.
        var bundles = CatalogBuilder.SelectBundles(manifest, ["PXD999999"], Store, latest: true);
        var notes = release is null ? null : new Dictionary<string, object?>(StringComparer.Ordinal) { ["release"] = release };
        return CatalogBuilder.BuildCatalog(bundles, Folder, instance: manifest.Instance, notes: notes, manifest: manifest, keep: keep);
    }

    /// <summary>A new search of PXD999999: a changed database, so ingest writes a second bundle.</summary>
    private string ReSearch()
    {
        var db = Path.Combine(WorkRoot, "db", "test_human.xml");
        var before = BundleWriter.Sha256File(db);
        File.AppendAllText(db, "<!-- searched again -->\n", new UTF8Encoding(false));
        var provenance = Path.Combine(WorkRoot, "run_test", "PXD999999", "04_search", "provenance.json");
        var recorded = File.ReadAllText(provenance, Encoding.UTF8);
        File.WriteAllBytes(provenance, Encoding.UTF8.GetBytes(recorded.Replace(before, BundleWriter.Sha256File(db), StringComparison.Ordinal)));
        var bundle = BundleRef.Load(Ingester.Ingest(ManifestPath, "PXD999999", Store, rules: IngestRules.Current).BundlePath).BundleId;
        Assert.That(bundle, Is.Not.EqualTo(_bundle), "the fixture's re-search must write a new bundle");
        return bundle;
    }

    private Dictionary<string, object?> OnA() => Submission(_a.CatalogId, "PXD999999", _bundle);

    private ContributionSaved Save(Dictionary<string, object?> submission) => Contributions.Save(Store, Folder, submission);

    private static List<object?[]> Rows(string catalog, string sql) => CatalogBuilder.RunQuery(catalog, sql).Rows;

    private Dictionary<string, string> BundleFileHashes() =>
        Directory.EnumerateFiles(Path.Combine(Store, "PXD999999"), "*", SearchOption.AllDirectories)
            .ToDictionary(f => f, BundleWriter.Sha256File, StringComparer.Ordinal);

    // --- S3: the save ----------------------------------------------------------------------------------

    [Test]
    public void ASaveWritesOneRecordBesideTheBundlesAndNoEngineSeesIt()
    {
        var saved = Save(OnA());
        Assert.Multiple(() =>
        {
            Assert.That(saved.AlreadySaved, Is.False);
            Assert.That(saved.Id, Is.EqualTo(saved.Sha256[..16]));
            Assert.That(File.Exists(Path.Combine(Store, Contributions.Dir, saved.Id, Contributions.RecordFile)), Is.True);
            Assert.That(DataRepo.Catalog.Runner.DiscoverArtefacts(Store), Is.Empty, "a contribution is not an engine artefact");
            Assert.That(Directory.EnumerateDirectories(Path.Combine(Store, Contributions.Dir)).Select(Path.GetFileName),
                Is.EqualTo(new[] { saved.Id }), "no staging directory is left behind");
        });
        var record = Contributions.Discover(Store).Single();
        Assert.That(record.Record["contribution_sha256"], Is.EqualTo(saved.Sha256));
        Assert.That(record.Record["submitted_utc"], Is.Not.Null);
        Assert.That(record.Record["datarepo_version"], Is.EqualTo(BundleWriter.PackageVersion));
    }

    [Test]
    public void TheSameContributionTwiceIsAlreadySavedAndNotRewritten()
    {
        var first = Save(OnA());
        var file = Path.Combine(Store, Contributions.Dir, first.Id, Contributions.RecordFile);
        var bytes = File.ReadAllBytes(file);
        var second = Save(OnA());
        Assert.That(second.AlreadySaved, Is.True);
        Assert.That(second.Sha256, Is.EqualTo(first.Sha256));
        Assert.That(File.ReadAllBytes(file), Is.EqualTo(bytes), "the record is not rewritten, so its time stays the first save's");
    }

    [Test]
    public void NoBundleFileChangesWhenAContributionIsSaved()
    {
        var before = BundleFileHashes();
        Save(OnA());
        Assert.That(BundleFileHashes(), Is.EqualTo(before));
    }

    [Test]
    public void AnUnknownCatalogIsRefusedBeforeAnythingIsWritten()
    {
        Assert.That(() => Save(Submission("0000000000000000", "PXD999999", _bundle)),
            Throws.TypeOf<ContributionException>().With.Message.Contains("0000000000000000"));
        Assert.That(Directory.Exists(Path.Combine(Store, Contributions.Dir)), Is.False);
    }

    [Test]
    public void ABundleTheCitedCatalogDoesNotHoldIsRefused()
    {
        Assert.That(() => Save(Submission(_a.CatalogId, "PXD999999", "aaaaaaaaaaaaaaaa")),
            Throws.TypeOf<ContributionException>().With.Message.Contains("aaaaaaaaaaaaaaaa").And.Message.Contains(_a.CatalogId));
        Assert.That(() => Save(Submission(_a.CatalogId, "PXD000001", _bundle)),
            Throws.TypeOf<ContributionException>().With.Message.Contains("PXD000001"));
        Assert.That(Directory.Exists(Path.Combine(Store, Contributions.Dir)), Is.False);
    }

    [Test]
    public void ACatalogIsKnownByWhatItHoldsNotByItsFileName()
    {
        File.Copy(Path.Combine(Folder, CatalogPointer.FileOf(_a.CatalogId)), Path.Combine(Folder, CatalogPointer.FileOf("1111111111111111")));
        Assert.That(() => Save(Submission("1111111111111111", "PXD999999", _bundle)),
            Throws.TypeOf<ContributionException>().With.Message.Contains(_a.CatalogId));
    }

    [Test]
    public void OnlyTheServerThatRanAQueryMayMarkItObserved()
    {
        var submission = OnA();
        ((Dictionary<string, object?>)submission["method"]!)["queries"] = new List<object?>
        {
            Map(("sql", "SELECT 1"), ("observed", true), ("catalog_id", _a.CatalogId), ("result_sha256", new string('a', 64))),
        };
        Assert.That(() => Save(submission), Throws.TypeOf<ContributionException>().With.Message.Contains("observed"));
    }

    [Test]
    public void BuildingOnAContributionTheStoreDoesNotHoldIsRefused()
    {
        var submission = OnA();
        ((Dictionary<string, object?>)submission["basis"]!)["contributions"] = new List<object?> { "abababababababab" };
        Assert.That(() => Save(submission), Throws.TypeOf<ContributionException>().With.Message.Contains("abababababababab"));
    }

    [Test]
    public void ARecordChangedAfterItWasSavedStopsTheBuild()
    {
        var saved = Save(OnA());
        var file = Path.Combine(Store, Contributions.Dir, saved.Id, Contributions.RecordFile);
        File.WriteAllText(file, File.ReadAllText(file).Replace("Phosphosites", "Glycosites", StringComparison.Ordinal));
        Assert.That(() => Build(), Throws.TypeOf<ContributionException>().With.Message.Contains(saved.Id).And.Message.Contains("changed"));
    }

    // --- S4: the catalog build -------------------------------------------------------------------------

    [Test]
    public void ACatalogWithNoContributionsHasNoContributionTables()
    {
        Assert.That(Rows(Folder, "SELECT count(*) FROM information_schema.tables WHERE table_name LIKE 'contribution%'")[0][0], Is.EqualTo(0L));
    }

    [Test]
    public void ACatalogLoadsEveryContributionWithWhoMadeItHowAndFromWhichData()
    {
        var saved = Save(OnA());
        var b = Build();
        var row = Rows(Folder,
            "SELECT contribution_id, contribution_sha256, kind, model_provider, model_id, model_stated_by, submitted_by, "
            + "licence, reproducibility, basis_catalog_id, status FROM contributions")[0];
        Assert.That(row, Is.EqualTo(new object?[]
        {
            saved.Id, saved.Sha256, "site_list", "anthropic", "claude-opus-5-5", "client", "A. Tester",
            "CC-BY-4.0", "query", _a.CatalogId, "active",
        }));
        Assert.That(Rows(Folder, "SELECT subject_id, value, rank FROM contribution_items ORDER BY ordinal"),
            Is.EqualTo(new List<object?[]> { new object?[] { "P12345:S10", 0.5, 1L }, new object?[] { "P12345:T22", 0.25, 2L } }));
        Assert.That(Rows(Folder, "SELECT sql, observed FROM contribution_queries"), Is.EqualTo(new List<object?[]> { new object?[] { "SELECT 1", false } }));
        Assert.That(Rows(Folder, "SELECT dataset_id, bundle_id, in_this_catalog FROM contribution_basis"),
            Is.EqualTo(new List<object?[]> { new object?[] { "PXD999999", _bundle, true } }));
        Assert.That(Rows(Folder, "SELECT table_name FROM catalog_tables WHERE kind = 'contribution' ORDER BY table_name").Select(r => r[0]),
            Is.EqualTo(Contributions.Tables.Order(StringComparer.Ordinal)));
        Assert.That(b.Skipped, Is.False);
    }

    [Test]
    public void AContributionMovesTheCatalogIdButNotTheReleaseId()
    {
        Save(OnA());
        var b = Build();
        Assert.That(b.CatalogId, Is.Not.EqualTo(_a.CatalogId), "a catalog that serves a contribution answers differently");
        Assert.That(b.ReleaseId, Is.EqualTo(_a.ReleaseId), "the measured data did not change");
    }

    [Test]
    public void EveryContributionTableIsDocumented()
    {
        Assert.That(Contributions.TableDocs.Keys.Order(StringComparer.Ordinal), Is.EqualTo(Contributions.Tables.Order(StringComparer.Ordinal)));
    }

    // --- S5: carried forward ---------------------------------------------------------------------------

    [Test]
    public void AContributionIsCarriedIntoEveryLaterBuildUnchanged()
    {
        var saved = Save(OnA());
        var b = Build();
        ReSearch();
        var c = Build();
        Assert.That(c.CatalogId, Is.Not.EqualTo(b.CatalogId));
        foreach (var catalog in new[] { Path.Combine(Folder, CatalogPointer.FileOf(b.CatalogId)), Path.Combine(Folder, CatalogPointer.FileOf(c.CatalogId)) })
            Assert.That(Rows(catalog, "SELECT contribution_id, contribution_sha256, basis_catalog_id FROM contributions"),
                Is.EqualTo(new List<object?[]> { new object?[] { saved.Id, saved.Sha256, _a.CatalogId } }), catalog);
    }

    [Test]
    public void AReSearchedDepositIsShownBesideTheContributionNotDroppedFromIt()
    {
        Save(OnA());
        var now = ReSearch();
        Build();
        Assert.That(Rows(Folder, "SELECT dataset_id, bundle_id, in_this_catalog, catalog_bundle_id FROM contribution_basis"),
            Is.EqualTo(new List<object?[]> { new object?[] { "PXD999999", _bundle, false, now } }));
    }

    [Test]
    public void AReleaseRecordsItsContributionsAndALaterBuildRefusesToLoseOne()
    {
        var saved = Save(OnA());
        Build(release: "v1");
        var notes = (string)Rows(Folder, "SELECT notes FROM catalog_meta")[0][0]!;
        Assert.That(notes, Does.Contain(saved.Id));
        Directory.Delete(Path.Combine(Store, Contributions.Dir, saved.Id), true);
        Assert.That(() => Build(), Throws.TypeOf<CatalogException>().With.Message.Contains(saved.Id).And.Message.Contains("v1"));
    }

    [Test]
    public void KeepNeverPrunesTheCatalogAContributionCites()
    {
        Save(OnA());
        var b = Build(keep: 1);
        var second = OnA();
        second["title"] = "A second result";
        Save(second);
        Build(keep: 1);
        Assert.That(File.Exists(Path.Combine(Folder, CatalogPointer.FileOf(_a.CatalogId))), Is.True, "A is cited, so it is kept");
        Assert.That(File.Exists(Path.Combine(Folder, CatalogPointer.FileOf(b.CatalogId))), Is.False, "B is cited by nothing and released for nothing");
    }

    // --- S6: retraction and supersession ---------------------------------------------------------------

    private Dictionary<string, object?> Retraction(string target, string reason = "the query read the wrong table")
    {
        var retraction = OnA();
        retraction["kind"] = "retraction";
        retraction["target"] = target;
        retraction["reason"] = reason;
        retraction.Remove("items");
        return retraction;
    }

    [Test]
    public void RetractingDeletesNothingAndMarksTheTargetRetracted()
    {
        var saved = Save(OnA());
        var file = Path.Combine(Store, Contributions.Dir, saved.Id, Contributions.RecordFile);
        var bytes = File.ReadAllBytes(file);
        var retraction = Save(Retraction(saved.Id));
        Assert.That(File.ReadAllBytes(file), Is.EqualTo(bytes));
        Build();
        Assert.That(Rows(Folder, $"SELECT status, retracted_by FROM contributions WHERE contribution_id = '{saved.Id}'")[0],
            Is.EqualTo(new object?[] { "retracted", retraction.Id }));
        Assert.That(Rows(Folder, "SELECT count(*) FROM contributions_current")[0][0], Is.EqualTo(0L),
            "neither the retracted result nor the retraction itself is a current result");
    }

    [Test]
    public void SupersedingMarksTheOldOneSuperseded()
    {
        var old = Save(OnA());
        var replacement = OnA();
        replacement["title"] = "Corrected";
        replacement["supersedes"] = old.Id;
        var @new = Save(replacement);
        Build();
        Assert.That(Rows(Folder, "SELECT contribution_id, status, superseded_by FROM contributions ORDER BY status"),
            Is.EqualTo(new List<object?[]> { new object?[] { @new.Id, "active", null }, new object?[] { old.Id, "superseded", @new.Id } }));
        Assert.That(Rows(Folder, "SELECT contribution_id FROM contributions_current")[0][0], Is.EqualTo(@new.Id));
    }

    [Test]
    public void RetractingAnUnknownContributionIsRefused()
    {
        Assert.That(() => Save(Retraction("abababababababab")), Throws.TypeOf<ContributionException>().With.Message.Contains("abababababababab"));
    }

    [Test]
    public void AContributionIsRetractedOnce()
    {
        var saved = Save(OnA());
        var first = Save(Retraction(saved.Id));
        Assert.That(Save(Retraction(saved.Id)).AlreadySaved, Is.True, "the same retraction twice is the same retraction");
        Assert.That(() => Save(Retraction(saved.Id, "another reason")),
            Throws.TypeOf<ContributionException>().With.Message.Contains(first.Id));
    }
}
