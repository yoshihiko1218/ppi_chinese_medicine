#!/usr/bin/env python3
"""
Pipeline config loader.

Reads ./pipeline_config.json from the current working directory and exposes:
  - CONFIG (dict)
  - HERBS (list of dicts: cn, pinyin, latin[], supplement_compounds_csv?)
  - DISEASES (dict: key -> {name, opentargets_query})
  - FILTERS (dict: ob_min, dl_min, string_score_min, disease_top_n)
  - DOCKING (dict)

Each stage script should `import pipeline_config as PC` and use PC.HERBS etc.
If no pipeline_config.json is present in cwd, falls back to the
original hardcoded 健脑安神 formula + 3 diseases so old behavior is preserved.
"""
import json
import os


DEFAULT_HERBS = [
    {"cn": "酸枣仁", "pinyin": "Suanzaoren", "latin": ["Ziziphi Spinosae Semen"]},
    {"cn": "核桃仁", "pinyin": "Hetaoren", "latin": ["Juglandis Semen"]},
    {"cn": "黄精", "pinyin": "Huangjing", "latin": ["Polygonati Rhizoma"]},
    {"cn": "枸杞子", "pinyin": "Gouqizi", "latin": ["Lycii Fructus"]},
    {"cn": "桑葚", "pinyin": "Sangshen", "latin": ["Mori Fructus"]},
    {"cn": "当归", "pinyin": "Danggui", "latin": ["Angelicae Sinensis Radix"]},
    {"cn": "龙眼肉", "pinyin": "Longyanrou",
     "latin": ["Arillus Longan", "Longan Arillus", "Dimocarpus Longan"]},
    {"cn": "茯苓", "pinyin": "Fuling", "latin": ["Poria Cocos(Schw.) Wolf."]},
    {"cn": "莲子", "pinyin": "Lianzi", "latin": ["Nelumbinis Semen", "Nelumbinis Plumula"]},
    {"cn": "百合", "pinyin": "Baihe", "latin": ["Lilii Bulbus"]},
    {"cn": "益智仁", "pinyin": "Yizhiren", "latin": ["Alpiniae Oxyphyliae Fructus"]},
    {"cn": "五味子", "pinyin": "Wuweizi", "latin": ["Schisandrae Chinensis Fructus"]},
    {"cn": "天麻", "pinyin": "Tianma", "latin": ["Gastrodiae Rhizoma", "Gastrodia Elata"]},
    {"cn": "山药", "pinyin": "Shanyao", "latin": ["Rhizoma Dioscoreae"]},
]

DEFAULT_DISEASES = {
    "insomnia":  {"name": "Insomnia",            "opentargets_query": "Insomnia"},
    "alzheimer": {"name": "Alzheimer's disease", "opentargets_query": "Alzheimer's disease"},
    "anxiety":   {"name": "Anxiety disorder",    "opentargets_query": "Anxiety disorder"},
}

DEFAULT_FILTERS = {
    "ob_min": 30,
    "dl_min": 0.18,
    "supp_ob_min": 30,          # relaxed OB-only filter for supplement-herb compounds
    "supp_dl_min": None,        # None = skip DL filter for supplement herbs
    "string_score_min": 400,
    "disease_top_n": 500,
}

DEFAULT_DOCKING = {
    "enabled": False,
    "n_receptors": 5,
    "n_ligands": 5,
    "pdb_map_extra": {},
}


def _load():
    path = os.path.abspath("pipeline_config.json")
    if os.path.exists(path):
        with open(path) as f:
            cfg = json.load(f)
    else:
        cfg = {}

    herbs = cfg.get("herbs", DEFAULT_HERBS)
    diseases = cfg.get("diseases", DEFAULT_DISEASES)
    # Allow diseases as a list of dicts too (with `key`), normalize to dict
    if isinstance(diseases, list):
        diseases = {d["key"]: {"name": d["name"],
                               "opentargets_query": d.get("opentargets_query", d["name"])}
                    for d in diseases}

    filters = {**DEFAULT_FILTERS, **cfg.get("filters", {})}
    docking = {**DEFAULT_DOCKING, **cfg.get("docking", {})}

    return {
        "project_name": cfg.get("project_name", "default"),
        "config_path":  path if os.path.exists(path) else None,
        "herbs":        herbs,
        "diseases":     diseases,
        "filters":      filters,
        "docking":      docking,
    }


CONFIG = _load()
HERBS = CONFIG["herbs"]
DISEASES = CONFIG["diseases"]
FILTERS = CONFIG["filters"]
DOCKING = CONFIG["docking"]


def herb_map_tuples():
    """Legacy-compatible (cn, pinyin, [latin]) tuples for stage1 scraper."""
    return [(h["cn"], h["pinyin"], h.get("latin", [])) for h in HERBS]


def supplement_herbs():
    """List of herbs that ship a literature supplement CSV."""
    return [h for h in HERBS if h.get("supplement_compounds_csv")]


if __name__ == "__main__":
    print(f"project_name: {CONFIG['project_name']}")
    print(f"config_path:  {CONFIG['config_path']}")
    print(f"herbs:        {len(HERBS)}")
    for h in HERBS:
        tag = " (supplement)" if h.get("supplement_compounds_csv") else ""
        print(f"  - {h['cn']} / {h['pinyin']} / {h.get('latin', [])}{tag}")
    print(f"diseases:     {list(DISEASES.keys())}")
    print(f"filters:      {FILTERS}")
    print(f"docking:      {DOCKING}")
