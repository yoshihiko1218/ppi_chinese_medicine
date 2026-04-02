# Network Pharmacology Study of a 健脑安神 (Brain-Nourishing, Mind-Calming) Formula

## Complete Methods and Results Documentation

---

## 1. Active Compound Screening

### 1.1 TCMSP Database Search

**Platform:** TCMSP (Traditional Chinese Medicine Systems Pharmacology Database and Analysis Platform), https://www.tcmsp-e.com/

**Method:** Searched TCMSP for each of the 14 herbs in the formula by their Latin (English) names. For each herb, retrieved all registered chemical ingredients along with their pharmacokinetic properties.

**Herbs searched (14 total):**

| Herb (Chinese) | Search Name in TCMSP | Raw Compounds |
|---|---|---|
| 酸枣仁 | Ziziphi Spinosae Semen | 33 |
| 核桃仁 | Juglandis Semen | 42 |
| 黄精 | Polygonati Rhizoma | 38 |
| 枸杞子 | Lycii Fructus | 188 |
| 桑葚 | Mori Fructus | 91 |
| 当归 | Angelicae Sinensis Radix | 125 |
| 茯苓 | Poria Cocos(Schw.) Wolf. | 34 |
| 莲子 | Nelumbinis Plumula | 31 |
| 百合 | Lilii Bulbus | 84 |
| 益智仁 | Alpiniae Oxyphyliae Fructus | 41 |
| 五味子 | Schisandrae Chinensis Fructus | 130 |
| 山药 | Rhizoma Dioscoreae | 71 |
| 龙眼肉 | *Not in TCMSP — supplemented from literature* | 10 (supplemented) |
| 天麻 | *Not in TCMSP — supplemented from literature* | 11 (supplemented) |

**Note:** 龙眼肉 (Longan Arillus) and 天麻 (Gastrodiae Rhizoma) were not registered in the TCMSP database. Their active compounds were supplemented from published network pharmacology literature. Known active compounds include Gallic acid, Ellagic acid, Quercetin, Kaempferol, beta-Sitosterol, Corilagin (for 龙眼肉) and Gastrodin, Vanillin, 4-Hydroxybenzyl alcohol, Parishin A/B/C, beta-Sitosterol, Daucosterol, Succinic acid (for 天麻).

**Total raw compounds retrieved:** 908 entries (812 unique by MOL_ID)

### 1.2 Compound Filtering

**Filtering criteria (same as reference thesis):**
- Oral Bioavailability (OB) ≥ 30%
- Drug-Likeness (DL) ≥ 0.18

For TCMSP-sourced herbs (12 herbs), the strict OB ≥ 30% and DL ≥ 0.18 filter was applied. For supplementary herbs (龙眼肉, 天麻), a relaxed filter of OB ≥ 30% was used because many of their key bioactive compounds (e.g., Gastrodin, DL=0.06) are small molecules with well-documented pharmacological activity but low DL values.

**Result after filtering:** 160 compound-herb entries, corresponding to **145 unique compounds** across all 14 herbs.

**Per-herb filtered compound count:**

| Herb | Filtered Compounds |
|---|---|
| 枸杞子 | 45 |
| 山药 | 16 |
| 茯苓 | 15 |
| 黄精 | 12 |
| 莲子 | 11 |
| 天麻 | 11 |
| 龙眼肉 | 10 |
| 酸枣仁 | 9 |
| 五味子 | 8 |
| 百合 | 7 |
| 桑葚 | 6 |
| 核桃仁 | 4 |
| 益智仁 | 4 |
| 当归 | 2 |

### 1.3 SMILES Retrieval

**Platform:** PubChem (https://pubchem.ncbi.nlm.nih.gov/), accessed via PUG REST API

**Method:** For each unique compound, queried PubChem by compound name to retrieve the Canonical SMILES (Simplified Molecular Input Line Entry System) notation and PubChem CID.

**Result:** 113 out of 145 unique compounds (78%) successfully matched to PubChem entries with valid SMILES. The 30 unmatched compounds were mostly obscure sterols and complex glycosides with non-standard naming.

**Output files:**
- `data/compounds/compounds_filtered_all.csv` — All filtered compounds with SMILES
- `data/compounds/smiles_lookup.csv` — SMILES lookup table

---

## 2. Drug Target Prediction

### 2.1 TCMSP Target Retrieval

**Platform:** TCMSP (https://www.tcmsp-e.com/)

**Method:** For each herb page in TCMSP, retrieved the compound-target interaction data (grid2 data). TCMSP provides predicted and validated targets for each compound, including target name, DrugBank ID, and prediction scores (SVM_score, RF_score).

**Result:** 4,000 total compound-target entries from 12 TCMSP-registered herbs. After filtering for only our selected active compounds: **851 entries** involving **249 unique target names**.

### 2.2 Target Supplementation for Missing Herbs

For 龙眼肉 and 天麻, targets were obtained by:
1. Matching shared compounds (e.g., Quercetin, beta-Sitosterol, Ellagic acid) to their TCMSP target data from other herbs
2. UniProt protein database search for remaining unique compounds

**Result:** 541 supplementary target entries added for 龙眼肉 and 天麻.

### 2.3 Gene Symbol Standardization

**Platform:** UniProt (https://rest.uniprot.org/), REST API

**Method:** Each target protein name was queried against UniProt (species: Homo sapiens, organism_id: 9606) to obtain the standardized HGNC gene symbol and UniProt accession ID.

**Parameters:**
- Query: `protein_name:"[target name]" AND organism_id:9606`
- Format: JSON
- Fields: gene_primary, protein_name, accession

**Result:** 173 out of 249 TCMSP target names (69.5%) were successfully mapped to standard gene symbols. After mapping supplementary targets, the final dataset contains:
- **980 compound-target entries**
- **197 unique gene symbols**

**Per-herb target counts:**

| Herb | Unique Gene Targets |
|---|---|
| 莲子 | 143 |
| 枸杞子 | 129 |
| 龙眼肉 | 125 |
| 桑葚 | 108 |
| 黄精 | 63 |
| 天麻 | 57 |
| 百合 | 43 |
| 当归 | 39 |
| 山药 | 32 |
| 酸枣仁 | 26 |
| 益智仁 | 23 |
| 核桃仁 | 16 |
| 茯苓 | 15 |
| 五味子 | 12 |

**Output files:**
- `data/targets/drug_targets.csv` — Full drug target data with gene symbols
- `data/targets/drug_target_genes.csv` — Unique gene symbol list

---

## 3. Disease Target Collection

### 3.1 Databases Used

**Platform 1:** Open Targets Platform (https://platform.opentargets.org/), GraphQL API

**Method:** For each disease, queried the Open Targets GraphQL API to:
1. Search for the disease entity ID (EFO/MONDO ontology)
2. Retrieve the top 500 associated target genes ranked by overall association score

**Parameters:**
- Disease search: `queryString: "[disease name]"`, entityNames: ["disease"]
- Target retrieval: `page: {size: 500, index: 0}`

**Disease IDs resolved:**
- Insomnia → EFO_0004698
- Alzheimer's disease → MONDO_0004975
- Anxiety disorder → EFO_0006788

**Platform 2:** NCBI Gene (https://eutils.ncbi.nlm.nih.gov/), E-utilities API

**Method:** Searched NCBI Gene database using the Disease/Phenotype field for each disease name, limited to Homo sapiens.

**Parameters:**
- Database: gene
- Term: `"[disease name]"[Disease/Phenotype] AND Homo sapiens[Organism]`
- retmax: 500

### 3.2 Results

| Disease | Open Targets | NCBI Gene | Total Unique |
|---|---|---|---|
| Insomnia | 500 | 19 | **514** |
| Alzheimer's disease | 500 | 227 | **695** |
| Anxiety disorder | 500 | 0 | **500** |
| **Union (all 3 diseases)** | | | **1,483** |

**Output files:**
- `data/targets/disease_targets.csv` — All disease targets with source and scores
- `data/targets/disease_targets_insomnia.csv` — Insomnia-specific gene list
- `data/targets/disease_targets_alzheimer.csv` — Alzheimer-specific gene list
- `data/targets/disease_targets_anxiety.csv` — Anxiety-specific gene list

---

## 4. Intersection Analysis & Venn Diagram

### 4.1 Method

Drug target genes (197) were intersected with the union of all disease target genes (1,483) to identify common drug-disease targets. Additional per-disease intersections were computed.

**Tool:** Python (matplotlib-venn package)

### 4.2 Results

| Intersection | Count |
|---|---|
| Drug ∩ All diseases | **55** |
| Drug ∩ Insomnia | 11 |
| Drug ∩ Alzheimer's disease | 32 |
| Drug ∩ Anxiety disorder | 34 |

**All 55 common targets:**
ACHE, ADCY2, ADRA1A, ADRA1B, ADRA1D, ADRA2A, ADRA2B, ADRA2C, ADRB1, ADRB2, ALDH5A1, BCHE, CAV1, CDC25B, CDK2, CDK4, CHRNA2, CRP, DCAF5, DRD1, DRD2, DRD3, DRD4, EGFR, ESR1, ESR2, FOSL1, GABRA6, GSK3B, HTR3A, IL10, IL2, IL6, MAOA, MAOB, MAPK14, ME2, MMP3, MPO, MTOR, NOS1, NR3C1, NUF2, OPRD1, OPRM1, PGR, PRKCA, PTGS1, PTGS2, RUNX1T1, SCN5A, SLC6A2, SLC6A4, TP53, VEGFA

### 4.3 Output Figures

| File | Description |
|---|---|
| **`results/figures/venn_drug_disease.pdf`** | Venn diagram: Drug targets (197) vs All disease targets (1,483), showing 55 overlapping targets |
| **`results/figures/venn_per_disease.pdf`** | Three panels showing Drug vs Insomnia (11), Drug vs Alzheimer (32), Drug vs Anxiety (34) |
| **`results/figures/venn_three_diseases.pdf`** | 3-way Venn of common targets distributed across the three diseases |

**Output data:**
- `data/targets/common_targets.csv` — List of 55 common targets

---

## 5. PPI Network Construction & Core Target Selection

### 5.1 STRING Database Query

**Platform:** STRING (Search Tool for the Retrieval of Interacting Genes/Proteins), https://string-db.org/, REST API v11

**Method:** The 55 common target genes were submitted to the STRING API to retrieve protein-protein interaction (PPI) data.

**Parameters:**
- API endpoint: `https://string-db.org/api/json/network`
- Species: 9606 (Homo sapiens)
- Minimum required interaction score: 400 (medium confidence, equivalent to 0.4)
- Isolated nodes (no interactions) were removed

### 5.2 Network Analysis

**Tool:** Python NetworkX library (mimicking Cytoscape CentiScaPe plugin)

**Topology metrics calculated:**
- **Degree** — Number of direct interaction partners
- **Betweenness centrality** — Fraction of shortest paths passing through a node
- **Closeness centrality** — Average inverse distance to all other nodes

**Core target selection:** Nodes with Degree ≥ median Degree (12.5) were classified as core hub targets.

### 5.3 Results

| Metric | Value |
|---|---|
| Total nodes | 54 (2 isolated nodes removed: DCAF5, VEGFA) |
| Total edges | 346 |
| Median Degree | 12.5 |
| Core targets (Degree ≥ 12.5) | **27** |

**Top 10 Core Targets:**

| Rank | Gene | Degree | Betweenness | Closeness |
|---|---|---|---|---|
| 1 | PTGS2 | 30 | 0.087 | 0.688 |
| 2 | IL6 | 30 | 0.082 | 0.697 |
| 3 | ESR1 | 28 | 0.098 | 0.679 |
| 4 | EGFR | 25 | 0.058 | 0.639 |
| 5 | TP53 | 24 | 0.069 | 0.596 |
| 6 | NR3C1 | 22 | 0.040 | 0.631 |
| 7 | MAOA | 21 | 0.054 | 0.609 |
| 8 | SLC6A4 | 21 | 0.057 | 0.609 |
| 9 | DRD2 | 20 | 0.056 | 0.602 |
| 10 | GSK3B | 20 | 0.025 | 0.602 |

### 5.4 Output Figures and Tables

| File | Description |
|---|---|
| **`results/figures/ppi_network.pdf`** | Full PPI network (54 nodes, 346 edges). Node size and color represent Degree. Labels shown for core targets only. |
| **`results/figures/ppi_core_network.pdf`** | Core hub PPI subnetwork (27 nodes). All nodes labeled. |
| `results/tables/ppi_topology.csv` | Full topology metrics (Degree, Betweenness, Closeness) for all 54 nodes |
| `results/tables/core_targets.csv` | Core target list (27 genes) with topology metrics |
| `results/tables/ppi_edges.csv` | Edge list with STRING confidence scores (Cytoscape-importable) |

---

## 6. GO & KEGG Enrichment Analysis

### 6.1 Method

**Platform:** Enrichr (https://maayanlab.cloud/Enrichr/), accessed via Python gseapy package

**Method:** The 55 common target genes were submitted for:
1. **GO (Gene Ontology) enrichment** — Biological Process (BP), Cellular Component (CC), Molecular Function (MF), using GO_2023 gene sets
2. **KEGG pathway enrichment** — using KEGG_2021_Human gene sets

**Parameters:**
- Organism: human
- Significance threshold: Adjusted P-value (Benjamini-Hochberg) < 0.05

### 6.2 Results

**GO Enrichment:**

| Category | Significant Terms (P.adj < 0.05) |
|---|---|
| Biological Process (BP) | 311 |
| Cellular Component (CC) | 4 |
| Molecular Function (MF) | 34 |

**Top 5 GO Biological Processes:**
1. Adenylate cyclase-modulating G protein-coupled receptor signaling pathway
2. Positive regulation of cytosolic calcium ion concentration
3. G protein-coupled receptor signaling pathway
4. Inflammatory response
5. Response to drug

**KEGG Pathway Enrichment: 147 significant pathways (P.adj < 0.05)**

**Top 20 KEGG Pathways:**

| Rank | Pathway | Adjusted P-value | Gene Count |
|---|---|---|---|
| 1 | Neuroactive ligand-receptor interaction | 4.58e-15 | 17/341 |
| 2 | Pathways in cancer | 8.74e-10 | 15/531 |
| 3 | Human cytomegalovirus infection | 1.38e-09 | 11/225 |
| 4 | cGMP-PKG signaling pathway | 1.38e-09 | 10/167 |
| 5 | Chemical carcinogenesis | 1.53e-09 | 11/239 |
| 6 | Calcium signaling pathway | 1.53e-09 | 11/240 |
| 7 | Dopaminergic synapse | 2.62e-09 | 9/132 |
| 8 | Salivary secretion | 4.23e-09 | 8/93 |
| 9 | Adrenergic signaling in cardiomyocytes | 6.43e-09 | 9/150 |
| 10 | Breast cancer | 1.32e-07 | 8/147 |
| 11 | Serotonergic synapse | 4.65e-07 | 7/113 |
| 12 | PI3K-Akt signaling pathway | 6.61e-07 | 10/354 |
| 13 | Kaposi sarcoma-associated herpesvirus infection | 8.55e-07 | 8/193 |
| 14 | Proteoglycans in cancer | 1.27e-06 | 8/205 |
| 15 | Gap junction | 2.05e-06 | 6/88 |
| 16 | IL-17 signaling pathway | 2.86e-06 | 6/94 |
| 17 | Prostate cancer | 3.24e-06 | 6/97 |
| 18 | Regulation of lipolysis in adipocytes | 4.70e-06 | 5/55 |
| 19 | Relaxin signaling pathway | 1.56e-05 | 6/129 |
| 20 | Glioma | 1.92e-05 | 5/75 |

### 6.3 Output Figures and Data

| File | Description |
|---|---|
| **`results/figures/go_barplot.pdf`** | Bar plot of top 10 GO terms per category (BP, CC, MF). X-axis: -log10(Adjusted P-value). Three panels. |
| **`results/figures/kegg_bubble.pdf`** | Bubble plot of top 20 KEGG pathways. X-axis: Gene Ratio. Bubble size: gene count. Color: -log10(Adjusted P-value). |
| `data/enrichment/GO_Biological_Process_2023.csv` | Full GO-BP results (311 terms) |
| `data/enrichment/GO_Cellular_Component_2023.csv` | Full GO-CC results (4 terms) |
| `data/enrichment/GO_Molecular_Function_2023.csv` | Full GO-MF results (34 terms) |
| `data/enrichment/KEGG_2021_Human.csv` | Full KEGG results (147 pathways) |

---

## 7. Molecular Docking

### 7.1 Target and Ligand Selection

**Receptors (top 5 core targets by PPI Degree):**

| Target | PDB ID | Description |
|---|---|---|
| PTGS2 | 5IKR | Cyclooxygenase-2 |
| IL6 | 1ALU | Interleukin-6 |
| ESR1 | 1ERE | Estrogen receptor alpha |
| EGFR | 1M17 | Epidermal growth factor receptor |
| TP53 | 1TSR | Tumor protein p53 |

**Ligands (top 5 compounds by number of targets in the network):**

| Compound | Number of Targets |
|---|---|
| Quercetin | 108 |
| Luteolin | 42 |
| 4'-methyl-N-methylcoclaurine | 27 |
| Succinic acid | 27 |

(Note: quercetin/Quercetin appeared twice due to case difference from two herb sources)

### 7.2 Structure Preparation

**Receptor structures:**
- **Source:** RCSB PDB (https://www.rcsb.org/)
- **Processing:** Converted PDB to PDBQT format using Open Babel 3.1 (`obabel -xr` to remove water molecules and add partial charges)

**Ligand structures:**
- **Source:** SMILES from PubChem, converted to 3D coordinates
- **Processing:** SMILES → 3D SDF (Open Babel, `--gen3d -h` for 3D generation and hydrogen addition) → PDBQT format

### 7.3 Docking Protocol

**Software:** AutoDock Vina 1.1.2

**Parameters:**
- Search box size: 25 × 25 × 25 Å (centered on protein center of mass)
- Exhaustiveness: 8
- Number of modes: 3
- Scoring: AutoDock Vina force field

**Binding energy interpretation:**
- < -5.0 kcal/mol: Good binding affinity
- < -7.0 kcal/mol: Strong binding affinity

### 7.4 Results

**Docking Binding Energies (kcal/mol):**

| Compound \ Target | PTGS2 | IL6 | ESR1 | EGFR | TP53 |
|---|---|---|---|---|---|
| Quercetin | -4.8 | -5.4 | -6.9 | **-7.3** | -6.7 |
| Luteolin | -4.1 | -5.2 | **-7.0** | **-7.3** | -6.5 |
| 4'-methyl-N-methylcoclaurine | -3.4 | -5.3 | -6.4 | **-7.7** | -5.9 |
| Succinic acid | -3.6 | -3.8 | -3.4 | -4.0 | -4.5 |

**Key findings:**
- **Strongest binding:** 4'-methyl-N-methylcoclaurine → EGFR (**-7.7 kcal/mol**)
- **Strong bindings (< -7.0):** Quercetin → EGFR (-7.3), Luteolin → EGFR (-7.3), Luteolin → ESR1 (-7.0)
- **Good bindings (< -5.0):** Most flavonoid-target pairs showed good affinity
- **Weak binding:** Succinic acid showed poor affinity with all targets (> -4.5), consistent with its small molecular size

### 7.5 Output Figures and Data

| File | Description |
|---|---|
| **`results/figures/docking_heatmap.pdf`** | Heatmap of binding energies (5 targets × 5 compounds). Color scale: green (strong) to red (weak). Annotated with energy values. |
| `results/tables/docking_results.csv` | All 25 docking results with binding energies |
| `results/docking/receptors/` | Receptor PDB and PDBQT files |
| `results/docking/ligands/` | Ligand PDB, SDF, and PDBQT files |
| `results/docking/*_out.pdbqt` | Docking output poses (best 3 modes per pair) |

---

## Summary of All Output Figures (PDF)

| # | File Path | Content |
|---|---|---|
| 1 | `results/figures/venn_drug_disease.pdf` | Drug targets vs Disease targets Venn diagram |
| 2 | `results/figures/venn_per_disease.pdf` | Drug vs each disease (3 panels) |
| 3 | `results/figures/venn_three_diseases.pdf` | 3-way Venn across Insomnia/Alzheimer/Anxiety |
| 4 | `results/figures/ppi_network.pdf` | Full PPI network (54 nodes, 346 edges) |
| 5 | `results/figures/ppi_core_network.pdf` | Core hub PPI subnetwork (27 nodes) |
| 6 | `results/figures/go_barplot.pdf` | GO enrichment bar plots (BP, CC, MF) |
| 7 | `results/figures/kegg_bubble.pdf` | KEGG pathway bubble plot (top 20) |
| 8 | `results/figures/docking_heatmap.pdf` | Molecular docking binding energy heatmap |

---

## Software and Databases Summary

| Tool/Database | Version/URL | Purpose |
|---|---|---|
| TCMSP | https://www.tcmsp-e.com/ | Active compound screening (OB, DL) and drug targets |
| PubChem | https://pubchem.ncbi.nlm.nih.gov/ (PUG REST API) | SMILES structure retrieval |
| UniProt | https://rest.uniprot.org/ (REST API) | Gene symbol standardization |
| Open Targets | https://platform.opentargets.org/ (GraphQL API) | Disease-associated target genes |
| NCBI Gene | https://eutils.ncbi.nlm.nih.gov/ (E-utilities) | Supplementary disease genes |
| STRING | https://string-db.org/ (REST API v11) | Protein-protein interaction network |
| Enrichr | https://maayanlab.cloud/Enrichr/ (via gseapy) | GO and KEGG enrichment analysis |
| RCSB PDB | https://www.rcsb.org/ | Receptor 3D structures |
| AutoDock Vina | v1.1.2 | Molecular docking |
| Open Babel | v3.1 | Molecular format conversion |
| Python | 3.10 (conda env: ppi) | All scripting |
| NetworkX | Python library | PPI network topology analysis |
| gseapy | Python library | GO/KEGG enrichment |
| matplotlib / seaborn | Python libraries | Visualization |
| matplotlib-venn | Python library | Venn diagrams |

---

## Conda Environment Reproduction

```bash
mamba create -n ppi python=3.10 -y
mamba install -n ppi -y pandas requests beautifulsoup4 matplotlib seaborn networkx openbabel lxml openpyxl
mamba install -n ppi -y -c conda-forge gseapy matplotlib-venn autodock-vina pymol-open-source
```
