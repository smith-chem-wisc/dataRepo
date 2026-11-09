"""Compare the trial catalogs: the split one against the whole one, and a 1.4.5 scratch build of aging's store against
aging's serving catalog. Read only."""
import json
import os
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
S = sys.argv[1]
mode = sys.argv[2]


def catalog(folder):
    with open(os.path.join(folder, "latest.json"), encoding="utf-8") as handle:
        latest = json.load(handle)
    return duckdb.connect(os.path.join(folder, latest["catalog"]), read_only=True), latest


def rows(con, sql):
    return con.execute(sql).fetchall()


if mode == "trial":
    split, ls = catalog(os.path.join(S, "cat_split"))
    whole, lw = catalog(os.path.join(S, "cat_whole"))
    lone, ll = catalog(os.path.join(S, "cat_lone"))
    print("split", ls["catalog_id"], ls["catalog_version"], "| whole", lw["catalog_id"], "| lone", ll["catalog_id"])
    print("release ids:", ls["release_id"], lw["release_id"], ll["release_id"])
    q = "SELECT dataset_id, bundle_id, accession, split_group, split_reason, n_runs, n_psms_1pct, n_protein_groups_1pct FROM dataset_overview ORDER BY 1"
    for name, con in (("split", split), ("whole", whole), ("lone", lone)):
        print(f"-- {name} dataset_overview")
        for r in rows(con, q):
            print("  ", r)
        print(f"-- {name} deposits")
        for r in rows(con, "SELECT * FROM deposits ORDER BY accession"):
            print("  ", r)
        print(f"-- {name} split/census checks")
        for r in rows(con, "SELECT name, ok, observed, expected, detail FROM catalog_checks WHERE kind IN ('split', 'census')"):
            print("  ", r)
        print(f"-- {name} failed checks:", rows(con, "SELECT count(*) FROM catalog_checks WHERE NOT ok")[0][0],
              "of", rows(con, "SELECT count(*) FROM catalog_checks")[0][0])
    for table, key in (("protein_index", "protein_accession"), ("peptide_index", "base_sequence")):
        cols = "n_datasets, n_datasets_1pct, n_datasets_contaminant" if table == "protein_index" else "n_datasets"
        a = rows(split, f"SELECT {key}, {cols} FROM {table} ORDER BY 1")
        b = rows(whole, f"SELECT {key}, {cols} FROM {table} ORDER BY 1")
        c = rows(lone, f"SELECT {key}, {cols} FROM {table} ORDER BY 1")
        print(f"{table}: split {len(a)} rows, whole {len(b)}, lone {len(c)}; split == whole: {a == b}; lone == whole: {c == b}")
        # and the count by key, which 1.4.4 gave: how many rows would have read 2 deposits for PXD027754's parts
        by_key = rows(split, f"SELECT count(*) FROM {table} WHERE len(dataset_ids) > n_datasets")[0][0]
        print(f"  rows whose dataset_ids is longer than n_datasets (a count by key would have read more): {by_key}")
else:
    new, ln = catalog(os.path.join(S, "full"))
    with open(os.path.join(S, "served.json"), encoding="utf-8") as handle:
        served = json.load(handle)
    old = duckdb.connect(os.path.join("F:/aging_data/repo/catalogs", served["catalog"]), read_only=True)
    print("new", ln["catalog_id"], ln["catalog_version"], ln["builder_version"], "release", ln["release_id"])
    print("old", served["catalog_id"], served["builder"], "release",
          rows(old, "SELECT release_id FROM catalog_meta")[0][0])
    same_bundles = rows(new, "SELECT dataset_id, bundle_id FROM catalog_bundles ORDER BY 1") == \
        rows(old, "SELECT dataset_id, bundle_id FROM catalog_bundles ORDER BY 1")
    print("same bundles:", same_bundles)
    for table, key in (("protein_index", "protein_accession"), ("peptide_index", "base_sequence"), ("protein_datasets", "dataset_id, protein_accession")):
        cols = [r[0] for r in rows(old, f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position")]
        sel = ", ".join(cols)
        a = rows(new, f"SELECT {sel} FROM {table} ORDER BY {key}")
        b = rows(old, f"SELECT {sel} FROM {table} ORDER BY {key}")
        print(f"{table}: {len(a)} rows new, {len(b)} old; every column equal: {a == b}")
    cols = [r[0] for r in rows(old, "SELECT column_name FROM information_schema.columns WHERE table_name = 'dataset_overview' ORDER BY ordinal_position")]
    a = rows(new, f"SELECT {', '.join(cols)} FROM dataset_overview ORDER BY dataset_id")
    b = rows(old, f"SELECT {', '.join(cols)} FROM dataset_overview ORDER BY dataset_id")
    print(f"dataset_overview: {len(cols)} old columns, equal: {a == b}")
    print("new overview columns:", [r[0] for r in rows(new, "SELECT column_name FROM information_schema.columns WHERE table_name = 'dataset_overview' ORDER BY ordinal_position") if r[0] not in cols])
    print("deposits:", rows(new, "SELECT count(*), sum(n_datasets), count(*) FILTER (WHERE len(split_groups) > 0) FROM deposits")[0])
    print("accession = dataset_id everywhere:", rows(new, "SELECT bool_and(accession = dataset_id AND split_group IS NULL AND split_reason IS NULL) FROM dataset_overview")[0][0])
    print("split check:", rows(new, "SELECT ok, observed, expected FROM catalog_checks WHERE kind = 'split'"))
    print("failed checks:", rows(new, "SELECT count(*) FROM catalog_checks WHERE NOT ok")[0][0], "of", rows(new, "SELECT count(*) FROM catalog_checks")[0][0],
          "| old:", rows(old, "SELECT count(*) FROM catalog_checks")[0][0])
    print("census rows new/old:", rows(new, "SELECT count(*) FROM dataset_candidates")[0][0], rows(old, "SELECT count(*) FROM dataset_candidates")[0][0])
