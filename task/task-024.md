# task-024 — Exportar normal map + material map por animación (iluminar en la GPU del juego)

**Estado:** pendiente
**Origen:** análisis del proyecto (2026-10-03).

## Contexto

`exportar.py` genera PNG + JSON (frames/pivote/fps) + GIF, pero **no exporta información de superficie**.
Los motores 2D actuales (Godot 4 con `Light2D`, Unity URP 2D) iluminan sprites en la **GPU** usando un
**normal map** alineado con el sprite: luces dinámicas, muchas a la vez, sin costo por CPU. Hoy, como el
JSON no trae normal/material, esa iluminación no es posible en el juego.

El kit ya calcula la normal y el material por píxel; exportarlos es casi gratis una vez hecha task-019.

## Criterio de aceptación

- Por animación, además de la tira PNG, exportar `<nombre>_normal.png` y `<nombre>_material.png`
  **alineados** (mismas celdas, mismo pivote) que el JSON referencie.
- El normal map codifica N en RGB ([−1,1] → [0,255]); el material map usa un id por material y el JSON
  incluye el mapa `id → nombre de material`.
- Test: el normal map de un frame coincide en tamaño con el sprite; píxeles con `lam` alto dan normal
  hacia la luz.
- Documentar en `docs/` el formato para el motor del juego.

## Depende de

- task-019 (buffer de normal por frame).

## Notas

- Mantener retrocompatibilidad: el JSON actual debe seguir siendo válido; los mapas son campos extra.
- El material map habilita también máscaras de emisivo/transparencia del lado del motor.
