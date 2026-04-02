#!/usr/bin/env python3
"""
Create a comprehensive Excel workbook with all results across multiple sheets.
"""
import pandas as pd
import os

writer = pd.ExcelWriter("results/tables/network_pharmacology_results.xlsx", engine="openpyxl")

# === Sheet 1: Active Compounds ===
compounds = pd.read_csv("data/compounds/compounds_filtered_all.csv")
compounds_clean = compounds[[
    'MOL_ID', 'molecule_name', 'molecule_name_cn', 'ob', 'dl', 'mw',
    'herb_cn', 'herb_pinyin', 'SMILES', 'PubChem_CID'
]].copy()
compounds_clean.columns = [
    'MOL_ID', 'Compound (English)', 'Compound (Chinese)', 'OB (%)', 'DL',
    'Molecular Weight', 'Herb (Chinese)', 'Herb (Pinyin)', 'SMILES', 'PubChem CID'
]
compounds_clean.to_excel(writer, sheet_name="Active Compounds", index=False)

# === Sheet 2: Unique Compounds Summary ===
unique = compounds_clean.drop_duplicates(subset='MOL_ID').copy()
# Add herb sources as comma-separated
herb_sources = compounds_clean.groupby('MOL_ID')['Herb (Chinese)'].apply(
    lambda x: ', '.join(sorted(set(x)))
).reset_index()
herb_sources.columns = ['MOL_ID', 'Source Herbs']
unique = unique.drop(columns=['Herb (Chinese)', 'Herb (Pinyin)']).merge(herb_sources, on='MOL_ID')
unique = unique.sort_values('OB (%)', ascending=False)
unique.to_excel(writer, sheet_name="Unique Compounds", index=False)

# === Sheet 3: Drug Targets ===
drug_targets = pd.read_csv("data/targets/drug_targets.csv")
dt_clean = drug_targets[[
    'MOL_ID', 'molecule_name', 'gene_symbol', 'uniprot_id',
    'target_name', 'herb_cn', 'herb_pinyin'
]].copy()
dt_clean.columns = [
    'MOL_ID', 'Compound', 'Gene Symbol', 'UniProt ID',
    'Target Protein', 'Herb (Chinese)', 'Herb (Pinyin)'
]
dt_clean.to_excel(writer, sheet_name="Drug Targets", index=False)

# === Sheet 4: Disease Targets ===
disease_targets = pd.read_csv("data/targets/disease_targets.csv")
dis_clean = disease_targets[[
    'gene_symbol', 'disease', 'source', 'score'
]].copy()
dis_clean.columns = ['Gene Symbol', 'Disease', 'Source Database', 'Association Score']
dis_clean.to_excel(writer, sheet_name="Disease Targets", index=False)

# === Sheet 5: Common Targets (55) ===
common = pd.read_csv("data/targets/common_targets.csv")
# Enrich with disease info
insomnia = set(pd.read_csv("data/targets/common_targets_insomnia.csv")['gene_symbol'])
alzheimer = set(pd.read_csv("data/targets/common_targets_alzheimer.csv")['gene_symbol'])
anxiety = set(pd.read_csv("data/targets/common_targets_anxiety.csv")['gene_symbol'])

common_enriched = common.copy()
common_enriched['Insomnia'] = common_enriched['gene_symbol'].apply(lambda x: 'Yes' if x in insomnia else '')
common_enriched["Alzheimer's"] = common_enriched['gene_symbol'].apply(lambda x: 'Yes' if x in alzheimer else '')
common_enriched['Anxiety'] = common_enriched['gene_symbol'].apply(lambda x: 'Yes' if x in anxiety else '')

# Add compound sources
gene_compounds = drug_targets.groupby('gene_symbol')['molecule_name'].apply(
    lambda x: ', '.join(sorted(set(x)))
).reset_index()
gene_compounds.columns = ['gene_symbol', 'Active Compounds']

gene_herbs = drug_targets.groupby('gene_symbol')['herb_cn'].apply(
    lambda x: ', '.join(sorted(set(x)))
).reset_index()
gene_herbs.columns = ['gene_symbol', 'Source Herbs']

common_enriched = common_enriched.merge(gene_compounds, on='gene_symbol', how='left')
common_enriched = common_enriched.merge(gene_herbs, on='gene_symbol', how='left')
common_enriched.columns = ['Gene Symbol', 'Insomnia', "Alzheimer's", 'Anxiety', 'Active Compounds', 'Source Herbs']
common_enriched.to_excel(writer, sheet_name="Common Targets (55)", index=False)

# === Sheet 6: PPI Topology ===
ppi = pd.read_csv("results/tables/ppi_topology.csv")
ppi.columns = ['Gene Symbol', 'Degree', 'Betweenness Centrality', 'Closeness Centrality']
ppi['Core Target'] = ppi['Degree'].apply(lambda x: 'Yes' if x >= 12.5 else '')
ppi.to_excel(writer, sheet_name="PPI Topology", index=False)

# === Sheet 7: KEGG Pathways ===
kegg = pd.read_csv("data/enrichment/KEGG_2021_Human.csv")
kegg_clean = kegg[['Term', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']].copy()
kegg_clean.columns = ['Pathway', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']
kegg_clean.to_excel(writer, sheet_name="KEGG Pathways", index=False)

# === Sheet 8: GO Biological Process ===
go_bp = pd.read_csv("data/enrichment/GO_Biological_Process_2023.csv")
go_bp_clean = go_bp[['Term', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']].copy()
go_bp_clean.columns = ['GO Term', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']
go_bp_clean.to_excel(writer, sheet_name="GO Biological Process", index=False)

# === Sheet 9: GO Molecular Function ===
go_mf = pd.read_csv("data/enrichment/GO_Molecular_Function_2023.csv")
go_mf_clean = go_mf[['Term', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']].copy()
go_mf_clean.columns = ['GO Term', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']
go_mf_clean.to_excel(writer, sheet_name="GO Molecular Function", index=False)

# === Sheet 10: Molecular Docking ===
docking = pd.read_csv("results/tables/docking_results.csv")
docking.columns = ['Target Protein', 'Active Compound', 'Binding Energy (kcal/mol)']
docking['Binding Strength'] = docking['Binding Energy (kcal/mol)'].apply(
    lambda x: 'Strong' if x <= -7.0 else ('Good' if x <= -5.0 else 'Weak')
)
docking = docking.sort_values('Binding Energy (kcal/mol)')
docking.to_excel(writer, sheet_name="Molecular Docking", index=False)

writer.close()

# Check file
fsize = os.path.getsize("results/tables/network_pharmacology_results.xlsx")
print(f"Saved: results/tables/network_pharmacology_results.xlsx ({fsize/1024:.0f} KB)")
print(f"\nSheets:")
xls = pd.ExcelFile("results/tables/network_pharmacology_results.xlsx")
for sheet in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet)
    print(f"  {sheet}: {df.shape[0]} rows x {df.shape[1]} columns")
