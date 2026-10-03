# task-014 — Test automático del motor

**Estado:** pendiente
**Origen:** revisión del motor 3D→2D (2026-10-02).

## Problema

La única forma de verificar el motor es `motor/debug.py` (captura 6 frames a mano). No hay tests en
`tests/` para el motor, y `pytest` no lo cubre.

## Fix

Tests headless (SDL dummy) que verifiquen: el contrato `Estado`, la lógica (movimiento/salto/agachado
y transición de animación), el game loop (timestep fijo) y que el render devuelve una superficie no
vacía por dirección/animación.

## Criterio de aceptación

`.venv/bin/python -m pytest` incluye el motor y pasa sin display.
