# task-027 — Colisiones con tiles y depth-sorting en el mundo

**Estado:** pendiente
**Origen:** análisis del proyecto (2026-10-03).

## Contexto

`motor/mundo.py` tiene tipos `PISO/MURO/ARBOL` y expone `tile_en(tx, ty)`, pero **el motor no lo usa**:
`motor/main.py` mueve al personaje libremente (solo clampea a los bordes del mapa) y lo blitea **siempre
encima** de la superficie del mundo. Resultado: el personaje **atraviesa muros y árboles** y, con
árboles, no puede pasar "por detrás".

## Criterio de aceptación

- **Colisión**: el personaje no puede ocupar tiles `MURO` (usar el punto de los pies + un radio chico,
  no la celda entera). `ARBOL` no bloquea.
- **Depth-sorting**: los árboles y el personaje se dibujan ordenados por su Y del mundo, así el
  personaje pasa por delante o por detrás según su posición.
- Test en `tests/test_mundo.py` (colisión: no se entra al muro; el borde sigue bloqueando) y en
  `tests/test_motor.py` (orden de dibujo por Y).

## Notas

- `motor/main.py` estaba con cambios sin commitear al escribir esta task: coordinar antes de tocarlo.
- El mundo es de 80×50 tiles; conviene verificar el costo de reemplazar el blit único por un blit
  ordenado solo de los tiles visibles.
