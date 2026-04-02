#!/usr/bin/env python3
"""
Stage 4: Intersection Analysis & Venn Diagram
Intersect drug targets with disease targets, generate Venn diagram.
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
import os

os.makedirs("results/figures", exist_ok=True)
os.makedirs("results/tables", exist_ok=True)

# Load data
drug_targets = pd.read_csv("data/targets/drug_targets.csv")
disease_targets = pd.read_csv("data/targets/disease_targets.csv")

drug_genes = set(drug_targets['gene_symbol'].unique())
print(f"Drug target genes: {len(drug_genes)}")

# Disease gene sets
insomnia_genes = set(disease_targets[disease_targets['disease_key'] == 'insomnia']['gene_symbol'].unique())
alzheimer_genes = set(disease_targets[disease_targets['disease_key'] == 'alzheimer']['gene_symbol'].unique())
anxiety_genes = set(disease_targets[disease_targets['disease_key'] == 'anxiety']['gene_symbol'].unique())
all_disease_genes = insomnia_genes | alzheimer_genes | anxiety_genes

print(f"Insomnia genes: {len(insomnia_genes)}")
print(f"Alzheimer genes: {len(alzheimer_genes)}")
print(f"Anxiety genes: {len(anxiety_genes)}")
print(f"All disease genes (union): {len(all_disease_genes)}")

# Intersection
common_genes = drug_genes & all_disease_genes
print(f"\n=== Common targets (drug ∩ disease): {len(common_genes)} ===")

# Per-disease intersection
insomnia_common = drug_genes & insomnia_genes
alzheimer_common = drug_genes & alzheimer_genes
anxiety_common = drug_genes & anxiety_genes

print(f"Drug ∩ Insomnia: {len(insomnia_common)}")
print(f"Drug ∩ Alzheimer: {len(alzheimer_common)}")
print(f"Drug ∩ Anxiety: {len(anxiety_common)}")

# Save common targets
common_df = pd.DataFrame({"gene_symbol": sorted(common_genes)})
common_df.to_csv("data/targets/common_targets.csv", index=False)
print(f"\nSaved {len(common_df)} common targets to data/targets/common_targets.csv")

# Save per-disease common targets
for name, genes in [("insomnia", insomnia_common), ("alzheimer", alzheimer_common), ("anxiety", anxiety_common)]:
    pd.DataFrame({"gene_symbol": sorted(genes)}).to_csv(
        f"data/targets/common_targets_{name}.csv", index=False
    )

# === Figure 1: Venn diagram - Drug targets vs All disease targets ===
fig, ax = plt.subplots(figsize=(8, 6))
v = venn2([drug_genes, all_disease_genes], set_labels=('Drug Targets', 'Disease Targets'), ax=ax)
# Style
for text in v.set_labels:
    text.set_fontsize(14)
    text.set_fontweight('bold')
for text in v.subset_labels:
    if text:
        text.set_fontsize(12)
ax.set_title('Intersection of Drug Targets and Disease Targets', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig("results/figures/venn_drug_disease.png", dpi=300, bbox_inches='tight')
plt.savefig("results/figures/venn_drug_disease.pdf", bbox_inches='tight')
print("Saved: results/figures/venn_drug_disease.png")

# === Figure 2: Venn diagram - Drug targets vs 3 individual diseases ===
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for ax, (name, disease_set, label) in zip(axes, [
    ("insomnia", insomnia_genes, "Insomnia"),
    ("alzheimer", alzheimer_genes, "Alzheimer's Disease"),
    ("anxiety", anxiety_genes, "Anxiety Disorder"),
]):
    v = venn2([drug_genes, disease_set], set_labels=('Drug', label), ax=ax)
    for text in v.set_labels:
        text.set_fontsize(11)
        text.set_fontweight('bold')
    for text in v.subset_labels:
        if text:
            text.set_fontsize(10)
    ax.set_title(f'Drug ∩ {label}', fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig("results/figures/venn_per_disease.png", dpi=300, bbox_inches='tight')
plt.savefig("results/figures/venn_per_disease.pdf", bbox_inches='tight')
print("Saved: results/figures/venn_per_disease.png")

# === Figure 3: 3-way Venn of disease intersections ===
fig, ax = plt.subplots(figsize=(8, 8))
v3 = venn3(
    [insomnia_common, alzheimer_common, anxiety_common],
    set_labels=('Insomnia', "Alzheimer's", 'Anxiety'),
    ax=ax
)
for text in v3.set_labels:
    text.set_fontsize(13)
    text.set_fontweight('bold')
for text in v3.subset_labels:
    if text:
        text.set_fontsize(11)
ax.set_title('Common Drug-Disease Targets Across Three Diseases', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("results/figures/venn_three_diseases.png", dpi=300, bbox_inches='tight')
plt.savefig("results/figures/venn_three_diseases.pdf", bbox_inches='tight')
print("Saved: results/figures/venn_three_diseases.png")

# Print common target list
print(f"\n=== All {len(common_genes)} common targets ===")
for g in sorted(common_genes):
    in_ins = "✓" if g in insomnia_common else " "
    in_alz = "✓" if g in alzheimer_common else " "
    in_anx = "✓" if g in anxiety_common else " "
    print(f"  {g:12s} Insomnia:{in_ins} Alzheimer:{in_alz} Anxiety:{in_anx}")
