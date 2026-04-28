# Supplement compound CSVs

Literature-based active compound lists for herbs that TCMSP does not cover
(typically animal/insect medicines, or recently standardized items).

A supplement CSV needs columns:
- `MOL_ID` (unique id, e.g. `JC001` for Jiangcan-001)
- `molecule_name`
- `ob` — oral bioavailability (%)
- `dl` — drug-likeness
- `herb_cn`, `herb_pinyin` (optional; will be filled from config if absent)

Filtering at Stage 1.5 uses `filters.supp_ob_min` and `filters.supp_dl_min`
from `pipeline_config.json`. By default these are `ob >= 30`, no DL filter —
this relaxation matches standard network-pharmacology practice for
well-documented actives whose DL falls below the 0.18 cutoff used for
high-throughput TCMSP-style screening.

To wire a CSV in, add `supplement_compounds_csv` to the herb entry in
`pipeline_config.json`:

```json
{"cn": "僵蚕", "pinyin": "Jiangcan", "latin": ["Bombyx Batryticatus"],
 "supplement_compounds_csv": "../../data/supplements/jiangcan.csv"}
```

The path is resolved relative to the `--run-dir` (e.g. `runs/qsfsg/`), so
`../../data/supplements/jiangcan.csv` points back to
`<repo>/data/supplements/jiangcan.csv`.
