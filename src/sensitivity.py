# -*- coding: utf-8 -*-
"""
Sensitivity kernel for Source–Redshift Sensitivity
==================================================

Implements the per-lens computation specified in docs/metric.md:

    M_inf(<θ_E; z_s) = π (D_l θ_E)^2 Σ_crit(z_l, z_s)

Primary sensitivity metric:
    S(z_s) = ∂ ln M_inf / ∂ z_s = ∂ ln Σ_crit / ∂ z_s

Finite difference (central):
    S(z_s) ≈ [ln Σ(z_s+h) - ln Σ(z_s-h)] / (2h)

Bias mapping:
    ΔM/M ≈ S(z_s) * Δz_s

This module performs:
- input validation (raw fields) via src.validate.validate_lens_inputs
- computed-quantity validation (finite/positive Σ_crit, finite S)
"""

from __future__ import division

import math

from src.validate import validate_lens_inputs

ARCSEC_TO_RAD = (math.pi / 180.0) / 3600.0


def _is_nan(x):
    return x != x

def _is_inf(x):
    return x == float('inf') or x == float('-inf')

def _is_finite(x):
    return (x is not None) and (not _is_nan(x)) and (not _is_inf(x))


def compute_sensitivity(theta_E_arcsec, z_l, z_s, cosmo, h=1e-3, delta_z=0.1):
    """
    Compute M_inf, S(z_s), and ΔM/M mapping for one lens system.

    Parameters
    ----------
    theta_E_arcsec : float
        Einstein radius in arcseconds (observed)
    z_l : float
        Lens redshift (observed)
    z_s : float
        Source redshift (assumed)
    cosmo : object
        Cosmology object providing:
            - angular_diameter_distance(z)
            - sigma_crit(z_l, z_s)
    h : float
        Finite-difference step for z_s (fixed). Must be > 0.
    delta_z : float
        Reference redshift error used for the derived mapping ΔM/M.

    Returns
    -------
    dict with keys:
        - is_valid : bool
        - flags : list[str]
        - theta_E_arcsec, z_l, z_s
        - theta_E_rad
        - D_l_m
        - Sigma_crit_kg_m2
        - M_inf_kg
        - S_dlnM_dzs
        - dM_over_M_for_delta_z
    """
    out = {
        'is_valid': False,
        'flags': [],
        'theta_E_arcsec': theta_E_arcsec,
        'z_l': z_l,
        'z_s': z_s,
        'theta_E_rad': float('nan'),
        'D_l_m': float('nan'),
        'Sigma_crit_kg_m2': float('nan'),
        'M_inf_kg': float('nan'),
        'S_dlnM_dzs': float('nan'),
        'dM_over_M_for_delta_z': float('nan'),
    }

    # ---- Raw input validation ----
    v = validate_lens_inputs(theta_E_arcsec, z_l, z_s, require_zs=True, strict=True)
    if not v['is_valid']:
        out['flags'] = list(v['flags'])
        return out

    th_arcsec = v['normalized']['theta_E_arcsec']
    zl = v['normalized']['z_l']
    zs = v['normalized']['z_s']

    if h is None or float(h) <= 0.0:
        out['flags'] = ['flag_invalid_h']
        return out

    # ---- Compute core quantities ----
    theta_rad = th_arcsec * ARCSEC_TO_RAD
    out['theta_E_rad'] = theta_rad

    D_l = cosmo.angular_diameter_distance(zl)
    out['D_l_m'] = D_l

    Sigma = cosmo.sigma_crit(zl, zs)
    out['Sigma_crit_kg_m2'] = Sigma

    # Validate computed Sigma and distance
    if (not _is_finite(D_l)) or D_l <= 0.0:
        out['flags'] = ['flag_nonfinite_D_l']
        return out
    if (not _is_finite(Sigma)) or Sigma <= 0.0:
        out['flags'] = ['flag_nonfinite_Sigma_crit']
        return out

    # M_inf(<θE; zs) = π (D_l θ_E)^2 Σ_crit
    R = D_l * theta_rad
    M_inf = math.pi * (R ** 2) * Sigma
    out['M_inf_kg'] = M_inf

    if (not _is_finite(M_inf)) or M_inf <= 0.0:
        out['flags'] = ['flag_nonfinite_M_inf']
        return out

    # ---- Sensitivity S(zs) = d ln Sigma / dzs via central difference ----
    # Guard against zs-h <= zl (Sigma becomes undefined). In that case use one-sided difference.
    flags = []

    z_minus = zs - float(h)
    z_plus = zs + float(h)

    def ln_sigma(zv):
        s = cosmo.sigma_crit(zl, zv)
        if (not _is_finite(s)) or s <= 0.0:
            return float('nan')
        return math.log(s)

    # Try central difference first.
    ln_sp = ln_sigma(z_plus)
    ln_sm = ln_sigma(z_minus)

    if _is_finite(ln_sp) and _is_finite(ln_sm):
        S = (ln_sp - ln_sm) / (2.0 * float(h))
    else:
        # Fallback: one-sided differences (prefer forward)
        ln_s0 = ln_sigma(zs)
        if not _is_finite(ln_s0):
            out['flags'] = ['flag_nonfinite_lnSigma_at_zs']
            return out

        ln_sp = ln_sigma(z_plus)
        if _is_finite(ln_sp):
            S = (ln_sp - ln_s0) / float(h)
            flags.append('flag_used_forward_diff')
        else:
            ln_sm = ln_sigma(z_minus)
            if _is_finite(ln_sm):
                S = (ln_s0 - ln_sm) / float(h)
                flags.append('flag_used_backward_diff')
            else:
                out['flags'] = ['flag_nonfinite_S']
                return out

    out['S_dlnM_dzs'] = S

    if not _is_finite(S):
        out['flags'] = ['flag_nonfinite_S']
        return out

    # Derived mapping for a reference redshift error delta_z
    dz = float(delta_z)
    out['dM_over_M_for_delta_z'] = S * dz

    # Success
    out['is_valid'] = True
    out['flags'] = flags
    out['theta_E_arcsec'] = th_arcsec
    out['z_l'] = zl
    out['z_s'] = zs
    return out

