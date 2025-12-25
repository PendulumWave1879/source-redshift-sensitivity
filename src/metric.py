"""
Source–Redshift Sensitivity Metric
=================================

This module implements the source–redshift sensitivity metric defined in:

    docs/metric.md

The metric quantifies how uncertainty in the assumed source redshift (z_s)
propagates into bias or uncertainty in the inferred enclosed lens mass for
strong gravitational lenses.

Authoritative Definition
------------------------
All notation, assumptions, and validity conditions are defined in
`docs/metric.md`. This module is an implementation of that specification.
Any change to the mathematical definition MUST be made in `docs/metric.md`
and then reflected here.

Metric Summary
--------------
Given:
    - Observed Einstein radius θ_E
    - Observed lens redshift z_l
    - Assumed source redshift z_s
    - Fixed background cosmology

The inferred enclosed mass is:

    M_inf(<θ_E; z_s) = π (D_l θ_E)^2 Σ_crit(z_l, z_s)

where Σ_crit is the critical surface density.

The primary sensitivity metric implemented here is the logarithmic derivative:

    S(z_s) = ∂ ln M_inf / ∂ z_s
           = ∂ ln Σ_crit(z_l, z_s) / ∂ z_s

In practice, S(z_s) is evaluated using a fixed central finite-difference
scheme with a pre-specified step size h.

Interpretation
--------------
S(z_s) measures the fractional change in inferred lens mass per unit change
in source redshift. For small redshift errors Δz_s:

    ΔM / M ≈ S(z_s) · Δz_s

Large |S| indicates systems whose mass inference is highly sensitive to
source-redshift uncertainty; small |S| indicates relative robustness.

Validity Conditions
-------------------
The metric is defined only for systems satisfying:
    - z_s > z_l
    - θ_E > 0
    - finite, well-defined angular diameter distances

Systems violating these conditions should be excluded or flagged upstream.

Implementation Notes
--------------------
- Cosmology is treated as fixed and supplied externally.
- This module performs no catalogue I/O.
- Input validation and flagging are handled separately (see validate.py).

"""

