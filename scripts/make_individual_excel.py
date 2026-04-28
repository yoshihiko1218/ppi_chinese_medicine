#!/usr/bin/env python3
"""
Write one Excel file per result table under results/tables/.

Config-driven: per-disease columns in `common_targets.xlsx` come from
pipeline_config.json. Skips tables whose CSV inputs don't exist.
"""
import glob
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_config as PC

OUTDIR = "results/tables"


def _read(path):
    return pd.read_csv(path) if os.path.exists(path) else None


def _select(df, cols):
    return df[[c for c in cols if c in df.columns]].copy()


def main():
    os.makedirs(OUTDIR, exist_ok=True)

    compounds = _read("data/compounds/compounds_filtered_all.csv")
    drug_targets = _read("data/targets/drug_targets.csv")
    disease_targets = _read("data/targets/disease_targets.csv")
    common = _read("data/targets/common_targets.csv")
    ppi = _read("results/tables/ppi_topology.csv")
    kegg = _read("data/enrichment/KEGG_2021_Human.csv")

    # 1. active_compounds
    if compounds is not None:
        c1 = _select(compounds, [
            "MOL_ID", "molecule_name", "molecule_name_cn",
            "ob", "dl", "mw", "herb_cn", "herb_pinyin", "SMILES", "PubChem_CID",
        ]).rename(columns={
            "molecule_name": "Compound (English)",
            "molecule_name_cn": "Compound (Chinese)",
            "ob": "OB (%)", "dl": "DL", "mw": "Molecular Weight",
            "herb_cn": "Herb (Chinese)", "herb_pinyin": "Herb (Pinyin)",
            "PubChem_CID": "PubChem CID",
        })
        c1.to_excel(f"{OUTDIR}/active_compounds.xlsx", index=False)

        # 2. unique_compounds
        if "Herb (Chinese)" in c1.columns:
            hs = c1.groupby("MOL_ID")["Herb (Chinese)"].apply(
                lambda x: ", ".join(sorted(set(x)))
            ).reset_index().rename(columns={"Herb (Chinese)": "Source Herbs"})
            u = (c1.drop_duplicates(subset="MOL_ID")
                   .drop(columns=[c for c in ["Herb (Chinese)", "Herb (Pinyin)"] if c in c1.columns])
                   .merge(hs, on="MOL_ID")
                   .sort_values("OB (%)", ascending=False))
            u.to_excel(f"{OUTDIR}/unique_compounds.xlsx", index=False)

    # 3. drug_targets
    if drug_targets is not None:
        dt = _select(drug_targets, [
            "MOL_ID", "molecule_name", "gene_symbol", "uniprot_id",
            "target_name", "herb_cn", "herb_pinyin",
        ]).rename(columns={
            "molecule_name": "Compound", "gene_symbol": "Gene Symbol",
            "uniprot_id": "UniProt ID", "target_name": "Target Protein",
            "herb_cn": "Herb (Chinese)", "herb_pinyin": "Herb (Pinyin)",
        })
        dt.to_excel(f"{OUTDIR}/drug_targets.xlsx", index=False)

    # 4. disease_targets
    if disease_targets is not None:
        dis = _select(disease_targets, ["gene_symbol", "disease", "source", "score"]).rename(columns={
            "gene_symbol": "Gene Symbol", "disease": "Disease",
            "source": "Source Database", "score": "Association Score",
        })
        dis.to_excel(f"{OUTDIR}/disease_targets.xlsx", index=False)

    # 5. common_targets
    if common is not None:
        ce = common.copy()
        for key, meta in PC.DISEASES.items():
            f = f"data/targets/common_targets_{key}.csv"
            present = set(_read(f)["gene_symbol"]) if _read(f) is not None else set()
            ce[meta["name"]] = ce["gene_symbol"].apply(lambda g: "Yes" if g in present else "")

        if drug_targets is not None:
            gc = (drug_targets.dropna(subset=["gene_symbol"])
                  .groupby("gene_symbol")["molecule_name"]
                  .apply(lambda x: ", ".join(sorted(set(x.dropna()))))
                  .reset_index()
                  .rename(columns={"molecule_name": "Active Compounds"}))
            gh = (drug_targets.dropna(subset=["gene_symbol"])
                  .groupby("gene_symbol")["herb_cn"]
                  .apply(lambda x: ", ".join(sorted(set(x.dropna()))))
                  .reset_index()
                  .rename(columns={"herb_cn": "Source Herbs"}))
            ce = ce.merge(gc, on="gene_symbol", how="left").merge(gh, on="gene_symbol", how="left")
        ce = ce.rename(columns={"gene_symbol": "Gene Symbol"})
        ce.to_excel(f"{OUTDIR}/common_targets.xlsx", index=False)

    # 6. ppi_topology
    if ppi is not None:
        p = ppi.rename(columns={
            "gene_symbol": "Gene Symbol", "Degree": "Degree",
            "Betweenness": "Betweenness Centrality",
            "Closeness": "Closeness Centrality",
        })
        median_degree = p["Degree"].median()
        p["Core Target"] = p["Degree"].apply(lambda x: "Yes" if x >= median_degree else "")
        p.to_excel(f"{OUTDIR}/ppi_topology.xlsx", index=False)

        # 7. core_targets
        core = p[p["Core Target"] == "Yes"].copy()
        if common is not None and "Gene Symbol" in core.columns:
            try:
                ce = pd.read_excel(f"{OUTDIR}/common_targets.xlsx")
                join_cols = ["Gene Symbol"] + [m["name"] for m in PC.DISEASES.values()]
                join_cols = [c for c in join_cols if c in ce.columns]
                if "Active Compounds" in ce.columns: join_cols.append("Active Compounds")
                if "Source Herbs"     in ce.columns: join_cols.append("Source Herbs")
                core = core.merge(ce[join_cols], on="Gene Symbol", how="left")
            except Exception:
                pass
        core.to_excel(f"{OUTDIR}/core_targets.xlsx", index=False)

    # 8. kegg_pathways
    if kegg is not None:
        k = _select(kegg, ["Term", "Overlap", "P-value", "Adjusted P-value", "Genes"]).rename(
            columns={"Term": "Pathway"})
        k.to_excel(f"{OUTDIR}/kegg_pathways.xlsx", index=False)

    # 9/10/11. go_biological_process / cellular_component / molecular_function
    for lib, fname in [
        ("GO_Biological_Process_2023", "go_biological_process.xlsx"),
        ("GO_Cellular_Component_2023", "go_cellular_component.xlsx"),
        ("GO_Molecular_Function_2023", "go_molecular_function.xlsx"),
    ]:
        df = _read(f"data/enrichment/{lib}.csv")
        if df is not None and len(df) > 0:
            d = _select(df, ["Term", "Overlap", "P-value", "Adjusted P-value", "Genes"]).rename(
                columns={"Term": "GO Term"})
            d.to_excel(f"{OUTDIR}/{fname}", index=False)

    # 12. molecular_docking (optional)
    docking = _read("results/tables/docking_results.csv")
    if docking is not None:
        d = docking.copy()
        d.columns = ["Target Protein", "Active Compound", "Binding Energy (kcal/mol)"]
        d["Binding Strength"] = d["Binding Energy (kcal/mol)"].apply(
            lambda x: "Strong" if x <= -7.0 else ("Good" if x <= -5.0 else "Weak")
        )
        d = d.sort_values("Binding Energy (kcal/mol)")
        d.to_excel(f"{OUTDIR}/molecular_docking.xlsx", index=False)

    # 13. ppi_edges
    edges = _read("results/tables/ppi_edges.csv")
    if edges is not None:
        edges.columns = ["Source", "Target", "STRING Score"]
        edges.to_excel(f"{OUTDIR}/ppi_edges.xlsx", index=False)

    print(f"Individual Excel files in {OUTDIR}/:")
    for f in sorted(glob.glob(f"{OUTDIR}/*.xlsx")):
        df = pd.read_excel(f)
        size = os.path.getsize(f) / 1024
        print(f"  {os.path.basename(f):40s} {df.shape[0]:>6d} rows × {df.shape[1]:>2d} cols  ({size:.0f} KB)")


if __name__ == "__main__":
    main()
