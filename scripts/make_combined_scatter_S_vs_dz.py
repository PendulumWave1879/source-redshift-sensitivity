import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def load(path: str, label: str):
    df = pd.read_parquet(path)
    df = df[df["is_valid"]].copy()
    df["dz"] = df["z_s"] - df["z_l"]
    df["catalog_label"] = label
    # Use absolute sensitivity (your S_log is already abs(dlnM_dzs) in the pipeline)
    df["S"] = df["S_log"].astype(float)
    df = df[np.isfinite(df["dz"]) & np.isfinite(df["S"])]
    return df

def main():
    slacs_path = "results/slacs/slacs_metrics.parquet"
    cao_path   = "results/cao2015/cao2015_metrics.parquet"

    slacs = load(slacs_path, "SLACS")
    cao   = load(cao_path, "Cao2015")

    outdir = "results/compare"
    os.makedirs(outdir, exist_ok=True)
    outpdf = os.path.join(outdir, "combined_S_vs_dz_slacs_plus_cao2015.pdf")

    # Same axes & scale
    allS = np.concatenate([slacs["S"].to_numpy(), cao["S"].to_numpy()])
    ymax = float(np.nanpercentile(allS, 99.5))
    ymax = max(ymax, float(np.nanmax(allS)))
    ymax = min(ymax, 10.0)      # readability; your max is ~8
    ymax = max(ymax, 3.0)

    plt.figure(figsize=(9.0, 5.5))

    # Plot SLACS and Cao2015 with different markers (color unspecified; matplotlib defaults)
    plt.scatter(slacs["dz"], slacs["S"], s=40, marker="o", alpha=0.75, label=f"SLACS (n={len(slacs)})")
    plt.scatter(cao["dz"],   cao["S"],   s=40, marker="^", alpha=0.75, label=f"Cao2015 (n={len(cao)})")

    # Reference lines
    plt.axhline(1.0, linestyle="--", linewidth=1)     # ~10% mass bias for Δz_s=0.1
    for x in [0.2, 0.4]:
        plt.axvline(x, linestyle=":", linewidth=1.5)

    plt.xlabel(r"$\Delta z = z_s - z_l$")
    plt.ylabel(r"$S = \left|\partial \ln M/\partial z_s\right|$")
    plt.title("Combined sensitivity vs source–lens separation: SLACS vs Cao2015 (same axes)")
    plt.ylim(0.0, ymax)

    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(outpdf)
    plt.close()

    print("Wrote:", outpdf)
    print("ymax used:", ymax)

if __name__ == "__main__":
    main()
