# task-019 — Guardar buffers de normal y material por frame (base de re-iluminación)

**Estado:** pendiente
**Origen:** análisis del proyecto (2026-10-03). Idea nueva surgida al revisar `render3d.py`.

## Contexto

`Escena.render` ya calcula, por píxel, el material (`mat`) y el término difuso `lam = N·luz`
(`render3d.py:243`), pero **descarta la normal**: `buffers=True` devuelve
`depth / mat / pieza / comp / solido`, no la dirección normal. `lam` se consume una sola vez para
elegir uno de los 3 tonos y se pierde.

Sin la normal por píxel, cualquier cambio de iluminación **exige re-renderizar la escena 3D**, lo que
choca con la caché por (anim, dir, frame) de task-011. Guardar el buffer de normal (y el de material,
que ya existe) es lo que habilita re-iluminar un frame ya renderizado.

## Criterio de aceptación

- `Escena.render(buffers=True)` (o una variante `buffers_completos`) devuelve además `normal`
  (RGB que codifica N en ejes de mundo) y `lam`, sin cambiar el PNG renderizado.
- Test en `tests/test_render3d.py`: donde `lam` es alto, la normal reconstruida apunta hacia la luz
  (dot > umbral); donde es bajo, apunta al lado opuesto.
- Documentar el formato (normal en [-1,1] → [0,255]; mismas dimensiones y alineación que el PNG).

## Notas

- Es la **base** de task-020 (luces puntuales), task-021 (key/fill/rim + AO) y task-024 (export de
  normal map): conviene hacerla primero.
- El buffer de material ya está; solo falta exponerlo de forma estable (id → nombre de material).
