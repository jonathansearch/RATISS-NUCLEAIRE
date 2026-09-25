# RATISS-FUSION

Bille de plasma D-T + implosion ICF + fusion réelle. SANS NEURONES.
Méthode maison : particules + réactivité Bosch-Hale + burn Monte-Carlo + α-heating.

## Physique (v0.1)

- **Ions** : n macros (D bleu / T rouge), poids w=1e7, Maxwellienne initiale.
- **Implosion** : force centrale (rampe 10 ps) = pression d'ablation.
- **Répulsion** : Coulomb écranté Debye λ=0.1µm (stagnation au centre).
- **Fusion** : taux Bosch-Hale D-T réel (Nucl. Fusion 1992), tirage Poisson par cellule.
- **α-heating** : dépôt local × confinement (proxy ρR : (n/3e26)², plafonné 1).
- **Q** = E_neutrons / E_injectée (travail positif cumulé, jamais récupéré).

Limites v0.1 : pas de déplétion D/T, pas de transport α, pas de rayonnement.

## Lancer

```bash
pip install -e .
pytest tests/ -q            # 4 tests : Bosch-Hale, froid=0, implosion, burn
python3 fusion/run.py       # run standard (n=2000)
python3 demos/ignition.py   # run + scène Three.js -> demos/ignition_3d.html
```

## Résultat v0.1 (n=2000, 80 ps)

R 7.45→3.14µm (×2.4), T→17.7keV, 428 fusions, Q : 0 -> pic 136 -> 87 final.
`demos/ignition_3d.html` : ouvrir avec Chrome (CDN three.js).

## Licence

MIT.
