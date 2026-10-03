# task-016 — Pre-calentar la caché del renderer

**Estado:** completada (2026-10-02)
**Origen:** benchmark del renderer (2026-10-02).

## Problema

La caché de cuadros funciona (0.006 ms/frame con caché caliente), pero **cada combinación nueva
tarda ~13 ms** en generarse (3D → pixel art): 176 combinaciones (4 animaciones × 8 direcciones ×
cuadros) tardan ~2.4 s en total. En runtime, la primera vez que aparece cada combinación se produce
un hitch.

## Fix

Pre-calentar la caché al iniciar (todas las combinaciones que se van a usar) o generarlas en un
hilo/worker, para que ningún frame en vivo page el costo de render 3D.

## Criterio de aceptación

Medir que no hay hitches por frame (p. ej. tiempo por frame estable) al recorrer todas las
animaciones/direcciones por primera vez.
