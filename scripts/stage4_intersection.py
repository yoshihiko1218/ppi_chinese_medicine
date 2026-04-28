#!/usr/bin/env python3
"""
Stage 4: Intersection Analysis & Venn Diagrams (config-driven).

For N diseases in the config:
  * Always produces a 2-way Venn of drug targets vs. all-disease-targets union
  * Produces a grid of per-disease 2-way Venns
  * If N == 2 or N == 3, produces an N-way Venn of drug∩disease sets
"""
import os
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_config as PC

os.makedirs("results/figures", exist_ok=True)
os.makedirs("results/tables", exist_ok=True)
os.makedirs("data/targets", exist_ok=True)

# Load data
drug_targets = pd.read_csv("data/targets/drug_targets.csv")
disease_targets = pd.read_csv("data/targets/disease_targets.csv")

drug_genes = set(drug_targets["gene_symbol"].dropna().unique())
print(f"Drug target genes: {len(drug_genes)}")

# Build per-disease gene sets in config order
disease_sets = {}
for key, meta in PC.DISEASES.items():
    g = set(
        disease_targets[disease_targets["disease_key"] == key]["gene_symbol"]
        .dropna()
        .unique()
    )
    disease_sets[key] = (meta["name"], g)
    print(f"  {meta['name']:35s} genes: {len(g)}")

all_disease_genes = set()
for _, (_, g) in disease_sets.items():
    all_disease_genes |= g
print(f"All disease genes (union): {len(all_disease_genes)}")

# Intersection
common_genes = drug_genes & all_disease_genes
print(f"\n=== Common targets (drug ∩ disease): {len(common_genes)} ===")

# Per-disease intersection
per_disease_common = {k: drug_genes & g for k, (_, g) in disease_sets.items()}
for k, s in per_disease_common.items():
    print(f"Drug ∩ {disease_sets[k][0]}: {len(s)}")

# Save common targets
common_df = pd.DataFrame({"gene_symbol": sorted(common_genes)})
common_df.to_csv("data/targets/common_targets.csv", index=False)
print(f"\nSaved {len(common_df)} common targets to data/targets/common_targets.csv")

for k, s in per_disease_common.items():
    pd.DataFrame({"gene_symbol": sorted(s)}).to_csv(
        f"data/targets/common_targets_{k}.csv", index=False
    )

# === Figure 1: Venn diagram - Drug vs All disease targets ===
fig, ax = plt.subplots(figsize=(8, 6))
v = venn2([drug_genes, all_disease_genes],
          set_labels=("Drug Targets", "Disease Targets"), ax=ax)
for text in v.set_labels:
    if text:
        text.set_fontsize(14); text.set_fontweight("bold")
for text in v.subset_labels:
    if text:
        text.set_fontsize(12)
ax.set_title("Intersection of Drug Targets and Disease Targets",
             fontsize=16, fontweight="bold")
plt.tight_layout()
plt.savefig("results/figures/venn_drug_disease.png", dpi=300, bbox_inches="tight")
plt.savefig("results/figures/venn_drug_disease.pdf", bbox_inches="tight")
print("Saved: results/figures/venn_drug_disease.png")

# === Figure 2: Per-disease 2-way Venns ===
n = len(disease_sets)
fig, axes = plt.subplots(1, n, figsize=(6 * n, 6), squeeze=False)
axes = axes[0]
for ax, (key, (label, dset)) in zip(axes, disease_sets.items()):
    v = venn2([drug_genes, dset], set_labels=("Drug", label), ax=ax)
    for text in v.set_labels:
        if text:
            text.set_fontsize(11); text.set_fontweight("bold")
    for text in v.subset_labels:
        if text:
            text.set_fontsize(10)
    ax.set_title(f"Drug ∩ {label}", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("results/figures/venn_per_disease.png", dpi=300, bbox_inches="tight")
plt.savefig("results/figures/venn_per_disease.pdf", bbox_inches="tight")
print("Saved: results/figures/venn_per_disease.png")

# === Figure 3: N-way Venn of drug∩disease sets, if N in {2,3} ===
sets_list = list(per_disease_common.values())
labels_list = [disease_sets[k][0] for k in per_disease_common.keys()]

if n == 3:
    fig, ax = plt.subplots(figsize=(8, 8))
    v3 = venn3(sets_list, set_labels=tuple(labels_list), ax=ax)
    for text in v3.set_labels:
        if text:
            text.set_fontsize(13); text.set_fontweight("bold")
    for text in v3.subset_labels:
        if text:
            text.set_fontsize(11)
    ax.set_title("Common Drug-Disease Targets Across Three Diseases",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig("results/figures/venn_three_diseases.png", dpi=300, bbox_inches="tight")
    plt.savefig("results/figures/venn_three_diseases.pdf", bbox_inches="tight")
    print("Saved: results/figures/venn_three_diseases.png")
elif n == 2:
    fig, ax = plt.subplots(figsize=(8, 6))
    v = venn2(sets_list, set_labels=tuple(labels_list), ax=ax)
    for text in v.set_labels:
        if text:
            text.set_fontsize(13); text.set_fontweight("bold")
    ax.set_title("Common Drug-Disease Targets", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig("results/figures/venn_two_diseases.png", dpi=300, bbox_inches="tight")
    plt.savefig("results/figures/venn_two_diseases.pdf", bbox_inches="tight")
    print("Saved: results/figures/venn_two_diseases.png")
else:
    print(f"(Skipping N-way Venn: N={n} diseases not in {{2,3}})")

# Summary table
print(f"\n=== All {len(common_genes)} common targets ===")
keys = list(per_disease_common.keys())
header = "gene         " + " ".join(f"{disease_sets[k][0][:15]:15s}" for k in keys)
print(header)
for g in sorted(common_genes):
    row = f"{g:12s} " + " ".join(
        f"{('✓' if g in per_disease_common[k] else ' '):15s}" for k in keys
    )
    print(row)
