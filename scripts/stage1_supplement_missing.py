#!/usr/bin/env python3
"""
Stage 1.5: Supplement herbs that TCMSP doesn't cover well.

For each herb that declares `supplement_compounds_csv` in pipeline_config.json,
load that CSV and union its compounds into compounds_filtered_all.csv. The CSV
must have columns: MOL_ID, molecule_name, ob, dl (herb_cn/herb_pinyin will be
filled in from the herb entry if absent).

Supplement herbs use a relaxed filter (FILTERS['supp_ob_min'], typically OB-only)
because many well-documented bioactives (e.g. gastrodin) fall below the
standard DL>=0.18 cutoff.

If no herb declares a supplement CSV, this stage just copies
compounds_filtered.csv → compounds_filtered_all.csv so downstream stages have
a consistent input name.
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_config as PC


def main():
    main_path = "data/compounds/compounds_filtered.csv"
    out_path = "data/compounds/compounds_filtered_all.csv"
    main_df = pd.read_csv(main_path)
    print(f"Main filtered compounds: {len(main_df)} entries "
          f"({main_df['MOL_ID'].nunique()} unique MOL_IDs)")

    supp_herbs = PC.supplement_herbs()
    if not supp_herbs:
        print("No supplement_compounds_csv declared in config — "
              "copying main filtered compounds to compounds_filtered_all.csv")
        main_df.to_csv(out_path, index=False)
        return

    global_ob_min = PC.FILTERS.get("supp_ob_min", 30)
    global_dl_min = PC.FILTERS.get("supp_dl_min")  # may be None

    print(f"Default supplement filter: OB>={global_ob_min}"
          + (f", DL>={global_dl_min}" if global_dl_min is not None else " (no DL filter)"))

    supp_frames = []
    for herb in supp_herbs:
        csv_path = herb["supplement_compounds_csv"]
        if not os.path.exists(csv_path):
            # try relative to scripts dir
            alt = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", csv_path)
            if os.path.exists(alt):
                csv_path = alt
            else:
                print(f"WARNING: supplement CSV for {herb['cn']} not found at "
                      f"{herb['supplement_compounds_csv']} — skipping")
                continue
        sdf = pd.read_csv(csv_path)
        if "herb_cn" not in sdf.columns:
            sdf["herb_cn"] = herb["cn"]
        if "herb_pinyin" not in sdf.columns:
            sdf["herb_pinyin"] = herb["pinyin"]
        sdf["ob"] = pd.to_numeric(sdf["ob"], errors="coerce")
        sdf["dl"] = pd.to_numeric(sdf["dl"], errors="coerce")

        # Per-herb filter override (e.g. animal-derived herbs whose
        # main bioactives sit at OB ~20% but with high DL)
        hf = herb.get("supplement_filters") or {}
        ob_min = hf.get("ob_min", global_ob_min)
        dl_min = hf.get("dl_min", global_dl_min)
        filter_label = (f"OB>={ob_min}"
                        + (f", DL>={dl_min}" if dl_min is not None else ""))

        mask = sdf["ob"] >= ob_min
        if dl_min is not None:
            mask &= sdf["dl"] >= dl_min
        filt = sdf[mask].copy()
        override_tag = " (override)" if hf else ""
        print(f"  {herb['cn']} ({herb['pinyin']}) [{filter_label}{override_tag}]: "
              f"{len(filt)}/{len(sdf)} compounds kept from {os.path.basename(csv_path)}")
        # Persist per-herb supplement file for traceability
        out_supp = f"data/compounds/{herb['pinyin']}_ingredients_supplement.csv"
        sdf.to_csv(out_supp, index=False)
        supp_frames.append(filt)

    if supp_frames:
        supp_all = pd.concat(supp_frames, ignore_index=True)
        combined = pd.concat([main_df, supp_all], ignore_index=True)
    else:
        combined = main_df

    combined.to_csv(out_path, index=False)
    print(f"\nCombined total: {len(combined)} entries "
          f"({combined['MOL_ID'].nunique()} unique compounds)")
    for cn in combined["herb_cn"].dropna().unique():
        n = combined[combined["herb_cn"] == cn]["MOL_ID"].nunique()
        print(f"  {cn}: {n} compounds")


if __name__ == "__main__":
    main()
