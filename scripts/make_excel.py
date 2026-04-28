#!/usr/bin/env python3
"""
Build a single multi-sheet Excel workbook from pipeline outputs.

Config-driven: reads pipeline_config.json from the current working directory
(typically a runs/<name>/ run dir) for disease names. Handles missing optional
data (Chinese compound names, GO_MF, docking) gracefully.
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_config as PC

OUT_PATH = "results/tables/network_pharmacology_results.xlsx"


def _read(path, **kw):
    return pd.read_csv(path, **kw) if os.path.exists(path) else None


def _select(df, cols):
    """Keep only existing columns, in the order given."""
    keep = [c for c in cols if c in df.columns]
    return df[keep].copy()


def main():
    os.makedirs("results/tables", exist_ok=True)
    writer = pd.ExcelWriter(OUT_PATH, engine="openpyxl")

    # === 1. Active Compounds (full per-herb-compound table) ===
    compounds = _read("data/compounds/compounds_filtered_all.csv")
    if compounds is not None:
        c1 = _select(compounds, [
            "MOL_ID", "molecule_name", "molecule_name_cn",
            "ob", "dl", "mw", "herb_cn", "herb_pinyin",
            "SMILES", "PubChem_CID",
        ])
        rename = {
            "molecule_name": "Compound (English)",
            "molecule_name_cn": "Compound (Chinese)",
            "ob": "OB (%)", "dl": "DL", "mw": "Molecular Weight",
            "herb_cn": "Herb (Chinese)", "herb_pinyin": "Herb (Pinyin)",
            "PubChem_CID": "PubChem CID",
        }
        c1 = c1.rename(columns=rename)
        c1.to_excel(writer, sheet_name="Active Compounds", index=False)

        # === 2. Unique Compounds (deduped, source herbs as comma list) ===
        if "Herb (Chinese)" in c1.columns:
            herb_sources = c1.groupby("MOL_ID")["Herb (Chinese)"].apply(
                lambda x: ", ".join(sorted(set(x)))
            ).reset_index().rename(columns={"Herb (Chinese)": "Source Herbs"})
            unique = (c1.drop_duplicates(subset="MOL_ID")
                        .drop(columns=[c for c in ["Herb (Chinese)", "Herb (Pinyin)"] if c in c1.columns])
                        .merge(herb_sources, on="MOL_ID")
                        .sort_values("OB (%)", ascending=False))
            unique.to_excel(writer, sheet_name="Unique Compounds", index=False)

    # === 3. Drug Targets ===
    drug_targets = _read("data/targets/drug_targets.csv")
    if drug_targets is not None:
        dt = _select(drug_targets, [
            "MOL_ID", "molecule_name", "gene_symbol", "uniprot_id",
            "target_name", "herb_cn", "herb_pinyin",
        ]).rename(columns={
            "molecule_name": "Compound", "gene_symbol": "Gene Symbol",
            "uniprot_id": "UniProt ID", "target_name": "Target Protein",
            "herb_cn": "Herb (Chinese)", "herb_pinyin": "Herb (Pinyin)",
        })
        dt.to_excel(writer, sheet_name="Drug Targets", index=False)

    # === 4. Disease Targets ===
    disease_targets = _read("data/targets/disease_targets.csv")
    if disease_targets is not None:
        dis = _select(disease_targets, [
            "gene_symbol", "disease", "source", "score",
        ]).rename(columns={
            "gene_symbol": "Gene Symbol", "disease": "Disease",
            "source": "Source Database", "score": "Association Score",
        })
        dis.to_excel(writer, sheet_name="Disease Targets", index=False)

    # === 5. Common Targets (drug ∩ disease) — flagged per disease ===
    common = _read("data/targets/common_targets.csv")
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
        sheet_name = f"Common Targets ({len(ce)})"
        ce.to_excel(writer, sheet_name=sheet_name, index=False)

    # === 6. PPI Topology + core flag ===
    ppi = _read("results/tables/ppi_topology.csv")
    if ppi is not None:
        ppi = ppi.rename(columns={
            "gene_symbol": "Gene Symbol", "Degree": "Degree",
            "Betweenness": "Betweenness Centrality",
            "Closeness": "Closeness Centrality",
        })
        median_degree = ppi["Degree"].median()
        ppi["Core Target"] = ppi["Degree"].apply(lambda x: "Yes" if x >= median_degree else "")
        ppi.to_excel(writer, sheet_name="PPI Topology", index=False)

    # === 7. KEGG Pathways ===
    kegg = _read("data/enrichment/KEGG_2021_Human.csv")
    if kegg is not None:
        k = _select(kegg, ["Term", "Overlap", "P-value", "Adjusted P-value", "Genes"])
        k = k.rename(columns={"Term": "Pathway"})
        k.to_excel(writer, sheet_name="KEGG Pathways", index=False)

    # === 8/9/10. GO BP / CC / MF (whichever exist) ===
    for go_lib, sheet in [
        ("GO_Biological_Process_2023", "GO Biological Process"),
        ("GO_Cellular_Component_2023", "GO Cellular Component"),
        ("GO_Molecular_Function_2023", "GO Molecular Function"),
    ]:
        df = _read(f"data/enrichment/{go_lib}.csv")
        if df is not None and len(df) > 0:
            df2 = _select(df, ["Term", "Overlap", "P-value", "Adjusted P-value", "Genes"])
            df2 = df2.rename(columns={"Term": "GO Term"})
            df2.to_excel(writer, sheet_name=sheet, index=False)

    # === 11. Molecular Docking (only if generated) ===
    docking = _read("results/tables/docking_results.csv")
    if docking is not None:
        docking = docking.copy()
        docking.columns = ["Target Protein", "Active Compound", "Binding Energy (kcal/mol)"]
        docking["Binding Strength"] = docking["Binding Energy (kcal/mol)"].apply(
            lambda x: "Strong" if x <= -7.0 else ("Good" if x <= -5.0 else "Weak")
        )
        docking = docking.sort_values("Binding Energy (kcal/mol)")
        docking.to_excel(writer, sheet_name="Molecular Docking", index=False)

    writer.close()

    fsize = os.path.getsize(OUT_PATH) / 1024
    print(f"Saved: {OUT_PATH} ({fsize:.0f} KB)")
    print("\nSheets:")
    xls = pd.ExcelFile(OUT_PATH)
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        print(f"  {sheet:35s} {df.shape[0]:>6d} rows × {df.shape[1]:>2d} cols")


if __name__ == "__main__":
    main()
