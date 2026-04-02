#!/usr/bin/env python3
"""
Stage 6: GO & KEGG Enrichment Analysis
Using gseapy's Enrichr wrapper for GO and KEGG pathway enrichment.
"""
import pandas as pd
import gseapy as gp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

os.makedirs("results/figures", exist_ok=True)
os.makedirs("data/enrichment", exist_ok=True)

# Load common targets
common = pd.read_csv("data/targets/common_targets.csv")
genes = common['gene_symbol'].tolist()
print(f"Genes for enrichment: {len(genes)}")

# === GO Enrichment ===
print("\n=== GO Enrichment Analysis ===")
go_results = {}
for go_lib in ['GO_Biological_Process_2023', 'GO_Cellular_Component_2023', 'GO_Molecular_Function_2023']:
    print(f"  Querying {go_lib}...")
    try:
        enr = gp.enrichr(gene_list=genes,
                         gene_sets=go_lib,
                         organism='human',
                         outdir=None,
                         no_plot=True)
        df = enr.results
        df_sig = df[df['Adjusted P-value'] < 0.05].copy()
        go_results[go_lib] = df_sig
        print(f"  {go_lib}: {len(df_sig)} significant terms (P.adj < 0.05)")
        df_sig.to_csv(f"data/enrichment/{go_lib}.csv", index=False)
    except Exception as e:
        print(f"  Error: {e}")

# === KEGG Enrichment ===
print("\n=== KEGG Enrichment Analysis ===")
try:
    enr_kegg = gp.enrichr(gene_list=genes,
                          gene_sets='KEGG_2021_Human',
                          organism='human',
                          outdir=None,
                          no_plot=True)
    kegg_df = enr_kegg.results
    kegg_sig = kegg_df[kegg_df['Adjusted P-value'] < 0.05].copy()
    kegg_sig.to_csv("data/enrichment/KEGG_2021_Human.csv", index=False)
    print(f"KEGG significant pathways: {len(kegg_sig)}")
except Exception as e:
    print(f"KEGG error: {e}")
    kegg_sig = pd.DataFrame()

# === Visualization ===
# 1. GO Bar Plot (top 10 per category)
fig, axes = plt.subplots(1, 3, figsize=(24, 8))
go_labels = {
    'GO_Biological_Process_2023': ('Biological Process', '#e74c3c'),
    'GO_Cellular_Component_2023': ('Cellular Component', '#2ecc71'),
    'GO_Molecular_Function_2023': ('Molecular Function', '#3498db'),
}

for ax, (lib, (label, color)) in zip(axes, go_labels.items()):
    if lib in go_results and len(go_results[lib]) > 0:
        df = go_results[lib].head(10).copy()
        df['Term_short'] = df['Term'].apply(lambda x: x[:50] + '...' if len(x) > 50 else x)
        df = df.iloc[::-1]  # Reverse for horizontal bar
        ax.barh(df['Term_short'], -np.log10(df['Adjusted P-value']), color=color, alpha=0.8)
        ax.set_xlabel('-log10(Adjusted P-value)', fontsize=12)
        ax.set_title(f'GO {label}\n(Top 10)', fontsize=13, fontweight='bold')
        ax.tick_params(axis='y', labelsize=9)
    else:
        ax.text(0.5, 0.5, 'No significant terms', ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f'GO {label}', fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig("results/figures/go_barplot.png", dpi=300, bbox_inches='tight')
plt.savefig("results/figures/go_barplot.pdf", bbox_inches='tight')
print("Saved: results/figures/go_barplot.png")

# 2. KEGG Bubble Plot (top 20)
if len(kegg_sig) > 0:
    fig, ax = plt.subplots(figsize=(10, 8))
    top_kegg = kegg_sig.head(20).copy()
    top_kegg['Term_short'] = top_kegg['Term'].apply(lambda x: x[:45] + '...' if len(x) > 45 else x)
    top_kegg['Gene_count'] = top_kegg['Overlap'].apply(lambda x: int(x.split('/')[0]))
    top_kegg['Gene_ratio'] = top_kegg['Overlap'].apply(lambda x: int(x.split('/')[0]) / int(x.split('/')[1]))
    top_kegg = top_kegg.iloc[::-1]

    scatter = ax.scatter(
        top_kegg['Gene_ratio'],
        range(len(top_kegg)),
        s=top_kegg['Gene_count'] * 50,
        c=-np.log10(top_kegg['Adjusted P-value']),
        cmap='RdYlBu_r',
        alpha=0.8,
        edgecolors='gray',
        linewidth=0.5,
    )
    ax.set_yticks(range(len(top_kegg)))
    ax.set_yticklabels(top_kegg['Term_short'], fontsize=10)
    ax.set_xlabel('Gene Ratio', fontsize=12)
    ax.set_title('KEGG Pathway Enrichment (Top 20)', fontsize=14, fontweight='bold')

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.6)
    cbar.set_label('-log10(Adjusted P-value)', fontsize=11)

    # Size legend
    for s in [3, 6, 9]:
        ax.scatter([], [], s=s*50, c='gray', alpha=0.5, label=f'{s} genes')
    ax.legend(title='Gene count', loc='lower right', fontsize=9)

    plt.tight_layout()
    plt.savefig("results/figures/kegg_bubble.png", dpi=300, bbox_inches='tight')
    plt.savefig("results/figures/kegg_bubble.pdf", bbox_inches='tight')
    print("Saved: results/figures/kegg_bubble.png")

    # Print top KEGG pathways
    print("\n=== Top 20 KEGG Pathways ===")
    for _, row in kegg_sig.head(20).iterrows():
        print(f"  {row['Term'][:50]:50s} P.adj={row['Adjusted P-value']:.2e} Genes={row['Overlap']}")

print("\nDone!")
