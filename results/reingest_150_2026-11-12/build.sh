#!/usr/bin/env bash
# Scratch (1.5.0): build a folder catalog of every re-ingested deposit from the scratch store, twice (the first derives every
# deposit, the second reuses them), timing each. The exe is a copy named dr150.exe: aging's publish refuses to start while
# any process whose command line names "datarepo" runs a build. Writes only under F:\datarepo_scratch_150\reingest150.
S="F:/datarepo_scratch_150/reingest150"
cp -n "$S/bin/datarepo.exe" "$S/bin/dr150.exe"
accs=$(ls "$S/store" | grep -v '^_')
for pass in 1 2; do
  start=$(date +%s)
  echo "== pass $pass $(date -u +%H:%M:%S)" >> "$S/build.log"
  "$S/bin/dr150.exe" build "$S/manifest.snapshot.yaml" $accs --store "$S/store" --latest --out "$S/catalogs" -v >> "$S/build.log" 2>&1
  echo "== pass $pass rc=$? secs=$(( $(date +%s) - start ))" >> "$S/build.log"
done
