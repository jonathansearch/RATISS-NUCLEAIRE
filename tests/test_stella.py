"""Tests stellaires : effondrement puis ignition-explosion. MIT."""
import sys
sys.path.insert(0, '/home/user/RATISS-NUCLEAIRE')


def _run(n=500, T_end=200e-12, G=5e30):
    from fusion.plasma import Plasma
    pl = Plasma(n=n, R0=20e-6, Tkev=0.1)
    dt = 0.5e-12
    Rm, Tm = 1e9, 0
    while pl.t < T_end:
        pl.step(dt, G_eff=G)
        pl.burn(dt)
        pl.brem(dt)
        Rm = min(Rm, pl.radius())
        Tm = max(Tm, pl.Tmean())
    return pl, Rm, Tm


def test_stella_collapse():
    pl, Rm, Tm = _run()
    assert Rm < 12e-6, Rm  # collapse net depuis 15µm


def test_stella_ignition():
    pl, Rm, Tm = _run()
    assert pl.events > 0, 'pas dignition stellaire !'
    assert Tm > 5.0, Tm
    assert pl.E_grav > 0
