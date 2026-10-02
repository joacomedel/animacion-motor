# Auditoría funcional — kit de sprites "animaciones"

- **Fecha:** 2026-10-01
- **Alcance:** los 45 archivos `.py` del proyecto (~13.000 líneas, sin `.venv`/`__pycache__`): motor de render, datos, procesos, verificación, tests, scripts de ejemplo y el motor de video.
- **Estado del repo auditado:** commit `7054035` + trabajo sin commitear (`sprites_lib/*` modificados, `personajes/fichas/aldeano.yaml` sin trackear).
- **Método:** 7 auditores en paralelo (solo lectura) + verificación puntual con `grep`/`sed` + corrida end-to-end del CLI con `aldeano`. No se modificó código; los comandos corrieron solo sobre `salida/` (ignorado por git).
- **Lo que NO cubre:** no se corrieron los procesos de aprobación completos (estilo/anim/skin), no se revisó el contenido de imágenes/YAML de datos, ni `docs/` más allá de la coherencia con el código.
- **Marcas de verificación:** ✓ = verificado en esta auditoría (comando o lectura directa); el resto sale de la auditoría de código y se cita `archivo:línea`.

---

## 1. La idea del proyecto

Generador **procedimental** de sprites pixel art para un juego que todavía no existe: los sprites no se dibujan a mano, se construye un **muñeco 3D de primitivas** (esferas, elipsoides, cápsulas, cajas redondeadas, faldones) y se "fotografía" a resolución pixel art con z-buffer, 3 tonos por material y contorno por pieza (`render3d.py`).

Un sprite = **personaje** (`personajes/fichas/*.yaml`) + **movimiento** (`ciclos.py`) + **estilo** (`estilos.py`); las tres capas son intercambiables. La tesis central es la confiabilidad: las lecciones viven en código, tests y `CRITERIOS_ANIMACION.md`, no en la memoria del modelo. La exportación es genérica (PNG + JSON estilo Aseprite/TexturePacker + GIF) porque el motor del juego está sin definir.

---

## 2. Cómo interactúa el usuario

El humano **no corre comandos a mano**: habla con el agente de OpenCode (skills `sprite-personaje`, `sprite-referencia`, `sprite-analizar`, `sprite-estilo`, `sprite-revisar`, `sprite-2d-lateral`, `sprite-isometrico`) y el agente ejecuta el pipeline con `.venv/bin/python -m ...` desde la raíz. El único paso humano es **aprobar**.

### 2.1 El circuito

```
referencia → [sprite-referencia: separar sheet] → [sprite-analizar: medir]
→ [sprite-personaje: entrevista → ficha YAML → boceto → hoja + tests] → OK del usuario
→ animaciones → [proceso_anim smoke/validar: gates por números] → aprobar
→ proceso_skin (pintar PNG 32×32 → smoke → aprobar) → lote → ENTREGA al juego
```

### 2.2 Comandos disponibles (todos desde la raíz)

| Comando | Para qué |
|---|---|
| `personajes.generar boceto\|validar\|hoja\|tests\|aprobar <nombre>` | Ciclo de vida del personaje (exit 0/1/2) |
| `sprites_lib.proceso_estilo medir\|validar\|aprobar <estilo>` | Alta/ajuste de estilo con gate |
| `sprites_lib.proceso_anim smoke\|validar\|aprobar <anim> --estilo E` | Alta/ajuste de animación con gate |
| `sprites_lib.proceso_skin smoke\|aprobar\|lote <nombre>` | Skins y publicación al juego |
| `sprites_lib.zonas` / `sprites_lib.pulido` | Revisión por números de una animación |
| `sprites_lib.skins guia\|demo\|juego` / `sprites_lib.muneco demo\|ancho\|zonas` | Herramientas de skin/muñeco |
| `sprites_lib.referencia paneles\|detectar\|cortar` / `analizar` / `comparar_estilo` / `comparar_plantilla` / `lado_a_lado` / `mapa` | Referencias, comparaciones, índice |
| `main(mv)` de cada película pixel-art-video: `preview\|stills\|render\|gif\|wav` | Videos pixel art (motor aparte) |
| `sprites_x/detectar.py`, `sprites_x/exportar.py` | Scripts de ejemplo (Mega Man X), nivel módulo |

---

## 3. Qué genera (artefactos)

El kit no emite scripts: emite **imágenes y datos**. Los únicos `.py` escritos a mano dentro del flujo son `skins/pintar_<nombre>.py` (por patrón) y las fichas YAML.

| Etapa | Artefactos |
|---|---|
| Boceto / hoja | `salida/<nombre>/boceto.png`; `salida/<nombre>/<estilo>/`: `hoja_modelo.png`, `informe.md`, `quieto.png/.json/.gif`, `quieto_<dir>.gif`, `_estilo.png`, `diferencias/*.png` |
| Aprobación personaje | `personajes/aprobados/<nombre>/<estilo>/*.png` (fotos de control) |
| Aprobaciones de procesos | `aprobados/estilos/<E>/{control.png,metricas.json,estado.json}`; `aprobados/animaciones/<A>/<E>/{cuadros,metricas.json,estado.json}`; `aprobados/skins/<S>/{hoja,smoke.gif,metricas.json,estado.json}` |
| Revisión | `salida/zonas/<E>/<anim>.json/.md` (+ `_pulido`), `salida/zonas/lote_<S>.md` |
| Entrega al juego | `output/<skin>/<anim>/`: PNG + JSON + GIF (+ subcarpeta `cuadros/`) |
| Referencias | `boxes.json` + `hoja_numerada.png` (separar); `medidas.json` + `grilla_XX.png` (medir); `comparacion.png` (plantilla) |
| Videos | `<name>.mp4` / `.gif` / `_preview.png` / `_stills.png` / `.wav` |

---

## 4. Revisión archivo por archivo

### 4.1 Motor de render (`sprites_lib/`)

| Archivo | Rol | Interacción | Estado / notas |
|---|---|---|---|
| `render3d.py` (348) | Cámaras iso/cenital/lateral; `Escena` con z-buffer, 3 tonos, contornos, buffers | Interno | Sólido. Muerto: `ik_sagital` (:303), `sombra` (:326), `piso_iso` (:335) |
| `cuerpo.py` (245) | `anatomia()`/`posar()`: anclas 3D, IK 3D, trampas de cara/cabeza | Interno | Coherente. Los `18`/`34` de :204 sin documentar |
| `rig.py` (18) | IK de 2 huesos 2D | Interno | Queda huérfano: solo lo usa `ik_sagital`, sin llamadores |
| `componentes/__init__.py` (68) | Registro de componentes + `Contexto` + helpers | Interno | `estilos` por defecto (:14) omite `fry8`/`lpc` |
| `componentes/humano.py` (290) | Cuerpo base: cabeza/pelo/ojos/torso/brazos/piernas | Interno | Bug potencial: cresta usa `"pelo"`/`"pelo_b"` literales (:84) sin que la validación lo exija ✓ |
| `componentes/mago.py` (162) | Rastas, vincha, pulsera, runas, túnica, botas | Interno | Coherente |
| `componentes/robot.py` (187) | Prótesis, muñón con cables, visor, placa, cables de nuca | Interno | Params declarados y nunca leídos: `termina_en`, `pie` |
| `componentes/ropa.py` (143) | Remera rota, camisa, cinturón | Interno | Determinista (`default_rng(7)`) |
| `componentes/skin.py` (92) | Cuerpo base pintado desde PNG 32×32 | Interno | Bug potencial: `material(sk.color(*CARA))` (:35,:56) puede no existir en la paleta |
| `pixel2d.py` (59) | Utilidades 2D planas (tipo Mega Man) | — | **Código muerto**: sin importadores ni tests |
| `paleta.py` (77) | Tonos por estilo, `_b`/`mano`, emisivos, reducir paleta en Lab | Interno | Correcto |

### 4.2 Datos, armado y CLI de personaje

| Archivo | Rol | Interacción | Estado / notas |
|---|---|---|---|
| `personajes/generar.py` (139) | CLI principal: `boceto/validar/hoja/tests/aprobar` | **CLI** | `boceto` siempre exit 0 (:74-76); `tests` escribe en disco; `estilos:` de la ficha se ignora ✓ |
| `ficha.py` (179) | Carga/valida YAML con sugerencias de error | Interno | Exige `base=="humano"`; `base:skin` de `armado` queda inalcanzable |
| `armado.py` (115) | Ficha → `Cuadro` (imagen + buffers + anclas en px) | Interno | Coherente; `BASE_SKIN` sin camino desde YAML |
| `escala.py` (48) | Clases de altura, `celda`, `alto_objetivo_px` | Interno | Correcto |
| `ciclos.py` (131) | Movimientos medidos en rig lateral (CORRER, QUIETO, CAMINAR…) | Datos | `CORRER`/`CAMINAR` fuera de `POSES` (poses.py:13) |
| `poses.py` (48) | Registro `POSES` + metadatos (`cuadros/fps/loop/offset_y/ancho`) | Interno | Correcto |
| `estilos.py` (215) | Perfiles de look + `crear_camara`; `ACTIVOS=["stardew","lateral"]` | Interno | `stardew8` hereda el dict `referencia` de `stardew` (:146) ✓ |
| `proporciones.py` (97) | Contrato numérico del muñeco vs perfil | Gate | Hardcodea `pierna_humana@…` para la máscara |
| `hoja_modelo.py` (89) | Compone `hoja_modelo.png` (guías, paleta, tests) | Vía CLI | `ZOOM` sin `stardew8`/`fry8` |
| `tests_personaje.py` (516) | 10 reglas de consistencia + `informe_md` | Vía CLI | `FRENTE` sin `stardew8` (:33) → `t_simetria` omitido ✓ |
| `mapa.py` (67) + `MAPA.md` | Índice autogenerado por AST | **CLI** | `MODULOS` es manual: un módulo nuevo no entra y el test igual pasa |

### 4.3 Procesos y publicación

| Archivo | Rol | Interacción | Estado / notas |
|---|---|---|---|
| `proceso_estilo.py` (272) | `medir/validar/aprobar`: gate + congelado + doc propuesto | **CLI** | `check_referencia` nunca corre: sin `referencia.especimen` en ningún estilo ✓ |
| `proceso_anim.py` (249) | `smoke/validar/aprobar`: gate + congelado + export fuente | **CLI** | Doble análisis de pulido en `aprobar`; smoke funciona desde cualquier cwd |
| `proceso_skin.py` (281) | `smoke/aprobar/lote`: skin → entrega al juego | **CLI** | Exit 1 (vs 2 de anim) para skin inválida; CLI duplicada con proceso_anim |
| `gates.py` (134) | Checks comunes (determinismo, deriva, zonas, pulido) + veredicto | Interno | `omitido` cuenta como verde (:27); pulido solo bloquea sev MAL (:130-132) |
| `estado.py` (74) | Hash de fuentes + deriva + listado | Interno | `aprobado_por` hardcodeado a `"usuario"` |
| `fotos_control.py` (64) | Congela/compara cuadros (pixel-diff) | Interno | No borra PNG viejos si baja `n` |
| `skins.py` (321) | Skin 32×32 → ficha/render/export; guía y plantillas | **CLI** | `BRAZO_ACTIVO = {}` muerto (:188) |
| `muneco.py` (93) | Muñeco sin skin: demo/ancho/zonas | **CLI** | `ancho_necesario` con expresión no-op: `2*m + (2*m)%2` (:47) ✓ |

### 4.4 Verificación por números y referencias

| Archivo | Rol | Interacción | Estado / notas |
|---|---|---|---|
| `zonas.py` (1246) | Clasifica cada píxel por zona (buffers del render) + alertas + falsas conocidas | **CLI** | Enfoque sólido; whitelist de falsas muy ancha (:582-590); `sin_zona` sev 1 (:605-620) |
| `pulido.py` (1214) | Movimiento / limpieza / espejo sobre la imagen real | **CLI** | Solo mide ciclos de paso (:161-163); espejo duplicado por par (:893); `sep_ojos` no escala |
| `comparar_estilo.py` (229) | 11 métricas de look vs referencia + veredicto | **CLI** | Docstring documenta 8; revienta con celda vacía |
| `comparar_plantilla.py` (125) | Ciclo vs referencia LPC: IoU + error de huesos ≤2 px | **CLI** | Rutas hardcodeadas a `referencias/` (gitignored) |
| `referencia.py` (157) | `paneles/detectar/cortar` sheets | **CLI** | `cortar` no puede procesar el `boxes.json` de `sprites_x` ✓ (faltan claves `sheet`/`fondo`) |
| `analizar.py` (78) | Mide tiras: paleta, bbox, rebote → `medidas.json` + grillas | **CLI** | Revienta con celdas vacías (:33-35) |
| `exportar.py` (99) | PNG + JSON (rects/meta/pivot/animations) + GIF + revisión | Librería | **La entrega final no tiene test directo** ✓ |
| `lado_a_lado.py` (46) | Imágenes intercaladas ×14 para ojear | **CLI** | Simple y correcto |

### 4.5 Tests (`tests/`, 24 archivos + `apoyo.py`, ~2.000 líneas)

| Garantizan | Archivos |
|---|---|
| Fichas y validación | `test_ficha.py` (contamina `REGISTRO` al importar), `test_generar.py` (acepta exit 1 en :40 ✓) |
| Motor y esqueleto | `test_render3d.py`, `test_armado.py`, `test_cuerpo_poses.py`, `test_esqueleto.py`, `test_componentes_heroe.py`, `test_componentes_robot.py` |
| Escala y paleta | `test_escala_paleta.py` (valores dorados), `test_proporciones.py` |
| Verificación | `test_zonas.py`, `test_pulido.py` (detectores sintéticos), `test_tests_personaje.py`, `test_comparar_plantilla.py` (skip sin `referencias/`) |
| Procesos y estado | `test_proceso_estilo.py`, `test_proceso_anim.py`, `test_proceso_skin.py`, `test_gates.py`, `test_estado.py`, `test_deriva.py` |
| Regresión / juego | `test_animaciones_juego.py`, `test_determinismo.py` (solo `FICHA_MINIMA`/`quieto`), `test_skins.py`, `test_mapa.py` |

Huecos: export sin test; `sprites_x/` sin cobertura; determinismo débil; gates que pasan por omisión; fotos de control acotadas a stardew/neutra.

### 4.6 Scripts de ejemplo (`sprites_x/`)

- `detectar.py` (95): separa el panel "Helmet (X1)" del sheet real y propone cajas → `boxes.json` + `hoja_numerada.png`. Corre todo al importar (sin `__main__` guard); imprime "9 filas; 91 sprites".
- `exportar.py` (82): etiqueta a mano 14 animaciones, quita el fondo azul, alinea por pies → `animaciones/<nombre>.png/.gif` + `indice.png`.
- **No reproducibles con el CLI actual**: el `boxes.json` versionado solo tiene `panel`/`rows` y `referencia.cortar` pide `sheet`/`fondo` ✓. Es el ejemplo canónico en la doc, pero salió del flujo legacy.

### 4.7 Motor de video (`pixel-art-video/`)

- `scripts/pixelvid.py` (1603, autónomo): canvas + paletas, sprites ASCII, `humanoid`, clima/scroll/texto con cirílico, escenas como función pura del tiempo, `stills` con tiempos rotulados, MP4 vía `imageio_ffmpeg` y **chiptune sintetizada** (`Song`, osciladores, sfx, ambience).
- Ejemplos: `lighthouse.py`, `star_cat.py`, `super_pixel.py` (plataformero con cámara y HUD) y `template.py` (plantilla real; su ruta por defecto es `~/.claude/skills/...`, no la del repo ✓).
- **Cumple su promesa** (videos pixel art deterministas + música + revisión por stop-frames). Detalles: `from_ascii` con error críptico, WAV temporal no se borra, `Image.fromarray(..., "RGBA")` deprecado, `hrand` atado a `hash()` de CPython.

---

## 5. Flujos punta a punta

1. **Animación:** referencia → `referencia detectar/cortar` → `analizar` → ciclo en `ciclos.py`/`poses.py` → `proceso_anim smoke` → `validar` (zonas + pulido + determinismo + deriva + plantilla + fotos) → `aprobar` → export a `salida/animaciones/`.
2. **Estilo:** 2+ referencias → `proceso_estilo medir` (calibrar con control) → volcar perfil a `estilos.py`/`escala.py` → `validar` → `aprobar` → `aprobados/estilos/<E>/`.
3. **Skin:** pintar `skins/<nombre>.png` → `proceso_skin smoke` → `aprobar` → `lote` sobre las animaciones aprobadas → `output/<skin>/<anim>/`.
4. **Personaje:** ficha YAML → `validar` → `boceto` → `hoja` (tests + informe) → `aprobar` → animaciones.

---

## 6. Evidencia de la prueba end-to-end (✓)

```
$ .venv/bin/python -m personajes.generar validar aldeano
ficha 'aldeano' válida para: stardew, lateral          # ← ignora estilos:[stardew8] de la ficha
exit=0

$ .venv/bin/python -m personajes.generar boceto aldeano
boceto (stardew: S, E, W) → salida/aldeano/boceto.png
  OK tamaño y pivote / OK recorte
exit=0

$ .venv/bin/python -m personajes.generar hoja aldeano --estilo stardew8
hoja → salida/aldeano/stardew8/hoja_modelo.png
[stardew8] CON FALLAS: 6 ok, 1 fallas, 4 omitidos
   ✗ estilo vs referencia: degrade_R2 0.28 vs 0.12 · bandas 20.59 vs 35.90
exit=1
```

```
$ .venv/bin/python -m pytest -q
211 passed, 4 deselected in 25.09s
```

---

## 7. Veredicto: ¿cumple la utilidad principal?

**Sí, y es demostrable.** El motor renderiza (muñeco 3D → pixel art con z-buffer), las tres capas son intercambiables, los procesos congelan y exportan con orden coherente (estado último = marca del congelado), la revisión por números es un enfoque genuinamente original y el circuito referencia→medición→comparación→entrega está cableado. La suite pasa completa y el CLI funciona de punta a punta.

**Con cuatro costuras serias:**

1. **El gate de estilo no compara contra la referencia, aunque la doc diga que sí** (:  `referencia.especimen` no está declarado en ningún estilo → `check_referencia` siempre "omitido").
2. **`stardew8` está roto en el camino real**: la ficha declara `estilos:[stardew8]`, el CLI usa `ACTIVOS=[stardew, lateral]`, y forzando el estilo el gate falla contra la referencia de `stardew` (4 direcciones). El personaje en curso no puede aprobarse en su propio estilo.
3. **Los gates son más laxos de lo que aparentan**: whitelist de falsas muy ancha, `REVISAR` no bloquea, `otro/sin_zona` no bloquea, y "omitido" cuenta como verde — con referencias fuera de git, hay caminos que dan VERDE sin haber comparado nada.
4. **La entrega al motor no está testeada**: `exportar.py` no tiene un solo test; el contrato JSON (frames/meta/pivot/animations) queda sin garantía formal.

---

## 8. Hallazgos consolidados

### 8.1 Bloqueantes (con evidencia)

1. **Gate de estilo sin referencia** — ✓ `especimen` solo aparece en `proceso_estilo.py`; ningún estilo lo declara. Se puede aprobar un estilo con `calibrada=True` sin medir nada; `docs/procesos/estilo.md:17-19` promete lo contrario.
2. **`stardew8` inconsistente** — ✓ `ACTIVOS` excluye `stardew8` (estilos.py:190); `validar`/`hoja` ignoran `estilos:` de la ficha (ficha.py:86, generar.py:29-30); `FRENTE` sin `stardew8` (tests_personaje.py:33); referencia heredada (estilos.py:146). Probado: `hoja aldeano --estilo stardew8` → exit 1.
3. **Falsos negativos sistemáticos en zonas** — whitelist `extremidad_en_movimiento` / `pie_al_piso` (zonas.py:582-590) descarta categorías enteras, y el gate ignora todo `fp` (gates.py:119). Precedente admitido: `diminuta` tapó un cuello parpadeante (skill `sprite-revisar`).
4. **Export sin test** — ✓ ningún test importa `exportar.py`; solo se verifica que exista el PNG en `test_proceso_anim.py:157-159` y `test_proceso_skin.py:81`.
5. **`sprites_x/` no reproducible** — ✓ `boxes.json` = `['panel','rows']`; `referencia.cortar` exige `sheet`/`fondo` (referencia.py:117-118) → `KeyError`. La doc lo lista como kit activo.

### 8.2 Bugs puntuales

- Cresta de pelo con material `"pelo"` literal (humano.py:84) mientras la validación solo exige `pelo` para `corto` (ficha.py:83) → `ValueError` posible en render. ✓ mecanismo
- `TorsoSkin`/`CabezaSkin` con `material(sk.color(*CARA))` si el texel de cara es transparente (skin.py:35,:56) → nombre fuera de `Skin.paleta()`.
- `muneco.ancho_necesario`: `2*m + (2*m)%2` es siempre `2*m` (muneco.py:47). ✓
- `boceto` retorna 0 siempre (generar.py:74-76); `tests` escribe en disco; import `hoja` sombreado por variable local (generar.py:63).
- `base:skin` inalcanzable desde fichas YAML (`ficha.py:65` exige `humano`; `armado` soporta `BASE_SKIN`).
- Exit codes inconsistentes: skin inválida da 2 en `proceso_anim` y 1 en `proceso_skin`.
- `analizar` y `comparar_estilo.metricas` revientan con celdas vacías; `referencia` con `--flag` final → `IndexError`; `comparar_plantilla.imagen` asume un hueso comparable por cuadro.
- `pixelvid.py`: `template.py` apunta a `~/.claude/...` ✓; WAV temporal no se borra; `from_ascii` error críptico; deprecaciones `Image.fromarray(..., "RGBA")`.

### 8.3 Deuda y sugerencias

- **Código muerto:** `rig.py`+`ik_sagital`, `sombra`, `piso_iso`, `pixel2d.py`, `BRAZO_ACTIVO`, `Song.pattern_seconds`, `Palette.index_of`; `CORRER`/`CAMINAR` fuera de `POSES` (verificar consumidores).
- **Duplicaciones:** CLI de `proceso_anim`↔`proceso_skin`; geometría `humano.py`↔`skin.py`; `a_mundo`/`proyectar` entre cámaras.
- **Pulido:** movimiento solo en ciclos de paso; `sep_ojos` no escala por alto; `res["umbrales"]` reporta sin escalar; espejo duplicado por par E↔W.
- **Tests:** determinismo débil (solo `FICHA_MINIMA`/`quieto`); fotos de control acotadas; `test_generar.py:40` acepta exit 1 ✓; registro global en `test_ficha.py:8-18`; valores dorados acoplantes.
- **Gates:** `sin_zona` debería bloquear si ≠ 0; el `control.png` del estilo es write-only (no se compara en el gate); doble análisis de pulido en `proceso_anim.aprobar`.
- **Doc↔código:** `estilos.py:14` (celda), docstring de `comparar_estilo` (8 vs 11 métricas), `docs/procesos/estilo.md:12` ("2+ referencias"), `mapa.MODULOS` manual, `.claude/agents/pintor-skins.md` referencia `skins/pintar_mago.py` (archivado en v1).

---

## 9. Próximos pasos sugeridos

1. Arreglar `stardew8`: agregar a `FRENTE`, referencia/especimen propios, y decidir si el CLI respeta `estilos:` de la ficha.
2. Declarar `referencia.especimen` en los estilos (o retirar la promesa de la doc).
3. Test del contrato de export + cobertura mínima de `sprites_x` (o marcarlo legado y actualizar la doc).
4. Endurecer gates: `sin_zona != 0` bloqueante, revisar whitelist de falsas, decidir si `REVISAR` frena.
5. Limpieza chica: bugs de 8.2, exit codes, template de `pixel-art-video`, y el estado de `aldeano` (hoy no puede aprobarse en su estilo).

---

*Documento generado en una sesión de OpenCode (auditoría de solo lectura + corridas sobre `salida/`). Complementa a `ANALISIS-PROYECTO-ANIMACIONES.md` (arquitectura y técnicas) y a `CRITERIOS_ANIMACION.md` (memoria de animación).*
