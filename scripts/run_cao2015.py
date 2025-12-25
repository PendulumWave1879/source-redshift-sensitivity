# -*- coding: utf-8 -*-
"""
Run the Source–Redshift Sensitivity metric on the Cao+2015 lens compilation.

Inputs:
  data/processed/cao2015/cao2015_joined_clean.csv
    Required columns:
      - z_l   (lens redshift)
      - z_s   (source redshift)
      - theta_E_arcsec  (Einstein radius proxy, arcsec)
    Optional/provenance columns:
      - Name, Survey, etc.

Outputs:
  outputs/cao2015_results.csv

Usage (from project root):
  python scripts/run_cao2015.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

# If "src" isn't importable when running as a script, add project root to sys.path.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.sensitivity import compute_sensitivity  # noqa: E402


INFILE_DEFAULT = ROOT / "data" / "processed" / "cao2015" / "cao2015_joined_clean.csv"
OUTFILE_DEFAULT = ROOT / "outputs" / "cao2015_results.csv"


def main():
    infile = INFILE_DEFAULT
    outfile = OUTFILE_DEFAULT

    if not infile.exists():
        raise SystemExit(f"Missing input file: {infile}\n"
                         f"Did you run: python scripts/ingest_cao2015.py ?")

    outfile.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(infile)

    # Column normalization: accept a few common spellings
    colmap = {}
    for c in df.columns:
        lc = c.strip().lower()
        if lc in ("zl", "z_l", "lens_z", "zfg"):
            colmap[c] = "z_l"
        elif lc in ("zs", "z_s", "source_z", "zbg"):
            colmap[c] = "z_s"
        elif lc in ("thetae", "theta_e", "theta_e_arcsec", "thetae_arcsec", "bsie"):
            colmap[c] = "theta_E_arcsec"

    if colmap:
        df = df.rename(columns=colmap)

    required = {"z_l", "z_s", "theta_E_arcsec"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(
            "Missing required columns in input:\n"
            f"  {sorted(missing)}\n\n"
            f"Columns present:\n  {list(df.columns)}"
        )

    # Compute sensitivity per row
    rows = []
    invalid = 0
    for i, r in df.iterrows():
        name = r["Name"] if "Name" in df.columns else r.get("name", f"row_{i}")
        zl = float(r["z_l"])
        zs = float(r["z_s"])
        th = float(r["theta_E_arcsec"])

        # compute_sensitivity is assumed to do its own validation and return a dict
        res = compute_sensitivity(theta_E_arcsec=th, z_l=zl, z_s=zs)

        out = dict(r)  # keep provenance columns
        out["is_valid"] = bool(res.get("is_valid", True))
        out["flags"] = res.get("flags", [])
        if isinstance(out["flags"], list):
            out["flags"] = ";".join(out["flags"])

        # Standardize output column name
        out["S_dlnM_dzs"] = res.get("S_dlnM_dzs", np.nan)

        # Include a convenience delta_z
        out["delta_z"] = zs - zl

        # Keep a stable ID column
        out["lens_id"] = name

        if not out["is_valid"] or not np.isfinite(out["S_dlnM_dzs"]):
            invalid += 1

        rows.append(out)

    outdf = pd.DataFrame(rows)

    # Write
    outdf.to_csv(outfile, index=False)

    # Console summary
    total = len(outdf)
    valid = int((outdf["is_valid"] == True).sum())  # noqa: E712
    invalid = total - valid

    print(f"Input:  {infile}")
    print(f"Output: {outfile}\n")

    print(f"Total systems: {total}")
    print(f"Valid systems: {valid}")
    print(f"Invalid systems: {invalid}\n")

    # Flag counts
    flags_series = outdf.loc[outdf["flags"].fillna("") != "", "flags"].astype(str)
    flag_counts = {}
    for fstr in flags_series:
        for f in [x for x in fstr.split(";") if x]:
            flag_counts[f] = flag_counts.get(f, 0) + 1

    print("Flag counts:")
    if flag_counts:
        for k in sorted(flag_counts):
            print(f"  {k}: {flag_counts[k]}")
    else:
        print("  (none)")

    # Extremes (only on valid finite S)
    vdf = outdf[(outdf["is_valid"] == True) & np.isfinite(outdf["S_dlnM_dzs"])].copy()  # noqa: E712
    if len(vdf) == 0:
        print("\nNo valid finite S values to summarize.")
        return

    vdf = vdf.sort_values("S_dlnM_dzs")
    print("\nMost negative S (largest mass decrease per +Δz_s):")
    for _, rr in vdf.head(10).iterrows():
        print(
            f"  {rr['lens_id']:<12}  S={rr['S_dlnM_dzs']:+.6f}  "
            f"z_l={rr['z_l']:.3f}  z_s={rr['z_s']:.3f}  thetaE={rr['theta_E_arcsec']:.3f} arcsec"
        )

    print("\nLeast negative / most positive S:")
    for _, rr in vdf.tail(10).iloc[::-1].iterrows():
        print(
            f"  {rr['lens_id']:<12}  S={rr['S_dlnM_dzs']:+.6f}  "
            f"z_l={rr['z_l']:.3f}  z_s={rr['z_s']:.3f}  thetaE={rr['theta_E_arcsec']:.3f} arcsec"
        )


if __name__ == "__main__":
    main()

