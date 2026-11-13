#!/usr/bin/env bash
# Scratch: re-ingest one deposit with the 1.5.0 branch binary (aa9ad4b) into the scratch store, called as PXReprise calls
# it. Reads F:\aging_data only; writes only under F:\datarepo_scratch_150\reingest150.
S="F:/datarepo_scratch_150/reingest150"
acc="$1"
start=$(date +%s)
echo "$(date -u +%H:%M:%S) start $acc" >> "$S/progress.log"
"$S/bin/datarepo.exe" ingest "$S/manifest.snapshot.yaml" "$acc" --store "$S/store" --json > "$S/out/$acc.json" 2> "$S/out/$acc.err"
rc=$?
echo "$(date -u +%H:%M:%S) done  $acc rc=$rc secs=$(( $(date +%s) - start ))" >> "$S/progress.log"
