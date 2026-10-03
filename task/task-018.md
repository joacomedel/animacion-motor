# task-018 — Aplicar `paleta_fija` en el motor en vivo y en los diagnósticos

**Estado:** completada (2026-10-03)
**Origen:** hallazgo al implementar task-017 (2026-10-03).

## Contexto

Task-017 aplica `render.paleta_fija` solo en el camino de exportación (`skins.ajustar_a_paleta_fija`,
usado por `skins._por_dir_ficha` y `proceso_skin._por_dir_quieto`). Pero el **motor en vivo** dibuja con
`armado.render_cuadro` directo (`motor/renderer.py:181`), así que el sprite que se ve en pantalla **no**
cae en la paleta fija: el juego y las skins exportadas no coinciden en color.

Lo mismo pasa con diagnósticos que renderizan imágenes sin pasar por la exportación: `gates.py`,
`zonas.py`, `proceso_estilo.py`, `proceso_anim.py`, `muneco.py` (boceto/hoja de modelo),
`comparar_plantilla.py`.

## Opciones

1. Aplicar `ajustar_paleta` en el llenado de la caché del motor (`motor/renderer.py`), por combinación
   (anim, dir, frame) — el mapeo a lista fija es por píxel, así que no depende del agrupamiento.
2. Centralizar en `armado.render_cuadro` (o en un wrapper `render_cuadro_final`) para que *todo* consumidor
   salga con la paleta del estilo; los diagnósticos que necesiten los tonos crudos usan una variante.
   Es la opción más consistente, pero cambia el boceto/hoja de modelo y las mediciones de `zonas`.

## Criterio de aceptación

- El sprite del motor usa exactamente los mismos colores que la skin exportada del mismo estilo.
- Decisión documentada sobre si `render_cuadro` aplica la paleta por defecto o no.

## Nota

`motor/renderer.py`, `motor/main.py` y `motor/debug.py` estaban con cambios sin commitear al crear esta
tarea: coordinar antes de tocarlos.

## Resolución (2026-10-03)

Se eligió la **opción 1** (snap en el motor), para no alterar bocetos/hoja de modelo/mediciones de `zonas`:
`armado.render_cuadro` sigue devolviendo los tonos crudos y gana un parámetro `luces=None` para inyectar el
modelo de luces del motor sin mutar `ESTILOS`.

Regla del motor: **todo lo que se ve cae en la paleta fija del estilo**.

- `Renderer._superficie` snapea cada cuadro a `render.paleta_fija` (una vez, al llenar la caché).
- `Renderer.iluminar` snapea **solo los píxeles que la luz toca** (los de afuera del radio quedan intactos).
- `Renderer.ambientar` reemplaza el tinte plano de pantalla (task-013) por un **remapeo dentro de la paleta**:
  apaga cada color (factor) y lo corre un poco hacia el tono del ambiente, y lo vuelve a snappear. Se cachea
  por (superficie, ambiente), así el piso y el sprite no se reprocesan por frame.
- `snap_rgb` (en `sprites_lib/paleta.py`) es el snap por píxel sobre arrays/superficies; `ajustar_paleta`
  (PIL) sigue usándose en el camino de exportación.

Tests: `tests/test_motor_paleta.py` (sprite, luz dinámica, ambiente, luces, bloom, overrides).
