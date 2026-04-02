#!/usr/bin/env python3
"""Fetch SMILES from PubChem for all filtered compounds."""
import pandas as pd
import requests
import time
import urllib.parse

def get_pubchem_smiles(compound_name):
    """Get SMILES from PubChem by compound name."""
    # Clean up name for URL
    name = compound_name.strip()
    # Remove _qt suffix (TCMSP convention for aglycone form)
    name_clean = name.replace("_qt", "")

    for query_name in [name_clean, name]:
        try:
            encoded = urllib.parse.quote(query_name)
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded}/property/CanonicalSMILES,MolecularWeight/JSON"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                props = data["PropertyTable"]["Properties"][0]
                smiles = props.get("CanonicalSMILES") or props.get("ConnectivitySMILES", "")
                cid = props.get("CID", "")
                return smiles, cid
        except Exception:
            pass
    return "", ""

# Load filtered compounds
df = pd.read_csv("data/compounds/compounds_filtered_all.csv")
unique = df.drop_duplicates(subset='molecule_name')[['MOL_ID', 'molecule_name']].copy()
print(f"Fetching SMILES for {len(unique)} unique compounds...")

results = []
found = 0
for _, row in unique.iterrows():
    name = row['molecule_name']
    smiles, cid = get_pubchem_smiles(name)
    results.append({"molecule_name": name, "SMILES": smiles, "PubChem_CID": cid})
    if smiles:
        found += 1
        print(f"  OK: {name} (CID: {cid})")
    else:
        print(f"  NOT FOUND: {name}")
    time.sleep(0.35)

smiles_df = pd.DataFrame(results)
print(f"\nFound SMILES for {found}/{len(unique)} compounds")

# Merge SMILES back to main dataframe
df = df.drop(columns=['SMILES'], errors='ignore')
df = df.merge(smiles_df[['molecule_name', 'SMILES', 'PubChem_CID']], on='molecule_name', how='left')
df.to_csv("data/compounds/compounds_filtered_all.csv", index=False)

# Also save SMILES lookup table
smiles_df.to_csv("data/compounds/smiles_lookup.csv", index=False)

# Summary
n_with = df['SMILES'].notna() & (df['SMILES'] != '')
print(f"\nFinal: {n_with.sum()}/{len(df)} entries have SMILES")
print(f"Unique compounds with SMILES: {df[n_with]['MOL_ID'].nunique()}")
print(f"Missing SMILES:")
missing = df[~n_with]['molecule_name'].unique()
for m in missing:
    print(f"  {m}")
