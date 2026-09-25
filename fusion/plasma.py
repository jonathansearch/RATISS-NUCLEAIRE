"""Plasma D-T : bille de macroparticules (poids w) + implosion ICF + fusion.
Par cellule : T (dispersion), λ = nD·nT·<σv>·V·dt (Poisson), α-heating 3.5MeV
local, neutrons 14.1MeV -> E_out. Unités SI. MIT."""
import numpy as np
from .bosch_hale import sigma_v

KB, AMU = 1.380649e-23, 1.660539e-27
M_D, M_T = 2.014 * AMU, 3.016 * AMU
MEV_J = 1.602176634e-13
E_ALPHA, E_NEUT = 3.5 * MEV_J, 14.1 * MEV_J


class Plasma:
    def __init__(self, n=2000, R0=10e-6, Tkev=0.5, w=1e7, seed=11):
        rng = np.random.default_rng(seed)
        self.n, self.w = n, w
        self.rng = rng
        u = rng.normal(0, 1, (n, 3))
        u /= np.linalg.norm(u, axis=1, keepdims=True)
        self.X = u * (R0 * rng.uniform(0, 1, n) ** (1 / 3))[:, None]
        self.is_D = rng.random(n) < 0.5
        m = np.where(self.is_D, M_D, M_T)
        vth = np.sqrt(2 * Tkev * 1e3 * 1.602176634e-19 / m)
        self.V = rng.normal(0, 1, (n, 3)) * vth[:, None]
        self.m = m
        self.R0 = R0
        self.t = 0.0
        self.E_drive = 0.0
        self.E_out = 0.0
        self.events = 0
        self.alive = np.ones(n, bool)

    def step(self, dt, A_imp=0.0, C_rep=1e-24, eps=0.1e-6, lamD=0.1e-6):
        X, V = self.X[self.alive], self.V[self.alive]
        r = np.linalg.norm(X, axis=1, keepdims=True)
        r = np.maximum(r, 1e-12)
        F_d = -A_imp * X / r
        F = F_d.copy()
        d = X[:, None, :] - X[None, :, :]
        dist = np.sqrt((d ** 2).sum(-1) + eps ** 2)
        np.fill_diagonal(dist, np.inf)
        F += (C_rep * np.exp(-dist / lamD)[:, :, None] * (d / dist[:, :, None] ** 3)).sum(1)  # Debye
        m = self.m[self.alive]
        V += F / m[:, None] * dt
        dE = float((F_d * V * dt).sum()) * self.w
        self.E_drive += max(dE, 0.0)  # energie injectee (jamais recuperee)
        X += V * dt
        self.X[self.alive], self.V[self.alive] = X, V
        self.t += dt

    def cell_stats(self, nc=6):
        X = self.X[self.alive]
        lo, hi = X.min(0), X.max(0) + 1e-18
        idx = np.clip(((X - lo) / (hi - lo) * nc).astype(int), 0, nc - 1)
        key = idx[:, 0] * nc * nc + idx[:, 1] * nc + idx[:, 2]
        vol = float(np.prod(hi - lo)) / nc ** 3
        cells = {}
        for k in np.unique(key):
            m = key == k
            ii = np.where(self.alive)[0][m]
            v = self.V[ii]
            vd = v - v.mean(0)
            T_J = (self.m[ii][:, None] * vd ** 2).sum() / max(3 * len(ii), 1)
            cells[int(k)] = {'idx': ii, 'Tkev': float(T_J / (1e3 * 1.602176634e-19)),
                             'vol': vol}
        return cells

    def burn(self, dt):
        for c in self.cell_stats().values():
            ii, T, V = c['idx'], c['Tkev'], c['vol']
            if T < 0.5 or len(ii) < 4:
                continue
            nD = (self.is_D[ii].sum() * self.w) / V
            nT = ((~self.is_D[ii]).sum() * self.w) / V
            lam = nD * nT * float(sigma_v(T)) * V * dt
            f_dep = min(1.0, ((nD + nT) / 2 / 3e26) ** 2)  # confinement alpha (proxy rho-R)
            nev = self.rng.poisson(min(lam, 20))
            nev = min(nev, len(ii) // 2)
            if nev <= 0:
                continue
            self.events += nev
            self.E_out += nev * E_NEUT * self.w
            dE = nev * E_ALPHA * f_dep / len(ii)  # par ion reel (macro: E*w sur m*w)
            kick = np.sqrt(2 * dE / self.m[ii])
            u = self.rng.normal(0, 1, (len(ii), 3))
            u /= np.linalg.norm(u, axis=1, keepdims=True)
            self.V[ii] += u * kick[:, None]

    def radius(self):
        return float(np.linalg.norm(self.X[self.alive], axis=1).mean())

    def Tmean(self):
        v = self.V[self.alive]
        vd = v - v.mean(0)
        m = self.m[self.alive]
        return float((m[:, None] * vd ** 2).sum() / (3 * len(v)) / (1e3 * 1.602176634e-19))
