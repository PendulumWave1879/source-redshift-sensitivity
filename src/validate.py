"""
Input Validation for Source–Redshift Sensitivity Metric
======================================================

Strict validation and flagging for per-system inputs used to compute the
source–redshift sensitivity metric defined in docs/metric.md.

Core validity conditions:
    - z_s > z_l
    - theta_E > 0
    - z_l >= 0
    - inputs numeric and finite (not NaN/inf)

This module validates raw catalogue fields only. Cosmology-derived quantities
(distance finiteness, Sigma_crit finiteness) should be validated in the metric
kernel after computation.
"""

def _is_nan(x):
    return x != x

def _is_inf(x):
    return x == float('inf') or x == float('-inf')

def validate_lens_inputs(theta_E_arcsec, z_l, z_s, require_zs=True, strict=True):
    """
    Validate raw per-system inputs.

    Returns a dict:
        {
          'is_valid': bool,
          'flags': [str, ...],
          'normalized': {'theta_E_arcsec': float, 'z_l': float, 'z_s': float?}
        }
    """
    flags = []
    normalized = {}

    def _to_float(x, name):
        if x is None:
            flags.append('flag_missing_%s' % name)
            return None
        try:
            v = float(x)
        except (TypeError, ValueError):
            flags.append('flag_non_numeric_%s' % name)
            return None
        if _is_nan(v):
            flags.append('flag_nan_%s' % name)
            return None
        if _is_inf(v):
            flags.append('flag_inf_%s' % name)
            return None
        return v

    th = _to_float(theta_E_arcsec, 'thetaE')
    zl = _to_float(z_l, 'zl')

    # z_s may be optional upstream, but metric computation still requires it.
    zs = None
    if require_zs or (z_s is not None):
        zs = _to_float(z_s, 'zs')

    if th is not None and th <= 0.0:
        flags.append('flag_thetaE_nonpositive')

    if zl is not None and zl < 0.0:
        flags.append('flag_zl_negative')

    if require_zs:
        if zs is not None and zs < 0.0:
            flags.append('flag_zs_negative')
        if zs is not None and zl is not None and not (zs > zl):
            flags.append('flag_zs_le_zl')
    else:
        if zs is not None:
            if zs < 0.0:
                flags.append('flag_zs_negative')
            if zl is not None and not (zs > zl):
                flags.append('flag_zs_le_zl')

    is_valid = (len(flags) == 0) if strict else True

    if is_valid:
        normalized = {'theta_E_arcsec': th, 'z_l': zl}
        if zs is not None:
            normalized['z_s'] = zs

    return {'is_valid': is_valid, 'flags': flags, 'normalized': normalized}
