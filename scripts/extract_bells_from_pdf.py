import re
from pathlib import Path
import pandas as pd

PDF = Path("data/external/bells/bells_brownstein2012.pdf")
OUT = Path("data/processed/bells/bells_clean.csv")

def pdf_to_text(pdf_path: Path) -> str:
    # pdfplumber is the least painful for text-based PDFs like this one
    import pdfplumber
    chunks = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            chunks.append(t)
    return "\n".join(chunks)

def norm_name(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    # normalize minus sign variants
    s = s.replace("−", "-").replace("–", "-")
    return s

def main():
    if not PDF.exists():
        raise FileNotFoundError(f"Missing {PDF}. Download it first.")

    text = pdf_to_text(PDF)

    # ---- Parse Table 2 lines containing zL and zS ----
    # Example from the PDF text:
    # SDSS J015107.37 + 004909.0 ... 0.5171 1.3636 ...
    t2 = {}
    t2_pat = re.compile(
        r"^(SDSS J\d{6}\.\d{2}\s*[+-]\s*\d{6}\.\d)\s+\S+\s+(\d\.\d{4})\s+(\d\.\d{4})\s+",
        re.MULTILINE
    )
    for m in t2_pat.finditer(text):
        name = norm_name(m.group(1))
        zl = float(m.group(2))
        zs = float(m.group(3))
        t2[name] = (zl, zs)

    # ---- Parse Table 5 lines containing theta_E for Grade-A ----
    # Example from the PDF text:
    # SDSS J0151 + 0049 0.676 0.752 111.0 ...
    t5 = {}
    t5_pat = re.compile(
        r"^(SDSS J\d{4}\s*[+-]\s*\d{4})\s+(\d\.\d{3})\s+(\d\.\d{3})\s+(\d+\.\d)\s+",
        re.MULTILINE
    )
    for m in t5_pat.finditer(text):
        name = norm_name(m.group(1))
        thetaE = float(m.group(2))
        t5[name] = thetaE

    # Join: Table5 names are truncated; match them to Table2 by prefix
    rows = []
    for short, thetaE in t5.items():
        # Find the unique Table2 entry that starts with this truncated name
        candidates = [k for k in t2.keys() if k.startswith(short.replace("  ", " "))]
        if len(candidates) != 1:
            continue
        full = candidates[0]
        zl, zs = t2[full]
        # Create lens_id format like your pipeline expects (JHHMM±DDMM)
        lens_id = short.replace("SDSS ", "").replace(" ", "")
        # lens_id becomes e.g. "J0151+0049"
        rows.append(dict(
            lens_id=lens_id,
            z_l=zl,
            z_s=zs,
            theta_E_arcsec=thetaE,
            z_s_type="spec",
            z_s_sigma=pd.NA,
            theta_E_sigma_arcsec=pd.NA,
        ))

    if len(rows) == 0:
        print("ERROR: No BELLS systems parsed.")
        print("Parsed Table2 entries:", len(t2))
        print("Parsed Table5 entries:", len(t5))
        print("This indicates a regex mismatch with the PDF layout.")
        return

    df = pd.DataFrame(rows).drop_duplicates(subset=["lens_id"]).sort_values("lens_id").reset_index(drop=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    print("Parsed Table2 entries:", len(t2))
    print("Parsed Table5 entries:", len(t5))
    print("Wrote:", OUT, "rows=", len(df))
    print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
