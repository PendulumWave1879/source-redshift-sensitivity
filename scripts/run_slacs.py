# -*- coding: utf-8 -*-
"""
Run SLACS sensitivity analysis on the joined clean dataset.

Reads:
  data/processed/slacs/slacs_joined_clean.csv

Writes:
  outputs/slacs_results.csv
  outputs/slacs_report.txt

Usage (from project root):
  python scripts/run_slacs.py

Notes:
  - This script assumes your ingest created columns:
      slacs_id, theta_E_arcsec, z_l, z_s, Good, Ring, ...
  - Sensitivity is computed via src.sensitivity.compute_sensitivity.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------
# Ensure `import src.*` works when running as a script:
# project_root/scripts/run_slacs.py -> add project_root to sys.path
# ---------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cosmology import FlatLambdaCDM  # noqa: E402
from src.sensitivity import compute_sensitivity  # noqa: E402


def _as_float(x):
    try:
        if pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan


def main() -> None:
    input_path = ROOT / "data" / "processed" / "slacs" / "slacs_joined_clean.csv"
    out_dir = ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_csv = out_dir / "slacs_results.csv"
    out_report = out_dir / "slacs_report.txt"

    if not input_path.exists():
        raise SystemExit(f"Missing input: {input_path}\nRun: python scripts/ingest_slacs.py")

    df = pd.read_csv(input_path)

    # Minimal column expectations
    required = ["slacs_id", "theta_E_arcsec", "z_l", "z_s"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Input is missing required columns: {missing}\nFound: {list(df.columns)}")

    # Config (override via env if desired)
    H0 = float(os.environ.get("H0_KM_S_MPC", "70.0"))
    Om0 = float(os.environ.get("OM0", "0.3"))
    h = float(os.environ.get("FD_H", "1e-3"))
    delta_z = float(os.environ.get("DELTA_Z", "0.1"))

    cosmo = FlatLambdaCDM(H0_km_s_Mpc=H0, Om0=Om0)

    rows = []
    flag_counts = {}

    n_total = len(df)
    n_valid = 0
    n_invalid = 0

    for _, r in df.iterrows():
        lens_id = str(r["slacs_id"])

        thetaE = _as_float(r["theta_E_arcsec"])
        zl = _as_float(r["z_l"])
        zs = _as_float(r["z_s"])

        res = compute_sensitivity(
            theta_E_arcsec=thetaE,
            z_l=zl,
            z_s=zs,
            cosmo=cosmo,
            h=h,
            delta_z=delta_z,
        )

        is_valid = bool(res.get("is_valid", False))
        flags = res.get("flags", []) or []
        if isinstance(flags, str):
            flags = [flags] if flags else []

        if is_valid:
            n_valid += 1
        else:
            n_invalid += 1

        for f in flags:
            flag_counts[f] = flag_counts.get(f, 0) + 1

        out = {
            "lens_id": lens_id,
            "theta_E_arcsec": thetaE,
            "z_l": zl,
            "z_s": zs,
            "is_valid": is_valid,
            "flags": ";".join(flags),
            # Key outputs from compute_sensitivity
            "S_dlnM_dzs": res.get("S_dlnM_dzs", np.nan),
            "dM_over_M_for_delta_z": res.get("dM_over_M_for_delta_z", np.nan),
            "M_inf_Msun": res.get("M_inf_Msun", np.nan),
        }

        # Carry through any useful provenance columns if present
        for col in ("Good", "Ring", "name_table4", "name_table5"):
            if col in df.columns:
                out[col] = r[col]

        rows.append(out)

    out_df = pd.DataFrame(rows)
    out_df.to_csv(out_csv, index=False)

    # Report
    report_lines = []
    report_lines.append(f"Input:  {input_path}")
    report_lines.append(f"Output: {out_csv}")
    report_lines.append("")
    report_lines.append(f"Total systems: {n_total}")
    report_lines.append(f"Valid systems: {n_valid}")
    report_lines.append(f"Invalid systems: {n_invalid}")
    report_lines.append("")

    report_lines.append("Flag counts:")
    if flag_counts:
        for k in sorted(flag_counts.keys()):
            report_lines.append(f"  {k}: {flag_counts[k]}")
    else:
        report_lines.append("  (none)")
    report_lines.append("")

    # Rank by S (more negative = larger decrease in inferred mass for +Δz_s)
    valid = out_df[out_df["is_valid"] == True].copy()
    if len(valid) > 0 and "S_dlnM_dzs" in valid.columns:
        valid = valid.sort_values("S_dlnM_dzs", ascending=True)

        report_lines.append("Most negative S (largest mass decrease per +Δz_s):")
        for _, rr in valid.head(10).iterrows():
            report_lines.append(
                f"  {rr['lens_id']:<12}  S={rr['S_dlnM_dzs']:.6f}  "
                f"z_l={rr['z_l']:.3f}  z_s={rr['z_s']:.3f}  thetaE={rr['theta_E_arcsec']:.3f} arcsec"
            )

        report_lines.append("")
        report_lines.append("Least negative / most positive S:")
        for _, rr in valid.tail(10).sort_values("S_dlnM_dzs", ascending=False).iterrows():
            report_lines.append(
                f"  {rr['lens_id']:<12}  S={rr['S_dlnM_dzs']:.6f}  "
                f"z_l={rr['z_l']:.3f}  z_s={rr['z_s']:.3f}  thetaE={rr['theta_E_arcsec']:.3f} arcsec"
            )

    out_report.write_text("\n".join(report_lines), encoding="utf-8")

    print("\n".join(report_lines))


if __name__ == "__main__":
    main()

