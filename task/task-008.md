# task-008 — Reparar layout git: el kit quedó movido dentro de `referencias/`

**Estado:** completada (2026-10-02)
**Origen:** revisión del motor 3D→2D (2026-10-02).

## Problema

Al "limpiar" la raíz para el motor, `sprites_lib/`, `personajes/`, `skins/`, `tests/`, `docs/`,
`output/`, `visor/`, `sprites_x/`, `aprobados/` y `.claude/` se movieron dentro de `referencias/`,
que está en `.gitignore`. Git ve 188 archivos borrados y `motor/` sin trackear; el `renderer.py`
funciona solo por un `sys.path.insert(..., "referencias")`.

## Fix

Restaurar el kit en la raíz desde HEAD, mover los duplicados de `referencias/` a un backup
(no borrar), quitar el `sys.path` hack del renderer, agregar `debug_frame_*.png` al `.gitignore`
y commitear en la rama `motor-3d-tiempo-real` (nunca en `main`).

## Criterio de aceptación

`git status` limpio salvo lo intencional; `.venv/bin/python -m motor.debug` corre sin el path hack.
