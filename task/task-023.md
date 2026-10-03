# task-023 — Bloom/halo para materiales emisivos (antorcha, runas, visor)

**Estado:** pendiente
**Origen:** análisis del proyecto (2026-10-03).

## Contexto

Los materiales emisivos (`fuego`, runas, visor del robot, `arma_brillo` en `skins.py`) hoy **solo se
aclaran**: `tonos(..., emisivo=True)` no los oscurece y la luz es un tono más claro. A 16-32 px, sin un
**halo** que se derrame, un emisivo no se lee como "brilla": se lee como un color claro más.

## Criterio de aceptación

- Post-proceso barato que, a partir de los píxeles marcados como emisivos en el buffer de material,
  expande un **halo** de 1-2 px (mezcla aditiva del color emisivo sobre los vecinos).
- El halo **no sangra el contorno** exterior del sprite ni tiñe material no emisivo más allá del radio.
- Aplicable tanto en la exportación (PNG/GIF) como en el motor en vivo.
- Test: un sprite con un material emisivo gana píxeles de halo alrededor; sin emisivos, no cambia.

## Notas

- Usa el buffer de material (ya existe) para ubicar los emisivos; no requiere la normal.
- Mantener determinismo: sin aleatoriedad.
