# task-001 — Caballero carmesí: bloque rojo en la cabeza al caminar N

**Estado:** pendiente
**Origen:** revisión humana de las 10 skins del experimento con modelos free (2026-10-02).

## Problema

En `skins/caballero_carmesi.py` se pinta `cabeza` cols `[0, 1]` con `carmesi_o` creyendo que son
costados, pero en la zona `cabeza` la col 0/23 es la nuca; al mirar al N se ve rojo tapando la cabeza.

## Fix propuesto

Repintar la nuca con color de pelo (o mover el detalle fuera de las columnas traseras), verificar con
`skins.columnas_por_direccion("stardew")` y regenerar `salida/caballero_carmesi/caminar_lpc/`.

## Criterio de aceptación

Caminar hacia N sin rojo en la cabeza; tests del archivo tocado en verde.
