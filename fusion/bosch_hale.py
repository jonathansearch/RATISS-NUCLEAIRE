"""Réactivité D-T <σv> — Bosch-Hale 1992 (Nuclear Fusion), SI (m³/s).
T en keV. Sanity : <σv>(10keV) ≈ 1.1e-22 m³/s. MIT."""
import numpy as np

BG = 34.3827
MRC2 = 1124656.0
C1, C2, C3, C4 = 1.17302e-9, 1.51361e-2, 7.51886e-2, 4.60643e-3
C5, C6, C7 = 1.35e-2, -1.0675e-4, 1.366e-5


def sigma_v(Tkev):
    """<σv> D-T en m³/s. Bosch-Hale (formule d'origine en cm³/s × 1e-6)."""
    T = np.maximum(np.asarray(Tkev, float), 0.2)
    th = T / (1 - T * (C2 + T * (C4 + T * C6)) / (1 + T * (C3 + T * (C5 + T * C7))))
    xi = (BG ** 2 / (4 * th)) ** (1 / 3)
    sv_cm = C1 * th * np.sqrt(xi / (MRC2 * T ** 3)) * np.exp(-3 * xi)
    return sv_cm * 1e-6
