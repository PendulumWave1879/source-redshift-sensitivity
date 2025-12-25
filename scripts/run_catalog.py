cat > scripts/run_catalog.py <<'PY'
from __future__ import annotations
import argparse
import os
import pandas as pd
import numpy as np

from src.metrics.sensitivity import dlnM_dzs, Minf
from src.plots.report import (
    fig1_hist_S, fig2_scatter_S_vs_zsep, fig3_scatter_S_vs_zl, fig4_bias_proxy,
    table1_summary, table2_top_sensitive
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--infile", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--H0_km_s_Mpc", type=float, default=70.0)
    ap.add_argument("--Om0", type=float, default=0.3)
    ap.add_argument("--dz", type=float, default=1e-3)
    args = ap.parse_args()

    H0 = args.H0_km_s_Mpc * 1000.0 / 3.0856775814913673e22  # s^-1

    df = pd.read_parquet(args.infile).copy()

    df["dlnM_dzs"] = np.nan
    df["S_log"] = np.nan
    df["delta_lnM_0p1"] = np.nan
    df["Minf_zs"] = np.nan

    valid = df["is_valid"].astype(bool).to_numpy()
    for i in np.where(valid)[0]:
        zl = float(df.loc[i, "z_l"])
        zs = float(df.loc[i, "z_s"])
        th = float(df.loc[i, "theta_E_arcsec"])
        d = dlnM_dzs(th, zl, zs, H0, args.Om0, dz=args.dz)
        df.loc[i, "dlnM_dzs"] = d
        df.loc[i, "S_log"] = abs(d) if np.isfinite(d) else np.nan
        df.loc[i, "delta_lnM_0p1"] = abs(d) * 0.1 if np.isfinite(d) else np.nan
        df.loc[i, "Minf_zs"] = Minf(th, zl, zs, H0, args.Om0)

    figdir = os.path.join(args.outdir, "figures")
    tabdir = os.path.join(args.outdir, "tables")
    os.makedirs(figdir, exist_ok=True)
    os.makedirs(tabdir, exist_ok=True)

    df.to_parquet(os.path.join(args.outdir, f"{args.catalog}_metrics.parquet"), index=False)

    dvalid = df[df["is_valid"]].copy()
    fig1_hist_S(dvalid, os.path.join(figdir, "fig1_hist_S.pdf"))
    fig2_scatter_S_vs_zsep(dvalid, os.path.join(figdir, "fig2_S_vs_zs_minus_zl.pdf"))
    fig3_scatter_S_vs_zl(dvalid, os.path.join(figdir, "fig3_S_vs_zl.pdf"))
    fig4_bias_proxy(dvalid, os.path.join(figdir, "fig4_hist_dlnM_dz0p1.pdf"))

    t1 = table1_summary(df)
    t1.to_csv(os.path.join(tabdir, "table1_summary.csv"), index=False)
    t1.to_latex(os.path.join(tabdir, "table1_summary.tex"), index=False, float_format="%.4g")

    t2 = table2_top_sensitive(df, k=20)
    t2.to_csv(os.path.join(tabdir, "table2_top20_sensitive.csv"), index=False)
    t2.to_latex(os.path.join(tabdir, "table2_top20_sensitive.tex"), index=False, float_format="%.4g")

if __name__ == "__main__":
    main()
PY

