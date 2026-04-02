#!/usr/bin/env python3
"""
Stage 7: Molecular Docking
- Select top core targets as receptors
- Select top active compounds as ligands
- Download structures from PDB/PubChem
- Dock with AutoDock Vina
- Generate binding energy heatmap
"""
import pandas as pd
import requests
import subprocess
import os
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

os.makedirs("results/docking", exist_ok=True)
os.makedirs("results/docking/receptors", exist_ok=True)
os.makedirs("results/docking/ligands", exist_ok=True)

# Load data
core = pd.read_csv("results/tables/core_targets.csv")
compounds = pd.read_csv("data/compounds/compounds_filtered_all.csv")
drug_targets = pd.read_csv("data/targets/drug_targets.csv")

# Select top 5 core targets by Degree
top_targets = core.head(5)
print("=== Top 5 Core Targets (Receptors) ===")
print(top_targets[['gene_symbol', 'Degree']].to_string(index=False))

# Select top compounds by network connectivity (number of targets)
compound_connectivity = drug_targets.groupby('molecule_name')['gene_symbol'].nunique().reset_index()
compound_connectivity.columns = ['molecule_name', 'n_targets']
compound_connectivity = compound_connectivity.sort_values('n_targets', ascending=False)

# Filter for compounds with SMILES available
compounds_with_smiles = compounds.dropna(subset=['SMILES'])
valid_compounds = compound_connectivity[
    compound_connectivity['molecule_name'].isin(compounds_with_smiles['molecule_name'].unique())
].head(5)

print("\n=== Top 5 Compounds (Ligands) ===")
print(valid_compounds.to_string(index=False))

# Known PDB IDs for common targets
PDB_MAP = {
    "PTGS2": "5IKR",    # COX-2
    "IL6": "1ALU",      # IL-6
    "ESR1": "1ERE",     # Estrogen receptor alpha
    "EGFR": "1M17",     # EGFR kinase
    "TP53": "1TSR",     # p53
    "NR3C1": "1M2Z",    # Glucocorticoid receptor
    "MAOA": "2Z5X",     # Monoamine oxidase A
    "DRD2": "6CM4",     # Dopamine D2 receptor
    "GSK3B": "1Q5K",    # GSK3-beta
    "SLC6A4": "5I6X",   # Serotonin transporter
}

def download_pdb(pdb_id, outpath):
    """Download PDB structure."""
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    r = requests.get(url, timeout=30)
    if r.status_code == 200:
        with open(outpath, 'w') as f:
            f.write(r.text)
        return True
    return False

def smiles_to_pdb(smiles, name, outdir):
    """Convert SMILES to 3D PDB using OpenBabel."""
    sdf_path = os.path.join(outdir, f"{name}.sdf")
    pdb_path = os.path.join(outdir, f"{name}.pdb")

    # Write SMILES to file
    smi_path = os.path.join(outdir, f"{name}.smi")
    with open(smi_path, 'w') as f:
        f.write(smiles)

    # Convert SMILES -> 3D SDF -> PDB
    try:
        subprocess.run(
            ["obabel", smi_path, "-O", sdf_path, "--gen3d", "-h"],
            capture_output=True, text=True, timeout=60
        )
        subprocess.run(
            ["obabel", sdf_path, "-O", pdb_path],
            capture_output=True, text=True, timeout=30
        )
        if os.path.exists(pdb_path) and os.path.getsize(pdb_path) > 0:
            return pdb_path
    except Exception as e:
        print(f"    OpenBabel error for {name}: {e}")
    return None

def prepare_receptor(pdb_path, pdbqt_path):
    """Prepare receptor for Vina (remove water, add charges)."""
    # Use obabel to convert PDB to PDBQT
    try:
        result = subprocess.run(
            ["obabel", pdb_path, "-O", pdbqt_path, "-xr"],
            capture_output=True, text=True, timeout=60
        )
        if os.path.exists(pdbqt_path) and os.path.getsize(pdbqt_path) > 0:
            return True
    except:
        pass
    return False

def prepare_ligand(pdb_path, pdbqt_path):
    """Prepare ligand for Vina."""
    try:
        result = subprocess.run(
            ["obabel", pdb_path, "-O", pdbqt_path],
            capture_output=True, text=True, timeout=60
        )
        if os.path.exists(pdbqt_path) and os.path.getsize(pdbqt_path) > 0:
            return True
    except:
        pass
    return False

def get_center_of_mass(pdb_path):
    """Get center of mass from PDB for docking box."""
    coords = []
    with open(pdb_path) as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                coords.append((x, y, z))
    if coords:
        coords = np.array(coords)
        return coords.mean(axis=0)
    return [0, 0, 0]

def run_vina(receptor_pdbqt, ligand_pdbqt, center, output_path, box_size=25):
    """Run AutoDock Vina."""
    try:
        cmd = [
            "vina",
            "--receptor", receptor_pdbqt,
            "--ligand", ligand_pdbqt,
            "--center_x", str(center[0]),
            "--center_y", str(center[1]),
            "--center_z", str(center[2]),
            "--size_x", str(box_size),
            "--size_y", str(box_size),
            "--size_z", str(box_size),
            "--out", output_path,
            "--exhaustiveness", "8",
            "--num_modes", "3"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        # Parse binding energy from output
        for line in result.stdout.split('\n'):
            if line.strip().startswith('1'):
                parts = line.split()
                if len(parts) >= 2:
                    return float(parts[1])
    except Exception as e:
        print(f"    Vina error: {e}")
    return None


# === Download and prepare receptors ===
print("\n=== Downloading receptor structures ===")
receptor_files = {}
for _, row in top_targets.iterrows():
    gene = row['gene_symbol']
    if gene in PDB_MAP:
        pdb_id = PDB_MAP[gene]
        pdb_path = f"results/docking/receptors/{gene}_{pdb_id}.pdb"
        pdbqt_path = f"results/docking/receptors/{gene}_{pdb_id}.pdbqt"

        if download_pdb(pdb_id, pdb_path):
            if prepare_receptor(pdb_path, pdbqt_path):
                center = get_center_of_mass(pdb_path)
                receptor_files[gene] = {"pdbqt": pdbqt_path, "center": center}
                print(f"  {gene} ({pdb_id}): OK, center={center}")
            else:
                print(f"  {gene}: PDBQT preparation failed")
        else:
            print(f"  {gene}: PDB download failed")

# === Download and prepare ligands ===
print("\n=== Preparing ligand structures ===")
# Get SMILES for top compounds
ligand_files = {}
for _, row in valid_compounds.iterrows():
    name = row['molecule_name']
    smiles_row = compounds_with_smiles[compounds_with_smiles['molecule_name'] == name].iloc[0]
    smiles = smiles_row['SMILES']

    # Clean name for filename
    safe_name = "".join(c if c.isalnum() else '_' for c in name)[:30]
    pdb_path = smiles_to_pdb(smiles, safe_name, "results/docking/ligands")

    if pdb_path:
        pdbqt_path = pdb_path.replace('.pdb', '.pdbqt')
        if prepare_ligand(pdb_path, pdbqt_path):
            ligand_files[name] = pdbqt_path
            print(f"  {name}: OK")
        else:
            print(f"  {name}: PDBQT preparation failed")
    else:
        print(f"  {name}: 3D generation failed")

# === Run Docking ===
print(f"\n=== Running Molecular Docking ===")
print(f"Receptors: {len(receptor_files)}, Ligands: {len(ligand_files)}")

docking_results = []
for target, rec_info in receptor_files.items():
    for compound, lig_path in ligand_files.items():
        safe_compound = "".join(c if c.isalnum() else '_' for c in compound)[:20]
        out_path = f"results/docking/{target}_{safe_compound}_out.pdbqt"

        print(f"  Docking {compound} -> {target}...", end=" ")
        energy = run_vina(rec_info["pdbqt"], lig_path, rec_info["center"], out_path)

        if energy is not None:
            print(f"{energy:.2f} kcal/mol")
            docking_results.append({
                "target": target,
                "compound": compound,
                "binding_energy": energy
            })
        else:
            print("FAILED")

# === Generate Heatmap ===
if docking_results:
    results_df = pd.DataFrame(docking_results)
    results_df.to_csv("results/tables/docking_results.csv", index=False)

    # Pivot for heatmap
    pivot = results_df.pivot(index='compound', columns='target', values='binding_energy')

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', center=-5,
                linewidths=0.5, ax=ax, cbar_kws={'label': 'Binding Energy (kcal/mol)'})
    ax.set_title('Molecular Docking Results\n(Binding Energy, kcal/mol)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Target Protein', fontsize=12)
    ax.set_ylabel('Active Compound', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig("results/figures/docking_heatmap.png", dpi=300, bbox_inches='tight')
    plt.savefig("results/figures/docking_heatmap.pdf", bbox_inches='tight')
    print("\nSaved: results/figures/docking_heatmap.png")

    print("\n=== Docking Summary ===")
    print(results_df.sort_values('binding_energy').to_string(index=False))
    print(f"\nNote: More negative values indicate stronger binding")
    print(f"Threshold: < -5.0 kcal/mol = good, < -7.0 = strong")
else:
    print("\nNo docking results obtained!")
