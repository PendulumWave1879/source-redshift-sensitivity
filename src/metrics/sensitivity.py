cat > src/metrics/sensitivity.py <<'PY'
from __future__ import annotations
import numpy as np

C = 299792458.0
G = 6.67430e-11
ARCSEC_TO_RAD = np.deg2rad(1/3600)

def E(z: float, Om0: float) -> float:
    return np.sqrt(Om0*(1+z)**3 + (1-Om0))

def comoving_distance(z: float, H0: float, Om0: float, n: int = 4096) -> float:
    if z <= 0:
        return 0.0
    if n % 2 == 1:
        n += 1
    zs = np.linspace(0.0, z, n+1)
    f = 1.0 / E(zs, Om0)
    h = z / n
    S = f[0] + f[-1] + 4*np.sum(f[1:-1:2]) + 2*np.sum(f[2:-2:2])
    integral = (h/3.0) * S
    return (C / H0) * integral  # meters

def angular_diameter_distance(z: float, H0: float, Om0: float) -> float:
    Dc = comoving_distance(z, H0, Om0)
    return Dc / (1.0 + z)

def angular_diameter_distance_z1z2(z1: float, z2: float, H0: float, Om0: float) -> float:
    if z2 <= z1:
        return np.nan
    Dc1 = comoving_distance(z1, H0, Om0)
    Dc2 = comoving_distance(z2, H0, Om0)
    return (Dc2 - Dc1) / (1.0 + z2)

def sigma_crit(zl: float, zs: float, H0: float, Om0: float) -> float:
    Dl = angular_diameter_distance(zl, H0, Om0)
    Ds = angular_diameter_distance(zs, H0, Om0)
    Dls = angular_diameter_distance_z1z2(zl, zs, H0, Om0)
    if not np.isfinite(Dls) or Dls <= 0 or Dl <= 0 or Ds <= 0:
        return np.nan
    return (C**2/(4*np.pi*G)) * (Ds / (Dl * Dls))

def Minf(thetaE_arcsec: float, zl: float, zs: float, H0: float, Om0: float) -> float:
    Dl = angular_diameter_distance(zl, H0, Om0)
    if not np.isfinite(Dl) or Dl <= 0:
        return np.nan
    theta = thetaE_arcsec * ARCSEC_TO_RAD
    Sig = sigma_crit(zl, zs, H0, Om0)
    if not np.isfinite(Sig):
        return np.nan
    R = Dl * theta
    return np.pi * (R**2) * Sig

def dlnM_dzs(thetaE_arcsec: float, zl: float, zs: float, H0: float, Om0: float,
             dz: float = 1e-3) -> float:
    z1 = zs - dz
    z2 = zs + dz
    if z1 <= zl + 1e-6:
        z1 = zs
        z2 = zs + 2*dz
    M1 = Minf(thetaE_arcsec, zl, z1, H0, Om0)
    M2 = Minf(thetaE_arcsec, zl, z2, H0, Om0)
    if not np.isfinite(M1) or not np.isfinite(M2) or M1 <= 0 or M2 <= 0:
        return np.nan
    return (np.log(M2) - np.log(M1)) / (z2 - z1)
PY

