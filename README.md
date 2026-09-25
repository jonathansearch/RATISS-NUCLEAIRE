# RATISS-NUCLEAIRE

Fusion ICF + stellaire. SANS NEURONES. Méthode maison : particules + Bosch-Hale
+ burn Monte-Carlo + α + gravité. Importe RATISS-FUSION v0.1, puis v0.2 + stellaire.

## Physique

**ICF v0.2** : bille D-T (w=1e7), drive central, répulsion Debye, Bosch-Hale réel,
déplétion D/T (fuel→cendre), α : dépôt local × confinement ρR + transport
diffusif (portée ~T²/n) + échappement compté, bremstrahlung, Q=E_neutrons/E_injectée.

**Stellaire** : même moteur + gravité sphérique M_enc(r), G_eff renormalisé
(jouet : masses ~1e-16 kg, G boosté pour t_ff ~ ps — assumé, cf code).

**Cinétique macro (assumée, honnête)** : densités réelles n=compte·w/V, chaque
événement Poisson = w paires. Sans ce boost ×w, le jouet (ρR~1e-10 g/cm²,
à 1e10 de l'ignition NIF) ne brûlerait jamais. Testé : taux ÷w → 0 events
même à C=3.3, T=31 keV. Le boost est le choix de modélisation explicite.

## Lancer

```bash
pip install -e .
pytest tests/ -q              # 9 tests : 7 fusion + 2 stellaires
python3 demos/ignition.py     # ICF v0.2 -> demos/ignition_3d.html
python3 demos/stellar.py      # supernova -> demos/stellar_3d.html
```

## Résultats

- ICF v0.2 (n=2000, 80 ps) : R 7.45→3.21µm, T→18.4 keV, 436 fusions,
  Q : 0 → pic 101 → 60. Burn auto-étouffé par déplétion locale. ✅
- Stellaire (n=1500, 60 ps) : R 14.9→5.3µm, T 0.2→16 keV → flash 173 ev
  (T=161 keV) → explosion R=141µm. Effondrement→Ignition→Explosion. ✅

Scènes Three.js : télécharger + ouvrir avec Chrome (CDN bloqué en aperçu).

## Licence

MIT.
