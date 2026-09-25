"""Plasma D-T v0.2 : bille de macroparticules (poids w) + implosion ICF + fusion.
Par cellule : T (dispersion), lam = nD.nT.<sv>.V.dt (Poisson, densites ponderees
par fuel), depletion D/T, alpha : depot local f_dep + transport diffusif vers
cellule voisine (portee ~ T^2/n) + fraction echappee, bremstrahlung, neutrons
14.1MeV -> E_out. Gravite spherique M_enc(r) en option (stellaire). SI. MIT."""
import numpy as np
from .bosch_hale import sigma_v

KB, AMU = 1.380649e-23, 1.660539e-27
M_D, M_T = 2.014 * AMU, 3.016 * AMU
MEV_J = 1.602176634e-13
E_ALPHA, E_NEUT = 3.5 * MEV_J, 14.1 * MEV_J
KEV_J = 1e3 * 1.602176634e-19


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
        vth = np.sqrt(2 * Tkev * KEV_J / m)
        self.V = rng.normal(0, 1, (n, 3)) * vth[:, None]
        self.m = m
        self.fuel = np.ones(n)  # fraction combustible restante (1 -> 0 = cendre)
        self.R0 = R0
        self.t = 0.0
        self.E_drive = 0.0
        self.E_grav = 0.0  # energie fournie par gravite (positif cumule)
        self.E_out = 0.0
        self.E_rad = 0.0  # pertes bremstrahlung
        self.E_alpha_dep = 0.0  # alpha deposes (local + transport)
        self.E_alpha_lost = 0.0  # alpha echappes (non deposes)
        self.events = 0
        self.alive = np.ones(n, bool)

    def step(self, dt, A_imp=0.0, C_rep=1e-24, eps=0.1e-6, lamD=0.1e-6,
             G_eff=0.0):
        X, V = self.X[self.alive], self.V[self.alive]
        r = np.linalg.norm(X, axis=1, keepdims=True)
        r = np.maximum(r, 1e-12)
        F_d = -A_imp * X / r
        F = F_d.copy()
        if G_eff > 0:  # gravite spherique M_enc(r), O(N log N)
            rf = r.ravel()
            order = np.argsort(rf)
            m = self.m[self.alive]
            Menc = np.cumsum(m[order])[np.argsort(order)]
            Fg = G_eff * Menc * m / np.maximum(rf, 1e-9) ** 2
            F += -Fg[:, None] * X / r
        d = X[:, None, :] - X[None, :, :]
        dist = np.sqrt((d ** 2).sum(-1) + eps ** 2)
        np.fill_diagonal(dist, np.inf)
        F += (C_rep * np.exp(-dist / lamD)[:, :, None]
              * (d / dist[:, :, None] ** 3)).sum(1)  # Debye
        m = self.m[self.alive]
        V += F / m[:, None] * dt
        dE = float((F_d * V * dt).sum()) * self.w
        self.E_drive += max(dE, 0.0)  # energie injectee (jamais recuperee)
        if G_eff > 0:
            dEg = float(((-Fg[:, None] * X / r) * V * dt).sum()) * self.w
            self.E_grav += max(dEg, 0.0)
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
            cells[int(k)] = {'idx': ii, 'Tkev': float(T_J / KEV_J),
                             'vol': vol, 'C': self.X[ii].mean(0)}
        return cells

    def _kick(self, ii, E_real):
        """Depose E_real (joules reels) en chauffage isotrope sur macros ii."""
        if len(ii) == 0 or E_real <= 0:
            return 0.0
        dE = E_real / (len(ii) * self.w)  # par ion reel
        kick = np.sqrt(2 * dE / self.m[ii])
        u = self.rng.normal(0, 1, (len(ii), 3))
        u /= np.linalg.norm(u, axis=1, keepdims=True)
        self.V[ii] += u * kick[:, None]
        return E_real

    def burn(self, dt):
        cells = self.cell_stats()
        keys = list(cells.keys())
        centers = np.array([cells[k]['C'] for k in keys])
        for j, k in enumerate(keys):
            c = cells[k]
            ii, T, V = c['idx'], c['Tkev'], c['vol']
            if T < 0.5 or len(ii) < 4:
                continue
            iD = ii[self.is_D[ii]]
            iT = ii[~self.is_D[ii]]
            if len(iD) == 0 or len(iT) == 0:
                continue
            nD = (self.fuel[iD].sum() * self.w) / V
            nT = (self.fuel[iT].sum() * self.w) / V
            lam = nD * nT * float(sigma_v(T)) * V * dt  # cinetique MACRO : 1 event = w paires (boost xw explicite, cf README)
            nbar = (nD + nT) / 2
            f_dep = min(1.0, (nbar / 3e26) ** 2)  # confinement alpha (proxy rho-R)
            nev = self.rng.poisson(min(lam, 20))
            nev = min(nev, len(ii) // 2, int(self.fuel[iD].sum()),
                      int(self.fuel[iT].sum()))
            if nev <= 0:
                continue
            self.events += nev
            E_ev = nev * self.w  # joules reels par MeV-unit : x E_*
            self.E_out += nev * E_NEUT * self.w
            # depletion : chaque event brule 1 paire reelle par macro touchee
            self.fuel[iD] = np.clip(self.fuel[iD] - nev / len(iD), 0, 1)
            self.fuel[iT] = np.clip(self.fuel[iT] - nev / len(iT), 0, 1)
            # alpha : local + transport diffusif + echappement
            E_a = nev * E_ALPHA * self.w
            self.E_alpha_dep += self._kick(ii, E_a * f_dep)
            E_tr = E_a * (1 - f_dep)
            if E_tr > 0:
                Ra = 3e-6 * (T / 10) ** 2 / max(nbar / 3e26, 0.02)
                Ra = min(Ra, 60e-6)
                tgt = c['C'] + self.rng.normal(0, 1, 3)
                tgt = c['C'] + (tgt - c['C']) / max(np.linalg.norm(tgt - c['C']), 1e-18) * Ra
                dd = np.linalg.norm(centers - tgt, axis=1)
                jb = int(np.argmin(dd))
                if dd[jb] < 2 * V ** (1 / 3):
                    self.E_alpha_dep += self._kick(cells[keys[jb]]['idx'], E_tr)
                else:
                    self.E_alpha_lost += E_tr

    def brem(self, dt):
        """Bremstrahlung : P = 1.69e-45 ne^2 sqrt(T[eV]) W/m^3, refroidit."""
        for c in self.cell_stats().values():
            ii, T, V = c['idx'], c['Tkev'], c['vol']
            if T < 0.3 or len(ii) < 2:
                continue
            ne = len(ii) * self.w / V
            P = 1.69e-45 * ne ** 2 * np.sqrt(T * 1000)
            dE = P * V * dt
            Ecell = 1.5 * len(ii) * self.w * T * KEV_J
            if Ecell <= 0:
                continue
            frac = min(dE / Ecell, 0.1)
            if frac <= 0:
                continue
            vm = self.V[ii].mean(0)
            self.V[ii] = vm + (self.V[ii] - vm) * np.sqrt(1 - frac)
            self.E_rad += dE

    def radius(self):
        return float(np.linalg.norm(self.X[self.alive], axis=1).mean())

    def Tmean(self):
        v = self.V[self.alive]
        vd = v - v.mean(0)
        m = self.m[self.alive]
        return float((m[:, None] * vd ** 2).sum() / (3 * len(v)) / KEV_J)

    def fuel_left(self):
        return float(self.fuel[self.alive].sum())

    def ash_count(self):
        return int((self.fuel[self.alive] <= 0).sum())
