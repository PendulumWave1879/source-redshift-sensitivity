import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("outputs/pilot_results.csv")
df_valid = df[df["is_valid"] == True]

vals = df_valid["S_dlnM_dzs"].values

plt.figure()
plt.hist(vals, bins=5)
for v in vals:
    plt.axvline(v, ymin=0, ymax=0.06)
plt.axvline(vals.mean(), linestyle="--", label="mean")
plt.axvline(pd.Series(vals).median(), linestyle=":", label="median")
plt.xlabel("S = d ln M_inf / d z_s")
plt.ylabel("Count")
plt.title("Pilot distribution (binned + rug + mean/median)")
plt.legend()
plt.show()
