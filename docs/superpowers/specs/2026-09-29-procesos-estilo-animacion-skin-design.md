# Diseño: procesos del kit — estilo, animación y skin

Fecha: 2026-09-29 · Estado: para revisión · Rama: `diseno/procesos-estilo-animacion-skin`

## 1. Objetivo

Que el kit tenga **tres procesos claros y ejecutables**, en este orden: **estilo → animación → skin**.
Cada proceso termina con artefactos congelados y verificados por **gates deterministas** (números y tests, no ojo), y con tu aprobación como único paso humano.

Metas concretas:

- **Estilos bien definidos primero**: todo sprite se apoya en el perfil de su estilo, con medidas, reglas y umbrales documentados y verificables.
- **Animaciones hechas una sola vez**: se anima contra la skin de zonas, se itera solo hasta que los gates dan VERDE, y queda disponible para todos los personajes.
- **Skins al por mayor**: un personaje nuevo se pinta como PNG 32×32, se valida en una animación simple (`quieto`) y se aplica a todas las animaciones aprobadas con un comando de lote.
- **Máxima autonomía, gate final**: el agente itera mientras el gate dé ROJO; con VERDE, te presenta el paquete final y vos aprobás.

### Decisiones de la entrevista (2026-09-29)

| Tema | Decisión | Consecuencia |
|---|---|---|
| Variación "al por mayor" | **Personajes completos distintos** | El proceso de skin produce identidad propia (ropa, paleta, accesorios) sobre animaciones congeladas |
| Camino de skin | **PNG 32×32 principal**; ficha+componentes para el elenco | El proceso estándar no escribe código de componentes; el elenco (mago, clast) usa el mismo pipeline con un gate extra |
| Aprobaciones | **Máxima autonomía, gate final** | Los gates deterministas son el motor; el humano aprueba una vez por artefacto |
| Arquitectura | **Procesos ejecutables sobre el kit actual** (no re-arquitectura tipo LPC) | Se reutiliza `render3d`/`estilos`/`ciclos`/`zonas`/`pulido`; se agrega orquestación y tests |

## 2. Base existente que se reutiliza

| Pieza | Uso en los procesos |
|---|---|
| `render3d`, `cuerpo`, `armado` | Render del muñeco/personaje en cualquier estilo |
| `estilos` + `escala` | Perfil del estilo: vista, celda, proporciones, render, tonos |
| `ciclos` + `poses` | Movimiento como datos, independiente del personaje y del estilo |
| `zonas` | Revisión por números: alertas ALTA/MEDIA + falsas conocidas marcadas |
| `pulido` | Belleza: movimiento, limpieza, espejo |
| `comparar_estilo` | Métricas contra la referencia del estilo (calibradas con control) |
| `comparar_plantilla` | Ciclo contra su referencia: IoU + error de huesos por cuadro |
| `fotos_control` | Mecanismo de control visual (se generaliza a los tres procesos) |
| `skins` | PNG 32×32: `guia`, `demo`, `salida_juego` |
| `personajes/generar` + `tests_personaje` | Camino de elenco por ficha + componentes |

Lo nuevo es la **orquestación (procesos + gates + estado)** y los **tests deterministas** que faltan.

## 3. Modelo de artefactos y gates

### 3.1 Cada artefacto = fuente + métricas + control + test

| Proceso | Fuente (código/dato) | Congelado (versionado) | Gate determinista |
|---|---|---|---|
| Estilo | `estilos.py` + `escala.py` | `docs/estilos/<estilo>.md` + `aprobados/estilos/<estilo>/` (`control.png`, `metricas.json`, `estado.json`) | `comparar_estilo` vs referencia con umbrales calibrados + proporciones + determinismo |
| Animación (por animación × estilo) | `ciclos.py` + `poses.py` | `aprobados/animaciones/<anim>/<estilo>/` (cuadros de control, `metricas.json`, `estado.json`) | `zonas` 0 ALTA/MEDIA por revisar + `pulido` sin MAL + `comparar_plantilla` (si hay referencia) + tests |
| Skin | `skins/<nombre>.png` + `skins/pintar_<nombre>.py` | `aprobados/skins/<nombre>/` (`smoke.gif`, `metricas.json`, `estado.json`) | tests de skin + `zonas`/`pulido --skin` sobre `quieto` |

### 3.2 Ciclo de vida

```
borrador → validando (gate ROJO/VERDE) → VERDE → aprobado (humano) → congelado
             ↑ iteración autónoma (tope 3 vueltas; si no converge, consulta)
```

- **Aprobar** es la única acción humana: corre el gate (debe dar VERDE; una excepción se documenta con motivo) y escribe `estado.json` + cuadros de control.
- El **paquete final** que se muestra en la aprobación: imagen/GIF de control, informe resumido y preguntas abiertas (si las hay).

### 3.3 Dependencias y deriva

- Estilo es independiente; animación requiere ≥1 estilo aprobado; skin requiere ≥1 animación aprobada (`quieto` como mínimo; el set completo para el lote).
- `estado.json` guarda fecha, quién aprobó, hash de la fuente y métricas congeladas.
- **Deriva**: si la fuente declarada cambia, el hash no coincide y el gate da ROJO ("cambió desde la aprobación; re-validar"). Además, el render actual se compara contra los cuadros de control (pixel diff) para detectar cambios de motor o de estilo.

## 4. Proceso de estilo

| Paso | Acción | Gate / salida |
|---|---|---|
| 1 | Reunir 2+ referencias del mismo juego en `referencias/estilos/<juego>/` | — |
| 2 | Medir: `comparar_estilo` + celdas/proporciones; calibrar el control (2 sprites reales entre sí) | `metricas_ref.json` |
| 3 | Escribir perfil en `estilos.py` + `escala.TAMANOS` | validación de esquema |
| 4 | Render del muñeco de zonas (neutro/quieto, todas las direcciones) | — |
| 5 | Iterar autónomo hasta que las métricas entren en umbrales | **VERDE** |
| 6 | Paquete final: comparativa ×14 (referencia vs nuestro) + informe + `docs/estilos/<estilo>.md` propuesto | — |
| 7 | Aprobar: congelar `aprobados/estilos/<estilo>/` | gate humano |

Comando: `python -m sprites_lib.proceso_estilo medir|validar|aprobar <estilo>`.

El doc del estilo congela medidas de la referencia, reglas (paleta, contorno, luz), trampas conocidas y **umbrales**: cualquier sprite futuro se puede validar como "pertenece al estilo".

## 5. Proceso de animación

| Paso | Acción | Gate / salida |
|---|---|---|
| 1 | Origen del movimiento: referencia medida (`analizar` + huesos) o diseño propio (boceto) | — |
| 2 | Datos en `ciclos.py` + registro en `poses.py` (n, fps, desfase, loop, `offset_y`, ancho) | esquema |
| 3 | **Smoke**: 1 dirección con la skin de zonas (`skins/zonas.png`) | `zonas` 0 ALTA/MEDIA por revisar + `pulido` sin MAL |
| 4 | Completo: todas las direcciones del estilo (+ `comparar_plantilla` si hay referencia) | **VERDE** |
| 5 | Paquete final: GIF de todas las direcciones + hoja de zonas + informe | — |
| 6 | Aprobar: cuadros de control en `aprobados/animaciones/<anim>/<estilo>/` | gate humano |
| 7 | Export fuente: `salida/animaciones/<anim>/<estilo>/` (frames con skin de zonas) | disponible para el lote de skins |

Comando: `python -m sprites_lib.proceso_anim smoke|validar|aprobar <anim> --estilo <estilo>`.

Iteración autónoma con tope de 3 vueltas propias; si no converge a VERDE, se te consulta con el estado y las opciones.

## 6. Proceso de skin

| Paso | Acción | Gate / salida |
|---|---|---|
| 1 | Pintar `skins/pintar_<nombre>.py` sobre `skins/guia.png` (agente `pintor-skins`) o heredar de otra skin | — |
| 2 | **Smoke** en `quieto` (la animación simple genérica) | tests de skin + `zonas`/`pulido --skin` VERDE |
| 3 | Paquete final: smoke GIF ampliado + hoja de zonas + informe | — |
| 4 | Aprobar: congelar `aprobados/skins/<nombre>/` | gate humano |
| 5 | **Lote**: todas las animaciones aprobadas para esa skin | tests + `zonas` por animación; informe |
| 6 | Entrega: `output/<personaje>/<anim>/` (hoja + JSON + GIF + cuadros) | — |

Comando: `python -m sprites_lib.proceso_skin smoke|lote|aprobar <nombre>`.

Elenco (mago, clast): mismo pipeline por ficha + componentes, con gate extra `tests_personaje`.

## 7. Implementación

| Unidad | Responsabilidad |
|---|---|
| `sprites_lib/gates.py` | Corre tests + mediciones por alcance y agrega **VERDE/ROJO** + evidencia (JSON + texto para LLM) |
| `sprites_lib/proceso_estilo.py` | Pasos y congelado del estilo |
| `sprites_lib/proceso_anim.py` | Smoke, validación completa y congelado de animaciones |
| `sprites_lib/proceso_skin.py` | Smoke, aprobación y lote de skins |
| `sprites_lib/estado.py` | `estado.json`: hash de fuente, fecha, métricas; detección de deriva |
| `docs/procesos/{estilo,animacion,skin}.md` | Los pasos de cada proceso |
| `docs/estilos/<estilo>.md` | Ficha del estilo (se crea al aprobar; los existentes se escriben al adoptar el proceso) |
| `tests/test_proporciones.py` | Contrato numérico por estilo: alto, cabeza%, piernas%, hombros, brazos% |
| `tests/test_esqueleto.py` | muslo = canilla; cadera sobre tobillo en todas las poses; huesos no se estiran |
| `tests/test_determinismo.py` | Doble render → hash idéntico (estilo × pose × dirección) |
| `tests/test_deriva.py` | Fuente cambiada tras aprobar → gate ROJO |
| Skills + `CLAUDE.md` | Apuntan a los comandos de proceso; `MAPA.md` regenerado |

**Orden de desarrollo**: ① gates + tests deterministas (la base), ② proceso estilo, ③ proceso animación, ④ proceso skin + lote.

## 8. Criterios de aceptación

- Los tres comandos corren de punta a punta sobre artefactos reales del kit (p. ej. `proceso_anim smoke saltar --estilo stardew`).
- Un gate ROJO nunca permite congelar; `aprobar` escribe `estado.json` y cuadros de control.
- Si se edita la fuente de un artefacto congelado, el gate lo detecta (hash) y/o el pixel diff de control lo reporta.
- `pytest` completo en verde (los lentos, con `-m ""`).
- Los flujos actuales siguen funcionando: `personajes.generar`, `skins demo|juego`, `zonas`, `pulido`.

## 9. Fuera de alcance

- Re-arquitectura tipo LPC (capas + recolor en runtime) y variantes de color masivas.
- Herramienta web / visor y cualquier runtime JS.
- Cambios al render o a los estilos existentes: solo se agregan los del proceso.
- Migrar `personajes/aprobados/` (queda donde está).

## 10. Riesgos y calibración

- **Umbrales**: se calibran con un control (dos sprites reales del mismo juego); una métrica que falla en el control no bloquea.
- **Lote**: tiempo por personaje; primero secuencial, paralelizar solo si hace falta.
- **Nombres de comandos/módulos**: pueden cambiar al implementar sin tocar el diseño.
