#!/usr/bin/env python3
"""
Add Chinese molecular names to the compound list using PubChem API.
PubChem stores synonyms including Chinese names for many compounds.
"""
import pandas as pd
import requests
import time
import json
import urllib.parse

def get_chinese_name_pubchem(compound_name, cid=None):
    """Try to get Chinese synonym from PubChem."""
    # Try by CID first (more reliable)
    if cid and str(cid) != 'nan' and str(cid) != '':
        try:
            cid_int = int(float(cid))
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid_int}/synonyms/JSON"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                synonyms = data.get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])
                # Look for Chinese characters in synonyms
                for syn in synonyms:
                    if any('\u4e00' <= c <= '\u9fff' for c in syn):
                        return syn
        except Exception:
            pass

    # Fallback: try by name
    try:
        encoded = urllib.parse.quote(compound_name.replace("_qt", ""))
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded}/synonyms/JSON"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            synonyms = data.get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])
            for syn in synonyms:
                if any('\u4e00' <= c <= '\u9fff' for c in syn):
                    return syn
    except Exception:
        pass

    return ""

# Well-known Chinese names for common TCM compounds (manual supplement)
KNOWN_CHINESE = {
    "quercetin": "槲皮素",
    "Quercetin": "槲皮素",
    "luteolin": "木犀草素",
    "kaempferol": "山柰酚",
    "Kaempferol": "山柰酚",
    "beta-sitosterol": "β-谷甾醇",
    "beta-Sitosterol": "β-谷甾醇",
    "Stigmasterol": "豆甾醇",
    "campesterol": "菜油甾醇",
    "diosgenin": "薯蓣皂苷元",
    "baicalein": "黄芩素",
    "morin": "桑色素",
    "hederagenin": "常春藤皂苷元",
    "Daucosterol": "胡萝卜苷",
    "daucosterol_qt": "胡萝卜苷元",
    "ellagic acid": "鞣花酸",
    "Ellagic acid": "鞣花酸",
    "Gallic acid": "没食子酸",
    "glycitein": "鸡豆黄素A",
    "atropine": "阿托品",
    "Atropine": "阿托品",
    "Cycloartenol": "环阿屯醇",
    "Fucosterol": "墨角藻甾醇",
    "sitosterol": "谷甾醇",
    "Sitosterol alpha1": "α-谷甾醇",
    "phytosterol": "植物甾醇",
    "beta-carotene": "β-胡萝卜素",
    "pachymic acid": "茯苓酸",
    "Poricoic acid A": "茯苓新酸A",
    "Poricoic acid B": "茯苓新酸B",
    "poricoic acid C": "茯苓新酸C",
    "dehydroeburicoic acid": "去氢齿孔酸",
    "trametenolic acid": "栓菌酸",
    "Ergosterol peroxide": "过氧化麦角甾醇",
    "Cerevisterol": "脑甾醇",
    "Nuciferin": "荷叶碱",
    "Armepavine": "去甲荷叶碱",
    "Pronuciferin": "前荷叶碱",
    "(R)-Norcoclaurine": "(R)-去甲乌药碱",
    "(S)-Coclaurine": "(S)-乌药碱",
    "Gastrodin": "天麻素",
    "4-Hydroxybenzyl alcohol": "对羟基苯甲醇",
    "Vanillin": "香草醛",
    "4-Hydroxybenzaldehyde": "对羟基苯甲醛",
    "Vanillyl alcohol": "香草醇",
    "Parishin": "天麻苷A",
    "Parishin B": "天麻苷B",
    "Parishin C": "天麻苷C",
    "Succinic acid": "琥珀酸",
    "Adenine": "腺嘌呤",
    "Adenosine": "腺苷",
    "Uridine": "尿苷",
    "Ethyl gallate": "没食子酸乙酯",
    "Corilagin": "柯里拉京",
    "Mairin": "白桦脂酸",
    "swertisin": "当药黄素",
    "jujuboside A_qt": "酸枣仁皂苷A(苷元)",
    "sanjoinenine": "酸枣仁碱E",
    "zizyphusine": "枣属碱",
    "ceanothic acid": "鼠李酸",
    "Mandenol": "亚油酸乙酯",
    "Ethyl linolenate": "亚麻酸乙酯",
    "3'-Methoxydaidzein": "3'-甲氧基大豆苷元",
    "DFV": "7,4'-二羟基黄烷酮",
    "Isopimaric acid": "异海松酸",
    "Lophenol": "环木菠萝甾醇",
    "Obtusifoliol": "钝叶甾醇",
    "Longikaurin A": "长叶对映贝壳杉素A",
    "Deoxyharringtonine": "脱氧三尖杉酯碱",
    "3-Demethylcolchicine": "3-去甲基秋水仙碱",
    "Isofucosterol": "异墨角藻甾醇",
    "Schizandrer B": "五味子乙素",
    "Gomisin-A": "五味子酯甲",
    "Gomisin G": "五味子酯G",
    "Gomisin R": "五味子酯R",
    "Wuweizisu C": "五味子素丙",
    "Angeloylgomisin O": "当归酰基五味子酯O",
    "(-)-taxifolin": "(-)-花旗松素",
    "Denudatin B": "剥皮素B",
    "Kadsurenone": "南五味子酮",
    "piperlonguminine": "胡椒酰胺",
    "hancinol": "含笑内酯醇",
    "hancinone C": "含笑内酯C",
    "NSC90384": "异紫堇碱",
    "Loureirin A": "龙血素A",
    "Physalin A": "酸浆苦素A",
    "Physcion-8-O-beta-D-gentiobioside": "大黄素-8-O-β-D-龙胆二糖苷",
    "Lantadene A": "马缨丹烯A",
    "CLR": "胆固醇",
    "Cryptoxanthin monoepoxide": "隐黄质环氧化物",
    "delta-Carotene": "δ-胡萝卜素",
    "Doradexanthin": "金鱼黄质",
    "cyanin": "矢车菊素",
    "sitosterol palmitate": "谷甾醇棕榈酸酯",
    "IL10": "白细胞介素-10",
    "IL2": "白细胞介素-2",
    "IL6": "白细胞介素-6",
    "methylprotodioscin_qt": "甲基原薯蓣皂苷元",
    "(2R)-7-hydroxy-2-(4-hydroxyphenyl)chroman-4-one": "(2R)-7-羟基-2-(4-羟基苯基)色满-4-酮",
    "4',5-Dihydroxyflavone": "4',5-二羟基黄酮",
}

# Load compounds
df = pd.read_csv("data/compounds/compounds_filtered_all.csv")
unique = df.drop_duplicates(subset='molecule_name')[['molecule_name', 'PubChem_CID']].copy()

print(f"Looking up Chinese names for {len(unique)} unique compounds...")

# First apply known names
cn_map = {}
found_known = 0
for _, row in unique.iterrows():
    name = row['molecule_name']
    if name in KNOWN_CHINESE:
        cn_map[name] = KNOWN_CHINESE[name]
        found_known += 1

print(f"Known Chinese names: {found_known}")

# Then query PubChem for the rest
need_lookup = [row for _, row in unique.iterrows() if row['molecule_name'] not in cn_map]
print(f"Querying PubChem for {len(need_lookup)} remaining compounds...")

found_pubchem = 0
for row in need_lookup:
    name = row['molecule_name']
    cid = row['PubChem_CID']
    cn = get_chinese_name_pubchem(name, cid)
    if cn:
        cn_map[name] = cn
        found_pubchem += 1
        print(f"  {name} -> {cn}")
    time.sleep(0.35)

print(f"\nPubChem Chinese names found: {found_pubchem}")
print(f"Total with Chinese names: {len(cn_map)}/{len(unique)}")

# Add to dataframe
df['molecule_name_cn'] = df['molecule_name'].map(cn_map).fillna('')

# Save
df.to_csv("data/compounds/compounds_filtered_all.csv", index=False)
print(f"\nSaved updated compounds_filtered_all.csv with 'molecule_name_cn' column")

# Show summary
has_cn = df[df['molecule_name_cn'] != ''].drop_duplicates(subset='molecule_name')
print(f"\nCompounds with Chinese names: {len(has_cn)}/{df['molecule_name'].nunique()}")
print("\nSample:")
print(has_cn[['molecule_name', 'molecule_name_cn', 'herb_cn']].head(20).to_string())
