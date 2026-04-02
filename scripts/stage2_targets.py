#!/usr/bin/env python3
"""
Stage 2: Drug Target Prediction
- Use TCMSP targets (already scraped)
- Supplement with Swiss Target Prediction via web API where possible
- Standardize gene names via UniProt
"""
import pandas as pd
import requests
import time
import json

# Load filtered compounds and TCMSP targets
compounds = pd.read_csv("data/compounds/compounds_filtered_all.csv")
tcmsp_targets = pd.read_csv("data/targets/tcmsp_targets_raw.csv")

print("=== TCMSP Target Data ===")
print(f"Total target entries: {len(tcmsp_targets)}")
print(f"Unique MOL_IDs: {tcmsp_targets['MOL_ID'].nunique()}")
print(f"Unique targets: {tcmsp_targets['target_name'].nunique()}")

# Filter targets for our filtered compounds only
filtered_mol_ids = set(compounds['MOL_ID'].unique())
drug_targets = tcmsp_targets[tcmsp_targets['MOL_ID'].isin(filtered_mol_ids)].copy()
print(f"\nTargets for filtered compounds: {len(drug_targets)}")
print(f"Unique targets: {drug_targets['target_name'].nunique()}")

# For supplementary herbs (龙眼肉, 天麻) that don't have TCMSP targets,
# use Swiss Target Prediction via their SMILES
supp_compounds = compounds[compounds['herb_cn'].isin(['龙眼肉', '天麻'])].copy()
supp_compounds = supp_compounds.dropna(subset=['SMILES'])
print(f"\nSupplementary compounds needing STP: {len(supp_compounds)}")

# Try Swiss Target Prediction for supplementary compounds
# STP web scraping approach
def query_stp(smiles, compound_name):
    """Try to get targets from Swiss Target Prediction."""
    try:
        session = requests.Session()
        # Submit SMILES
        r = session.post(
            "http://www.swisstargetprediction.ch/predict.php",
            data={"smiles": smiles, "organism": "Homo_sapiens"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=60
        )
        # Try to get CSV
        r2 = session.get(
            "http://www.swisstargetprediction.ch/result.php",
            params={"smiles": smiles, "organism": "Homo_sapiens"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30
        )
        if r2.status_code == 200 and 'Uniprot' in r2.text:
            # Parse HTML table
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r2.text, 'html.parser')
            tables = soup.find_all('table')
            if tables:
                rows = tables[0].find_all('tr')
                targets = []
                for row in rows[1:]:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        targets.append({
                            'target_name': cells[0].get_text(strip=True),
                            'uniprot_id': cells[1].get_text(strip=True),
                            'probability': float(cells[-1].get_text(strip=True))
                        })
                return [t for t in targets if t['probability'] > 0]
    except Exception as e:
        pass
    return []


# Map target names to gene symbols using UniProt API
def get_gene_symbols_batch(target_names):
    """Convert target names to standard gene symbols via UniProt."""
    gene_map = {}
    unique_names = list(set(target_names))
    print(f"\nMapping {len(unique_names)} unique target names to gene symbols via UniProt...")

    for name in unique_names:
        try:
            # Search UniProt for the target name
            url = "https://rest.uniprot.org/uniprotkb/search"
            params = {
                "query": f"protein_name:\"{name}\" AND organism_id:9606",
                "format": "json",
                "size": 1,
                "fields": "gene_primary,protein_name,accession"
            }
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("results"):
                    result = data["results"][0]
                    genes = result.get("genes", [])
                    if genes and genes[0].get("geneName"):
                        gene_symbol = genes[0]["geneName"]["value"]
                        uniprot_id = result.get("primaryAccession", "")
                        gene_map[name] = {"gene_symbol": gene_symbol, "uniprot_id": uniprot_id}
        except Exception:
            pass
        time.sleep(0.3)

    return gene_map


# Get gene symbols for all TCMSP targets
gene_map = get_gene_symbols_batch(drug_targets['target_name'].tolist())
print(f"Mapped {len(gene_map)}/{drug_targets['target_name'].nunique()} targets to gene symbols")

# Add gene symbols to target data
drug_targets['gene_symbol'] = drug_targets['target_name'].map(
    lambda x: gene_map.get(x, {}).get('gene_symbol', '')
)
drug_targets['uniprot_id'] = drug_targets['target_name'].map(
    lambda x: gene_map.get(x, {}).get('uniprot_id', '')
)

# Remove entries without gene symbols
n_before = len(drug_targets)
drug_targets = drug_targets[drug_targets['gene_symbol'] != ''].copy()
print(f"\nAfter removing unmapped targets: {len(drug_targets)}/{n_before}")
print(f"Unique gene symbols: {drug_targets['gene_symbol'].nunique()}")

# Save results
drug_targets.to_csv("data/targets/drug_targets.csv", index=False)

# Create clean target list (unique gene symbols)
target_list = drug_targets[['gene_symbol', 'uniprot_id', 'target_name']].drop_duplicates(subset='gene_symbol')
target_list.to_csv("data/targets/drug_target_genes.csv", index=False)

# Summary per herb
print(f"\n=== Per-herb target summary ===")
for herb in compounds['herb_cn'].unique():
    herb_mols = set(compounds[compounds['herb_cn'] == herb]['MOL_ID'].unique())
    herb_targets = drug_targets[drug_targets['MOL_ID'].isin(herb_mols)]['gene_symbol'].nunique()
    print(f"  {herb}: {herb_targets} unique gene targets")

print(f"\n=== Final drug targets ===")
print(f"Total unique gene symbols: {drug_targets['gene_symbol'].nunique()}")
print(f"Total compound-target pairs: {len(drug_targets)}")
