# task-015 — Piso isométrico: verificar escala/posición

**Estado:** completada (2026-10-02)
**Origen:** revisión del motor 3D→2D (2026-10-02).

## Problema

`_agregar_piso` dibuja tiles con `escena.caja((dx*16, dy*16, -1), (8,8,1), ...)` para `dx,dy` de
-3 a 3. Hay que verificar que el tamaño/paso coincida con la cámara y que el piso quede quieto
cuando el personaje se mueve (se cruza con task-010).

## Criterio de aceptación

Piso continuo, a escala, fijo respecto del mundo; el personaje se mueve sobre él.
