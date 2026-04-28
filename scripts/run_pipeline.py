#!/usr/bin/env python3
"""
Pipeline orchestrator.

Usage:
    python scripts/run_pipeline.py --run-dir runs/qsfsg
    python scripts/run_pipeline.py --run-dir runs/qsfsg --from 3       # start at stage 3
    python scripts/run_pipeline.py --run-dir runs/qsfsg --only 5       # run only stage 5
    python scripts/run_pipeline.py --run-dir runs/qsfsg --force        # ignore resume cache
    python scripts/run_pipeline.py --run-dir runs/qsfsg --with-docking # run stage 7 too

Run dir must contain `pipeline_config.json`. All stage outputs (data/, results/,
logs/) are written under the run dir so multiple formulas don't clobber each
other.
"""
import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent

# Each stage: (id, label, script, required_outputs_for_skip)
STAGES = [
    (1, "scrape_tcmsp",       "stage1_scrape_all.py",
        ["data/compounds/compounds_filtered.csv"]),
    (1.5, "supplement_missing","stage1_supplement_missing.py",
        ["data/compounds/compounds_filtered_all.csv"]),
    (1.7, "fetch_smiles",     "stage1_get_smiles.py",
        ["data/compounds/smiles_lookup.csv"]),
    (2,   "drug_targets",     "stage2_targets.py",
        ["data/targets/drug_targets.csv"]),
    (2.5, "supp_drug_targets","stage2_supplement_targets.py",
        ["data/targets/drug_targets.csv"]),   # same output; re-run if upstream changed
    (3,   "disease_targets",  "stage3_disease_targets.py",
        ["data/targets/disease_targets.csv"]),
    (4,   "intersection",     "stage4_intersection.py",
        ["data/targets/common_targets.csv", "results/figures/venn_drug_disease.png"]),
    (5,   "ppi_network",      "stage5_ppi_network.py",
        ["results/tables/ppi_topology.csv", "results/tables/core_targets.csv"]),
    (6,   "enrichment",       "stage6_enrichment.py",
        ["data/enrichment/KEGG_2021_Human.csv"]),
    (7,   "docking",          "stage7_docking.py",
        ["results/tables/docking_results.csv"]),
    (8,   "excel_workbook",   "make_excel.py",
        ["results/tables/network_pharmacology_results.xlsx"]),
    (8.5, "excel_individual", "make_individual_excel.py",
        ["results/tables/active_compounds.xlsx"]),
    (9,   "report_md",        "make_report.py",
        ["METHODS_AND_RESULTS.md"]),
    (9.5, "report_pdf",       "make_pdf.py",
        ["METHODS_AND_RESULTS.pdf"]),
]


def outputs_exist(run_dir: Path, paths: list[str]) -> bool:
    return all((run_dir / p).exists() for p in paths)


def run_stage(stage_id, label, script, run_dir: Path, log_dir: Path, env):
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"stage{stage_id}_{label}_{ts}.log"
    cmd = [sys.executable, str(SCRIPTS / script)]
    print(f"\n{'='*60}")
    print(f"[stage {stage_id}: {label}] running")
    print(f"  script:  {script}")
    print(f"  cwd:     {run_dir}")
    print(f"  log:     {log_path}")
    print(f"{'='*60}", flush=True)
    with open(log_path, "w") as lf:
        proc = subprocess.run(
            cmd, cwd=run_dir, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        lf.write(proc.stdout or "")
    # Echo tail of log
    tail = (proc.stdout or "").splitlines()[-40:]
    for line in tail:
        print(line)
    if proc.returncode != 0:
        print(f"\n[stage {stage_id}] FAILED (exit {proc.returncode}) — see {log_path}")
        return False
    print(f"[stage {stage_id}: {label}] OK")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True,
                    help="Directory containing pipeline_config.json; outputs go here")
    ap.add_argument("--from", dest="from_stage", type=float, default=0,
                    help="Start at this stage id (e.g. 3 or 2.5)")
    ap.add_argument("--only", type=float, default=None,
                    help="Run only this stage id")
    ap.add_argument("--force", action="store_true",
                    help="Ignore cached outputs; re-run every stage")
    ap.add_argument("--with-docking", action="store_true",
                    help="Include stage 7 (molecular docking)")
    args = ap.parse_args()

    run_dir = Path(args.run_dir).resolve()
    cfg_path = run_dir / "pipeline_config.json"
    if not cfg_path.exists():
        print(f"ERROR: {cfg_path} not found")
        sys.exit(1)

    for sub in ["data/compounds", "data/targets", "data/enrichment",
                "results/tables", "results/figures", "results/docking", "logs"]:
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    log_dir = run_dir / "logs"

    env = os.environ.copy()
    # Ensure stages can `import pipeline_config` (same directory as run_pipeline.py)
    env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")

    print(f"Run directory: {run_dir}")
    print(f"Config:        {cfg_path}")

    for sid, label, script, req in STAGES:
        if args.only is not None and sid != args.only:
            continue
        if sid < args.from_stage:
            continue
        if sid == 7 and not args.with_docking and args.only != 7:
            print(f"[stage 7: docking] SKIP (use --with-docking to enable)")
            continue
        # Reports always re-generate when explicitly requested via --only or --from
        if sid >= 8 and not args.force and req and outputs_exist(run_dir, req):
            # allow re-running reports if user passed --only/--from explicitly
            if args.only is None and args.from_stage <= 1:
                print(f"[stage {sid}: {label}] SKIP (outputs already present)")
                continue
        if not args.force and req and outputs_exist(run_dir, req):
            print(f"[stage {sid}: {label}] SKIP (outputs already present: {req[0]})")
            continue
        ok = run_stage(sid, label, script, run_dir, log_dir, env)
        if not ok:
            sys.exit(2)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
