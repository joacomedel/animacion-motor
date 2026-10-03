# task-002 — Píxel oscuro que "popea" al caminar

**Estado:** pendiente
**Origen:** revisión humana de las 10 skins del experimento con modelos free (2026-10-02).

## Problema

Píxel oscuro que "popea" al caminar en `hechicera_hielo` (hacia adelante) y `fantasma_cian` (al sur).

La hechicera no tiene pintado propio (usa `desde_colores`), así que apunta a render/GIF (contorno o
transparencia) y no a la skin.

## Fix propuesto

Reproducir cuadro por cuadro con `sprites_lib.zonas` / `pulido` y aislar la causa.

## Criterio de aceptación

Sin píxel que aparezca/desaparezca en el recorrido del ciclo, por dirección.
