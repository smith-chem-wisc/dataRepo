$S = 'C:\Users\trish\AppData\Local\Temp\claude\af6e45eaa41babf7\cbfe7974-7464-465f-a2d2-2b1c8aa53a64\scratchpad\split'
$D = 'F:\aging_batch\datarepo-1.4.3\datarepo\datarepo.exe'
$sw = [Diagnostics.Stopwatch]::StartNew()
"== before: control and bare deposit"
& $D ingest "$S\before.yaml" PXD017944 PXD027754
"exit=$LASTEXITCODE  t=$([int]$sw.Elapsed.TotalSeconds)s"
"== after: the two split keys"
& $D ingest "$S\after.yaml" PXD027754-rat PXD027754-mouse
"exit=$LASTEXITCODE  t=$([int]$sw.Elapsed.TotalSeconds)s"
"== after: the retired bare entry must be refused"
& $D ingest "$S\after.yaml" PXD027754 --overwrite
"exit=$LASTEXITCODE"
"== store"
Get-ChildItem "$S\store" | ForEach-Object { "$($_.Name): " + ((Get-ChildItem $_.FullName -Directory | Select-Object -ExpandProperty Name) -join ', ') }
