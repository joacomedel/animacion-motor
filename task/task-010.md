# task-010 — Movimiento visible: cámara y piso respecto del mundo

**Estado:** pendiente
**Origen:** revisión del motor 3D→2D (2026-10-02).

## Problema

En `main.py`/`renderer.py` el personaje se renderiza siempre centrado (`x,y = 0,0`) y el piso se
dibuja alrededor del personaje, así que se traslada con él. No hay referencia fija: el usuario
reportó "se mueve para cualquier lado" y "no se ve movimiento".

## Fix

Renderizar el personaje en su posición del mundo y mover la cámara (o dejar el piso fijo y mover
al personaje sobre él), para que moverse/saltar/agacharse se perciban.

## Criterio de aceptación

Al mover/saltar, el personaje cambia de posición respecto del piso; el salto se ve en `z`.
