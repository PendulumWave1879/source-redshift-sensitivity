cat > src/io/canonical.py <<'PY'
from __future__ import annotations
import pandas as pd
import numpy as np

REQUIRED_COLS = [
    "lens_id", "catalog",
    "z_l", "z_s", "z_s_type", "z_s_sigma",
    "theta_E_arcsec", "theta_E_sigma_arcsec",
]

RECOMMENDED_COLS = ["ra_deg", "dec_deg", "ref", "notes"]

def enforce_canonical(df: pd.DataFrame, catalog: str) -> pd.DataFrame:
    df = df.copy()

    rename_map = {
        "zl": "z_l",
        "zs": "z_s",
        "theta_E": "theta_E_arcsec",
        "thetaE_arcsec": "theta_E_arcsec",
    }
    for k, v in rename_map.items():
        if k in df.columns and v not in df.columns:
            df.rename(columns={k: v}, inplace=True)

    df["catalog"] = catalog

    for c in REQUIRED_COLS:
        if c not in df.columns:
            df[c] = np.nan

    for c in RECOMMENDED_COLS:
        if c not in df.columns:
            df[c] = np.nan

    df["lens_id"] = df["lens_id"].astype(str)
    df["catalog"] = df["catalog"].astype(str)
    df["z_s_type"] = df["z_s_type"].fillna("unknown").astype(str)

    df["is_valid"] = True
    df["invalid_reason"] = ""

    def invalidate(mask, reason):
        df.loc[mask, "is_valid"] = False
        df.loc[mask, "invalid_reason"] = reason

    invalidate(df["z_l"].isna(), "missing_zl")
    invalidate(df["z_s"].isna(), "missing_zs")
    invalidate(df["theta_E_arcsec"].isna(), "missing_thetaE")
    invalidate(
        (df["z_s"] <= df["z_l"]) & df["z_s"].notna() & df["z_l"].notna(),
        "zs_le_zl",
    )

    col_order = REQUIRED_COLS + ["is_valid", "invalid_reason"] + RECOMMENDED_COLS
    extras = [c for c in df.columns if c not in col_order]
    return df[col_order + extras]
PY

