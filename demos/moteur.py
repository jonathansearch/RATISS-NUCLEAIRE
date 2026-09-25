"""Démo moteur unifié : turbulence -> ignition -> feedback. PNG + JSON. MIT."""
import sys
sys.path.insert(0, '/home/user/RATISS-NUCLEAIRE')
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from couple.moteur import run_couple

D = '/home/user/RATISS-NUCLEAIRE/demos/'
s, fl, pl = run_couple(n_nav=500, n_fus=300, quiet=False)
s0, _, _ = run_couple(n_nav=500, n_fus=300, feedback=False, quiet=True)
s = [p for p in s if 'R' in p]
s0 = [p for p in s0 if 'R' in p]
json.dump({'couple': s}, open(D + 'moteur.json', 'w'))
t = [p['t'] for p in s]
fig, ax = plt.subplots(2, 2, figsize=(11, 7))
ax[0, 0].plot(t, [p['E'] for p in s], 'b-', label='couplé (feu repousse)')
ax[0, 0].plot([p['t'] for p in s0], [p['E'] for p in s0], 'k--', label='sans feedback')
ax[0, 0].set_ylabel('E turbulente'); ax[0, 0].legend()
ax[0, 0].set_title('NAVIER : le feu pousse le fluide')
ax[0, 1].plot(t, [p['A'] for p in s], 'g-')
ax[0, 1].set_ylabel('A drive (N)'); ax[0, 1].set_title('Couplage : E -> drive')
ax[1, 0].plot(t, [p['R'] for p in s], 'r-', label='R (µm)')
ax[1, 0].plot(t, [p['T'] for p in s], 'm-', label='T (keV)')
ax[1, 0].set_ylabel('R/T'); ax[1, 0].legend(); ax[1, 0].set_xlabel('t navier')
ax[1, 0].set_title('FUSION : compression -> chauffage')
ax[1, 1].plot(t, [p['ev'] for p in s], 'c-', label='events')
ax[1, 1].set_ylabel('events'); ax[1, 1].set_xlabel('t navier')
ax[1, 1].set_title(f'FUSION : {s[-1]["ev"]} fusions (turbulence allume)')
fig.suptitle('MOTEUR UNIFIE : navier comprime -> fusion brule -> feu propulse')
fig.tight_layout()
fig.savefig(D + 'moteur.png', dpi=90)
print('[demo] png ok')
