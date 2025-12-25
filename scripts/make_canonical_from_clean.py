import argparse
import pandas as pd
from src.io.canonical import enforce_canonical

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--out_parquet", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.in_csv)

    # Minimal mapping; works if your clean CSV uses common names.
    rename = {}

    # lens id
    for c in ["lens_id", "slacs_id", "cao2015_id", "id", "ID", "name", "system_name", "lens", "lens_name"]:
        if c in df.columns:
            rename[c] = "lens_id"
            break

    # lens redshift
    for c in ["z_l", "zl", "zLens", "z_lens", "z_lens_spec"]:
        if c in df.columns:
            rename[c] = "z_l"
            break

    # source redshift
    for c in ["z_s", "zs", "zSource", "z_source", "z_src", "z_s_spec"]:
        if c in df.columns:
            rename[c] = "z_s"
            break

    # Einstein radius
    for c in ["theta_E_arcsec", "theta_E", "thetaE_arcsec", "theta_e", "thetaE", "rein_arcsec"]:
        if c in df.columns:
            rename[c] = "theta_E_arcsec"
            break

    df = df.rename(columns=rename)

    # Defaults if absent
    if "z_s_type" not in df.columns:
        df["z_s_type"] = "reported"
    if "z_s_sigma" not in df.columns:
        df["z_s_sigma"] = pd.NA
    if "theta_E_sigma_arcsec" not in df.columns:
        df["theta_E_sigma_arcsec"] = pd.NA

    out = enforce_canonical(df, catalog=args.catalog)
    out.to_parquet(args.out_parquet, index=False)

    print("Input columns:", list(df.columns))
    print(f"Wrote canonical parquet: {args.out_parquet} (rows={len(out)})")
    print("Canonical head:")
    print(out[["lens_id","catalog","z_l","z_s","theta_E_arcsec","is_valid","invalid_reason"]].head(5))

if __name__ == "__main__":
    main()
