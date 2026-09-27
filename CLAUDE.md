# Proyecto animaciones — generador de sprites para el juego

- Antes de crear o modificar cualquier animación o sprite, leer `CRITERIOS_ANIMACION.md`.
- Cada vez que me base en una animación existente (sprite sheet, video, referencia), analizarla
  píxel por píxel (proporciones, paleta, tiempos, trayectorias de articulaciones) y **anotar en
  `CRITERIOS_ANIMACION.md`** los criterios útiles y los errores corregidos.
- Ejecutar Python siempre desde la raíz del proyecto con `.venv/bin/python ...` (es el único
  comando con permiso automático).
- Al terminar una animación, abrirla con `xdg-open` para que el usuario la vea.
- La exportación es genérica (PNG + JSON + GIF): el motor del juego todavía no está definido.
- **Forma de trabajo:** mostrar algo rápido y pedir feedback en cada etapa (boceto antes de afinar); como máximo 2
  vueltas de corrección propias antes de consultar; estilos activos: stardew y lateral (volumen solo si se pide).
- **Tokens:** números antes que imágenes, un estilo por vez al iterar, tests del archivo tocado, ajuste fino largo → subagente.
  Para usar o extender la librería leer primero `sprites_lib/MAPA.md` (firmas, componentes, anclas) y abrir solo el
  archivo que haga falta; si cambia la API, regenerarlo con `.venv/bin/python -m sprites_lib.mapa`.
  `pytest` por defecto saltea los tests lentos (volumen); `-m ""` corre todos, solo al cerrar la rama.

## Kit de sprites
| Qué | Dónde |
|---|---|
| Skills | `.claude/skills/`: `sprite-personaje`, `sprite-referencia`, `sprite-analizar`, `sprite-estilo`, `sprite-2d-lateral`, `sprite-isometrico`, `pixel-art-video` |
| Librería común | `sprites_lib/`: `ciclos` (movimientos medidos), `rig` (IK), `pixel2d` (capas lateral), `render3d` (motor 3D: iso 8 direcciones o cenital 4), `estilos` (perfiles de look: volumen, stardew), `referencia` (cortar sheets), `analizar` (medir), `exportar` |
| Personajes | fichas en `personajes/fichas/*.yaml` → `personajes/generar.py` (boceto/validar/hoja/tests/aprobar); aprobados en `personajes/aprobados/`. `personajes/mago_*.py` = versión anterior sin ficha |
| Salida del juego | `salida/<personaje>/<anim>/` |
| Referencias descargadas | `referencias/` (y `sprites_x/`: Mega Man X separado en 14 animaciones) |
| Experimentos anteriores | `mago/`, `el_llamado/`, `prueba/` (no usar como base; la versión vigente está en `personajes/`) |

Un sprite = personaje (`personajes/`) + movimiento (`ciclos`) + estilo (`estilos`).
Personaje nuevo → skill `sprite-personaje` (entrevista → ficha → boceto → hoja + tests → aprobación → animaciones).
Flujo típico: referencia → analizar movimiento y/o estilo → personaje → revisar cuadros ampliados contra la referencia → exportar.
