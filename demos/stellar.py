"""Run stellaire : effondrement gravifique -> ignition -> explosion + scene Three.js.
G_eff renormalise (jouet, cf README). Usage : python3 demos/stellar.py. MIT."""
import sys
sys.path.insert(0, '/home/user/RATISS-NUCLEAIRE')
import json
import numpy as np

D = '/home/user/RATISS-NUCLEAIRE/demos/'
from fusion.plasma import Plasma

pl = Plasma(n=1500, R0=20e-6, Tkev=0.1)
dt, T_end, G = 0.5e-12, 60e-12, 3e30
serie, snaps, s = [], [], 0
flashes = []
while pl.t < T_end:
    pl.step(dt, G_eff=G)
    e0 = pl.events
    pl.burn(dt)
    pl.brem(dt)
    if pl.events > e0:
        i = pl.rng.integers(0, 1500, pl.events - e0)
        flashes.append({'t': round(pl.t * 1e12, 2),
                        'X': (pl.X[i] * 1e6).round(2).tolist()})
    if s % 10 == 0:
        serie.append({'t': round(pl.t * 1e12, 2), 'R': round(pl.radius() * 1e6, 3),
                      'T': round(pl.Tmean(), 2), 'ev': pl.events,
                      'Q': float(f'{pl.E_out / max(pl.E_grav, 1e-30):.3e}')})
    if s % 8 == 0:
        sp = np.linalg.norm(pl.V[::4], axis=1)
        sp = (sp / max(sp.max(), 1e-9)).round(3)
        snaps.append({'X': (pl.X[::4] * 1e6).round(2).tolist(),
                      'sp': sp.tolist(), 't': round(pl.t * 1e12, 2)})
    s += 1
json.dump({'serie': serie, 'flashes': flashes}, open(D + 'stellar.json', 'w'))
print(f"[stellar] R={serie[-1]['R']}µm T={serie[-1]['T']}keV ev={pl.events} "
      f"Q={serie[-1]['Q']} ({len(snaps)} frames)")

data = json.dumps({'frames': snaps, 'flashes': flashes, 'serie': serie})
html = open('/home/user/RATISS-NAVIER/scripts/make_three.py').read()
start = html.index('html = """') + len('html = """')
end = html.index(chr(34) * 3 + chr(10) + "html = html.replace")
tpl = html[start:end]
tpl = tpl.replace('<h3>🌊 Éclatement ν/100 (n=3000)</h3>',
                  '<h3>🌟 Effondrement stellaire (n=1500)</h3>')
tpl = tpl.replace("document.getElementById('om').textContent = Math.round(best.Om);",
                  "document.getElementById('om').textContent = best.T + ' keV';")
tpl = tpl.replace("document.getElementById('cc').textContent = best.C.toFixed(3);",
                  "document.getElementById('cc').textContent = best.ev + ' ev';")
tpl = tpl.replace('Ω=<b id="om">0</b><br>C=<b id="cc">1</b>',
                  'T=<b id="om">0</b><br>ev=<b id="cc">0</b>')
tpl = tpl.replace('const c = inferno(f.om[k]/20);', 'const c = inferno(f.sp[k]);')
tpl = tpl.replace("S.forEach((p,i)=>{ const x=p.t/2.5*300, y=115-p.Om/mx*105; i?cx.lineTo(x,y):cx.moveTo(x,y); });",
                  "S.forEach((p,i)=>{ const x=p.t/60*300, y=115-p.T/mxT*105; i?cx.lineTo(x,y):cx.moveTo(x,y); });")
tpl = tpl.replace('const mx = Math.max(...S.map(p=>p.Om));',
                  'const mx = Math.max(...S.map(p=>p.ev)); const mxT = Math.max(...S.map(p=>p.T));')
tpl = tpl.replace("S.forEach((p,i)=>{ const x=p.t/2.5*300, y=115-p.C*105; i?cx.lineTo(x,y):cx.moveTo(x,y); });",
                  "S.forEach((p,i)=>{ const x=p.t/60*300, y=115-p.ev/mx*105; i?cx.lineTo(x,y):cx.moveTo(x,y); });")
tpl = tpl.replace('cx.moveTo(tc/2.5*300,0); cx.lineTo(tc/2.5*300,120);',
                  'cx.moveTo(tc/60*300,0); cx.lineTo(tc/250*300,120);')
tpl = tpl.replace('cam.position.set(2, 2, 9);', 'cam.position.set(0, 0, 380);')
tpl = tpl.replace('ctl.target.set(2, 2, 2);', 'ctl.target.set(0, 0, 0);')
tpl = tpl.replace('PerspectiveCamera(55, innerWidth/innerHeight, 0.1, 100)',
                  'PerspectiveCamera(55, innerWidth/innerHeight, 0.1, 1200)')
tpl = tpl.replace("new THREE.PointsMaterial({size:0.07, vertexColors:true})",
                  "new THREE.PointsMaterial({size:2.5, vertexColors:true})")
tpl = tpl.replace('new THREE.BoxGeometry(4,4,4)', 'new THREE.BoxGeometry(340,340,340)')
tpl = tpl.replace('max="13"', f'max="{len(snaps)-1}"')
open(D + 'stellar_3d.html', 'w').write(tpl.replace('__DATA__', data))
print('[stellar] html ok')
