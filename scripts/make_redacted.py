#!/usr/bin/env python3
"""
Create a redacted version of METHODS_AND_RESULTS.md that hides
the formula composition (herb names, doses, pinyin, Latin names).
Replaces with generic "Herb 1", "Herb 2", etc.
"""
import re

with open("METHODS_AND_RESULTS.md", "r") as f:
    text = f.read()

# Herb mapping: all identifiers -> generic labels
herbs = [
    # (chinese, pinyin, latin, label)
    ("酸枣仁", "Suanzaoren", "Ziziphi Spinosae Semen", "Herb 1"),
    ("核桃仁", "Hetaoren", "Juglandis Semen", "Herb 2"),
    ("黄精", "Huangjing", "Polygonati Rhizoma", "Herb 3"),
    ("枸杞子", "Gouqizi", "Lycii Fructus", "Herb 4"),
    ("桑葚", "Sangshen", "Mori Fructus", "Herb 5"),
    ("当归", "Danggui", "Angelicae Sinensis Radix", "Herb 6"),
    ("龙眼肉", "Longyanrou", "Arillus Longan", "Herb 7"),
    ("茯苓", "Fuling", "Poria Cocos", "Herb 8"),
    ("莲子", "Lianzi", "Nelumbinis Plumula", "Herb 9"),
    ("百合", "Baihe", "Lilii Bulbus", "Herb 10"),
    ("益智仁", "Yizhiren", "Alpiniae Oxyphyliae Fructus", "Herb 11"),
    ("五味子", "Wuweizi", "Schisandrae Chinensis Fructus", "Herb 12"),
    ("天麻", "Tianma", "Gastrodiae Rhizoma", "Herb 13"),
    ("山药", "Shanyao", "Rhizoma Dioscoreae", "Herb 14"),
]

# Also need to handle partial Latin names and alternative forms
extra_replacements = [
    ("Longan Arillus", "Herb 7"),
    ("Poria Cocos(Schw.) Wolf.", "Herb 8 (Latin name)"),
    ("Nelumbinis Semen", "Herb 9"),
    ("Gastrodia elata", "Herb 13 plant"),
    ("Gastrodia Elata", "Herb 13 plant"),
    ("Dimocarpus longan", "Herb 7 plant"),
    ("longan arillus", "Herb 7"),
    ("longan", "Herb 7 plant"),
    ("Longan", "Herb 7"),
    # Specific compound names that reveal the herb
    ("Gastrodin", "Compound-H13-A"),
    ("gastrodin", "Compound-H13-A"),
    ("Parishin", "Compound-H13-B"),
    ("parishin", "Compound-H13-B"),
    ("jujuboside", "Compound-H1-A"),
    ("Jujuboside", "Compound-H1-A"),
    ("sanjoinenine", "Compound-H1-B"),
    ("zizyphusine", "Compound-H1-C"),
]

# Replace title
text = text.replace(
    "# Network Pharmacology Study of a 健脑安神 (Brain-Nourishing, Mind-Calming) Formula",
    "# Network Pharmacology Study of a Traditional Chinese Medicine Formula"
)
text = text.replace("健脑安神", "TCM")

# Replace the entire herb table section with a generic version
old_herb_table = """**Herbs searched (14 total):**

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
| 天麻 | *Not in TCMSP — supplemented from literature* | 11 (supplemented) |"""

new_herb_table = """**Herbs searched (14 total):**

| Herb | TCMSP Status | Raw Compounds |
|---|---|---|
| Herb 1 | Found | 33 |
| Herb 2 | Found | 42 |
| Herb 3 | Found | 38 |
| Herb 4 | Found | 188 |
| Herb 5 | Found | 91 |
| Herb 6 | Found | 125 |
| Herb 7 | *Supplemented from literature* | 10 |
| Herb 8 | Found | 34 |
| Herb 9 | Found | 31 |
| Herb 10 | Found | 84 |
| Herb 11 | Found | 41 |
| Herb 12 | Found | 130 |
| Herb 13 | *Supplemented from literature* | 11 |
| Herb 14 | Found | 71 |"""

text = text.replace(old_herb_table, new_herb_table)

# Replace the literature references sections for Herb 7 and 13
# Find and replace the entire 龙眼肉 literature section
longan_section_start = "#### 龙眼肉 (Longan Arillus) — Literature Sources for Active Compounds"
tianma_section_start = "#### 天麻 (Gastrodiae Rhizoma) — Literature Sources for Active Compounds"

# Replace both literature sections with generic versions
idx1 = text.find(longan_section_start)
idx2 = text.find(tianma_section_start)
if idx1 >= 0 and idx2 >= 0:
    # Find the end of Tianma section (next double newline + non-indented text)
    idx_end = text.find("\n**Total raw", idx2)
    if idx_end >= 0:
        old_section = text[idx1:idx_end]
        new_section = """#### Herb 7 — Literature Sources for Active Compounds

The active compounds of Herb 7 (including Gallic acid, Ellagic acid, Quercetin, Kaempferol, beta-Sitosterol, Adenine, Adenosine, Uridine, Ethyl gallate, Corilagin) were compiled from published phytochemistry reviews and network pharmacology studies. [5 references — details available upon request]

#### Herb 13 — Literature Sources for Active Compounds

The active compounds of Herb 13 (including specific characteristic compounds and shared compounds such as beta-Sitosterol, Vanillin, Daucosterol, Succinic acid) were compiled from published phytochemistry reviews and pharmacology studies. [5 references — details available upon request]

"""
        text = text[:idx1] + new_section + text[idx_end:]

# Replace the supplementary note
text = text.replace(
    "**Note:** 龙眼肉 (Longan Arillus) and 天麻 (Gastrodiae Rhizoma) were not registered in the TCMSP database. Their active compounds were supplemented from published phytochemistry and pharmacology literature, as detailed below.",
    "**Note:** Herb 7 and Herb 13 were not registered in the TCMSP database. Their active compounds were supplemented from published phytochemistry and pharmacology literature, as detailed below."
)

# Replace per-herb filtered compound table
old_filtered = """| Herb | Filtered Compounds |
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
| 当归 | 2 |"""

new_filtered = """| Herb | Filtered Compounds |
|---|---|
| Herb 4 | 45 |
| Herb 14 | 16 |
| Herb 8 | 15 |
| Herb 3 | 12 |
| Herb 9 | 11 |
| Herb 13 | 11 |
| Herb 7 | 10 |
| Herb 1 | 9 |
| Herb 12 | 8 |
| Herb 10 | 7 |
| Herb 5 | 6 |
| Herb 2 | 4 |
| Herb 11 | 4 |
| Herb 6 | 2 |"""

text = text.replace(old_filtered, new_filtered)

# Replace per-herb target table
old_targets = """| Herb | Unique Gene Targets |
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
| 五味子 | 12 |"""

new_targets = """| Herb | Unique Gene Targets |
|---|---|
| Herb 9 | 143 |
| Herb 4 | 129 |
| Herb 7 | 125 |
| Herb 5 | 108 |
| Herb 3 | 63 |
| Herb 13 | 57 |
| Herb 10 | 43 |
| Herb 6 | 39 |
| Herb 14 | 32 |
| Herb 1 | 26 |
| Herb 11 | 23 |
| Herb 2 | 16 |
| Herb 8 | 15 |
| Herb 12 | 12 |"""

text = text.replace(old_targets, new_targets)

# Replace remaining specific herb references
text = text.replace("For 龙眼肉 and 天麻, targets were obtained by:", "For Herb 7 and Herb 13, targets were obtained by:")
text = text.replace("541 supplementary target entries added for 龙眼肉 and 天麻.", "541 supplementary target entries added for Herb 7 and Herb 13.")
text = text.replace("For supplementary herbs (龙眼肉, 天麻)", "For supplementary herbs (Herb 7, Herb 13)")
text = text.replace("(e.g., Gastrodin, DL=0.06)", "(e.g., a characteristic small-molecule compound with DL=0.06)")

# Replace any remaining Chinese herb names
for cn, pinyin, latin, label in herbs:
    text = text.replace(cn, label)
    text = text.replace(pinyin, f"{label}-pinyin")
    if latin:
        text = text.replace(latin, f"{label} (Latin name)")

# Apply extra replacements
for old, new in extra_replacements:
    text = text.replace(old, new)

# Clean up any double-labels
text = text.replace("Herb 7 plant plant", "Herb 7 plant")

# Save redacted version
with open("METHODS_AND_RESULTS_REDACTED.md", "w") as f:
    f.write(text)

print("Saved: METHODS_AND_RESULTS_REDACTED.md")
print("Verifying no herb names remain...")

# Verify
remaining = []
check_terms = ["酸枣仁", "核桃仁", "黄精", "枸杞子", "桑葚", "当归", "龙眼肉", "茯苓",
               "莲子", "百合", "益智仁", "五味子", "天麻", "山药",
               "Suanzaoren", "Hetaoren", "Huangjing", "Gouqizi", "Sangshen",
               "Danggui", "Longyanrou", "Fuling", "Lianzi", "Baihe",
               "Yizhiren", "Wuweizi", "Tianma", "Shanyao",
               "Ziziphi", "Juglandis", "Polygonati", "Lycii Fructus",
               "Angelicae Sinensis", "Longan Arillus", "Poria Cocos",
               "Nelumbinis", "Lilii Bulbus", "Alpiniae Oxyphyllae",
               "Schisandrae", "Gastrodiae", "Dioscoreae",
               "健脑安神", "10g", "15g", "12g", "6g"]
for term in check_terms:
    if term in text:
        # Find line number
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if term in line:
                remaining.append(f"  Line {i+1}: '{term}' in: {line[:80]}")
                break

if remaining:
    print(f"WARNING: {len(remaining)} terms still found:")
    for r in remaining:
        print(r)
else:
    print("All herb identifiers successfully redacted!")
