#!/usr/bin/env python3
"""Scrape TCMSP for herb compound data using the embedded JSON approach."""
import os
import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import lxml.html
import time

class TCMSPScraper:
    def __init__(self):
        self.root_url = "https://www.tcmsp-e.com/tcmspsearch.php"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; NCE-AL10 Build/HUAWEINCE-AL10; wv) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self.token = None

    def get_token(self):
        resp = requests.get(self.root_url, headers=self.headers, timeout=30)
        root = lxml.html.fromstring(resp.content)
        token = root.xpath('//form[@id="SearchForm"]//input[@name="token"]/@value')
        if token:
            self.token = token[0]
            print(f"Token obtained: {self.token}")
            return True
        print("Failed to get token")
        return False

    def get_herb_data(self, herb_en_name):
        """Fetch ingredients, targets, diseases for a herb."""
        en_name = herb_en_name.replace(" ", "%20")
        url = f"{self.root_url}?qr={en_name}&qsr=herb_en_name&token={self.token}"

        resp = requests.get(url, headers=self.headers, timeout=30)
        html = resp.text

        soup = bs(html, "html.parser")
        scripts = soup.find_all("script")

        results = {}
        grid_labels = {"grid": "ingredients", "grid2": "targets", "grid3": "diseases"}

        for script in scripts:
            text = str(script)
            for grid_name, label in grid_labels.items():
                if grid_name in results:
                    continue
                # Match the kendo grid data pattern - more flexible regex
                pattern = rf'\$\(\s*"#\s*{grid_name}\s*"\s*\).*?data\s*:\s*(\[[\s\S]*?\])\s*[,\}}]'
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    raw_json = match.group(1)
                    # Clean up the JSON - remove newlines within strings
                    raw_json = re.sub(r'\n\s*', ' ', raw_json)
                    try:
                        data = json.loads(raw_json)
                        results[label] = data
                        print(f"  {label}: {len(data)} entries")
                    except json.JSONDecodeError as e:
                        # Try a more aggressive cleanup
                        # Sometimes there are unescaped characters
                        raw_json = raw_json.replace('\\"', '"').replace('\\n', ' ')
                        try:
                            data = json.loads(raw_json)
                            results[label] = data
                            print(f"  {label}: {len(data)} entries (cleaned)")
                        except json.JSONDecodeError:
                            print(f"  {label}: JSON parse error - {str(e)[:100]}")
                            # Save raw for debugging
                            with open(f"data/compounds/debug_{grid_name}.txt", "w") as f:
                                f.write(raw_json[:5000])

        return results

    def scrape_herb(self, herb_cn, herb_pinyin, herb_en, output_dir="data/compounds"):
        """Scrape and save data for one herb."""
        print(f"\nProcessing: {herb_cn} ({herb_pinyin})")
        data = self.get_herb_data(herb_en)

        if not data:
            print(f"  WARNING: No data for {herb_cn}")
            return None

        for label, records in data.items():
            if records:
                df = pd.DataFrame(records)
                outpath = os.path.join(output_dir, f"{herb_pinyin}_{label}.csv")
                df.to_csv(outpath, index=False)
                print(f"  Saved: {outpath} ({len(df)} rows)")

        return data


# Herb mapping: cn_name -> (pinyin, en_name)
HERB_MAP = {
    "酸枣仁": ("Suanzaoren", "Ziziphi Spinosae Semen"),
    "核桃仁": ("Hetaoren", "Juglandis Semen"),
    "黄精": ("Huangjing", "Polygonati Rhizoma"),
    "枸杞子": ("Gouqizi", "Lycii Fructus"),
    "桑葚": ("Sangshen", "Mori Fructus"),
    "当归": ("Danggui", "Angelicae Sinensis Radix"),
    "龙眼肉": ("Longyanrou", "Arillus Longan"),  # May not be in TCMSP
    "茯苓": ("Fuling", "Poria Cocos(Schw.) Wolf."),
    "莲子": ("Lianzi", "Nelumbinis Semen"),  # TCMSP has 莲子心
    "百合": ("Baihe", "Lilii Bulbus"),
    "益智仁": ("Yizhi", "Alpiniae Oxyphyliae Fructus"),
    "五味子": ("Wuweizi", "Schisandrae Chinensis Fructus"),
    "天麻": ("Tianma", "Gastrodiae Rhizoma"),  # May not be in TCMSP
    "山药": ("Shanyao", "Rhizoma Dioscoreae"),
}

if __name__ == "__main__":
    os.makedirs("data/compounds", exist_ok=True)

    scraper = TCMSPScraper()
    if not scraper.get_token():
        print("Cannot connect to TCMSP. Exiting.")
        exit(1)

    # Test with ONE herb first
    test_herb = "酸枣仁"
    pinyin, en_name = HERB_MAP[test_herb]
    data = scraper.scrape_herb(test_herb, pinyin, en_name)

    if data and "ingredients" in data:
        df = pd.DataFrame(data["ingredients"])
        print(f"\n=== {test_herb} Ingredients Summary ===")
        print(f"Total compounds: {len(df)}")
        print(f"Columns: {list(df.columns)}")

        # Show OB/DL filtering
        if 'OB(%)' in df.columns and 'DL' in df.columns:
            df['OB(%)'] = pd.to_numeric(df['OB(%)'], errors='coerce')
            df['DL'] = pd.to_numeric(df['DL'], errors='coerce')
            filtered = df[(df['OB(%)'] >= 30) & (df['DL'] >= 0.18)]
            print(f"After OB>=30%, DL>=0.18 filter: {len(filtered)} compounds")
            if len(filtered) > 0:
                print(filtered[['MOL_ID', 'molecule_name', 'OB(%)', 'DL']].to_string())
