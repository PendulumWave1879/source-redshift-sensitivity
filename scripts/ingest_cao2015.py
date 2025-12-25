# -*- coding: utf-8 -*-
"""
Ingest Cao+2015 strong-lens compilation into a clean, validated CSV.

Input (raw, immutable):
  data/external/cao2015/cao2015_raw.csv

Expected columns (from your header):
  Name,zl,zs,Sigma,e_Sigma,thetaE,Survey,thetaAp,thetaEff,Sig0,e_Sig0,Cat,SimbadName,_RA,_DE

Outputs:
  data/processed/cao2015/cao2015_with_flags.csv   (all rows, with validation flags)
  data/processed/cao2015/cao2015_clean.csv        (strictly valid subset)
  data/processed/cao2015/cao2015_ingest_report.txt

Validation rules (strict):
  - thetaE_arcsec > 0
  - zl >= 0, zs >= 0
  - zs > zl
"""

from __future__ import annotations

import numpy as np

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INFILE_DEFAULT = ROOT / "data" / "external" / "cao2015" / "cao2015_raw.csv"
OUTDIR = ROOT / "data" / "processed" / "cao2015"

OUT_WITH_FLAGS = OUTDIR / "cao2015_with_flags.csv"
OUT_CLEAN = OUTDIR / "cao2015_clean.csv"
OUT_REPORT = OUTDIR / "cao2015_ingest_report.txt"


def _to_float(x, flags: list[str], name: str):
    if pd.isna(x):
        flags.append(f"flag_missing_{name}")
        return None
    try:
        v = float(x)
    except Exception:
        flags.append(f"flag_non_numeric_{name}")
        return None
    if not np.isfinite(v):
        flags.append(f"flag_non_finite_{name}")
        return None
    return v


def validate_row(zl, zs, thetaE):
    flags: list[str] = []

    zl_v = _to_float(zl, flags, "z_l")
    zs_v = _to_float(zs, flags, "z_s")
    th_v = _to_float(thetaE, flags, "theta_E_arcsec")

    if zl_v is not None and zl_v < 0:
        flags.append("flag_zl_negative")
    if zs_v is not None and zs_v < 0:
        flags.append("flag_zs_negative")
    if th_v is not None and th_v <= 0:
        flags.append("flag_thetaE_nonpositive")
    if (zl_v is not None) and (zs_v is not None) and not (zs_v > zl_v):
        flags.append("flag_zs_le_zl")

    is_valid = (len(flags) == 0)
    norm = {}
    if is_valid:
        norm = {"z_l": float(zl_v), "z_s": float(zs_v), "theta_E_arcsec": float(th_v)}
    return is_valid, flags, norm


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)

    infile = INFILE_DEFAULT
    if not infile.exists():
        raise SystemExit(f"Missing input file: {infile}")

    df = pd.read_csv(infile)

    required = {"Name", "zl", "zs", "thetaE"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns in CSV: {missing}")

    rows = []
    for _, r in df.iterrows():
        is_valid, flags, norm = validate_row(r["zl"], r["zs"], r["thetaE"])
        out = dict(r)

        out["lens_id"] = str(r["Name"]).strip()
        out["is_valid"] = bool(is_valid)
        out["flags"] = ";".join(flags)

        out["z_l_norm"] = norm.get("z_l", "")
        out["z_s_norm"] = norm.get("z_s", "")
        out["theta_E_arcsec_norm"] = norm.get("theta_E_arcsec", "")

        rows.append(out)

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_WITH_FLAGS, index=False)

    clean = out_df[out_df["is_valid"] == True].copy()
    # Canonical columns for downstream metric code:
    clean = clean.rename(columns={
        "z_l_norm": "z_l",
        "z_s_norm": "z_s",
        "theta_E_arcsec_norm": "theta_E_arcsec",
    })
    keep = [
        "lens_id",
        "z_l", "z_s", "theta_E_arcsec",
        "Survey", "Cat",
        "Sigma", "e_Sigma", "Sig0", "e_Sig0",
        "thetaAp", "thetaEff",
        "SimbadName", "_RA", "_DE",
    ]
    keep = [c for c in keep if c in clean.columns]
    clean = clean[keep]
    clean.to_csv(OUT_CLEAN, index=False)

    # Report
    total = len(df)
    valid = int(out_df["is_valid"].sum())
    invalid = total - valid

    flag_counts = {}
    for fstr in out_df["flags"].fillna("").astype(str):
        if not fstr:
            continue
        for f in [x for x in fstr.split(";") if x]:
            flag_counts[f] = flag_counts.get(f, 0) + 1

    lines = []
    lines.append("Cao+2015 ingest report")
    lines.append("======================")
    lines.append(f"input:  {infile}")
    lines.append("")
    lines.append(f"rows:   {total}")
    lines.append(f"valid:  {valid}")
    lines.append(f"invalid:{invalid}")
    lines.append("")
    lines.append("Flag counts:")
    if flag_counts:
        for k in sorted(flag_counts):
            lines.append(f"  {k}: {flag_counts[k]}")
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append(f"Wrote: {OUT_WITH_FLAGS}")
    lines.append(f"Wrote: {OUT_CLEAN}")
    lines.append(f"Wrote: {OUT_REPORT}")

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

