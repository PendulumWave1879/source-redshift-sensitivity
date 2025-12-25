from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from astroquery.vizier import Vizier

CATALOG_ID = "J/ApJ/744/41"  # Brownstein et al. 2012, BELLS
OUT = Path("data/processed/bells/bells_clean.csv")


def norm_sysname(x: str) -> str:
    x = str(x).strip()
    x = x.replace("−", "-").replace("–", "-")
    x = re.sub(r"\s+", "", x)
    return x


def find_col(cols, candidates):
    cols_l = {str(c).lower(): c for c in cols}
    for cand in candidates:
        key = cand.lower()
        if key in cols_l:
            return cols_l[key]
    return None


def main():
    Vizier.ROW_LIMIT = -1
    tabs = Vizier.get_catalogs(CATALOG_ID)

    print("Vizier returned tables:")
    for k in tabs.keys():
        print(" ", k, "cols=", len(tabs[k].colnames))

    z_tab_key = None
    te_tab_key = None

    for k in tabs.keys():
        cols = tabs[k].colnames
        zl_col = find_col(cols, ["z_l", "zl", "zlens", "z_lens", "zl_"])
        zs_col = find_col(cols, ["z_s", "zs", "zsrc", "z_source", "zs_"])
        if zl_col and zs_col:
            z_tab_key = k

        te_col = find_col(cols, ["theta_e", "thetae", "theta_e_", "rein", "r_ein", "thetaein"])
        if te_col:
            te_tab_key = k

    if z_tab_key is None:
        raise RuntimeError("Could not find a BELLS table containing both z_l and z_s in Vizier response.")
    if te_tab_key is None:
        raise RuntimeError("Could not find a BELLS table containing an Einstein-radius-like column in Vizier response.")

    print("\nUsing redshift table:", z_tab_key)
    print("Using Einstein-radius table:", te_tab_key)

    zt = tabs[z_tab_key].to_pandas()
    tt = tabs[te_tab_key].to_pandas()

    z_name = find_col(zt.columns, ["name", "system", "sys", "sdss", "id", "object"])
    t_name = find_col(tt.columns, ["name", "system", "sys", "sdss", "id", "object"])
    if z_name is None or t_name is None:
        raise RuntimeError("Could not identify a system-name column in one or both BELLS tables.")

    zl_col = find_col(zt.columns, ["z_l", "zl", "zlens", "z_lens", "zl_"])
    zs_col = find_col(zt.columns, ["z_s", "zs", "zsrc", "z_source", "zs_"])
    te_col = find_col(tt.columns, ["theta_e", "thetae", "theta_e_", "rein", "r_ein", "thetaein"])

    if zl_col is None or zs_col is None or te_col is None:
        raise RuntimeError(f"Column detection failed: zl={zl_col}, zs={zs_col}, thetaE={te_col}")

    zt["_key"] = zt[z_name].map(norm_sysname)
    tt["_key"] = tt[t_name].map(norm_sysname)

    merged = tt.merge(
        zt[["_key", zl_col, zs_col]],
        on="_key",
        how="inner",
    )

    def make_lens_id(raw: str) -> str:
        raw = str(raw).replace("−", "-").replace("–", "-")
        raw = raw.replace("SDSS", "").replace(" ", "")
        m = re.search(r"J\d{4}[+-]\d{4}", raw)
        return m.group(0) if m else raw

    out = pd.DataFrame({
        "lens_id": merged[t_name].map(make_lens_id),
        "z_l": pd.to_numeric(merged[zl_col], errors="coerce"),
        "z_s": pd.to_numeric(merged[zs_col], errors="coerce"),
        "theta_E_arcsec": pd.to_numeric(merged[te_col], errors="coerce"),
        "z_s_type": "spec",
        "z_s_sigma": pd.NA,
        "theta_E_sigma_arcsec": pd.NA,
    }).dropna(subset=["lens_id", "z_l", "z_s", "theta_E_arcsec"]).drop_duplicates(subset=["lens_id"])

    out = out.sort_values("lens_id").reset_index(drop=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print("\nWrote:", OUT, "rows=", len(out))
    print(out.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
