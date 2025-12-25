# Source–Redshift Sensitivity Metric

## 1. Purpose and Scope

This document defines a **source–redshift sensitivity metric** that quantifies how errors or uncertainty in the source redshift \(z_s\) propagate into the inferred enclosed lens mass for strong gravitational lenses. The metric is designed to be:

- Explicitly conditioned on observables,
- Independent of absolute mass scale,
- Lightweight and applicable to existing public lens catalogues.

No lens mass modeling beyond the Einstein radius approximation is assumed.

---

## 2. Observed, Assumed, and Inferred Quantities

We explicitly separate quantities into three classes.

### Observed
- Einstein radius: \(\theta_E\)  
- Lens redshift: \(z_l\)

### Assumed
- Source redshift: \(z_s\)
- Cosmology (fixed for the analysis; see implementation notes)

### Inferred
The projected mass enclosed within the Einstein radius:
\[
M_{\mathrm{inf}}(<\theta_E; z_s)
\;\equiv\;
\pi \left(D_l \theta_E\right)^2 \,
\Sigma_{\mathrm{crit}}(z_l, z_s)
\]

where:
- \(D_l \equiv D_A(z_l)\) is the angular diameter distance to the lens,
- \(\Sigma_{\mathrm{crit}}\) is the critical surface density.

---

## 3. Critical Surface Density

The critical surface density is defined as
\[
\Sigma_{\mathrm{crit}}(z_l, z_s)
\;=\;
\frac{c^2}{4\pi G}
\frac{D_s}{D_l D_{ls}}
\]

with:
- \(D_s \equiv D_A(z_s)\),
- \(D_{ls} \equiv D_A(z_l,z_s)\).

All distance quantities are angular diameter distances evaluated in a fixed background cosmology.

---

## 4. Primary Sensitivity Metric

The primary metric is the **logarithmic sensitivity of the inferred mass to the source redshift**:
\[
S(z_s)
\;\equiv\;
\frac{\partial \ln M_{\mathrm{inf}}(<\theta_E; z_s)}{\partial z_s}
\;=\;
\frac{\partial \ln \Sigma_{\mathrm{crit}}(z_l, z_s)}{\partial z_s}
\]

This equality follows because \(D_l\) and \(\theta_E\) are independent of \(z_s\).

### Finite–Difference Evaluation
In practice, \(S(z_s)\) is evaluated numerically using a fixed central finite difference:
\[
S(z_s)
\;\approx\;
\frac{\ln \Sigma_{\mathrm{crit}}(z_l, z_s + h)
      - \ln \Sigma_{\mathrm{crit}}(z_l, z_s - h)}{2h}
\]
with a pre-specified step size \(h\).

---

## 5. Derived Bias Mapping

For a small redshift error \(\Delta z_s\), the corresponding fractional mass bias is:
\[
\frac{\Delta M}{M}
\;\approx\;
S(z_s)\,\Delta z_s
\]

This mapping is used to translate catalogued or assumed source–redshift uncertainties directly into mass–inference uncertainty.

---

## 6. Optional Summary Metrics

Depending on catalogue characteristics, the following scalar summaries may also be reported:

- **Point sensitivity**: \(S(z_s^{\mathrm{cat}})\), evaluated at the catalogued source redshift.
- **Range sensitivity**:
\[
R \equiv
\max_{z \in [z_{\min}, z_{\max}]} \ln M_{\mathrm{inf}}
-
\min_{z \in [z_{\min}, z_{\max}]} \ln M_{\mathrm{inf}}
\]
- **Posterior-averaged sensitivity** (when a redshift posterior \(p(z_s)\) is available):
\[
\mathbb{E}[S] = \int S(z_s)\,p(z_s)\,dz_s
\]

---

## 7. Interpretation

The sensitivity metric \(S(z_s)\) measures how *fragile* a lens mass estimate is to uncertainty in the source redshift, independent of the absolute mass scale or the Einstein radius itself. A large \(|S|\) indicates that even modest redshift errors induce substantial fractional biases in inferred mass, while small \(|S|\) identifies systems that are comparatively robust to redshift uncertainty. As a result, this metric enables catalogue-level ranking of lenses by susceptibility to redshift systematics and provides a direct, quantitative link between redshift measurement precision and mass-inference reliability.

---

## 8. Validity Conditions

The metric is defined only for systems satisfying:
- \(z_s > z_l\),
- \(\theta_E > 0\),
- finite and well-defined angular diameter distances.

Systems violating these conditions are excluded or flagged in analysis.

