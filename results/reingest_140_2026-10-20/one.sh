#!/usr/bin/env bash
# Scratch: re-ingest one deposit with the 1.4.0 branch binary into the scratch store. Reads F:\aging_data only.
S="C:/Users/trish/AppData/Local/Temp/claude/E--CodeReview-dataRepo/5e35477d-a91b-4a4a-9ac7-00253f67c9a5/scratchpad/reingest140"
acc="$1"
start=$(date +%s)
echo "$(date -u +%H:%M:%S) start $acc" >> "$S/progress.log"
"$S/bin/datarepo.exe" ingest "$S/manifest.snapshot.yaml" "$acc" --store "$S/store" --json > "$S/out/$acc.json" 2> "$S/out/$acc.err"
rc=$?
echo "$(date -u +%H:%M:%S) done  $acc rc=$rc secs=$(( $(date +%s) - start ))" >> "$S/progress.log"
