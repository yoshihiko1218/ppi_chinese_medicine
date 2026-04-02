#!/usr/bin/env python3
"""
Stage 3: Disease Target Collection
Query GeneCards, OMIM, and TTD for disease-associated genes.
Diseases: Insomnia, Alzheimer's disease, Anxiety disorder
"""
import requests
import pandas as pd
import time
import json
import re
from bs4 import BeautifulSoup

DISEASES = {
    "insomnia": "Insomnia",
    "alzheimer": "Alzheimer's disease",
    "anxiety": "Anxiety disorder",
}

def get_disgenet_targets(disease_name):
    """Get disease targets from DisGeNET (open access)."""
    targets = []
    try:
        # DisGeNET API
        url = "https://www.disgenet.org/api/gda/disease/search"
        params = {"disease": disease_name, "source": "ALL", "format": "json"}
        headers = {"Accept": "application/json"}
        r = requests.get(url, params=params, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            for entry in data:
                targets.append({
                    "gene_symbol": entry.get("gene_symbol", ""),
                    "gene_id": entry.get("geneid", ""),
                    "score": entry.get("score", 0),
                    "source": "DisGeNET"
                })
    except:
        pass
    return targets

def get_opentargets(disease_query):
    """Get disease targets from Open Targets Platform."""
    targets = []
    try:
        # First search for disease ID
        url = "https://api.platform.opentargets.org/api/v4/graphql"
        search_query = {
            "query": """
            query searchDisease($q: String!) {
                search(queryString: $q, entityNames: ["disease"]) {
                    hits { id name }
                }
            }
            """,
            "variables": {"q": disease_query}
        }
        r = requests.post(url, json=search_query, timeout=30)
        if r.status_code == 200:
            data = r.json()
            hits = data.get("data", {}).get("search", {}).get("hits", [])
            if hits:
                disease_id = hits[0]["id"]
                print(f"  Open Targets disease ID: {disease_id} ({hits[0]['name']})")

                # Get associated targets
                assoc_query = {
                    "query": """
                    query diseaseTargets($id: String!) {
                        disease(efoId: $id) {
                            associatedTargets(page: {size: 500, index: 0}) {
                                rows {
                                    target { approvedSymbol id }
                                    score
                                }
                            }
                        }
                    }
                    """,
                    "variables": {"id": disease_id}
                }
                r2 = requests.post(url, json=assoc_query, timeout=60)
                if r2.status_code == 200:
                    data2 = r2.json()
                    rows = data2.get("data", {}).get("disease", {}).get("associatedTargets", {}).get("rows", [])
                    for row in rows:
                        targets.append({
                            "gene_symbol": row["target"]["approvedSymbol"],
                            "ensembl_id": row["target"]["id"],
                            "score": row["score"],
                            "source": "OpenTargets"
                        })
    except Exception as e:
        print(f"  Open Targets error: {e}")
    return targets

def get_omim_targets(disease_query):
    """Get disease targets from OMIM via their API (no key needed for search)."""
    targets = []
    try:
        # Use NCBI Gene search as OMIM proxy
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "gene",
            "term": f"{disease_query}[Disease/Phenotype] AND Homo sapiens[Organism]",
            "retmax": 500,
            "retmode": "json"
        }
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])
            if id_list:
                # Fetch gene symbols in batches
                for i in range(0, len(id_list), 100):
                    batch = id_list[i:i+100]
                    ids = ",".join(batch)
                    url2 = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                    params2 = {"db": "gene", "id": ids, "retmode": "json"}
                    r2 = requests.get(url2, params=params2, timeout=30)
                    if r2.status_code == 200:
                        data2 = r2.json()
                        for gid in batch:
                            info = data2.get("result", {}).get(gid, {})
                            symbol = info.get("name", "")
                            if symbol and info.get("organism", {}).get("scientificname") == "Homo sapiens":
                                targets.append({
                                    "gene_symbol": symbol,
                                    "gene_id": gid,
                                    "score": 1.0,
                                    "source": "NCBI_Gene"
                                })
                    time.sleep(0.5)
    except Exception as e:
        print(f"  NCBI Gene error: {e}")
    return targets


# Collect targets for each disease
all_disease_targets = []

for key, disease_name in DISEASES.items():
    print(f"\n{'='*50}")
    print(f"Collecting targets for: {disease_name}")

    targets = []

    # 1. Open Targets Platform (most comprehensive)
    print("  Querying Open Targets...")
    ot_targets = get_opentargets(disease_name)
    print(f"  Open Targets: {len(ot_targets)} targets")
    targets.extend(ot_targets)

    # 2. NCBI Gene (OMIM proxy)
    print("  Querying NCBI Gene...")
    ncbi_targets = get_omim_targets(disease_name)
    print(f"  NCBI Gene: {len(ncbi_targets)} targets")
    targets.extend(ncbi_targets)

    # Deduplicate by gene symbol
    if targets:
        df = pd.DataFrame(targets)
        df = df.drop_duplicates(subset='gene_symbol')
        df['disease'] = disease_name
        df['disease_key'] = key
        all_disease_targets.append(df)
        print(f"  Total unique targets: {len(df)}")

    time.sleep(1)

# Combine all disease targets
if all_disease_targets:
    combined = pd.concat(all_disease_targets, ignore_index=True)
    combined.to_csv("data/targets/disease_targets.csv", index=False)

    # Summary
    print(f"\n{'='*50}")
    print("=== Disease Target Summary ===")
    for key, name in DISEASES.items():
        n = combined[combined['disease_key'] == key]['gene_symbol'].nunique()
        print(f"  {name}: {n} unique targets")

    # Union of all disease targets
    all_genes = combined['gene_symbol'].unique()
    print(f"\nTotal unique disease-related genes (union): {len(all_genes)}")

    # Save gene lists per disease
    for key in DISEASES:
        genes = combined[combined['disease_key'] == key]['gene_symbol'].unique()
        pd.DataFrame({"gene_symbol": genes}).to_csv(
            f"data/targets/disease_targets_{key}.csv", index=False
        )
