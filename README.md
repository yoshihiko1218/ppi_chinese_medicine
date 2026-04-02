# Network Pharmacology Analysis: 健脑安神 Formula

## Overview
Network pharmacology analysis of a 14-herb 健脑安神 (brain-nourishing, mind-calming) formula targeting Insomnia, Alzheimer's Disease, and Anxiety Disorder. Methodology follows the approach in 张松菊's thesis on QJHWF.

## Formula Composition (14 herbs)
| Herb (Chinese) | Pinyin | Dose | Latin Name |
|---|---|---|---|
| 酸枣仁 | Suanzaoren | 10g | Ziziphi Spinosae Semen |
| 核桃仁 | Hetaoren | 10g | Juglandis Semen |
| 黄精 | Huangjing | 15g | Polygonati Rhizoma |
| 枸杞子 | Gouqizi | 12g | Lycii Fructus |
| 桑葚 | Sangshen | 12g | Mori Fructus |
| 当归 | Danggui | 6g | Angelicae Sinensis Radix |
| 龙眼肉 | Longyanrou | 10g | Arillus Longan |
| 茯苓 | Fuling | 12g | Poria Cocos |
| 莲子 | Lianzi | 12g | Nelumbinis Semen |
| 百合 | Baihe | 12g | Lilii Bulbus |
| 益智仁 | Yizhiren | 6g | Alpiniae Oxyphyliae Fructus |
| 五味子 | Wuweizi | 6g | Schisandrae Chinensis Fructus |
| 天麻 | Tianma | 6g | Gastrodiae Rhizoma |
| 山药 | Shanyao | 15g | Rhizoma Dioscoreae |

## Pipeline Results Summary

| Stage | Result |
|---|---|
| 1. Active compounds | 124 unique compounds (OB>=30%, DL>=0.18), 113 with SMILES |
| 2. Drug targets | 197 unique gene targets |
| 3. Disease targets | 1,483 genes (Insomnia: 514, AD: 695, Anxiety: 500) |
| 4. Intersection | **55 common drug-disease targets** |
| 5. PPI network | 54 nodes, 346 edges, 27 core hub targets |
| 6. GO/KEGG enrichment | 311 GO-BP, 147 KEGG pathways (P.adj < 0.05) |
| 7. Molecular docking | Top binding: quercetin-EGFR (-7.3 kcal/mol) |

## Top 10 Core Targets (by PPI Degree)
PTGS2, IL6, ESR1, EGFR, TP53, NR3C1, MAOA, SLC6A4, DRD2, GSK3B

## Key KEGG Pathways
1. Neuroactive ligand-receptor interaction (P=4.58e-15)
2. cGMP-PKG signaling pathway (P=1.38e-09)
3. Dopaminergic synapse (P=2.62e-09)
4. Calcium signaling pathway (P=1.53e-09)
5. PI3K-Akt signaling pathway (P=6.61e-07)
6. Serotonergic synapse (P=4.65e-07)

## Directory Structure
```
ppi/
├── data/
│   ├── compounds/          # TCMSP compound data per herb + filtered compounds
│   ├── targets/            # Drug targets, disease targets, common targets
│   └── enrichment/         # GO and KEGG enrichment results
├── scripts/
│   ├── stage1_scrape_all.py         # TCMSP scraping for all herbs
│   ├── stage1_supplement_missing.py # Supplement 龙眼肉, 天麻 compounds
│   ├── stage1_get_smiles.py         # PubChem SMILES retrieval
│   ├── stage2_targets.py            # Drug target prediction via TCMSP + UniProt
│   ├── stage2_supplement_targets.py # Supplement targets for missing herbs
│   ├── stage3_disease_targets.py    # Disease target collection (OpenTargets + NCBI)
│   ├── stage4_intersection.py       # Venn diagram intersection analysis
│   ├── stage5_ppi_network.py        # STRING PPI + NetworkX topology
│   ├── stage6_enrichment.py         # GO & KEGG enrichment (gseapy)
│   └── stage7_docking.py            # AutoDock Vina molecular docking
├── results/
│   ├── figures/
│   │   ├── venn_drug_disease.png    # Drug vs disease Venn diagram
│   │   ├── venn_per_disease.png     # Per-disease Venn diagrams
│   │   ├── venn_three_diseases.png  # 3-way disease Venn
│   │   ├── ppi_network.png          # Full PPI network
│   │   ├── ppi_core_network.png     # Core hub network
│   │   ├── go_barplot.png           # GO enrichment bar plot
│   │   ├── kegg_bubble.png          # KEGG bubble plot
│   │   └── docking_heatmap.png      # Docking binding energy heatmap
│   ├── tables/
│   │   ├── ppi_topology.csv         # PPI node topology metrics
│   │   ├── core_targets.csv         # Core hub targets
│   │   ├── ppi_edges.csv            # PPI edges (Cytoscape-compatible)
│   │   └── docking_results.csv      # Docking binding energies
│   └── docking/                     # PDB/PDBQT files for docking
├── TCMSP-Spider/                    # Cloned TCMSP scraping tool
└── 张松菊毕业论文3.23(1).doc         # Reference thesis
```

## Environment
- Conda environment: `ppi` (Python 3.10)
- Key packages: pandas, requests, beautifulsoup4, networkx, gseapy, matplotlib, seaborn, matplotlib-venn, openbabel, autodock-vina, pymol-open-source

## Data Sources
- **TCMSP**: Active compounds (OB, DL) and drug targets
- **PubChem**: SMILES structures
- **UniProt**: Gene symbol standardization
- **Open Targets Platform**: Disease-associated genes
- **NCBI Gene**: Supplementary disease genes
- **STRING**: Protein-protein interaction network
- **Enrichr (via gseapy)**: GO and KEGG enrichment
- **RCSB PDB**: Receptor 3D structures
- **AutoDock Vina**: Molecular docking

## How to Reproduce
```bash
conda activate ppi
# Run stages in order:
python scripts/stage1_scrape_all.py
python scripts/stage1_supplement_missing.py
python scripts/stage1_get_smiles.py
python scripts/stage2_targets.py
python scripts/stage2_supplement_targets.py
python scripts/stage3_disease_targets.py
python scripts/stage4_intersection.py
python scripts/stage5_ppi_network.py
python scripts/stage6_enrichment.py
python scripts/stage7_docking.py
```
