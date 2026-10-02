# Tareas pendientes

Origen: revisión humana de las 10 skins del experimento con modelos free (2026-10-02).
Los criterios de generación quedaron anotados en `CRITERIOS_ANIMACION.md` (§ generación de skins por un LLM).

## Bugs

- [ ] **Caballero carmesí — bloque rojo en la cabeza al caminar N** (`skins/caballero_carmesi.py`).
      Pinta `cabeza` cols `[0, 1]` con `carmesi_o` creyendo que son costados, pero en la zona `cabeza`
      la col 0/23 es la nuca; al mirar al N se ve rojo tapando la cabeza.
      Fix: repintar la nuca con color de pelo (o mover el detalle fuera de las columnas traseras),
      verificar con `skins.columnas_por_direccion("stardew")` y regenerar
      `salida/caballero_carmesi/caminar_lpc/`.
- [ ] **Píxel oscuro que "popea" al caminar** en `hechicera_hielo` (hacia adelante) y `fantasma_cian` (al sur).
      La hechicera no tiene pintado propio (usa `desde_colores`), así que apunta a render/GIF (contorno o
      transparencia) y no a la skin. Reproducir cuadro por cuadro con `sprites_lib.zonas` / `pulido` y aislar.
- [ ] **Robot oxidado — detalle revertido** (`skins/robot_oxidado.py`). El intento de óxido rompía la
      costura (`[('cabeza', 1)]`) y quedó la base sin detalle. Repintar simétrico y regenerar.
- [ ] **`skins/pescador.py` — comentario corrupto** (línea 133: `一年内 горутина de la bota`). Limpiar.

## Menores / housekeeping

- [ ] `salida/_review/` son copias temporales para la review (y `salida/` ya está en `.gitignore`):
      decidir si se borran o se dejan.
- [ ] Subagentes cancelados: `space-bunny` (1ª corrida del pescador) y `nemotron` (2 intentos del
      explorador) devolvieron "Subagent cancelled" aunque el trabajo quedó hecho. Ver si es del harness.
- [ ] Revisar los scripts de los 5 que quedaron en `desde_colores` si se los quiere subir de nivel con el
      checklist de `CRITERIOS_ANIMACION.md` (aldeano, caballero, vampira, pescador y fantasma ya tienen detalle).
