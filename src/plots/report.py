cat > src/plots/report.py <<'PY'
from __future__ import annotations
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def _savefig(path: str):
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

def fig1_hist_S(df: pd.DataFrame, outpath: str):
    x = df["S_log"].to_numpy()
    x = x[np.isfinite(x)]
    plt.figure()
    plt.hist(x, bins=40)
    plt.xlabel(r"$S = |\partial \ln M / \partial z_s|$")
    plt.ylabel("Count")
    _savefig(outpath)

def fig2_scatter_S_vs_zsep(df: pd.DataFrame, outpath: str):
    x = (df["z_s"] - df["z_l"]).to_numpy()
    y = df["S_log"].to_numpy()
    m = np.isfinite(x) & np.isfinite(y)
    plt.figure()
    plt.scatter(x[m], y[m], s=10)
    plt.xlabel(r"$z_s - z_l$")
    plt.ylabel(r"$S$")
    _savefig(outpath)

def fig3_scatter_S_vs_zl(df: pd.DataFrame, outpath: str):
    x = df["z_l"].to_numpy()
    y = df["S_log"].to_numpy()
    m = np.isfinite(x) & np.isfinite(y)
    plt.figure()
    plt.scatter(x[m], y[m], s=10)
    plt.xlabel(r"$z_l$")
    plt.ylabel(r"$S$")
    _savefig(outpath)

def fig4_bias_proxy(df: pd.DataFrame, outpath: str):
    x = df["delta_lnM_0p1"].to_numpy()
    x = x[np.isfinite(x)]
    plt.figure()
    plt.hist(x, bins=40)
    plt.xlabel(r"$|\Delta \ln M|$ for $\Delta z_s = 0.1$")
    plt.ylabel("Count")
    _savefig(outpath)

def table1_summary(df: pd.DataFrame) -> pd.DataFrame:
    n_total = len(df)
    n_valid = int(df["is_valid"].sum())
    frac_valid = n_valid / n_total if n_total else np.nan
    out = pd.DataFrame([{
        "n_total": n_total,
        "n_valid": n_valid,
        "frac_valid": frac_valid,
        "S_median": np.nanmedian(df.loc[df["is_valid"], "S_log"]),
        "S_p90": np.nanpercentile(df.loc[df["is_valid"], "S_log"], 90),
    }])
    return out

def table2_top_sensitive(df: pd.DataFrame, k: int = 20) -> pd.DataFrame:
    d = df[df["is_valid"]].copy()
    d = d.sort_values("S_log", ascending=False).head(k)
    cols = ["lens_id","z_l","z_s","z_s_type","theta_E_arcsec","S_log","delta_lnM_0p1","catalog","ref"]
    cols = [c for c in cols if c in d.columns]
    return d[cols]
PY

