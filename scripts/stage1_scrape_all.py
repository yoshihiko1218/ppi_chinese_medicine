#!/usr/bin/env python3
"""Scrape TCMSP for all 14 herbs and filter compounds."""
import os
import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import lxml.html
import time
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_config as PC

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
            return True
        return False

    def get_herb_data(self, herb_en_name):
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
                if label in results:
                    continue
                pattern = rf'\$\(\s*"#\s*{grid_name}\s*"\s*\).*?data\s*:\s*(\[[\s\S]*?\])\s*[,\}}]'
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    raw_json = re.sub(r'\n\s*', ' ', match.group(1))
                    try:
                        results[label] = json.loads(raw_json)
                    except json.JSONDecodeError:
                        pass
        return results

    def resolve_cn_name(self, cn_name):
        """Resolve a Chinese herb name to TCMSP's official (cn, en, pinyin) triples.

        Uses the `qs=herb_all_name` endpoint which returns matches across all
        three name columns. Returns a list of dicts with herb_cn_name,
        herb_en_name, herb_pinyin. Empty list if no match.
        """
        import urllib.parse as _up
        url = (f"{self.root_url}?qs=herb_all_name"
               f"&q={_up.quote(cn_name)}&token={self.token}")
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
        except Exception:
            return []
        soup = bs(resp.text, "html.parser")
        for script in soup.find_all("script"):
            text = str(script)
            m = re.search(r"data:\s*(\[[\s\S]*?\])\s*,", text, re.DOTALL)
            if m:
                raw = re.sub(r'\n\s*', ' ', m.group(1))
                try:
                    rows = json.loads(raw)
                    if isinstance(rows, list):
                        return rows
                except Exception:
                    pass
        return []

# Herb mapping loaded from pipeline_config.json (falls back to 健脑安神 defaults)
HERB_MAP = PC.herb_map_tuples()

if __name__ == "__main__":
    os.makedirs("data/compounds", exist_ok=True)
    os.makedirs("data/targets", exist_ok=True)
    ob_min = PC.FILTERS["ob_min"]
    dl_min = PC.FILTERS["dl_min"]
    print(f"Pipeline: {PC.CONFIG['project_name']} "
          f"({len(HERB_MAP)} herbs, OB>={ob_min}%, DL>={dl_min})")

    scraper = TCMSPScraper()
    if not scraper.get_token():
        print("ERROR: Cannot connect to TCMSP")
        exit(1)

    all_ingredients = []
    all_targets = []
    failed_herbs = []

    for cn_name, pinyin, en_names in HERB_MAP:
        print(f"\n{'='*50}")
        print(f"Processing: {cn_name} ({pinyin})")

        data = None
        used_name = None
        for en_name in en_names:
            data = scraper.get_herb_data(en_name)
            if data and "ingredients" in data and len(data["ingredients"]) > 0:
                used_name = en_name
                break
            time.sleep(1)

        # If user-supplied names all failed, try auto-resolving via Chinese name
        if not (data and data.get("ingredients")):
            # Try the raw Chinese name and (for processed herbs) drop common prefixes
            for probe_cn in [cn_name,
                             cn_name.lstrip("酒生熟炙炒焦").strip() if cn_name[0] in "酒生熟炙炒焦" else None]:
                if not probe_cn:
                    continue
                rows = scraper.resolve_cn_name(probe_cn)
                for row in rows:
                    resolved_en = row.get("herb_en_name")
                    if not resolved_en:
                        continue
                    print(f"  Auto-resolved {probe_cn} -> {resolved_en}")
                    time.sleep(1)
                    data = scraper.get_herb_data(resolved_en)
                    if data and data.get("ingredients"):
                        used_name = f"{resolved_en} (auto-resolved from {probe_cn})"
                        break
                if data and data.get("ingredients"):
                    break
                time.sleep(0.5)

        if data and "ingredients" in data:
            print(f"  Found via: {used_name}")
            # Save raw data
            for label, records in data.items():
                if records:
                    df = pd.DataFrame(records)
                    df.to_csv(f"data/compounds/{pinyin}_{label}.csv", index=False)
                    print(f"  {label}: {len(df)} entries")

            # Add herb info to ingredients
            ing_df = pd.DataFrame(data["ingredients"])
            ing_df["herb_cn"] = cn_name
            ing_df["herb_pinyin"] = pinyin
            all_ingredients.append(ing_df)

            # Add herb info to targets
            if "targets" in data:
                tar_df = pd.DataFrame(data["targets"])
                tar_df["herb_cn"] = cn_name
                tar_df["herb_pinyin"] = pinyin
                all_targets.append(tar_df)
        else:
            print(f"  WARNING: No data found for {cn_name}!")
            failed_herbs.append(cn_name)

        time.sleep(2)  # Be polite to the server

    # Combine all ingredients
    if all_ingredients:
        combined = pd.concat(all_ingredients, ignore_index=True)
        combined.to_csv("data/compounds/all_ingredients_raw.csv", index=False)
        print(f"\n{'='*50}")
        print(f"Total raw ingredients: {len(combined)}")
        print(f"Unique compounds (by MOL_ID): {combined['MOL_ID'].nunique()}")

        # Filter: OB and DL thresholds from config
        combined['ob'] = pd.to_numeric(combined['ob'], errors='coerce')
        combined['dl'] = pd.to_numeric(combined['dl'], errors='coerce')
        filtered = combined[(combined['ob'] >= ob_min) & (combined['dl'] >= dl_min)].copy()
        filtered.to_csv("data/compounds/compounds_filtered.csv", index=False)
        print(f"After OB>={ob_min}%, DL>={dl_min}: {len(filtered)} entries ({filtered['MOL_ID'].nunique()} unique compounds)")

        # Summary per herb
        print(f"\nPer-herb summary (filtered):")
        for cn in filtered['herb_cn'].unique():
            n = filtered[filtered['herb_cn'] == cn]['MOL_ID'].nunique()
            print(f"  {cn}: {n} compounds")

    if all_targets:
        combined_tar = pd.concat(all_targets, ignore_index=True)
        combined_tar.to_csv("data/targets/tcmsp_targets_raw.csv", index=False)
        print(f"\nTotal TCMSP targets: {len(combined_tar)}")

    if failed_herbs:
        print(f"\nFailed herbs (need manual supplement): {failed_herbs}")
