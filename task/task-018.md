# task-018 — Aplicar `paleta_fija` en el motor en vivo y en los diagnósticos

**Estado:** pendiente
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
