# task-009 — Renderer del motor: reutilizar el kit real, no primitivas

**Estado:** completada (2026-10-02)
**Origen:** revisión del motor 3D→2D (2026-10-02).

## Problema

`motor/renderer.py` redibuja el personaje con primitivas (esfera + cápsulas) usando solo
`bob`/`mano`/`pie` de `ciclos.py`. No usa `ficha`/`armado`/`componentes`/`skins`, que es lo que
produce el personaje pixel-art del kit. Resultado: un "blob" chiquito (lo reportado por el usuario).

## Fix

Que el renderer arme el cuadro con el flujo real del kit (`armado.render_cuadro` o equivalente),
por personaje + animación + dirección + frame, y lo convierta a superficie de Pygame. Sin caché
todavía (eso es task-011).

## Criterio de aceptación

El frame renderizado se ve como el personaje del kit (mismo pixel art), no como primitivas.
