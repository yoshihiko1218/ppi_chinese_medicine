#!/usr/bin/env python3
"""
Generate METHODS_AND_RESULTS.md for the current run by combining
pipeline_config.json + the produced data tables.

Layout mirrors the original 健脑安神 report: sections 1–7 (compounds → docking)
plus an appendix with method explanations. Stages whose outputs are missing
(e.g. docking when not run, GO-MF when rate-limited) are quietly skipped.
"""
import os
import sys
import datetime as dt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_config as PC


def _read(path):
    return pd.read_csv(path) if os.path.exists(path) else None


def _md_table(df, max_rows=None, float_fmt=None):
    """Render a DataFrame as a GitHub-flavored markdown table."""
    if max_rows is not None:
        df = df.head(max_rows)
    df = df.copy()
    if float_fmt:
        for c in df.columns:
            if pd.api.types.is_float_dtype(df[c]):
                df[c] = df[c].map(lambda v: float_fmt.format(v) if pd.notnull(v) else "")
    cols = list(df.columns)
    head = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    rows = ["| " + " | ".join("" if pd.isnull(v) else str(v) for v in row) + " |"
            for row in df.itertuples(index=False)]
    return "\n".join([head, sep] + rows)


def main():
    out_path = "METHODS_AND_RESULTS.md"
    pn = PC.CONFIG.get("project_name", "(unnamed)")
    desc = PC.CONFIG.get("description", "")
    today = dt.date.today().isoformat()
    parts = []

    # -- Header --
    parts.append(f"# Network Pharmacology Study — {pn}\n")
    if desc:
        parts.append(f"_{desc}_\n")
    parts.append(f"## Complete Methods and Results Documentation")
    parts.append(f"_Generated: {today}_\n")

    # -- Formula composition --
    parts.append("## Formula Composition\n")
    formula = pd.DataFrame([
        {"Herb (Chinese)": h["cn"],
         "Pinyin": h.get("pinyin", ""),
         "Latin": (h.get("latin") or [""])[0],
         "Notes": "literature supplement" if h.get("supplement_compounds_csv") else ""}
        for h in PC.HERBS
    ])
    parts.append(_md_table(formula))
    parts.append("")
    parts.append(f"**Diseases targeted:** "
                 + ", ".join(m["name"] for m in PC.DISEASES.values()))
    parts.append("")

    # -- Literature sources for any supplement herbs --
    supp_with_refs = [h for h in PC.HERBS if h.get("supplement_references")]
    if supp_with_refs:
        parts.append("### Literature Sources for Supplement Herbs\n")
        parts.append("Some herbs are not registered in TCMSP (typically animal-derived "
                     "drugs or recently added items) and their active compound lists are "
                     "drawn from published phytochemistry / pharmacology reviews.\n")
        for h in supp_with_refs:
            parts.append(f"#### {h['cn']} ({h.get('pinyin','')}) — Literature Sources\n")
            for i, ref in enumerate(h["supplement_references"], 1):
                parts.append(f"{i}. {ref}")
            parts.append("")

    # -- Pipeline overview --
    compounds = _read("data/compounds/compounds_filtered_all.csv")
    drug_targets = _read("data/targets/drug_targets.csv")
    disease_targets = _read("data/targets/disease_targets.csv")
    common = _read("data/targets/common_targets.csv")
    ppi = _read("results/tables/ppi_topology.csv")
    core = _read("results/tables/core_targets.csv")
    kegg = _read("data/enrichment/KEGG_2021_Human.csv")
    go_bp = _read("data/enrichment/GO_Biological_Process_2023.csv")
    go_cc = _read("data/enrichment/GO_Cellular_Component_2023.csv")
    go_mf = _read("data/enrichment/GO_Molecular_Function_2023.csv")
    docking = _read("results/tables/docking_results.csv")

    n_compounds = compounds["MOL_ID"].nunique() if compounds is not None else 0
    n_drug_genes = drug_targets["gene_symbol"].nunique() if drug_targets is not None else 0
    n_disease_genes = disease_targets["gene_symbol"].nunique() if disease_targets is not None else 0
    n_common = len(common) if common is not None else 0
    n_ppi_nodes = len(ppi) if ppi is not None else 0
    n_ppi_edges = len(_read("results/tables/ppi_edges.csv")) if _read("results/tables/ppi_edges.csv") is not None else 0
    n_core = len(core) if core is not None else 0

    parts.append("## Overall Pipeline Logic\n")
    parts.append(
        "Network pharmacology asks: **\"How does a multi-herb formula treat a disease "
        "at the molecular level?\"** The pipeline answers this by connecting "
        "herbs → compounds → protein targets → disease mechanisms, step by step.\n")
    parts.append("```")
    parts.append(f"Herbs ({len(PC.HERBS)}) → Active Compounds ({n_compounds}) "
                 f"→ Drug Targets ({n_drug_genes} genes)")
    parts.append("                                              ↓")
    parts.append(f"                              Disease Targets ({n_disease_genes} genes)")
    parts.append("                                              ↓")
    parts.append(f"                                    Common Targets ({n_common} genes)")
    parts.append("                                              ↓")
    parts.append(f"                              PPI Network ({n_ppi_nodes} nodes / {n_ppi_edges} edges) "
                 f"→ Core Hubs ({n_core} genes)")
    parts.append("                                              ↓")
    parts.append("                              GO/KEGG → Key Pathways & Processes")
    if docking is not None:
        parts.append("                                              ↓")
        parts.append("                              Molecular Docking → Binding Validation")
    parts.append("```\n")

    # -- 1. Compound screening --
    parts.append("## 1. Active Compound Screening\n")
    parts.append(f"**Filter:** OB ≥ {PC.FILTERS['ob_min']}%, "
                 f"DL ≥ {PC.FILTERS['dl_min']} for TCMSP-sourced herbs; "
                 f"OB ≥ {PC.FILTERS.get('supp_ob_min', 30)}"
                 f"{', DL ≥ ' + str(PC.FILTERS['supp_dl_min']) if PC.FILTERS.get('supp_dl_min') else ' (no DL filter)'} "
                 f"for literature-supplement herbs.\n")
    if compounds is not None:
        per_herb = (compounds.groupby("herb_cn")["MOL_ID"].nunique()
                             .reset_index(name="Filtered Compounds")
                             .sort_values("Filtered Compounds", ascending=False)
                             .rename(columns={"herb_cn": "Herb"}))
        parts.append("**Per-herb filtered compound count:**\n")
        parts.append(_md_table(per_herb))
        parts.append("")
        # SMILES coverage
        if "SMILES" in compounds.columns:
            uc = compounds.drop_duplicates(subset="MOL_ID")
            with_smiles = uc["SMILES"].notna() & (uc["SMILES"].astype(str) != "")
            parts.append(f"**SMILES retrieved (PubChem):** "
                         f"{int(with_smiles.sum())}/{len(uc)} unique compounds\n")

    # -- 2. Drug targets --
    parts.append("## 2. Drug Target Prediction\n")
    parts.append(
        "TCMSP-listed targets per compound were standardized to HGNC gene symbols via UniProt "
        f"(`organism_id:9606`). For herbs flagged as literature supplements, targets were inferred "
        "by matching shared compounds to TCMSP target data plus UniProt search.\n")
    if drug_targets is not None:
        per_herb_t = (drug_targets.dropna(subset=["gene_symbol"])
                      .groupby("herb_cn")["gene_symbol"].nunique()
                      .reset_index(name="Unique Gene Targets")
                      .sort_values("Unique Gene Targets", ascending=False)
                      .rename(columns={"herb_cn": "Herb"}))
        parts.append("**Per-herb unique gene targets:**\n")
        parts.append(_md_table(per_herb_t))
        parts.append("")
        parts.append(f"**Total compound–target pairs:** {len(drug_targets)}")
        parts.append(f"**Unique gene symbols:** {n_drug_genes}\n")

    # -- 3. Disease targets --
    parts.append("## 3. Disease Target Collection\n")
    parts.append(
        "**Sources:** Open Targets Platform (GraphQL, top "
        f"{PC.FILTERS.get('disease_top_n', 500)} associations) + NCBI Gene "
        "(`Disease/Phenotype` field, Homo sapiens).\n")
    if disease_targets is not None:
        per_d = (disease_targets.groupby(["disease_key", "disease"])["gene_symbol"]
                                .nunique()
                                .reset_index(name="Unique Targets"))
        per_d = per_d.merge(
            pd.DataFrame([{"disease_key": k, "order": i}
                          for i, k in enumerate(PC.DISEASES.keys())]),
            on="disease_key", how="left"
        ).sort_values("order").drop(columns=["order"])
        parts.append(_md_table(per_d.rename(columns={
            "disease_key": "Key", "disease": "Disease"})))
        parts.append("")
        parts.append(f"**Union of disease genes:** {n_disease_genes}\n")

    # -- 4. Intersection --
    parts.append("## 4. Intersection (Drug ∩ Disease) and Venn Diagrams\n")
    if common is not None and disease_targets is not None and drug_targets is not None:
        drug_set = set(drug_targets["gene_symbol"].dropna())
        rows = []
        for key, meta in PC.DISEASES.items():
            d_set = set(disease_targets[disease_targets["disease_key"] == key]["gene_symbol"].dropna())
            rows.append({"Disease": meta["name"], "Drug ∩ Disease": len(drug_set & d_set)})
        rows.append({"Disease": "Drug ∩ ALL diseases (union)", "Drug ∩ Disease": n_common})
        parts.append(_md_table(pd.DataFrame(rows)))
        parts.append("")
        common_list = ", ".join(sorted(common["gene_symbol"]))
        parts.append(f"**All {n_common} common targets:**")
        parts.append(common_list + "\n")

        for fig in ["venn_drug_disease.png", "venn_per_disease.png",
                    "venn_three_diseases.png", "venn_two_diseases.png"]:
            if os.path.exists(f"results/figures/{fig}"):
                parts.append(f"![{fig}](results/figures/{fig})")
        parts.append("")

    # -- 5. PPI --
    parts.append("## 5. PPI Network & Core Targets\n")
    parts.append(
        f"Common targets submitted to STRING (`species=9606`, "
        f"`required_score={PC.FILTERS.get('string_score_min', 400)}`); "
        "isolates dropped. Topology computed with NetworkX.\n")
    if ppi is not None:
        median_d = ppi["Degree"].median()
        parts.append(f"**Network:** {n_ppi_nodes} nodes / {n_ppi_edges} edges, "
                     f"median Degree = {median_d:g}, **{n_core} core hubs** (Degree ≥ median).\n")
        parts.append("**Top 10 core targets by Degree:**\n")
        top10 = ppi.head(10).rename(columns={
            "gene_symbol": "Gene", "Betweenness": "Betweenness", "Closeness": "Closeness"})
        parts.append(_md_table(top10, float_fmt="{:.3f}"))
        parts.append("")
        for fig in ["ppi_network.png", "ppi_core_network.png"]:
            if os.path.exists(f"results/figures/{fig}"):
                parts.append(f"![{fig}](results/figures/{fig})")
        parts.append("")

    # -- 6. Enrichment --
    parts.append("## 6. GO & KEGG Enrichment\n")
    parts.append("Enrichr via `gseapy`; significance threshold P.adj < 0.05.\n")
    counts = []
    for name, df in [("GO Biological Process", go_bp),
                     ("GO Cellular Component", go_cc),
                     ("GO Molecular Function", go_mf),
                     ("KEGG (2021 Human)",     kegg)]:
        counts.append({"Category": name,
                       "Significant terms": len(df) if df is not None else "(not generated)"})
    parts.append(_md_table(pd.DataFrame(counts)))
    parts.append("")

    if kegg is not None and len(kegg) > 0:
        parts.append("**Top 20 KEGG pathways:**\n")
        kk = kegg.head(20)[["Term", "Overlap", "Adjusted P-value", "Genes"]].rename(
            columns={"Term": "Pathway", "Adjusted P-value": "P.adj"})
        kk["P.adj"] = kk["P.adj"].map(lambda v: f"{v:.2e}")
        parts.append(_md_table(kk))
        parts.append("")
    if go_bp is not None and len(go_bp) > 0:
        parts.append("**Top 10 GO Biological Process terms:**\n")
        gg = go_bp.head(10)[["Term", "Adjusted P-value"]].rename(
            columns={"Term": "GO BP Term", "Adjusted P-value": "P.adj"})
        gg["P.adj"] = gg["P.adj"].map(lambda v: f"{v:.2e}")
        parts.append(_md_table(gg))
        parts.append("")

    for fig in ["go_barplot.png", "kegg_bubble.png"]:
        if os.path.exists(f"results/figures/{fig}"):
            parts.append(f"![{fig}](results/figures/{fig})")
    parts.append("")

    # -- 7. Docking (optional) --
    if docking is not None:
        parts.append("## 7. Molecular Docking\n")
        parts.append("AutoDock Vina, top core targets × top compounds. Binding "
                     "energy ≤ −7 kcal/mol = strong; ≤ −5 = good.\n")
        d = docking.copy()
        d.columns = ["Target", "Compound", "Binding Energy (kcal/mol)"]
        d = d.sort_values("Binding Energy (kcal/mol)").head(20)
        parts.append("**Top 20 binding pairs:**\n")
        parts.append(_md_table(d, float_fmt="{:.2f}"))
        parts.append("")
        if os.path.exists("results/figures/docking_heatmap.png"):
            parts.append("![docking_heatmap.png](results/figures/docking_heatmap.png)")
        parts.append("")

    # -- Appendix --
    parts.append("## Appendix: Method Notes\n")
    parts.append(
        "**A1. OB / DL.** OB (oral bioavailability, %) and DL (drug-likeness, "
        "Tanimoto-based) are the standard ADME filters used by TCMSP and the "
        "thesis methodology this pipeline follows. The 30% / 0.18 cutoffs are "
        "the convention in network-pharmacology studies of TCM formulas.")
    parts.append(
        "**A2. STRING confidence.** STRING's interaction score is in [0, 1000]. "
        f"`required_score={PC.FILTERS.get('string_score_min', 400)}` means the API "
        "returns only interactions with combined evidence ≥ 0.4 (medium confidence).")
    parts.append(
        "**A3. PPI topology.** Degree = direct neighbours; Betweenness = "
        "fraction of shortest paths through the node; Closeness = average "
        "inverse shortest-path length. We pick core hubs as nodes with "
        "Degree ≥ median, the standard ‘above-median Degree’ rule.")
    parts.append(
        "**A4. Enrichment.** Enrichr uses Fisher's exact test with "
        "Benjamini–Hochberg adjustment. We keep terms with P.adj < 0.05.")
    parts.append("")
    parts.append("## Software & databases\n"
                 "TCMSP, PubChem, UniProt, Open Targets (GraphQL), NCBI Gene, "
                 "STRING, Enrichr (via gseapy). Python 3.10, conda env `ppi`.\n")

    # Write
    with open(out_path, "w") as f:
        f.write("\n".join(parts))
    print(f"Saved: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB, "
          f"{sum(1 for _ in open(out_path))} lines)")


if __name__ == "__main__":
    main()
