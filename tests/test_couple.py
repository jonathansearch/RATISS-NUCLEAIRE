"""Tests moteur unifié : turbulence allume, calme éteint, feu repousse. MIT."""
import os as _os, pathlib as _pl  # RATISS: chemins portables (dépôts clonés côte à côte, ou RATISS_HOME)
_RATISS_HOME = _os.environ.get('RATISS_HOME') or str(_pl.Path(__file__).resolve().parents[2])
import sys
sys.path.insert(0, (_RATISS_HOME + '/RATISS-NUCLEAIRE'))


def test_turbulence_allume():
    from couple.moteur import run_couple
    s, fl, pl = run_couple(quiet=True)
    assert pl.events > 0, 'la turbulence n allume pas !'
    assert min(p['R'] for p in s if 'R' in p) < 6.0  # compression x1.2+


def test_calme_eteint():
    from couple.moteur import run_couple
    s, fl, pl = run_couple(force=False, quiet=True)
    assert pl.events == 0, pl.events  # plancher seul : pas de burn


def test_feedback_chauffe():
    from couple.moteur import run_couple
    s1, _, _ = run_couple(feedback=True, quiet=True)
    s0, _, _ = run_couple(feedback=False, quiet=True)
    assert s1[-1]['E'] > s0[-1]['E'], (s1[-1]['E'], s0[-1]['E'])
