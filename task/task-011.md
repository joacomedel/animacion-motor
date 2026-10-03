# task-011 — Caché de frames por (animación, dirección, frame) y medir FPS

**Estado:** completada (2026-10-02)
**Origen:** revisión del motor 3D→2D (2026-10-02).

## Problema

`renderer.py` recrea la `Escena` 3D y re-renderiza todo el cuadro en cada frame. Para el concepto
(3D→2D en vivo) la optimización clave es pre-renderizar cada combinación (animación, dirección,
frame) una vez y reusarla. El rendimiento era un requisito explícito del usuario.

## Fix

Caché de superficies por clave `(personaje, animación, dirección, frame)` (y por skin/estilo).
Mostrar FPS en pantalla o loguearlos.

## Criterio de aceptación

FPS medidos y estables (objetivo 60) y el render no recalcula frames ya cacheados.
