#!/usr/bin/env python3
"""
Supplement targets for 龙眼肉 and 天麻 using:
1. Shared compound targets from other herbs in TCMSP
2. UniProt search for known compound-target relationships
"""
import pandas as pd
import requests
import time

# Load current data
compounds = pd.read_csv("data/compounds/compounds_filtered_all.csv")
drug_targets = pd.read_csv("data/targets/drug_targets.csv")
tcmsp_all_targets = pd.read_csv("data/targets/tcmsp_targets_raw.csv")

# Get compounds for 龙眼肉 and 天麻
supp_herbs = compounds[compounds['herb_cn'].isin(['龙眼肉', '天麻'])].copy()
print("Supplementary compounds:")
print(supp_herbs[['MOL_ID', 'molecule_name', 'herb_cn']].to_string())

# For shared compounds (like quercetin, beta-sitosterol), find targets from TCMSP data
# These compounds appear in other herbs too
shared_names = ['quercetin', 'Quercetin', 'beta-sitosterol', 'beta-Sitosterol',
                'Kaempferol', 'kaempferol', 'luteolin', 'Stigmasterol',
                'Daucosterol', 'daucosterol', 'Ellagic acid', 'ellagic acid',
                'baicalein', 'morin', 'hederagenin']

print("\n=== Looking for shared compound targets in TCMSP ===")
supp_targets = []
for _, row in supp_herbs.iterrows():
    mol_name = row['molecule_name']
    mol_id = row['MOL_ID']
    herb_cn = row['herb_cn']

    # Search for this compound name in ALL TCMSP target data
    name_matches = tcmsp_all_targets[
        tcmsp_all_targets['molecule_name'].str.lower() == mol_name.lower()
    ]

    if len(name_matches) > 0:
        # Copy targets and reassign to our herb
        for _, t in name_matches.iterrows():
            supp_targets.append({
                'molecule_ID': t.get('molecule_ID', ''),
                'MOL_ID': t['MOL_ID'],
                'molecule_name': mol_name,
                'target_name': t['target_name'],
                'target_ID': t.get('target_ID', ''),
                'drugbank_ID': t.get('drugbank_ID', ''),
                'validated': t.get('validated', ''),
                'SVM_score': t.get('SVM_score', ''),
                'RF_score': t.get('RF_score', ''),
                'herb_cn': herb_cn,
                'herb_pinyin': row['herb_pinyin'],
            })
        print(f"  {mol_name} ({herb_cn}): {len(name_matches)} targets from TCMSP")
    else:
        print(f"  {mol_name} ({herb_cn}): No TCMSP targets, trying UniProt search...")

        # For unique compounds (gastrodin, parishin, etc.), search UniProt for known targets
        try:
            url = "https://rest.uniprot.org/uniprotkb/search"
            params = {
                "query": f'(cc_interaction:"{mol_name}") AND organism_id:9606',
                "format": "json",
                "size": 20,
                "fields": "gene_primary,protein_name,accession"
            }
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("results"):
                    for result in data["results"]:
                        genes = result.get("genes", [])
                        gene_name = genes[0]["geneName"]["value"] if genes and genes[0].get("geneName") else ""
                        prot_name = result.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "")
                        if gene_name:
                            supp_targets.append({
                                'molecule_ID': '',
                                'MOL_ID': mol_id,
                                'molecule_name': mol_name,
                                'target_name': prot_name,
                                'target_ID': '',
                                'drugbank_ID': '',
                                'validated': '',
                                'SVM_score': '',
                                'RF_score': '',
                                'herb_cn': herb_cn,
                                'herb_pinyin': row['herb_pinyin'],
                                'gene_symbol': gene_name,
                                'uniprot_id': result.get("primaryAccession", ""),
                            })
                    print(f"    Found {len(data['results'])} UniProt results")
            time.sleep(0.5)
        except Exception as e:
            print(f"    UniProt search failed: {e}")

if supp_targets:
    supp_df = pd.DataFrame(supp_targets)
    print(f"\nTotal supplementary target entries: {len(supp_df)}")

    if 'gene_symbol' not in supp_df.columns:
        supp_df['gene_symbol'] = ''
    if 'uniprot_id' not in supp_df.columns:
        supp_df['uniprot_id'] = ''
    supp_df['gene_symbol'] = supp_df['gene_symbol'].fillna('')
    supp_df['uniprot_id'] = supp_df['uniprot_id'].fillna('')

    # Use existing gene_map from drug_targets
    existing_map = dict(zip(drug_targets['target_name'], drug_targets['gene_symbol']))
    existing_uid = dict(zip(drug_targets['target_name'], drug_targets['uniprot_id']))

    unmapped = []
    for idx, row in supp_df.iterrows():
        if not row.get('gene_symbol'):
            if row['target_name'] in existing_map:
                supp_df.at[idx, 'gene_symbol'] = existing_map[row['target_name']]
                supp_df.at[idx, 'uniprot_id'] = existing_uid.get(row['target_name'], '')
            else:
                unmapped.append(row['target_name'])

    # Map remaining via UniProt
    unmapped_unique = list(set(unmapped))
    print(f"Mapping {len(unmapped_unique)} remaining targets via UniProt...")
    for name in unmapped_unique:
        try:
            url = "https://rest.uniprot.org/uniprotkb/search"
            params = {
                "query": f'protein_name:"{name}" AND organism_id:9606',
                "format": "json",
                "size": 1,
                "fields": "gene_primary,accession"
            }
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("results"):
                    genes = data["results"][0].get("genes", [])
                    if genes and genes[0].get("geneName"):
                        gene = genes[0]["geneName"]["value"]
                        uid = data["results"][0].get("primaryAccession", "")
                        mask = supp_df['target_name'] == name
                        supp_df.loc[mask, 'gene_symbol'] = gene
                        supp_df.loc[mask, 'uniprot_id'] = uid
            time.sleep(0.3)
        except:
            pass

    # Remove entries without gene symbols
    supp_df = supp_df[supp_df['gene_symbol'] != ''].copy()
    print(f"Supplementary targets with gene symbols: {len(supp_df)}")

    # Combine with existing drug targets
    combined = pd.concat([drug_targets, supp_df], ignore_index=True)
    combined.to_csv("data/targets/drug_targets.csv", index=False)

    # Update gene list
    target_list = combined[['gene_symbol', 'uniprot_id', 'target_name']].drop_duplicates(subset='gene_symbol')
    target_list.to_csv("data/targets/drug_target_genes.csv", index=False)

    print(f"\n=== Updated drug targets ===")
    print(f"Total entries: {len(combined)}")
    print(f"Unique gene symbols: {combined['gene_symbol'].nunique()}")
    for herb in compounds['herb_cn'].unique():
        herb_mols = set(compounds[compounds['herb_cn'] == herb]['MOL_ID'].unique())
        n = combined[combined['MOL_ID'].isin(herb_mols)]['gene_symbol'].nunique()
        print(f"  {herb}: {n} targets")
