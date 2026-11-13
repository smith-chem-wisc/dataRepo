"""Scratch (1.5.0): engines.py replayed each serving logs artefact for the deposits it was first requested for; three were
requested only for deposits now excluded (PXD042428, PXD016793, PXD073999), so three databases went unresolved and six
deposits lost their gene names. Run logs.resolve_genes the way an operator should after a re-ingest: every re-ingested
deposit of each species, with that species' inputs. Appends to engines.log."""
import json, os, subprocess, sys, time
import yaml

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "bin", "datarepo.exe")
STORE = os.path.join(HERE, "store")
done = {d for d in os.listdir(STORE) if not d.startswith("_")}
m = yaml.safe_load(open(os.path.join(HERE, "manifest.snapshot.yaml"), encoding="utf-8"))
org = {e["accession"]: e.get("organism") for e in m["datasets"]}
LOGS = r"E:\CodeReview\logs\results"
REF = r"F:\aging_data\reference\ensembl116"
species = {
    "NCBITaxon:9606": ("Homo_sapiens.GRCh38.116.genes.tsv.gz", "Homo_sapiens.GRCh38.116.uniprot.tsv.gz"),
    "NCBITaxon:10090": ("Mus_musculus.GRCm39.116.genes.tsv.gz", "Mus_musculus.GRCm39.116.uniprot.tsv.gz"),
    "NCBITaxon:10116": ("Rattus_norvegicus.GRCr8.116.genes.tsv.gz", "Rattus_norvegicus.GRCr8.116.uniprot.tsv.gz"),
}
log = open(os.path.join(HERE, "engines.log"), "a", encoding="utf-8")
other = sorted(a for a in done if org.get(a) not in species)
log.write(f"== fix: deposits of no listed species (not run): {[(a, org.get(a)) for a in other]}\n")
for taxon, (genes, xref) in species.items():
    accs = sorted(a for a in done if org.get(a) == taxon)
    cmd = [EXE, "run", "logs.resolve_genes", *accs, "--store", STORE, "--latest",
           "--input", f"gene_set={LOGS}\\gene_sets\\{genes}", "--input", f"xref={REF}\\{xref}",
           "--input", f"logs_manifest={LOGS}\\resolver_inputs_e116.json"]
    log.write(f"== {time.strftime('%H:%M:%S', time.gmtime())} fix logs.resolve_genes {taxon} {len(accs)} deposits\n")
    t = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log.write(p.stdout[-8000:] + ("\n-- stderr:\n" + p.stderr[-4000:] if p.stderr.strip() else "") + "\n")
    log.write(f"== done fix {taxon} rc={p.returncode} secs={time.time() - t:.0f}\n\n")
    log.flush()
    print(taxon, len(accs), "rc", p.returncode, f"{time.time() - t:.0f}s", flush=True)
