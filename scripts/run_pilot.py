# scripts/run_pilot.py
# -*- coding: utf-8 -*-
"""
Run a pilot batch for the Source–Redshift Sensitivity metric.

Reads:   data/pilot_lenses.csv
Writes:  outputs/pilot_results.csv
Prints:  summary stats, flag counts, and top/bottom systems by sensitivity.

Expected input columns (header required):
    lens_id,theta_E_arcsec,z_l,z_s

Notes:
- This script performs per-row validation inside compute_sensitivity().
- Systems that fail validation are still written to the output with flags and NaNs.
- Intended for small pilot tables (10–50 rows), but works for larger CSVs.
"""

from __future__ import division

import csv
import os
import sys
from collections import Counter

# Ensure project root on sys.path when running as a script.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.cosmology import FlatLambdaCDM
from src.sensitivity import compute_sensitivity


INPUT_CSV = os.path.join(PROJECT_ROOT, "data", "pilot_lenses.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "pilot_results.csv")


def _safe_float(x):
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() in ("na", "nan", "none", "null"):
        return None
    return float(s)


def _ensure_dirs():
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def _read_input_rows(path):
    if not os.path.exists(path):
        raise IOError("Input CSV not found: %s" % path)

    with open(path, "r") as f:
        reader = csv.DictReader(f)
        required = ["lens_id", "theta_E_arcsec", "z_l", "z_s"]
        for r in required:
            if r not in reader.fieldnames:
                raise ValueError("Missing required column '%s' in %s" % (r, path))

        rows = []
        for row in reader:
            rows.append(row)
        return rows


def _write_output(path, rows, fieldnames):
    with open(path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main():
    _ensure_dirs()

    # Cosmology defaults for v1 pilot (keep fixed).
    cosmo = FlatLambdaCDM(H0_km_s_Mpc=70.0, Om0=0.3, n_int=1024)

    # Finite difference and reference dz (keep fixed).
    h = 1e-3
    delta_z = 0.1

    in_rows = _read_input_rows(INPUT_CSV)

    out_rows = []
    flag_counts = Counter()
    n_valid = 0

    for row in in_rows:
        lens_id = (row.get("lens_id") or "").strip()

        try:
            th = _safe_float(row.get("theta_E_arcsec"))
        except Exception:
            th = row.get("theta_E_arcsec")  # pass through for validation flags

        try:
            zl = _safe_float(row.get("z_l"))
        except Exception:
            zl = row.get("z_l")

        try:
            zs = _safe_float(row.get("z_s"))
        except Exception:
            zs = row.get("z_s")

        res = compute_sensitivity(
            theta_E_arcsec=th,
            z_l=zl,
            z_s=zs,
            cosmo=cosmo,
            h=h,
            delta_z=delta_z,
        )

        # Flatten flags into a compact string for CSV output.
        flags = res.get("flags", [])
        flags_str = ";".join(flags) if flags else ""

        if res.get("is_valid"):
            n_valid += 1
        for fl in flags:
            flag_counts[fl] += 1

        out_row = {
            "lens_id": lens_id,
            "is_valid": bool(res.get("is_valid")),
            "flags": flags_str,

            "theta_E_arcsec": res.get("theta_E_arcsec"),
            "z_l": res.get("z_l"),
            "z_s": res.get("z_s"),

            "theta_E_rad": res.get("theta_E_rad"),
            "D_l_m": res.get("D_l_m"),
            "Sigma_crit_kg_m2": res.get("Sigma_crit_kg_m2"),
            "M_inf_kg": res.get("M_inf_kg"),

            "S_dlnM_dzs": res.get("S_dlnM_dzs"),
            "delta_z_ref": float(delta_z),
            "dM_over_M_for_delta_z": res.get("dM_over_M_for_delta_z"),
        }
        out_rows.append(out_row)

    fieldnames = [
        "lens_id",
        "is_valid",
        "flags",
        "theta_E_arcsec",
        "z_l",
        "z_s",
        "theta_E_rad",
        "D_l_m",
        "Sigma_crit_kg_m2",
        "M_inf_kg",
        "S_dlnM_dzs",
        "delta_z_ref",
        "dM_over_M_for_delta_z",
    ]

    _write_output(OUTPUT_CSV, out_rows, fieldnames)

    # ---- Console summary ----
    n_total = len(out_rows)
    print("Input:  %s" % INPUT_CSV)
    print("Output: %s" % OUTPUT_CSV)
    print("Total systems: %d" % n_total)
    print("Valid systems: %d" % n_valid)
    print("Invalid systems: %d" % (n_total - n_valid))

    if flag_counts:
        print("\nFlag counts:")
        for k, v in sorted(flag_counts.items(), key=lambda kv: (-kv[1], kv[0])):
            print("  %-28s %d" % (k, v))
    else:
        print("\nFlag counts: (none)")

    # Rank by S among valid rows
    valid_rows = [r for r in out_rows if r["is_valid"] and r["S_dlnM_dzs"] is not None]
    # Filter out NaNs (string "nan" may appear depending on writer/float formatting)
    def _finite(x):
        try:
            xf = float(x)
            return (xf == xf) and (xf != float("inf")) and (xf != float("-inf"))
        except Exception:
            return False

    valid_rows = [r for r in valid_rows if _finite(r["S_dlnM_dzs"])]

    if valid_rows:
        valid_rows_sorted = sorted(valid_rows, key=lambda r: float(r["S_dlnM_dzs"]))
        k = min(5, len(valid_rows_sorted))

        print("\nMost negative S (largest mass decrease per +Δz_s):")
        for r in valid_rows_sorted[:k]:
            print("  %-20s  S=% .6f  z_l=%.3f  z_s=%.3f  thetaE=%.3f arcsec" %
                  (r["lens_id"], float(r["S_dlnM_dzs"]), float(r["z_l"]), float(r["z_s"]), float(r["theta_E_arcsec"])))

        print("\nMost positive S (largest mass increase per +Δz_s):")
        for r in valid_rows_sorted[-k:][::-1]:
            print("  %-20s  S=% .6f  z_l=%.3f  z_s=%.3f  thetaE=%.3f arcsec" %
                  (r["lens_id"], float(r["S_dlnM_dzs"]), float(r["z_l"]), float(r["z_s"]), float(r["theta_E_arcsec"])))
    else:
        print("\nNo valid systems with finite S found to rank.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

