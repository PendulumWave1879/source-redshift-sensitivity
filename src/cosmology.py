# -*- coding: utf-8 -*-
"""
Cosmology utilities for Source–Redshift Sensitivity
===================================================

Implements angular diameter distances and critical surface density Σ_crit
for a fixed background (flat) ΛCDM cosmology.

Definitions (flat ΛCDM):
    E(z) = sqrt(Ωm (1+z)^3 + ΩΛ)

Comoving distance:
    D_C(z) = (c/H0) ∫_0^z dz'/E(z')

Angular diameter distance:
    D_A(z) = D_C(z) / (1+z)

Lens-source angular diameter distance:
    D_A(z_l, z_s) = (D_C(z_s) - D_C(z_l)) / (1+z_s)   for z_s > z_l

Critical surface density:
    Σ_crit(z_l, z_s) = (c^2 / (4πG)) * D_s / (D_l * D_ls)

Units:
- Distances are returned in meters (SI).
- Σ_crit returned in kg / m^2 (SI).

Notes:
- This module is intentionally minimal and self-contained (no astropy/scipy).
- Numerical integration uses Simpson's rule with a fixed number of intervals.
"""

from __future__ import division

import math

# Optional numpy acceleration (fallback to pure python if unavailable).
try:
    import numpy as np
except Exception:
    np = None

# Physical constants (SI)
C_LIGHT = 299792458.0               # m/s
G_NEWTON = 6.67430e-11              # m^3 / (kg s^2)
MPC_TO_M = 3.0856775814913673e22    # m
KM_TO_M = 1000.0                    # m


def _simpson_integrate(f, a, b, n):
    """
    Simpson's rule integration of f from a to b using n subintervals.
    n must be even.
    """
    if n <= 0 or (n % 2) != 0:
        raise ValueError("Simpson integration requires positive even n.")

    h = (b - a) / float(n)

    if np is not None:
        x = np.linspace(a, b, n + 1)
        y = f(x)
        # Simpson: h/3 [y0 + yn + 4*sum(y_odd) + 2*sum(y_even)]
        return (h / 3.0) * (y[0] + y[-1] + 4.0 * y[1:-1:2].sum() + 2.0 * y[2:-1:2].sum())

    # Pure python fallback
    s0 = f(a) + f(b)
    s1 = 0.0
    s2 = 0.0
    for i in range(1, n):
        x = a + i * h
        if i % 2 == 1:
            s1 += f(x)
        else:
            s2 += f(x)
    return (h / 3.0) * (s0 + 4.0 * s1 + 2.0 * s2)


class FlatLambdaCDM(object):
    """
    Minimal flat ΛCDM cosmology.

    Parameters
    ----------
    H0_km_s_Mpc : float
        Hubble constant in km/s/Mpc
    Om0 : float
        Matter density parameter at z=0
    Ode0 : float or None
        Dark energy density parameter at z=0; if None, set to 1-Om0
    n_int : int
        Even number of subintervals for Simpson integration
    """
    def __init__(self, H0_km_s_Mpc=70.0, Om0=0.3, Ode0=None, n_int=2048):
        self.H0_km_s_Mpc = float(H0_km_s_Mpc)
        self.Om0 = float(Om0)
        self.Ode0 = float(1.0 - self.Om0) if Ode0 is None else float(Ode0)
        self.n_int = int(n_int)
        if self.n_int % 2 != 0:
            self.n_int += 1  # enforce even

        # H0 in SI (s^-1)
        self.H0_SI = (self.H0_km_s_Mpc * KM_TO_M) / MPC_TO_M

    def E(self, z):
        """Dimensionless expansion function E(z)."""
        if np is not None and hasattr(z, "__len__"):
            z = np.asarray(z, dtype=float)
            return np.sqrt(self.Om0 * (1.0 + z) ** 3 + self.Ode0)
        z = float(z)
        return math.sqrt(self.Om0 * (1.0 + z) ** 3 + self.Ode0)

    def comoving_distance(self, z):
        """
        Line-of-sight comoving distance D_C(z) in meters.
        """
        z = float(z)
        if z < 0.0:
            raise ValueError("z must be >= 0")

        def invE(x):
            return 1.0 / self.E(x)

        integral = _simpson_integrate(invE, 0.0, z, self.n_int) if z > 0.0 else 0.0
        return (C_LIGHT / self.H0_SI) * integral

    def angular_diameter_distance(self, z):
        """
        Angular diameter distance D_A(z) in meters.
        """
        z = float(z)
        if z < 0.0:
            raise ValueError("z must be >= 0")
        Dc = self.comoving_distance(z)
        return Dc / (1.0 + z)

    def angular_diameter_distance_z1z2(self, z1, z2):
        """
        Angular diameter distance between z1 and z2 (z2 > z1), in meters:
            D_A(z1,z2) = (D_C(z2) - D_C(z1)) / (1+z2)
        """
        z1 = float(z1)
        z2 = float(z2)
        if z1 < 0.0 or z2 < 0.0:
            raise ValueError("z must be >= 0")
        if z2 <= z1:
            return float("nan")
        Dc1 = self.comoving_distance(z1)
        Dc2 = self.comoving_distance(z2)
        return (Dc2 - Dc1) / (1.0 + z2)

    def sigma_crit(self, z_l, z_s):
        """
        Critical surface density Σ_crit(z_l, z_s) in kg/m^2.
        Returns NaN if z_s <= z_l.
        """
        z_l = float(z_l)
        z_s = float(z_s)
        if z_s <= z_l:
            return float("nan")

        D_l = self.angular_diameter_distance(z_l)
        D_s = self.angular_diameter_distance(z_s)
        D_ls = self.angular_diameter_distance_z1z2(z_l, z_s)

        if (D_l <= 0.0) or (D_s <= 0.0) or (D_ls <= 0.0) or (D_l != D_l) or (D_s != D_s) or (D_ls != D_ls):
            return float("nan")

        pref = (C_LIGHT ** 2) / (4.0 * math.pi * G_NEWTON)
        return pref * (D_s / (D_l * D_ls))

