import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def load_S(path: str) -> np.ndarray:
    df = pd.read_parquet(path)
    d = df[df["is_valid"]].copy()
    x = d["S_log"].to_numpy(dtype=float)
    return x[np.isfinite(x)]

def main():
    slacs_path = "results/slacs/slacs_metrics.parquet"
    cao_path   = "results/cao2015/cao2015_metrics.parquet"

    slacs = load_S(slacs_path)
    cao   = load_S(cao_path)

    outdir = "results/compare"
    os.makedirs(outdir, exist_ok=True)
    outpdf = os.path.join(outdir, "S_compare_slacs_vs_cao2015.pdf")

    data = [slacs, cao]
    labels = [f"SLACS (n={len(slacs)})", f"Cao2015 (n={len(cao)})"]

    # Same axes, same scale: set y-limits from pooled robust range (with room for tail)
    pooled = np.concatenate(data)
    y_min = 0.0
    y_max = float(np.nanpercentile(pooled, 99.5))  # robust upper bound
    y_max = max(y_max, float(np.nanmax(pooled)))   # ensure max fits
    y_max = min(y_max, 10.0)                       # cap at 10 for readability (your tails ~8)
    y_max = max(y_max, 3.0)

    plt.figure(figsize=(7.5, 4.8))

    # Violin
    vp = plt.violinplot(
        data,
        positions=[1, 2],
        showmeans=False,
        showmedians=True,
        showextrema=True,
        widths=0.8
    )

    # Box overlay (for quartiles + whiskers)
    plt.boxplot(
        data,
        positions=[1, 2],
        widths=0.25,
        showfliers=False
    )

    plt.xticks([1, 2], labels, rotation=0)
    plt.ylabel(r"$S = \left|\partial \ln M / \partial z_s\right|$")
    plt.title("Source-redshift sensitivity S: SLACS vs Cao2015 (same scale)")
    plt.ylim(y_min, y_max)

    # Helpful reference line: S=1 corresponds to ~10% mass bias for Δz_s=0.1
    plt.axhline(1.0, linestyle="--", linewidth=1)

    plt.tight_layout()
    plt.savefig(outpdf)
    plt.close()

    print("Wrote:", outpdf)
    print("y_max used:", y_max)

if __name__ == "__main__":
    main()
