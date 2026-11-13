using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using DataRepo.Bundle;

namespace DataRepo.Catalog;

/// <summary>One call's place in a session record, as its answer names it.</summary>
public sealed record SessionEntry(string SessionId, long Seq, string EntrySha256);

/// <summary>One session record as a build reads it.</summary>
/// <param name="SessionId">The session's id (16 hex).</param>
/// <param name="Path">The record file.</param>
/// <param name="Entries">Every complete line, in order: the <c>session</c> header, then <c>client</c> and <c>call</c> entries.</param>
/// <param name="ChainOk">Every entry hashes to its <c>entry_sha256</c> and names the one before it.</param>
/// <param name="BrokenAtSeq">The first entry that does not (0 is the header), or null.</param>
/// <param name="Incomplete">The last line was half written (the server stopped mid-write); it is left out, which is
/// not tampering.</param>
public sealed record SessionRef(string SessionId, string Path, IReadOnlyList<IReadOnlyDictionary<string, object?>> Entries,
    bool ChainOk, long? BrokenAtSeq, bool Incomplete);

/// <summary>The MCP server's own record of every call it answers (design/AI_CONTRIBUTIONS.md A18).</summary>
/// <remarks>
/// <para>The user, 2026-10-28: the server keeps every interaction itself, and "this is a public repo. no question is
/// private". So the record never depends on an agent choosing to save anything, and it is public: the server says
/// so to every client when it connects (<see cref="Notice"/>).</para>
/// <para>One file per session, <c>&lt;store&gt;/_sessions/&lt;yyyy-MM-dd&gt;/&lt;session id&gt;.jsonl</c>, beside the
/// bundles and never in one, appended one line per entry and never rewritten. Each line names the hash of the line
/// before it (<c>prev_sha256</c>) and its own (<c>entry_sha256</c>, over the line without it), so an edited, removed
/// or reordered line shows when the record is read. It holds what the server saw: the tool, its arguments, the
/// catalog it ran on, the outcome, and hashes of the answer. The server never sees the prompt or the model's prose,
/// so neither is in it; the client application is recorded as the client reported it (MCP <c>clientInfo</c>), which
/// never names the model.</para>
/// </remarks>
public static class Sessions
{
    public const string Dir = "_sessions";

    /// <summary>What every client is told when it connects (MCP <c>instructions</c>).</summary>
    public const string Notice =
        "This dataRepo server keeps a PUBLIC record of every call made to it: the tool, its arguments (the SQL or search "
        + "text), the catalog it ran on, the outcome, and a hash of the answer. The record is published with the "
        + "catalog, so anyone can see which questions were asked of which data. It does not hold your prompt, the "
        + "model's own text, or who you are. Each answer names its place in the record (session_call).";

    /// <summary>The catalog tables a build creates when the store holds at least one session record.</summary>
    public static readonly IReadOnlyList<string> Tables = ["sessions", "session_calls"];

    public static readonly IReadOnlyDictionary<string, string> TableDocs = new Dictionary<string, string>(StringComparer.Ordinal)
    {
        ["sessions"] = "One row per MCP session the server recorded: when it started, the catalog it served, the client "
            + "application as the client reported it (never the model: no server can see one), how many calls it made, "
            + "and whether its hash chain is intact (`chain_ok`; `broken_at_seq` is the first entry that does not "
            + "verify). Every session is public (`visibility`).",
        ["session_calls"] = "Every call of every recorded session, in order: the tool, its arguments, the catalog it ran on, "
            + "the outcome (ok, error, or invalid arguments), and hashes of the answer (`answer_sha256`) and of its rows "
            + "regardless of order (`rows_sha256`), and the catalog tables a query read (`tables_touched`, a JSON list). A "
            + "contribution's query marked `observed` is one of these.",
    };

    /// <summary>The hash of a SQL answer's rows, whatever their order: the columns, then each row's JSON, sorted.</summary>
    public static string RowsSha256(IEnumerable<string> columns, IEnumerable<string> rowTexts)
    {
        var text = new StringBuilder(PyFormat.Json(columns.Cast<object?>().ToList(), ensureAscii: true)).Append('\n');
        foreach (var row in rowTexts.Order(StringComparer.Ordinal)) text.Append(row).Append('\n');
        return Sha(text.ToString());
    }

    /// <summary>The sha256 of UTF-8 text, as lowercase hex.</summary>
    public static string Sha(string text) => Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(text)));

    /// <summary>The canonical text an entry's hash covers: the entry without <c>entry_sha256</c>, keys sorted, ASCII.</summary>
    internal static string Canonical(IReadOnlyDictionary<string, object?> entry) =>
        PyFormat.Json(entry.Where(kv => kv.Key != "entry_sha256").ToDictionary(kv => kv.Key, kv => kv.Value, StringComparer.Ordinal),
            sortKeys: true, ensureAscii: true);

    /// <summary>Every session record in <paramref name="store"/>, ordered by start then id, each with its chain checked.</summary>
    /// <remarks>A record is read, never refused: a broken chain is reported in <see cref="SessionRef.ChainOk"/>, so one
    /// damaged file cannot stop a catalog build, and nobody can hide a record by damaging it.</remarks>
    public static List<SessionRef> Read(string store)
    {
        var root = System.IO.Path.Combine(store, Dir);
        if (!Directory.Exists(root)) return [];
        var found = new List<SessionRef>();
        foreach (var file in Directory.EnumerateFiles(root, "*.jsonl", SearchOption.AllDirectories))
        {
            string text;
            using (var stream = new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
            using (var reader = new StreamReader(stream, new UTF8Encoding(false)))
                text = reader.ReadToEnd();
            var incomplete = text.Length > 0 && !text.EndsWith('\n');
            var lines = text.Split('\n');
            var complete = incomplete ? lines[..^1] : lines.Where(l => l.Length > 0).ToArray();
            var entries = new List<IReadOnlyDictionary<string, object?>>();
            var ok = true;
            long? broken = null;
            var prev = "";
            foreach (var line in complete.Where(l => l.Length > 0))
            {
                IReadOnlyDictionary<string, object?> entry;
                try
                {
                    entry = Contributions.Parse(line.TrimEnd('\r'));
                }
                catch (ContributionException)
                {
                    ok = false;
                    broken ??= entries.Count;
                    continue;
                }
                var seq = entry.GetValueOrDefault("seq") as long? ?? entries.Count;
                if (ok && (entry.GetValueOrDefault("prev_sha256") as string != prev || entry.GetValueOrDefault("entry_sha256") as string != Sha(Canonical(entry))))
                {
                    ok = false;
                    broken = seq;
                }
                prev = entry.GetValueOrDefault("entry_sha256") as string ?? "";
                entries.Add(entry);
            }
            if (entries.Count == 0) continue;
            var id = entries[0].GetValueOrDefault("session_id") as string ?? System.IO.Path.GetFileNameWithoutExtension(file);
            found.Add(new SessionRef(id, BundleWriter.PathText(file), entries, ok, broken, incomplete));
        }
        return found
            .OrderBy(s => s.Entries[0].GetValueOrDefault("started_utc") as string, StringComparer.Ordinal)
            .ThenBy(s => s.SessionId, StringComparer.Ordinal)
            .ToList();
    }
}

/// <summary>The writing side of one session's record: opened when the server starts serving, one line per call.</summary>
/// <remarks>Thread-safe: the server answers one call at a time already, and the lock keeps the chain whole if that ever
/// changes. A line is written and flushed before the answer goes back, so an answer never names an entry that is not
/// on disk. The file is opened, appended to and closed for each line, so a hosted server carrying thousands of
/// sessions holds no file open between calls.</remarks>
public sealed class SessionLog : IDisposable
{
    private readonly object _lock = new();
    private readonly string _file;
    private readonly Dictionary<long, IReadOnlyDictionary<string, object?>> _calls = [];
    private string _prev;
    private long _seq;
    private bool _client;

    public string SessionId { get; }

    /// <summary>The client application as it reported itself, or null before it did.</summary>
    public (string Name, string? Version)? Client { get; private set; }

    /// <summary>A call this session recorded, as written, or null: what the save tool copies when a call is cited.</summary>
    public IReadOnlyDictionary<string, object?>? Call(long seq)
    {
        lock (_lock) return _calls.GetValueOrDefault(seq);
    }

    public string Path { get; }

    private SessionLog(string sessionId, string file, string prev)
    {
        SessionId = sessionId;
        Path = BundleWriter.PathText(file);
        _file = file;
        _prev = prev;
    }

    /// <summary>Starts a new session record under <paramref name="root"/> (a store's <c>_sessions</c> folder).</summary>
    /// <param name="catalogId">The catalog the server serves.</param>
    public static SessionLog Open(string root, string catalogId)
    {
        var now = DateTime.UtcNow;
        var id = Convert.ToHexStringLower(RandomNumberGenerator.GetBytes(8));
        var folder = System.IO.Path.Combine(root, now.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture));
        Directory.CreateDirectory(folder);
        var path = System.IO.Path.Combine(folder, $"{id}.jsonl");
        new FileStream(path, FileMode.CreateNew, FileAccess.Write).Dispose();  // a fresh id names a fresh file, or this throws
        var log = new SessionLog(id, path, "");
        log.Write(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["type"] = "session",
            ["seq"] = 0L,
            ["session_id"] = id,
            ["started_utc"] = now.ToString("yyyy-MM-dd'T'HH:mm:ss.fff'Z'", CultureInfo.InvariantCulture),
            ["datarepo_version"] = BundleWriter.PackageVersion,
            ["catalog_id"] = catalogId,
            ["visibility"] = "public",
        });
        return log;
    }

    /// <summary>Records the client application once, as the client reported it at <c>initialize</c>.</summary>
    public void SetClient(string? name, string? version)
    {
        lock (_lock)
        {
            if (_client || name is null) return;
            _client = true;
            Client = (name, version);
            Write(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["type"] = "client",
                ["seq"] = _seq,
                ["utc"] = Utc(),
                ["name"] = name,
                ["version"] = version,
                ["source"] = "mcp clientInfo, as reported by the client",
            });
        }
    }

    /// <summary>Records one call and returns its place in the record.</summary>
    /// <param name="outcome"><c>ok</c>, <c>error</c> (the tool answered with an error payload) or <c>invalid</c> (the
    /// call never reached a tool: unknown tool, or arguments that do not fit).</param>
    public SessionEntry Record(string tool, IReadOnlyDictionary<string, object?> arguments, object? catalogId, string outcome,
        string? error, long? rowCount, bool? truncated, string answerSha256, string? rowsSha256, IReadOnlyList<string>? tablesTouched = null)
    {
        lock (_lock)
        {
            var entry = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["type"] = "call",
                ["seq"] = _seq + 1,
                ["utc"] = Utc(),
                ["tool"] = tool,
                ["arguments"] = arguments,
                ["catalog_id"] = catalogId,
                ["outcome"] = outcome,
                ["answer_sha256"] = answerSha256,
            };
            if (error is not null) entry["error"] = error;
            if (rowCount is not null) entry["row_count"] = rowCount;
            if (truncated is not null) entry["truncated"] = truncated;
            if (rowsSha256 is not null) entry["rows_sha256"] = rowsSha256;
            // Which catalog tables the query read (the server's own reading of the statement): how a later user who
            // asks is shown earlier work on the same tables.
            if (tablesTouched is not null) entry["tables_touched"] = tablesTouched.Order(StringComparer.Ordinal).Cast<object?>().ToList();
            var sha = Write(entry);
            _calls[(long)entry["seq"]!] = entry;
            return new SessionEntry(SessionId, (long)entry["seq"]!, sha);
        }
    }

    private static string Utc() => DateTime.UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss.fff'Z'", CultureInfo.InvariantCulture);

    /// <summary>Chains, hashes, writes and flushes one entry.</summary>
    private string Write(Dictionary<string, object?> entry)
    {
        entry["prev_sha256"] = _prev;
        var sha = Sessions.Sha(Sessions.Canonical(entry));
        entry["entry_sha256"] = sha;
        var bytes = Encoding.UTF8.GetBytes(PyFormat.Json(entry, sortKeys: true, ensureAscii: true) + "\n");
        using (var stream = new FileStream(_file, FileMode.Append, FileAccess.Write, FileShare.Read | FileShare.Delete))
        {
            stream.Write(bytes);
            stream.Flush(flushToDisk: true);
        }
        _prev = sha;
        _seq = (long)entry["seq"]!;
        return sha;
    }

    /// <summary>Nothing to release: no file is held between lines. Kept so a session reads as a resource in a <c>using</c>.</summary>
    public void Dispose()
    {
    }
}
