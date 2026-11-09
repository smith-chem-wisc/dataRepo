param([string]$Exe)
# The 1.4.5 split trial: ingest PXD027754 as two stand-in parts with this branch, serve them beside a control, and refuse
# the whole deposit beside its parts. Reads aging's search folders and served bundles in place; writes nothing under F:.
$S = 'C:\Users\trish\AppData\Local\Temp\claude\af6e45eaa41babf7\ddef7e36-d8aa-47c4-8b48-ed5763fee5c3\scratchpad\split145'
$sw = [Diagnostics.Stopwatch]::StartNew()
python -I "$S\make_manifest.py" $S
"== ingest the parts (093 on 1.4.3: -rat 6f88a1ee622775bf, -mouse 5a6fd7af5b7544f5)"
& $Exe ingest "$S\manifest.yaml" PXD027754-rat PXD027754-mouse
"exit=$LASTEXITCODE  t=$([int]$sw.Elapsed.TotalSeconds)s"
"== junction the served whole deposit and the control into the scratch store (read only)"
foreach ($pair in @(@('PXD027754', '2799534125b81db3'), @('PXD017944', '3cd52dd1b39472d8'))) {
    $dir = Join-Path "$S\store" $pair[0]
    New-Item -ItemType Directory -Force $dir | Out-Null
    $link = Join-Path $dir $pair[1]
    if (-not (Test-Path $link)) { cmd /c mklink /J "$link" "F:\aging_data\repo\store\$($pair[0])\$($pair[1])" | Out-Null }
}
"== build: the parts and the control (must pass)"
& $Exe build "$S\manifest.yaml" PXD017944 PXD027754-rat PXD027754-mouse --store "$S\store" --out "$S\cat_split"
"exit=$LASTEXITCODE  t=$([int]$sw.Elapsed.TotalSeconds)s"
"== build: the whole deposit and the control (the comparison)"
& $Exe build "$S\manifest.yaml" PXD017944 PXD027754 --store "$S\store" --out "$S\cat_whole"
"exit=$LASTEXITCODE  t=$([int]$sw.Elapsed.TotalSeconds)s"
"== build: the whole deposit beside its parts (must be refused)"
& $Exe build "$S\manifest.yaml" PXD017944 PXD027754 PXD027754-rat PXD027754-mouse --store "$S\store" --out "$S\cat_both"
"exit=$LASTEXITCODE"
"== build: one part alone and the control (a lone part)"
& $Exe build "$S\manifest.yaml" PXD017944 PXD027754-rat --store "$S\store" --out "$S\cat_lone"
"exit=$LASTEXITCODE  t=$([int]$sw.Elapsed.TotalSeconds)s"
"== site from the split catalog"
& $Exe site "$S\cat_split" --out "$S\site_split" --base-url "https://example.org/repo/"
"exit=$LASTEXITCODE"
& $Exe site "$S\cat_lone" --out "$S\site_lone"
"exit=$LASTEXITCODE  t=$([int]$sw.Elapsed.TotalSeconds)s"
