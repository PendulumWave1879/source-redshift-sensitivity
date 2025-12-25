# tests/test_sensitivity.py
# -*- coding: utf-8 -*-
"""
Minimal unit tests for src/sensitivity.py

Locks three key behaviors:
1) Valid inputs produce finite outputs (S, Sigma_crit, M_inf) and is_valid=True.
2) Unphysical geometry (z_s <= z_l) is invalid and flagged.
3) Sensitivity S is (approximately) invariant to theta_E_arcsec, since:
       S(z_s) = d ln M_inf / dz_s = d ln Sigma_crit / dz_s
   and does not depend on theta_E or D_l.
"""

from __future__ import division

import math

from src.cosmology import FlatLambdaCDM
from src.sensitivity import compute_sensitivity


def _is_finite(x):
    return (x is not None) and (not math.isnan(x)) and (not math.isinf(x))


def test_compute_sensitivity_valid_is_finite():
    cosmo = FlatLambdaCDM(H0_km_s_Mpc=70.0, Om0=0.3, n_int=1024)
    res = compute_sensitivity(theta_E_arcsec=1.2, z_l=0.3, z_s=1.1, cosmo=cosmo, h=1e-3, delta_z=0.1)

    assert res["is_valid"] is True
    assert res["flags"] == []

    assert _is_finite(res["D_l_m"]) and res["D_l_m"] > 0.0
    assert _is_finite(res["Sigma_crit_kg_m2"]) and res["Sigma_crit_kg_m2"] > 0.0
    assert _is_finite(res["M_inf_kg"]) and res["M_inf_kg"] > 0.0
    assert _is_finite(res["S_dlnM_dzs"])
    assert _is_finite(res["dM_over_M_for_delta_z"])


def test_compute_sensitivity_zs_le_zl_is_invalid_and_flagged():
    cosmo = FlatLambdaCDM(H0_km_s_Mpc=70.0, Om0=0.3, n_int=1024)

    res = compute_sensitivity(theta_E_arcsec=1.2, z_l=0.8, z_s=0.8, cosmo=cosmo, h=1e-3, delta_z=0.1)

    assert res["is_valid"] is False
    # Raw input validation should catch this before cosmology is used.
    assert "flag_zs_le_zl" in res["flags"]


def test_S_is_invariant_to_thetaE_arcsec_to_tolerance():
    cosmo = FlatLambdaCDM(H0_km_s_Mpc=70.0, Om0=0.3, n_int=1024)

    res1 = compute_sensitivity(theta_E_arcsec=0.5, z_l=0.3, z_s=1.1, cosmo=cosmo, h=1e-3, delta_z=0.1)
    res2 = compute_sensitivity(theta_E_arcsec=2.0, z_l=0.3, z_s=1.1, cosmo=cosmo, h=1e-3, delta_z=0.1)

    assert res1["is_valid"] is True and res2["is_valid"] is True

    S1 = res1["S_dlnM_dzs"]
    S2 = res2["S_dlnM_dzs"]

    assert _is_finite(S1) and _is_finite(S2)

    # Numerical integration / finite difference introduces small error; require close agreement.
    # Tight enough to catch regressions, loose enough to be stable across machines.
    assert abs(S1 - S2) < 1e-6

