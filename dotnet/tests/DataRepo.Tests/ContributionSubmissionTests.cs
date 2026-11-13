using DataRepo.Catalog;

namespace DataRepo.Tests;

/// <summary>S1 and S2 of design/AI_CONTRIBUTIONS.md: what a contribution must say before it is saved, and its id.</summary>
/// <remarks>A contribution is a result an AI model (or a person) computed from a catalog and saves back into the store
/// (the SCP renewal's Task 3.3). These tests need no store: they hold the submission's shape (A4-A8, A12, A16, A17)
/// and the id rule (A2): a sha256 over exactly what the submitter stated, never the time, the install or the schema
/// version, so a contribution keeps its id through every later release.</remarks>
public class ContributionSubmissionTests
{
    internal const string CatalogId = "0123456789abcdef";
    internal const string BundleId = "fedcba9876543210";

    /// <summary>A minimal valid site list, as plain values (what JSON parses to).</summary>
    internal static Dictionary<string, object?> Submission(string catalogId = CatalogId, string datasetId = "PXD999999",
        string bundleId = BundleId) => new(StringComparer.Ordinal)
    {
        ["contribution_version"] = "1",
        ["kind"] = "site_list",
        ["title"] = "Phosphosites that rise with age in mouse liver",
        ["summary"] = "Sites whose occupancy rises in old animals.",
        ["model"] = Map(("provider", "anthropic"), ("id", "claude-opus-5-5"), ("stated_by", "client")),
        ["submitted_by"] = Map(("name", "A. Tester")),
        ["licence"] = "CC-BY-4.0",
        ["reproducibility"] = "query",
        ["basis"] = Map(("catalog_id", catalogId),
            ("bundles", new List<object?> { Map(("dataset_id", datasetId), ("bundle_id", bundleId)) })),
        ["method"] = Map(("description", "One query over ptm_sites."),
            ("queries", new List<object?> { Map(("sql", "SELECT 1"), ("observed", false)) })),
        ["items"] = new List<object?>
        {
            Map(("subject_type", "ptm_site"), ("subject_id", "P12345:S10"), ("value", 0.5), ("rank", 1L)),
            Map(("subject_type", "ptm_site"), ("subject_id", "P12345:T22"), ("value", 0.25), ("rank", 2L)),
        },
    };

    internal static Dictionary<string, object?> Map(params (string Key, object? Value)[] pairs)
    {
        var map = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var (key, value) in pairs) map[key] = value;
        return map;
    }

    private static Dictionary<string, object?> Sub(Dictionary<string, object?> parent, string key) =>
        (Dictionary<string, object?>)parent[key]!;

    [Test]
    public void AContributionWithEveryRequiredFieldValidates()
    {
        var normalised = Contributions.Validate(Submission());
        Assert.That(normalised["kind"], Is.EqualTo("site_list"));
        Assert.That(((List<object?>)normalised["items"]!).Count, Is.EqualTo(2));
    }

    [TestCase("contribution_version")]
    [TestCase("kind")]
    [TestCase("title")]
    [TestCase("model")]
    [TestCase("submitted_by")]
    [TestCase("licence")]
    [TestCase("reproducibility")]
    [TestCase("basis")]
    [TestCase("method")]
    public void EachMissingRequiredFieldIsNamed(string field)
    {
        var submission = Submission();
        submission.Remove(field);
        Assert.That(() => Contributions.Validate(submission),
            Throws.TypeOf<ContributionException>().With.Message.Contains(field));
    }

    [Test]
    public void AnUnknownFieldIsRefusedNotIgnored()
    {
        var submission = Submission();
        submission["confidence"] = "high";
        Assert.That(() => Contributions.Validate(submission),
            Throws.TypeOf<ContributionException>().With.Message.Contains("confidence"));
        var nested = Submission();
        Sub(nested, "model")["temperature"] = 0.2;
        Assert.That(() => Contributions.Validate(nested),
            Throws.TypeOf<ContributionException>().With.Message.Contains("model.temperature"), "unknown keys are refused at every level");
    }

    [Test]
    public void TheServerOwnsTheIdAndTheTimeNotTheSubmitter()
    {
        foreach (var key in new[] { "contribution_sha256", "contribution_id", "submitted_utc" })
        {
            var submission = Submission();
            submission[key] = "x";
            Assert.That(() => Contributions.Validate(submission),
                Throws.TypeOf<ContributionException>().With.Message.Contains(key), key);
        }
    }

    [Test]
    public void AKindOutsideTheListIsRefusedAndTheListIsShown()
    {
        var submission = Submission();
        submission["kind"] = "vibes";
        Assert.That(() => Contributions.Validate(submission),
            Throws.TypeOf<ContributionException>().With.Message.Contains("site_list").And.Message.Contains("relation_graph"));
    }

    [TestCase("ABC")]
    [TestCase("0123456789ABCDEF")]
    [TestCase("0123456789abcdef0")]
    public void ACatalogIdThatIsNotSixteenLowercaseHexIsRefused(string id)
    {
        Assert.That(() => Contributions.Validate(Submission(catalogId: id)),
            Throws.TypeOf<ContributionException>().With.Message.Contains("basis.catalog_id"));
    }

    [Test]
    public void ABasisWithNoBundleIsRefused()
    {
        var submission = Submission();
        Sub(submission, "basis")["bundles"] = new List<object?>();
        Assert.That(() => Contributions.Validate(submission),
            Throws.TypeOf<ContributionException>().With.Message.Contains("basis.bundles"));
    }

    [Test]
    public void TheLicenceIsOneTheCatalogCanServe()
    {
        var submission = Submission();
        submission["licence"] = "free";
        Assert.That(() => Contributions.Validate(submission),
            Throws.TypeOf<ContributionException>().With.Message.Contains("CC-BY-4.0"));
        submission["licence"] = "CC0-1.0";
        Assert.That(() => Contributions.Validate(submission), Throws.Nothing);
    }

    [Test]
    public void AModelAliasIsRefusedBecauseItNamesNoFixedModel()
    {
        var submission = Submission();
        Sub(submission, "model")["id"] = "claude-latest";
        Assert.That(() => Contributions.Validate(submission),
            Throws.TypeOf<ContributionException>().With.Message.Contains("model.id"));
    }

    [Test]
    public void TheModelSaysWhoStatedIt()
    {
        var submission = Submission();
        Sub(submission, "model")["stated_by"] = "server";
        Assert.That(() => Contributions.Validate(submission),
            Throws.TypeOf<ContributionException>().With.Message.Contains("client").And.Message.Contains("operator"));
    }

    [Test]
    public void ASiteListNeedsItemsAndAGraphNeedsEdges()
    {
        var list = Submission();
        list.Remove("items");
        Assert.That(() => Contributions.Validate(list), Throws.TypeOf<ContributionException>().With.Message.Contains("items"));
        var graph = Submission();
        graph["kind"] = "relation_graph";
        Assert.That(() => Contributions.Validate(graph), Throws.TypeOf<ContributionException>().With.Message.Contains("edges"));
        graph["edges"] = new List<object?>
        {
            Map(("source_type", "cell_type"), ("source_id", "hepatocyte"), ("target_type", "cell_type"), ("target_id", "Kupffer cell"), ("weight", 0.8)),
        };
        Assert.That(() => Contributions.Validate(graph), Throws.Nothing);
    }

    [Test]
    public void ARetractionNamesItsTargetAndReasonAndCarriesNoResult()
    {
        var retraction = Submission();
        retraction["kind"] = "retraction";
        Assert.That(() => Contributions.Validate(retraction), Throws.TypeOf<ContributionException>().With.Message.Contains("target"));
        retraction["target"] = "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"[..16];
        retraction["reason"] = "the query read the wrong table";
        Assert.That(() => Contributions.Validate(retraction), Throws.TypeOf<ContributionException>().With.Message.Contains("items"));
        retraction.Remove("items");
        Assert.That(() => Contributions.Validate(retraction), Throws.Nothing);
    }

    [Test]
    public void CrlfAndLfReadAlike()
    {
        var lf = Submission();
        Sub(lf, "method")["description"] = "line one\nline two";
        var crlf = Submission();
        Sub(crlf, "method")["description"] = "line one\r\nline two";
        Assert.That(Contributions.Sha256Of(Contributions.Validate(crlf)), Is.EqualTo(Contributions.Sha256Of(Contributions.Validate(lf))));
    }

    [Test]
    public void TheIdIsTheSameWhateverTheKeyOrBundleOrder()
    {
        var a = Submission();
        Sub(a, "basis")["bundles"] = new List<object?>
        {
            Map(("dataset_id", "PXD000001"), ("bundle_id", BundleId)),
            Map(("dataset_id", "PXD999999"), ("bundle_id", BundleId)),
        };
        var b = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var key in a.Keys.Reverse()) b[key] = a[key];
        b["basis"] = Map(
            ("bundles", new List<object?>
            {
                Map(("bundle_id", BundleId), ("dataset_id", "PXD999999")),
                Map(("bundle_id", BundleId), ("dataset_id", "PXD000001")),
            }),
            ("catalog_id", CatalogId));
        Assert.That(Contributions.Sha256Of(Contributions.Validate(b)), Is.EqualTo(Contributions.Sha256Of(Contributions.Validate(a))));
    }

    [Test]
    public void TheIdIsAFullSha256()
    {
        Assert.That(Contributions.Sha256Of(Contributions.Validate(Submission())), Does.Match("^[0-9a-f]{64}$"));
    }

    /// <summary>Every stated field moves the id: two contributions that differ in anything a reader could see are two.</summary>
    [TestCase("title")]
    [TestCase("model.id")]
    [TestCase("submitted_by.name")]
    [TestCase("basis.catalog_id")]
    [TestCase("basis.bundles")]
    [TestCase("method.queries")]
    [TestCase("items")]
    [TestCase("licence")]
    [TestCase("reproducibility")]
    public void EveryStatedFieldMovesTheId(string field)
    {
        var before = Contributions.Sha256Of(Contributions.Validate(Submission()));
        var changed = Submission();
        switch (field)
        {
            case "title": changed["title"] = "Another title"; break;
            case "model.id": Sub(changed, "model")["id"] = "claude-sonnet-5-5"; break;
            case "submitted_by.name": Sub(changed, "submitted_by")["name"] = "B. Tester"; break;
            case "basis.catalog_id": Sub(changed, "basis")["catalog_id"] = "1123456789abcdef"; break;
            case "basis.bundles": Sub(changed, "basis")["bundles"] = new List<object?> { Map(("dataset_id", "PXD999999"), ("bundle_id", "aedcba9876543210")) }; break;
            case "method.queries": Sub(changed, "method")["queries"] = new List<object?> { Map(("sql", "SELECT 2"), ("observed", false)) }; break;
            case "items": ((List<object?>)changed["items"]!).RemoveAt(1); break;
            case "licence": changed["licence"] = "CC0-1.0"; break;
            case "reproducibility": changed["reproducibility"] = "judgement"; break;
        }
        Assert.That(Contributions.Sha256Of(Contributions.Validate(changed)), Is.Not.EqualTo(before), field);
    }

    [Test]
    public void TheIdHashesNoSchemaOrRunnerVersion()
    {
        var normalised = Contributions.Validate(Submission());
        var canonical = Contributions.Canonical(normalised);
        Assert.That(canonical, Does.Not.Contain("schema").And.Not.Contain("runner"));
        Assert.That(Contributions.Sha256Of(normalised), Is.EqualTo(Convert.ToHexStringLower(
            System.Security.Cryptography.SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(canonical)))));
    }

    [Test]
    public void JsonTextParsesToTheSameContribution()
    {
        var json = """
        {"contribution_version": "1", "kind": "finding", "title": "t", "summary": "s",
         "model": {"provider": "anthropic", "id": "claude-opus-5-5", "stated_by": "client"},
         "submitted_by": {"name": "A. Tester", "orcid": "0000-0002-1825-0097"},
         "licence": "CC-BY-4.0", "reproducibility": "judgement",
         "basis": {"catalog_id": "0123456789abcdef", "bundles": [{"dataset_id": "PXD999999", "bundle_id": "fedcba9876543210"}]},
         "method": {"description": "d", "queries": []}}
        """;
        var parsed = Contributions.Parse(json);
        Assert.That(() => Contributions.Validate(parsed), Throws.Nothing);
        Assert.That(() => Contributions.Parse("{\"kind\": 1, \"kind\": 2}"),
            Throws.TypeOf<ContributionException>().With.Message.Contains("kind"), "a duplicated key is refused, never last-one-wins");
    }

    [Test]
    public void AnOrcidMustLookLikeOne()
    {
        var submission = Submission();
        Sub(submission, "submitted_by")["orcid"] = "12345";
        Assert.That(() => Contributions.Validate(submission),
            Throws.TypeOf<ContributionException>().With.Message.Contains("submitted_by.orcid"));
    }
}
