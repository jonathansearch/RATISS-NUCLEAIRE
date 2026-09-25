"""Run ignition n=2000 + scène Three.js (D bleu, T rouge, fusions flash).
Usage : python3 demos/ignition.py. MIT."""
import sys
sys.path.insert(0, '/home/user/RATISS-FUSION')
import json
import numpy as np

D = '/home/user/RATISS-FUSION/demos/'
from fusion.plasma import Plasma

pl = Plasma(n=2000, Tkev=0.5)
dt, T_end, A = 0.5e-12, 80e-12, 6e-10
serie, snaps, s = [], [], 0
flashes = []
while pl.t < T_end:
    pl.step(dt, A_imp=A * min(1.0, pl.t / 10e-12))
    e0 = pl.events
    pl.burn(dt)
    if pl.events > e0:
        i = pl.rng.integers(0, 2000, pl.events - e0)
        flashes.append({'t': round(pl.t * 1e12, 2),
                        'X': (pl.X[i] * 1e6).round(2).tolist()})
    if s % 8 == 0:
        serie.append({'t': round(pl.t * 1e12, 2), 'R': round(pl.radius() * 1e6, 3),
                      'T': round(pl.Tmean(), 2), 'ev': pl.events,
                      'Q': float(f'{pl.E_out / max(pl.E_drive, 1e-30):.3e}')})
    if s % 12 == 0:
        snaps.append({'X': (pl.X[::4] * 1e6).round(2).tolist(),
                      'D': pl.is_D[::4].tolist(), 't': round(pl.t * 1e12, 2)})
    s += 1
json.dump({'serie': serie, 'flashes': flashes}, open(D + 'ignition.json', 'w'))
print(f"[ignition] R={serie[-1]['R']}µm T={serie[-1]['T']}keV ev={pl.events} "
      f"Q={serie[-1]['Q']} ({len(snaps)} frames, {len(flashes)} flash-events)")

data = json.dumps({'frames': snaps, 'flashes': flashes,
                   'serie': serie})
html = open('/home/user/RATISS-NAVIER/scripts/make_three.py').read()
start = html.index('html = """') + len('html = """')
end = html.index(chr(34)*3 + chr(10) + "html = html.replace")
tpl = html[start:end]
tpl = tpl.replace('<h3>🌊 Éclatement ν/100 (n=3000)</h3>',
                  '<h3>⚛️ Ignition D-T (n=2000)</h3>')
tpl = tpl.replace("document.getElementById('om').textContent = Math.round(best.Om);",
                  "document.getElementById('om').textContent = best.T + ' keV';")
tpl = tpl.replace("document.getElementById('cc').textContent = best.C.toFixed(3);",
                  "document.getElementById('cc').textContent = best.ev + ' ev';")
tpl = tpl.replace('Ω=<b id="om">0</b><br>C=<b id="cc">1</b>',
                  'T=<b id="om">0</b><br>ev=<b id="cc">0</b>')
tpl = tpl.replace('const c = inferno(f.om[k]/20);',
                  'const c = f.D ? (f.D[k] ? [0.2,0.5,1] : [1,0.35,0.3]) : [1,1,1];')
tpl = tpl.replace("S.forEach((p,i)=>{ const x=p.t/2.5*300, y=115-p.Om/mx*105; i?cx.lineTo(x,y):cx.moveTo(x,y); });",
                  "S.forEach((p,i)=>{ const x=p.t/80*300, y=115-p.T/mxT*105; i?cx.lineTo(x,y):cx.moveTo(x,y); });")
tpl = tpl.replace('const mx = Math.max(...S.map(p=>p.Om));',
                  'const mx = Math.max(...S.map(p=>p.ev)); const mxT = Math.max(...S.map(p=>p.T));')
tpl = tpl.replace("S.forEach((p,i)=>{ const x=p.t/2.5*300, y=115-p.C*105; i?cx.lineTo(x,y):cx.moveTo(x,y); });",
                  "S.forEach((p,i)=>{ const x=p.t/80*300, y=115-p.ev/mx*105; i?cx.lineTo(x,y):cx.moveTo(x,y); });")
tpl = tpl.replace('cx.moveTo(tc/2.5*300,0); cx.lineTo(tc/2.5*300,120);',
                  'cx.moveTo(tc/80*300,0); cx.lineTo(tc/80*300,120);')
tpl = tpl.replace('cam.position.set(2, 2, 9);', 'cam.position.set(0, 0, 40);')
tpl = tpl.replace('ctl.target.set(2, 2, 2);', 'ctl.target.set(0, 0, 0);')
tpl = tpl.replace("new THREE.PointsMaterial({size:0.07, vertexColors:true})",
                  "new THREE.PointsMaterial({size:0.5, vertexColors:true})")
tpl = tpl.replace('new THREE.BoxGeometry(4,4,4)', 'new THREE.BoxGeometry(24,24,24)')
tpl = tpl.replace('max="13"', f'max="{len(snaps)-1}"')
open(D + 'ignition_3d.html', 'w').write(tpl.replace('__DATA__', data))
print('[ignition] html ok')
