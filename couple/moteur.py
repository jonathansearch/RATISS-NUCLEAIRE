"""MOTEUR UNIFIÉ v0.1 : NAVIER comprime -> FUSION brûle -> énergie repoussée.

Couplage 0D (échange global, splitting d'opérateurs) :
- NAVIER -> FUSION : pression dynamique turbulente E_turb -> drive implosion
  A = min(A_base * E/E_ref, A_max). La turbulence COMPRIME le combustible.
- FUSION -> NAVIER : E_fusion produite -> kick isotrope du coeur fluide
  (r < 1.5), kick = sqrt(2.dE.G_c / (n_coeur.m_code)). Le feu POUSSE le fluide.
Constantes jouet assumées : E_ref, A_base, A_max, G_c (cf README). MIT.
"""
import sys
sys.path.insert(0, '/home/user/RATISS-NAVIER')
sys.path.insert(0, '/home/user/RATISS-NUCLEAIRE')
import numpy as np


def run_couple(n_nav=300, n_fus=200, T_nav=1.2, A_base=2e-10, E_ref=10.0,
               A_max=2e-9, A_floor=1e-10, G_c=20000.0, feedback=True, force=True, sub=4,
               seed=7, quiet=False):
    from navier.sph import Flow
    from navier.vortex import Forcing
    from fusion.plasma import Plasma
    fl = Flow(n=n_nav, nu=0.01, seed=seed)
    fl.settle()
    fc = Forcing(active=force)
    pl = Plasma(n=n_fus, Tkev=0.5, seed=seed)
    rng = np.random.default_rng(seed)
    m_code = 1.0 * 4 ** 3 / n_nav
    dt_f = 0.5e-12
    serie, E_prev, E_inj = [], 0.0, 0.0
    s = 0
    while fl.t < T_nav:
        dt = fl.step(f_ext=fc)
        if not (np.isfinite(fl.V).all() and np.isfinite(fl.rho).all()):
            serie.append({'t': round(fl.t, 4), 'CRASH': True})
            break
        E = fl.energy()
        A = min(max(A_base * E / E_ref, A_floor), A_max)
        for _ in range(sub):
            pl.step(dt_f, A_imp=A)
            pl.burn(dt_f)
            pl.brem(dt_f)
        dE = pl.E_out - E_prev
        E_prev = pl.E_out
        if feedback and dE > 0:
            d = np.linalg.norm(fl.X - 2.0, axis=1)
            core = np.where(d < 1.5)[0]
            if len(core) > 0:
                kick = min(np.sqrt(2 * dE * G_c / (len(core) * m_code)), 3.0)
                u = rng.normal(0, 1, (len(core), 3))
                u /= np.linalg.norm(u, axis=1, keepdims=True)
                fl.V[core] += u * kick
                E_inj += dE * G_c
        if s % 20 == 0:
            serie.append({'t': round(fl.t, 4), 'E': round(E, 3),
                          'A': float(f'{A:.2e}'), 'R': round(pl.radius() * 1e6, 3),
                          'T': round(pl.Tmean(), 2), 'ev': pl.events,
                          'Efus': float(f'{pl.E_out:.3e}'),
                          'Einj': float(f'{E_inj:.3e}')})
        s += 1
    if not quiet:
        print(f"[moteur] E_nav={serie[-1].get('E')} ev={pl.events} "
              f"Efus={pl.E_out:.2e}J Einj={E_inj:.2e} (feedback={feedback})")
    return serie, fl, pl
