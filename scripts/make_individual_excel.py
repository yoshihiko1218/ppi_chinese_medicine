#!/usr/bin/env python3
"""Create individual Excel files for each result table."""
import pandas as pd
import os

outdir = "results/tables"

# Reuse the same data processing from make_excel.py

# === 1. Active Compounds ===
compounds = pd.read_csv("data/compounds/compounds_filtered_all.csv")
c1 = compounds[[
    'MOL_ID', 'molecule_name', 'molecule_name_cn', 'ob', 'dl', 'mw',
    'herb_cn', 'herb_pinyin', 'SMILES', 'PubChem_CID'
]].copy()
c1.columns = [
    'MOL_ID', 'Compound (English)', 'Compound (Chinese)', 'OB (%)', 'DL',
    'Molecular Weight', 'Herb (Chinese)', 'Herb (Pinyin)', 'SMILES', 'PubChem CID'
]
c1.to_excel(f"{outdir}/active_compounds.xlsx", index=False)

# === 2. Unique Compounds ===
unique = c1.drop_duplicates(subset='MOL_ID').copy()
herb_sources = c1.groupby('MOL_ID')['Herb (Chinese)'].apply(
    lambda x: ', '.join(sorted(set(x)))
).reset_index()
herb_sources.columns = ['MOL_ID', 'Source Herbs']
unique = unique.drop(columns=['Herb (Chinese)', 'Herb (Pinyin)']).merge(herb_sources, on='MOL_ID')
unique = unique.sort_values('OB (%)', ascending=False)
unique.to_excel(f"{outdir}/unique_compounds.xlsx", index=False)

# === 3. Drug Targets ===
drug_targets = pd.read_csv("data/targets/drug_targets.csv")
dt = drug_targets[[
    'MOL_ID', 'molecule_name', 'gene_symbol', 'uniprot_id',
    'target_name', 'herb_cn', 'herb_pinyin'
]].copy()
dt.columns = [
    'MOL_ID', 'Compound', 'Gene Symbol', 'UniProt ID',
    'Target Protein', 'Herb (Chinese)', 'Herb (Pinyin)'
]
dt.to_excel(f"{outdir}/drug_targets.xlsx", index=False)

# === 4. Disease Targets ===
disease_targets = pd.read_csv("data/targets/disease_targets.csv")
dis = disease_targets[['gene_symbol', 'disease', 'source', 'score']].copy()
dis.columns = ['Gene Symbol', 'Disease', 'Source Database', 'Association Score']
dis.to_excel(f"{outdir}/disease_targets.xlsx", index=False)

# === 5. Common Targets ===
common = pd.read_csv("data/targets/common_targets.csv")
insomnia = set(pd.read_csv("data/targets/common_targets_insomnia.csv")['gene_symbol'])
alzheimer = set(pd.read_csv("data/targets/common_targets_alzheimer.csv")['gene_symbol'])
anxiety = set(pd.read_csv("data/targets/common_targets_anxiety.csv")['gene_symbol'])

ce = common.copy()
ce['Insomnia'] = ce['gene_symbol'].apply(lambda x: 'Yes' if x in insomnia else '')
ce["Alzheimer's"] = ce['gene_symbol'].apply(lambda x: 'Yes' if x in alzheimer else '')
ce['Anxiety'] = ce['gene_symbol'].apply(lambda x: 'Yes' if x in anxiety else '')

gene_compounds = drug_targets.groupby('gene_symbol')['molecule_name'].apply(
    lambda x: ', '.join(sorted(set(x)))
).reset_index()
gene_compounds.columns = ['gene_symbol', 'Active Compounds']
gene_herbs = drug_targets.groupby('gene_symbol')['herb_cn'].apply(
    lambda x: ', '.join(sorted(set(x)))
).reset_index()
gene_herbs.columns = ['gene_symbol', 'Source Herbs']

ce = ce.merge(gene_compounds, on='gene_symbol', how='left')
ce = ce.merge(gene_herbs, on='gene_symbol', how='left')
ce.columns = ['Gene Symbol', 'Insomnia', "Alzheimer's", 'Anxiety', 'Active Compounds', 'Source Herbs']
ce.to_excel(f"{outdir}/common_targets.xlsx", index=False)

# === 6. PPI Topology ===
ppi = pd.read_csv("results/tables/ppi_topology.csv")
ppi.columns = ['Gene Symbol', 'Degree', 'Betweenness Centrality', 'Closeness Centrality']
ppi['Core Target'] = ppi['Degree'].apply(lambda x: 'Yes' if x >= 12.5 else '')
ppi.to_excel(f"{outdir}/ppi_topology.xlsx", index=False)

# === 7. Core Targets ===
core = ppi[ppi['Core Target'] == 'Yes'].copy()
core = core.merge(ce[['Gene Symbol', 'Insomnia', "Alzheimer's", 'Anxiety', 'Active Compounds', 'Source Herbs']],
                  on='Gene Symbol', how='left')
core.to_excel(f"{outdir}/core_targets.xlsx", index=False)

# === 8. KEGG Pathways ===
kegg = pd.read_csv("data/enrichment/KEGG_2021_Human.csv")
kegg_clean = kegg[['Term', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']].copy()
kegg_clean.columns = ['Pathway', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']
kegg_clean.to_excel(f"{outdir}/kegg_pathways.xlsx", index=False)

# === 9. GO Biological Process ===
go_bp = pd.read_csv("data/enrichment/GO_Biological_Process_2023.csv")
go_bp[['Term', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']].rename(
    columns={'Term': 'GO Term'}
).to_excel(f"{outdir}/go_biological_process.xlsx", index=False)

# === 10. GO Cellular Component ===
go_cc = pd.read_csv("data/enrichment/GO_Cellular_Component_2023.csv")
go_cc[['Term', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']].rename(
    columns={'Term': 'GO Term'}
).to_excel(f"{outdir}/go_cellular_component.xlsx", index=False)

# === 11. GO Molecular Function ===
go_mf = pd.read_csv("data/enrichment/GO_Molecular_Function_2023.csv")
go_mf[['Term', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']].rename(
    columns={'Term': 'GO Term'}
).to_excel(f"{outdir}/go_molecular_function.xlsx", index=False)

# === 12. Molecular Docking ===
docking = pd.read_csv("results/tables/docking_results.csv")
docking.columns = ['Target Protein', 'Active Compound', 'Binding Energy (kcal/mol)']
docking['Binding Strength'] = docking['Binding Energy (kcal/mol)'].apply(
    lambda x: 'Strong' if x <= -7.0 else ('Good' if x <= -5.0 else 'Weak')
)
docking = docking.sort_values('Binding Energy (kcal/mol)')
docking.to_excel(f"{outdir}/molecular_docking.xlsx", index=False)

# === 13. PPI Edges (for Cytoscape) ===
edges = pd.read_csv("results/tables/ppi_edges.csv")
edges.columns = ['Source', 'Target', 'STRING Score']
edges.to_excel(f"{outdir}/ppi_edges.xlsx", index=False)

# Summary
print("Individual Excel files created in results/tables/:")
import glob
for f in sorted(glob.glob(f"{outdir}/*.xlsx")):
    name = os.path.basename(f)
    df = pd.read_excel(f)
    size = os.path.getsize(f) / 1024
    print(f"  {name:45s} {df.shape[0]:>5d} rows x {df.shape[1]:>2d} cols  ({size:.0f} KB)")
