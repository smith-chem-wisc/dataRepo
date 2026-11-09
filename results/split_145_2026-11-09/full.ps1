param([string]$Exe)
# The whole of aging's store, rebuilt by 1.4.5 into a scratch folder with the very bundles aging serves. Reads the store in
# place; writes only under the scratchpad. The exe is a copy named dr145.exe: aging's publish refuses to start while any
# process whose command line names "datarepo" runs a build, and this one touches nothing of theirs.
$S = 'C:\Users\trish\AppData\Local\Temp\claude\af6e45eaa41babf7\ddef7e36-d8aa-47c4-8b48-ed5763fee5c3\scratchpad\split145'
$served = Get-Content "$S\served.json" -Raw | ConvertFrom-Json
$keys = @(); $pins = @()
foreach ($b in $served.bundles) { $keys += $b[0]; $pins += @('--bundle', "$($b[0])=$($b[1])") }
"== $($keys.Count) bundles of $($served.catalog) (built by $($served.builder))"
foreach ($pass in 1, 2) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $Exe build 'F:/aging_data/batch/manifest.yaml' @keys @pins --store 'F:/aging_data/repo/store' --out "$S\full" 2>&1 | ForEach-Object { "$_" }
    "== pass $pass exit=$LASTEXITCODE  t=$([int]$sw.Elapsed.TotalSeconds)s"
}
