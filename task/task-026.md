# task-026 — Movimiento secundario (pelo/faldón/capa) e interpolación/blending de animaciones

**Estado:** pendiente
**Origen:** análisis del proyecto (2026-10-03).

## Contexto

El kit ya tiene IK (`rig.ik`, `render3d.ik_3d`, `ik_sagital`), pero:

- El **pelo rizado, el faldón y la capa son rígidos**: siguen al cuerpo sin inercia. Un salto o un giro
  brusco no se "arrastra" en esas partes.
- Las animaciones son **cuadros discretos medidos**; no hay interpolación ni mezcla entre ellas. Pasar
  de `quieto` a `correr` es un corte seco.

## Criterio de aceptación

- **Movimiento secundario**: pelo/faldón/capa con retardo tipo resorte respecto del movimiento del
  cuerpo (parámetro por estilo); determinista (sin aleatoriedad).
- **Blending**: transición `quieto → correr → quieto` que interpole poses (o cuadros) sin artefactos de
  píxel (sin colores ni píxeles fuera de la paleta del estilo).
- Feature detrás de flag; no debe romper la caché por (anim, dir, frame) ni el determinismo de la
  exportación (el PNG exportado sigue siendo el actual si el flag está apagado).

## Notas

- Probar en `stardew` primero (estilo activo y barato).
- Medir que no se dispara el costo por frame en el motor.
