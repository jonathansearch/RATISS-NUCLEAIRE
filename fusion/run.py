"""Run implosion v0.2 : drive -> compression -> burn (depletion, alpha, brem). MIT."""


def run(n=2000, T_end=60e-12, dt=0.5e-12, A_imp=1e-10, Tkev=0.5, quiet=False):
    import numpy as np
    from .plasma import Plasma
    pl = Plasma(n=n, Tkev=Tkev)
    serie = []
    s = 0
    while pl.t < T_end:
        ramp = min(1.0, pl.t / 10e-12)
        pl.step(dt, A_imp=A_imp * ramp)
        pl.burn(dt)
        pl.brem(dt)
        if s % 10 == 0:
            serie.append({'t': round(pl.t * 1e12, 2), 'R': round(pl.radius() * 1e6, 3),
                          'T': round(pl.Tmean(), 2), 'ev': pl.events,
                          'Eout': float(f'{pl.E_out:.3e}'),
                          'Edrive': float(f'{pl.E_drive:.3e}'),
                          'Erad': float(f'{pl.E_rad:.3e}'),
                          'fuel': round(pl.fuel_left(), 1),
                          'ash': pl.ash_count()})
        s += 1
    if not quiet:
        print(f"[fusion] R={serie[-1]['R']}µm T={serie[-1]['T']}keV ev={pl.events} "
              f"Q={pl.E_out / max(pl.E_drive, 1e-30):.2e} fuel={pl.fuel_left():.0f} "
              f"ash={pl.ash_count()} Erad={pl.E_rad:.2e}")
    return serie, pl
