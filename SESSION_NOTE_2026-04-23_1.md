# Session Note — 2026-04-23 (1)

## Goal
User asked: "Check how process in this folder was getting ppi analysis with given components and disease."

## Actions
- Listed folder: scripts/, data/, results/, TCMSP-Spider/, README.md
- Read README.md — comprehensive pipeline description (stages 1–7)
- Read scripts/stage1_scrape_all.py, stage2_targets.py, stage3_disease_targets.py,
  stage4_intersection.py, stage5_ppi_network.py

## PPI pipeline summary (herbs → disease → PPI)
- Components: 14-herb 健脑安神 formula (names in README.md lines 7–23)
- Diseases: Insomnia, Alzheimer's disease, Anxiety disorder
- Stage 1 (stage1_scrape_all.py + stage1_get_smiles.py): scrape TCMSP for each
  herb's ingredients (grid/grid2/grid3 regex), filter OB>=30% & DL>=0.18,
  pull SMILES from PubChem → 124 compounds, 113 with SMILES
- Stage 2 (stage2_targets.py): compound targets come from TCMSP grid2;
  UniProt standardizes gene symbols; Swiss Target Prediction fills herbs
  missing from TCMSP (龙眼肉, 天麻) → 197 drug target genes
- Stage 3 (stage3_disease_targets.py): Open Targets GraphQL + DisGeNET +
  NCBI Gene for the three diseases → 1,483 disease genes
- Stage 4 (stage4_intersection.py): drug_genes ∩ (insomnia ∪ alzheimer ∪ anxiety)
  → 55 common targets saved to data/targets/common_targets.csv
- Stage 5 (stage5_ppi_network.py) — the actual PPI:
    - POST-style GET to https://string-db.org/api/json/network with
      identifiers = common genes, species=9606, required_score=400
    - Build nx.Graph, drop isolates → 54 nodes, 346 edges
    - Degree / Betweenness / Closeness centrality
    - Core targets = Degree >= median → 27 hubs (PTGS2, IL6, ESR1, EGFR,
      TP53, NR3C1, MAOA, SLC6A4, DRD2, GSK3B, ...)
    - Outputs: results/tables/ppi_topology.csv, core_targets.csv,
      ppi_edges.csv (Cytoscape) + figures ppi_network.png, ppi_core_network.png
- Stages 6–7 feed off the core targets (GO/KEGG enrichment, AutoDock Vina docking)

## 2026-04-23 — Built config-driven pipeline + ran QSFSG formula
New files:
- scripts/pipeline_config.py  (loads runs/<name>/pipeline_config.json, falls back to 健脑安神 defaults)
- scripts/run_pipeline.py     (orchestrator: --run-dir, --from, --only, --force, --with-docking)
- runs/qsfsg/pipeline_config.json   (12 herbs QSFSG + 3 diseases NAFLD/liver injury/dyslipidemia)
- data/supplements/jiangcan.csv, shuizhi.csv, README.md

Modified stages:
- stage1_scrape_all.py  — HERB_MAP from config + auto-resolve Chinese name via TCMSP qs=herb_all_name endpoint
- stage1_supplement_missing.py — generic; per-herb supplement CSVs referenced by config
- stage2_targets.py, stage2_supplement_targets.py — supplement-herb list from config
- stage3_disease_targets.py — DISEASES from config
- stage4_intersection.py — loops N diseases, generates 2-way or 3-way Venn accordingly

Stage 1 results (TCMSP + supplement):
- 9 herbs returned TCMSP data: 红参 4, 黄芪 20, 熟地黄 2, 山药 16, 酒萸肉 20, 茯苓 15, 牡丹皮 11, 生大黄 16, 炙甘草 92
- 蝉蜕: 8 raw ingredients but 0 passed OB>=30%,DL>=0.18 — contributes nothing this run
- 僵蚕, 水蛭: not in TCMSP — using literature supplement CSVs (sterols)
Total: 196 filtered entries / 177 unique compounds across 9 TCMSP herbs (pre-supplement merge)

Usage going forward:
  python scripts/run_pipeline.py --run-dir runs/<name> [--from N | --only N | --force | --with-docking]

## QSFSG run — results
- Drug targets (S2+S2.5): 181 unique gene symbols; 1670 compound-target pairs across 9 herbs (僵蚕/水蛭 contributed 0 after UniProt mapping)
- Disease targets (S3): NAFLD 503, Liver Injury 111, Dyslipidemia 500 — union 1023
- Intersection (S4): 45 common targets; per-disease: NAFLD 27, Liver Injury 12, Dyslipidemia 18
- PPI (S5, STRING score>=400): 45 nodes / 411 edges (2 isolates dropped: ACP3, VEGFA); median degree 19 → 23 core hubs
  Top hubs by degree: AKT1 (37), IL6 (35), EGFR (34), TP53 (34), IL1B (33), CASP3 (32), ESR1 (32), PTGS2 (29), TGFB1 (29), CCL2 (28)
- Enrichment (S6): GO-BP 595 terms, GO-CC 39, KEGG 140 (GO-MF got 429 rate limit from Enrichr; retry later)
  Top KEGG: Lipid and atherosclerosis (P.adj=9.56e-17), AGE-RAGE diabetic (2.49e-14), Pathways in cancer (4.74e-14), Fluid shear stress & atherosclerosis (5.17e-13), TNF signaling (2.16e-12), NAFLD (1.97e-08)
- Outputs under runs/qsfsg/: data/, results/tables/{ppi_topology, core_targets, ppi_edges}.csv, results/figures/{venn*, ppi_network, ppi_core_network, go_barplot, kegg_bubble}.png+pdf

## 2026-04-27 — Report generation + herb_cn fix + lit-cited supplements

### Bug fix in stage2_targets.py
Original logic kept herb_cn from tcmsp_targets_raw.csv (the herb whose TCMSP page returned the row). Rewritten to drop that and re-attribute via inner-merge on MOL_ID with compounds_filtered_all.csv — one (herb, MOL_ID, target) row per source herb. Drug-target row count 1670 → 2023 → 2332 across iterations as supplements grew.

### New report-generation stages (8, 8.5, 9)
- scripts/make_excel.py        — single multi-sheet workbook (config-driven, optional Chinese names / GO-MF / docking)
- scripts/make_individual_excel.py — 1 xlsx per result table
- scripts/make_report.py       — generates METHODS_AND_RESULTS.md from data + config
- All wired into run_pipeline.py; --only / --from skip respects existing outputs

### Citation-backed supplement CSVs
data/supplements/jiangcan.csv — 10 compounds (Hu 2017 PMC6151799, Liu 2025, Wang 2022)
data/supplements/shuizhi.csv  — 10 compounds (Dong 2016 ECAM, Chen 2025 PMC12195895, Zhang PMC11002550)
References embedded in pipeline_config.json under herb.supplement_references; rendered automatically by make_report.py mirroring the original 龙眼肉/天麻 layout.

### QSFSG final stats (post-fix)
- 213 compound-herb entries / 194 unique compounds across 11 herbs (蝉蜕 0 — see methods)
- 2332 drug-target row pairs / 181 unique gene symbols
  Per-herb (post-attribution): 炙甘草 171, 黄芪 142, 僵蚕 134, 牡丹皮 122, 酒萸肉 39, 水蛭 39, 红参 33, 山药 27, 生大黄 27, 熟地黄 23, 茯苓 15
- 45 common drug-disease targets; per-disease: NAFLD 27, Liver Injury 12, Dyslipidemia 18
- PPI: 45 nodes / 411 edges (2 isolates: ACP3, VEGFA); median Degree 19 → 23 core hubs
- Top hubs: AKT1 (37), IL6 (35), EGFR (34), TP53 (34), IL1B (33), CASP3 (32), ESR1 (32), PTGS2 (29), TGFB1 (29), CCL2 (28)
- 595 GO-BP, 39 GO-CC, 140 KEGG (P.adj < 0.05); GO-MF still rate-limited (429)
- Top KEGG: Lipid & atherosclerosis (9.56e-17), AGE-RAGE (2.49e-14), TNF (2.16e-12), NAFLD (1.97e-08), Hep B/C, MAPK signaling
- Outputs: runs/qsfsg/METHODS_AND_RESULTS.md (217 lines) + 12 xlsx files in results/tables/
