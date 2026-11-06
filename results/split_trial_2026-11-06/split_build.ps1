$S = 'C:\Users\trish\AppData\Local\Temp\claude\af6e45eaa41babf7\cbfe7974-7464-465f-a2d2-2b1c8aa53a64\scratchpad\split'
$D = 'F:\aging_batch\datarepo-1.4.3\datarepo\datarepo.exe'
"== build after.yaml (bare retired, two keys, control)"
& $D build "$S\after.yaml" --store "$S\store" --out "$S\after.duckdb" --overwrite
"exit=$LASTEXITCODE"
"== build naming the retired bare entry"
& $D build "$S\after.yaml" PXD027754 PXD027754-rat --store "$S\store" --out "$S\named.duckdb" --overwrite
"exit=$LASTEXITCODE"
"== both.yaml: bare still include beside its halves"
$text = Get-Content "$S\after.yaml" -Raw
$text = $text -replace 'status: superseded', 'status: include'
[IO.File]::WriteAllText("$S\both.yaml", $text, (New-Object Text.UTF8Encoding $false))
& $D build "$S\both.yaml" --store "$S\store" --out "$S\both.duckdb" --overwrite
"exit=$LASTEXITCODE"
"== site from after.duckdb"
& $D site --help
& $D site "$S\after.duckdb" --out "$S\site"
"exit=$LASTEXITCODE"
Get-ChildItem "$S\site\datasets" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
