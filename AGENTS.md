# Proyecto animaciones — generador de sprites para el juego

Guía para trabajar en este repo con OpenCode. Reemplaza a `CLAUDE.md` como guía activa (OpenCode V2 solo lee `AGENTS.md`; `CLAUDE.md` queda como referencia de Claude Code).

## Reglas

- Antes de crear o modificar cualquier animación o sprite, leer `CRITERIOS_ANIMACION.md`.
- Cada vez que se use una animación existente como base (sprite sheet, video, referencia), analizarla píxel por
  píxel (proporciones, paleta, tiempos, trayectorias de articulaciones) y **anotar en `CRITERIOS_ANIMACION.md`**
  los criterios útiles y los errores corregidos.
- Ejecutar Python siempre desde la raíz del proyecto con `.venv/bin/python ...`.
- **Mostrar los PNG generados:** cada vez que generes un PNG/GIF nuevo (skin, hoja, render, guía, recorte), mostrarlo
  en el chat (incluir la imagen en la respuesta) además de abrirlo con `xdg-open`; la ventana puede abrirse del lado
  del servidor y no verse.
- La exportación es genérica (PNG + JSON + GIF): el motor del juego todavía no está definido.
- **Forma de trabajo:** mostrar algo rápido y pedir feedback en cada etapa (boceto antes de afinar); como máximo 2
  vueltas de corrección propias antes de consultar; estilos activos: `stardew` y `lateral` (volumen solo si se pide).
- **Tokens:** números antes que imágenes; un estilo por vez al iterar; correr los tests del archivo tocado;
  ajuste fino largo → subagente.
- Para usar o extender la librería, leer primero `sprites_lib/MAPA.md` (firmas, componentes, anclas) y abrir solo
  el archivo necesario; si cambia la API, regenerarlo con `.venv/bin/python -m sprites_lib.mapa`.
- `pytest` por defecto saltea los tests lentos (volumen); `-m ""` corre todos, solo al cerrar la rama.
- En los procesos de `docs/procesos/`: tope 3 vueltas propias; si no converge, consultar con el estado y las
  opciones. Nunca subir un umbral "para que dé verde" sin mirar qué era.

## Flujos

- **Animación**: referencia (sprite sheet / video) → skill `sprite-referencia` (descargar y separar) → skill
  `sprite-analizar` (medir movimiento píxel por píxel) → animación con ciclos → skill `sprite-revisar` (revisión
  por números con zonas + pulido) → exportar (PNG + JSON + GIF) → `xdg-open`.
- **Personaje nuevo**: skill `sprite-personaje` — entrevista → ficha YAML (`validar`) → boceto → hoja de modelo +
  tests → aprobación (congela fotos de control) → recién después animaciones.
- **Procesos con gates** (`docs/procesos/`): `proceso_estilo` → `proceso_anim` → `proceso_skin` (y `lote` exporta
  al juego). Aprobar es el único paso humano; los artefactos quedan congelados en `aprobados/`.
- Un sprite = **personaje** (`personajes/`) + **movimiento** (`sprites_lib/ciclos.py`) + **estilo**
  (`sprites_lib/estilos.py`). Las tres capas son intercambiables.

## Kit de sprites

| Qué | Dónde |
|---|---|
| Skills | `.claude/skills/`: `sprite-personaje`, `sprite-referencia`, `sprite-analizar`, `sprite-estilo`, `sprite-2d-lateral`, `sprite-isometrico`, `sprite-revisar`, `pixel-art-video` (OpenCode las descubre desde ahí; cargar con la herramienta `skill`) |
| Librería común | `sprites_lib/`: `ciclos` (movimientos medidos), `rig` (IK), `pixel2d` (capas lateral), `render3d` (motor 3D: iso 8 direcciones o cenital 4), `estilos` (perfiles de look), `referencia` (cortar sheets), `analizar` (medir), `exportar` |
| Personajes | fichas en `personajes/fichas/*.yaml` → `personajes/generar.py` (`boceto`/`validar`/`hoja`/`tests`/`aprobar`); aprobados en `personajes/aprobados/` |
| Procesos | `.venv/bin/python -m sprites_lib.proceso_estilo` / `proceso_anim` / `proceso_skin` (pasos y gates en `docs/procesos/`); congelan en `aprobados/estilos/`, `aprobados/animaciones/` y `aprobados/skins/` |
| Salidas | `salida/<personaje>/<estilo>/<anim>/` (trabajo; `<estilo>` = `stardew` 4 dir o `stardew8` 8 dir); el lote de skins exporta la entrega del juego a `output/<nombre>/<estilo>/<anim>/`. Diagnósticos (zonas, vistas previas, review) en `docs/diagnostico/` |
| Referencias descargadas | `referencias/` (y `sprites_x/`: Mega Man X separado en 14 animaciones) |
| Archivo v1 | contenido anterior (skins, fichas, `mago/`, `el_llamado/`, `prueba/`) fuera de este repo, en `/home/jm/claude-code/archivo-animaciones-v1/` |

## Subagentes

- Delegación según la naturaleza de la tarea (regla global): mecánica acotada (pintar skins, variantes, un fix)
  → modelo barato; integración/depuración (revisar sprites, medir plantillas nuevas) → modelo estándar; diseño
  del motor y revisión final de rama → sesión principal (modelo más capaz).
- Las **imágenes no deben entrar al contexto principal** para *revisiones*: la revisión visual va a un subagente que
  mira una vez y devuelve un veredicto corto (≤ 10 líneas). Excepción: los PNG recién generados se muestran al usuario
  en el chat (regla "Mostrar los PNG generados").
- Tareas de 1-2 comandos (correr tests, generar una demo) hacerlas directo: delegar cuesta más.
- No cambiar de modelo a mitad de sesión (rompe la caché); hacer compactación antes de una pausa larga.
- Hay prompts de subagente listos en `.claude/agents/` (`pintor-skins`, `revisor-sprites`, `medidor-animaciones`);
  en OpenCode no se carga esa carpeta: van en `.opencode/agents/<nombre>.md` si se quieren usar como subagentes.
