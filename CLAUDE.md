# Proyecto animaciones — generador de sprites para el juego

- Antes de crear o modificar cualquier animación o sprite, leer `CRITERIOS_ANIMACION.md`.
- Cada vez que me base en una animación existente (sprite sheet, video, referencia), analizarla
  píxel por píxel (proporciones, paleta, tiempos, trayectorias de articulaciones) y **anotar en
  `CRITERIOS_ANIMACION.md`** los criterios útiles y los errores corregidos.
- Ejecutar Python siempre desde la raíz del proyecto con `.venv/bin/python ...` (es el único
  comando con permiso automático).
- Al terminar una animación, abrirla con `xdg-open` para que el usuario la vea.
- La exportación es genérica (PNG + JSON + GIF): el motor del juego todavía no está definido.

## Kit de sprites
| Qué | Dónde |
|---|---|
| Skills | `.claude/skills/`: `sprite-referencia`, `sprite-analizar`, `sprite-estilo`, `sprite-2d-lateral`, `sprite-isometrico`, `pixel-art-video` |
| Librería común | `sprites_lib/`: `ciclos` (movimientos medidos), `rig` (IK), `pixel2d` (capas lateral), `render3d` (motor 3D: iso 8 direcciones o cenital 4), `estilos` (perfiles de look: volumen, stardew), `referencia` (cortar sheets), `analizar` (medir), `exportar` |
| Personajes (plantillas) | `personajes/mago_lateral.py`, `personajes/mago_iso.py`, `personajes/mago_stardew.py` → copiar para personajes nuevos |
| Salida del juego | `salida/<personaje>/<anim>/` |
| Referencias descargadas | `referencias/` (y `sprites_x/`: Mega Man X separado en 14 animaciones) |
| Experimentos anteriores | `mago/`, `el_llamado/`, `prueba/` (no usar como base; la versión vigente está en `personajes/`) |

Un sprite = personaje (`personajes/`) + movimiento (`ciclos`) + estilo (`estilos`).
Flujo típico: referencia → analizar movimiento y/o estilo → personaje → revisar cuadros ampliados contra la referencia → exportar.
