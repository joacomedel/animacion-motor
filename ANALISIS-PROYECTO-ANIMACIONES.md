# Análisis del proyecto "animaciones" (kit generador de sprites para un juego)

Fuente analizada: `/home/jm/claude-code/animaciones/` (fecha: 2026-09-29)

---

## 1. Propósito general

Generar **sprites pixel art de personajes para un videojuego** de forma 100% procedimental, predecible y verificable:
- Personajes consistentes en todas las direcciones, poses, animaciones y cuadros (misma cara, mismos colores, mismo tamaño).
- Calidad que **no depende de que el agente de IA improvise**: las lecciones aprendidas viven en código y en tests, no en la memoria del modelo.
- La exportación es **genérica** (PNG + JSON + GIF): el motor del juego todavía no existe; el JSON trae metadatos estilo Aseprite/TexturePacker para cualquier motor.
- Cada decisión de diseño queda explicada (campos `por_que` en las fichas YAML).

Idea central: los sprites **no se dibujan a mano**. Se construye un **muñeco 3D de primitivas** (esferas, cápsulas, elipsoides, faldones) que se "fotografía" a resolución de pixel art con z-buffer — la técnica de los sprites pre-renderizados de Diablo II, pero renderizada directo a píxeles, con 3 tonos por material, contorno por pieza y luz coherente.

Un sprite = **personaje** (`personajes/`) + **movimiento** (`sprites_lib/ciclos.py`) + **estilo** (`sprites_lib/estilos.py`). Las tres capas son intercambiables: el mismo muñeco puede verse "pre-renderizado" o "Stardew Valley" cambiando solo el estilo.

---

## 2. Manera en que resuelve (flujos de trabajo)

### 2.1 Flujo general de una animación
```
referencia (sprite sheet / video)
  → sprite-referencia (buscar, descargar, separar sheet en animaciones)
  → sprite-analizar (medir movimiento píxel por píxel → números → ciclo reutilizable)
  → sprite-personaje (entrevista → ficha YAML → boceto → hoja de modelo + tests → aprobación)
  → animaciones con ciclos → sprite-revisar (revisión por números con zonas)
  → exportar (PNG + JSON + GIF) → xdg-open para que el usuario lo vea
```

### 2.2 Flujo de un personaje nuevo (skill `sprite-personaje`)
1. **Entrevista corta** (1–2 tandas de preguntas con opciones y una recomendada).
2. **Ficha YAML** (`personajes/fichas/<nombre>.yaml`) con identidad, cuerpo, paleta, componentes, reglas y `por_que` de cada decisión. Validar con `python -m personajes.generar validar <nombre>`. → **pausa: OK del usuario**.
3. **Boceto rápido** (`generar boceto`) — frente y perfil en <1 s, sin tests. Mostrar y preguntar feedback antes de afinar.
4. **Hoja de modelo + tests** (`generar hoja`): todas las direcciones alineadas con líneas guía (coronilla, ojos, hombros, cintura, suelo) + informe ✓/✗. Máximo 2 vueltas de corrección propias; si sigue fallando, el usuario decide (excepción documentada / cambio de diseño / seguir).
5. **Aprobación** (`generar aprobar`): se congelan las "fotos de control" (PNGs versionados en `personajes/aprobados/`). Si cualquier cambio futuro altera 1 píxel, el test lo reporta con imagen antes/después.
6. Recién después: animaciones (fase 2, poses clave medidas en referencias).

### 2.3 Principios operativos (de CLAUDE.md)
- Leer `CRITERIOS_ANIMACION.md` antes de tocar cualquier animación; **anotar ahí** cada lección nueva (es la "memoria" del proyecto).
- Mostrar algo rápido y pedir feedback en cada etapa; **máximo 2 vueltas de corrección propias** antes de consultar.
- **Tokens**: números antes que imágenes; un estilo por vez al iterar; tests del archivo tocado; ajuste fino largo → subagente barato.
- Subagentes por tarea (ver §6); no cambiar de modelo a mitad de sesión (rompe caché).
- Ejecutar Python siempre con `.venv/bin/python` desde la raíz (único comando con permiso automático).

---

## 3. Arquitectura de la librería (`sprites_lib/`)

```
ficha YAML → ficha.cargar (valida) → armado.render_cuadro
  (cuerpo base + componentes → cuerpo.posar → render3d.Escena)
  → Cuadro (img + buffers de píxel) → tests / hoja de modelo / exportar
```

### 3.1 El muñeco 3D (`render3d.py`) — el corazón
- Ejes **locales** del personaje: `f` = adelante, `l` = izquierda, `u` = arriba (1 unidad ≈ 1 px).
- **Cámara y luz fijas en el mundo**; lo que rota es el personaje. Así las 8 direcciones quedan iluminadas coherentemente entre sí (de espaldas queda más oscuro, y está bien — como en un juego).
- `Escena` acumula **puntos de superficie** (posición, normal, material, pieza, componente) y `render()` hace: proyección → z-buffer (los puntos ordenados estable, el más cercano a cámara gana) → 3 tonos por material según luz → contorno interior (entre piezas y por salto de profundidad) → detalles de 1 px → contorno exterior.
- Primitivas: `esfera`, `elipsoide`, `caja` (superelipsoide, lados rectos = look dibujado a mano), `capsula`, `faldon` (cono truncado abierto, para túnicas/capas), `detalle` (1 px visible si pasa el z-buffer).
- **El material puede ser una función de la dirección** (`mat(d)`), para pintar cara/pelo/vincha sobre la cabeza según dónde mire la cámara. Ej. de componentes: capa = `faldon` con `conservar=lambda d: d[...,0] < -.2` (solo atrás).
- **`esc.pieza`** se asigna antes de cada parte: da contorno donde dos piezas distintas se tocan (puño y antebrazo, brazo y torso) aunque la diferencia de profundidad sea mínima (> 0.8) — es lo que hace que se lean las manos.
- Cámaras: `Camara` (isométrica 2:1, 8 dir.), `CamaraCenital` (3/4 top-down tipo Stardew/Zelda, 4 dir.), `CamaraLateral` (perfil ortográfico, plataformas).
- IK: `ik_sagital` (2D) e `ik_3d` (3D con vector "polo": rodilla dobla hacia adelante, codo hacia atrás; respeta desplazamientos laterales).

### 3.2 Esqueleto (`cuerpo.py`)
- **Vocabulario fijo de anclas** (~35: suelo, cadera_derecha, rodilla_izquierda, muneca_derecha, sien_izquierda, nuca…) y de **segmentos** (brazo_derecho = hombro→codo→muñeca→mano). Si una ficha nombra mal un ancla, la validación falla sugiriendo el correcto.
- `anatomia(estilo, clase, complexión)`: proporciones derivadas de fracciones del alto por estilo. Clases de altura: nino .75, adulto 1.0, grande 1.25, gigante 1.6.
- `posar()`: convierte una pose (formato del rig lateral) en posiciones 3D de todas las anclas. Los huesos **nunca se estiran**: si la mano queda fuera de alcance, se recorta al largo del brazo.
- **`centro_cara()` — "trampa de Stardew"**: la cara se corre hacia la cámara (frente + fuerza·hacia_cámara). De frente queda adelante; de perfil, sobre el costado visible (si no, de costado solo se vería pelo); de espaldas queda oculta.
- `sobre_caja()`: apoya cara y ojos sobre la superficie real de la caja de la cabeza (superelipsoide girada). Si se gira la caja y no se mueven los anclas, los ojos quedan flotando en el borde de la silueta.
- `giro_cabeza()`/`cabeza_pantalla`: alinea la caja de la cabeza a la pantalla para que mida lo mismo en las 8 direcciones; `cabeza_diagonal` angosta la cabeza ~2 px en diagonales (como hacen los juegos de 8 dir).

### 3.3 Movimiento (`ciclos.py` + `poses.py`)
- Todos los ciclos viven en el **"rig lateral"**: x adelante, y abajo, piso en y=34, cadera en x=18. Un ciclo define por cuadro: `bob` (rebote de la cabeza), `pie` (tobillo de la pierna A), `pie_ang`, y la trayectoria de la mano (fórmula seno **o** lista `xy` medida cuadro a cuadro — el seno no alcanza cuando la mano acelera en el cruce).
- La pierna/brazo B es la misma curva **desfasada** medio ciclo (caminar/correr) o curvas propias `mano_b`/`pie_b` (animaciones asimétricas como golpear).
- Metadatos por ciclo que van al JSON: `loop` (caminar se repite, saltar se juega 1 vez), `offset_y` (cuánto levanta el motor el sprite por cuadro — para el salto la altura NO está en el dibujo), `ancho` (celda propia por animación en stardew8).
- Ciclos existentes: `CORRER` (Mega Man X), `QUIETO`, `CAMINAR` (Stardew 4 cuadros), `CAMINAR_LPC` (LPC 8 cuadros), `SALTAR` (Mega Man X), `AGACHAR` (boceto propio), `GOLPEAR` (boceto propio).

### 3.4 Estilos (`estilos.py`)
Perfiles que deciden el "look": vista, direcciones, celda, parámetros de render (umbrales de tono, contorno negro vs. de color/selout, sombreado por luz o "borde"), proporciones, reglas de tonos (sombra→violeta, luz→amarillo en Stardew), tipo de ojos y referencia para autoanálisis.

| estilo | vista | direcciones | adulto px | celda | estado |
|---|---|---|---|---|---|
| volumen | iso | 8 (SE…S) | 36 | 56×60 | inactivo |
| stardew | cenital 3/4 | 4 (S,E,N,W) | 26 | 16×32 | **activo** |
| lateral | perfil | 2 (E,W) | 33 | 40×40 | **activo** |
| lpc | perfil | 2 | 43 | 64×64 | solo verificación |
| stardew8 | cenital 3/4 | 8 | 26 | 16×32 | boceto |
| fry8 | cenital 3/4 | 8 | 54 | 48×64 | boceto |

### 3.5 Paleta (`paleta.py`)
- La ficha da **solo el tono base** de cada material; el estilo deriva sombra y luz con corrimiento de tono propio (`tonos()`). Agrega `<material>_b` (variante más oscura para texturas) y `mano` (piel un tono más clara).
- **Emisivos** (runas, visor, chispas): no se oscurecen, brillan igual en todos lados.
- `reducir_paleta(por_dir, n)`: une de a pares los colores más parecidos (distancia **Lab** ponderada por píxeles), conserva siempre el más usado — nunca inventa colores. Clast pasó de 70 a 28 colores para acercarse a los 14 de la referencia Fry.

### 3.6 Armado (`armado.py`)
`expandir(ficha)` resuelve cuerpo base (salvo sustituciones o componentes propios) + componentes de la ficha, cada uno con id `tipo@ancla` y `pieza_base`. `render_cuadro()` arma el `Cuadro` (img + buffers + anclas proyectadas). Soporta espejar el brazo activo de animaciones asimétricas (`brazo_activo`).

### 3.7 Componentes (`componentes/`)
Cada pieza del personaje sabe dibujarse en su ancla: `humano.py` (cuerpo base), `mago.py` (rastas, vincha, pulsera, tatuaje_runas, tunica_abierta, botas), `robot.py` (brazos robóticos, muñón con cables que chispean, piernas robóticas, visor, placa, cables_nuca), `ropa.py` (remera_larga_rota, cinturon), `skin.py` (piezas que toman el color de un PNG de skin). El render **marca qué componente pintó cada píxel** (buffer `comp` + `pieza`): eso habilita tests por componente y el análisis por zonas.

---

## 4. Trucos técnicos destacados

### Render y pixel art
1. **Muñeco 3D "fotografiado" en pixel art**: volúmenes simples + z-buffer a baja resolución. Dibujar líneas/polígonos 2D proyectados queda plano (primer intento fallido documentado).
2. **Caja redondeada (superelipsoide n=3–4) en vez de esfera**: las siluetas con curvas perfectas "gritan 3D"; los lados rectos se leen dibujados a mano.
3. **"Parece 3D" no es (solo) el sombreado**: es silueta curva + superficies lisas sin micro-detalle + tamaños de cara/cabeza que no son del estilo. La referencia tiene MÁS ruido que el render (grupos de color de 1.9 px vs 3.4), contra la intuición inicial.
4. **Contorno interior por salto de profundidad (> 3.2) y por pieza distinta (> 0.8)**: separa brazo/torso/pierna sin dibujar líneas a mano; el contorno por pieza es lo que hace leíbles las manos.
5. **Selout automático** (`contorno="color"`): cada borde toma el tono oscuro de su propio material — 0% de negro en Stardew.
6. **Sombreado "borde"**: tono base plano + luz en el borde superior-izquierdo de cada pieza y sombra en el inferior-derecho, como lo haría un artista (look plano de Stardew).
7. **Detalles de 1 px al final** (ojos, runas, gemas) solo si el punto 3D pasa el z-buffer.
8. **`_mover()` en vez de `np.roll`**: un bug real — `np.roll` "da la vuelta" y el contorno de los pies aparecía arriba de la celda. Desplazamiento sin envolver.
9. **`_dirs_n` con `lru_cache`**: las direcciones de esfera se piden miles de veces por hoja.
10. **Manos legibles**: pieza propia, radio mayor que el antebrazo (1.95 vs 1.35), un tono más clara, brazalete en la muñeca, 1 px de brillo en los nudillos; en iso **no** subir el puño a la altura de la cara (la tapa).

### Movimiento y rig
11. **Rig lateral normalizado** (piso y=34, cadera x=18): los ciclos medidos en cualquier referencia se escalan y trasladan a ese sistema una vez, y todos los personajes/estilos los usan.
12. **IK de 2 huesos** (rig.ik, render3d.ik_3d): la pose se define solo con cadera + pie (rodilla) y hombro + mano (codo). Codo siempre doblado (~90°): si no, el brazo queda como barra horizontal.
13. **Brazos opuestos a las piernas**; en iso **no se refleja medio ciclo** (cada extremidad conserva su lado) — reflejar da dos pasos idénticos.
14. **`bob_px` (rebote en píxeles enteros)**: con fracciones (0.84 px) la pestaña/ceja caen en filas distintas según el cuadro y los ojos "parpadean". Parpadeo de 1 px = defecto real que las métricas de imagen pueden esconder.
15. **Salto: la altura NO está en el dibujo** (`bob` nunca negativo, `offset_y` en el JSON para el motor). Un `bob` negativo cortaba la cabeza contra el borde superior de la celda. La sensación de altura la dan pose + `offset_y`.
16. **`loop` y `pivot` son metadatos del JSON**: loop por animación; pivot (pies) sale de proyectar el ancla `suelo` — idéntico para cualquier pose/dirección/personaje del estilo.
17. **Animaciones asimétricas** (golpear): verificar en imagen, por dirección, cuál extremidad es cuál (el brazo cercano cambia con la dirección). Un golpe con el brazo amputado no tiene mano: la ficha manda.

### Estilos y cámara
18. **Trampa de Stardew** (`centro_cara`, `cara_hacia_camara=.9`): la cara se dibuja casi de frente aunque la cámara mire desde arriba; de perfil se corre al costado visible.
19. **Cabeza que se angosta en diagonal** (`cabeza_diagonal=.85`): 13 px de frente → 10–11 en 3/4, medido en referencias de 8 dir (Witch, TheNess, Fry).
20. **Parámetros de cara que se compensan**: subir `sep_ojos_diagonal` empuja el ojo cercano al borde → hay que subir `cara_diagonal`. Medir con máscaras de componente, no por color (los colores cambian con el sombreado).
21. **Calibrar métricas con un control** (dos sprites reales del mismo juego): la métrica que falla en el control no discrimina estilo, no hay que perseguirla.

### Verificación sin imágenes (lo más original del proyecto)
22. **`zonas.py` + `pulido.py`: revisar animaciones leyendo texto/JSON en vez de imágenes**. Cada píxel se clasifica por los buffers del render (componente/pieza/material), no por color. Informe con ALERTAS (ALTA/MEDIA/baja) + catálogo de patrones feos con firma → causa → arreglo que funcionó. Una imagen ampliada cuesta muchos tokens y se reenvía en cada turno; los números no.
23. **Falsas conocidas marcadas, no borradas**: cada alerta trae `fp` (falsa conocida y motivo). 297 alertas → 10 por revisar + 265 falsas marcadas. Regla: nunca subir un umbral "para que dé verde" sin mirar qué era. (Y una falsa "por diseño" se confirma mirando el GIF: una de ellas escondió un ojo blanco sobresaliendo de la silueta.)
24. **`comparar_estilo.py`**: métricas objetivas contra referencia (colores, borde negro, planitud, degradé R², píxeles huérfanos, tamaño de grupos de color, bandas, recorte, rectitud de silueta, ancho de cabeza) con diagnóstico y corrección impresa.
25. **`comparar_plantilla.py`**: verificación de un ciclo contra su referencia original — silueta (IoU) y error de cada hueso cuadro por cuadro (≤ 2 px), con imagen de siluetas superpuestas.
26. **`fotos_control.py`**: las poses aprobadas quedan congeladas en git; cualquier cambio de motor/componente que altere 1 píxel se reporta con imagen antes/después. Los sprites aprobados son el "test de regresión visual" del proyecto.
27. **Tests de consistencia (`tests_personaje.py`)**: visibilidad de componentes, anclas a la vista, líneas guía, paleta permitida, tamaño de clase, recorte, cara, simetría, distinto de otros personajes del elenco. Cada falla trae pose/dirección/cuadro exactos.
28. **`test_animaciones_juego.py`**: ningún cuadro de NINGUNA animación/estilo activo toca la fila 0 de la celda (un motor sin margen cortaría cabeza/pelo).

### Skins
29. **Skins tipo Minecraft** (`skins.py`): un solo PNG 32×32 con cada parte "desenrollada" (centro = frente, bordes = espalda, arriba = punta). El muñeco y las animaciones son siempre los mismos; el personaje es solo un PNG. Sombras/luces/contorno los pone el estilo, así que se pinta con colores planos. Las skins se **pintan por código** (`skins/pintar_clast.py`: piel, cresta, canas en las sienes, metal rayado, ropa gastada).
30. **`plantilla_zonas()` / `muneco zonas`**: skin con un color plano por parte (derecha cálidos, izquierda fríos) para depurar qué se mueve dónde.

### Proceso / ingeniería
31. **`mapa.py` → `MAPA.md` autogenerado**: lee los archivos con `ast`, extrae docstrings y firmas, y regenera el índice de la librería (con un test que avisa si quedó desactualizado). Los agentes leen el mapa y abren solo el archivo que necesitan — ahorro masivo de contexto.
32. **`CRITERIOS_ANIMACION.md` como memoria**: cada referencia analizada deja proporciones, tiempos, trayectorias medidas y — clave — **los errores cometidos al replicarla y cómo se corrigieron**, con checklists al final de cada sección.
33. **Fichas con `por_que` en cada color/componente** + `decisiones` (registro de la entrevista) + `excepciones` (oclusión declarada, no error) + `objeciones_resueltas`.
34. **Delegación por modelo** (regla del usuario): mecánica acotada → haiku; integración/depuración → sonnet; arquitectura/revisión final → opus. Tareas de 1–2 comandos directo (delegar cuesta más).
35. **Flujo SDD (subagent-driven-development)** en `.superpowers/sdd/`: plan → tareas con briefs, tests que fallan primero, ledger con "Rulings" (decisiones técnicas y su costo si salen mal), commit por tarea.
36. **Informe de personaje en `informe.md`** junto a la hoja de modelo; las salidas en `salida/` (ignorado por git), los aprobados en `personajes/aprobados/` (versionados).

---

## 5. Inventario de rutas

### Raíz
| Ruta | Qué es |
|---|---|
| `CLAUDE.md` | Reglas del proyecto: leer CRITERIOS antes de tocar animaciones, flujo de feedback, política de tokens y subagentes, mapa del kit |
| `CRITERIOS_ANIMACION.md` | La "memoria" del proyecto: cada referencia analizada (Mega Man X correr/saltar, FFT, Isometric Hero, Stardew, LPC, Fry) con medidas, errores corregidos y checklists |
| `pytest.ini` | `testpaths = tests`, `pythonpath = .`; marker `lento` (volumen) salteado por defecto; `-m ""` corre todo al cerrar rama |
| `.gitignore` | `salida/`, `referencias/`, `.superpowers/`, `.claude/settings.local.json` fuera de git (referencias con copyright solo local) |

### Skills (`.claude/skills/`)
| Ruta | Qué hace |
|---|---|
| `sprite-personaje/SKILL.md` | Entrevista → ficha YAML → boceto → hoja de modelo + tests → aprobación → animaciones. Con reglas de ahorro de tokens |
| `sprite-referencia/SKILL.md` | Buscar/descargar sheets (Spriters Resource, OpenGameArt, Kenney, itch.io) y separarlos en animaciones alineadas por los pies |
| `sprite-analizar/SKILL.md` | Medir una animación píxel por píxel (paleta, bbox, rebote, trayectorias, articulaciones) → ciclo reutilizable en ciclos.py + anotar criterios |
| `sprite-estilo/SKILL.md` | Analizar el look de un juego → perfil en estilos.py → autoanálisis obligatorio contra referencia (métricas + comparación ×14) antes de mostrar |
| `sprite-2d-lateral/SKILL.md` | Personajes 2D de perfil con capas + contorno propio (Mega Man/Metroid), usando ciclos medidos |
| `sprite-isometrico/SKILL.md` | Personajes iso con volumen real en 8 direcciones con el muñeco 3D de primitivas |
| `sprite-revisar/SKILL.md` | Revisión cuadro por cuadro leyendo números (zonas) + catálogo de patrones feos con firma → causa → arreglo; incluye pulido |
| `pixel-art-video/` | Motor aparte para **videos** pixel art (ver §7) |

### Agentes (`.claude/agents/`)
| Ruta | Modelo | Qué hace |
|---|---|---|
| `pintor-skins.md` | haiku | Pinta skins por código (`skins/pintar_<nombre>.py`), sin mirar imágenes, devuelve solo archivos y ruta del GIF |
| `revisor-sprites.md` | sonnet | Revisa visualmente una hoja ampliada UNA vez + corre tests del archivo tocado; veredicto corto de ≤10 líneas; las imágenes no entran al contexto principal |
| `medidor-animaciones.md` | sonnet | Mide plantillas nuevas de animación (sprite-analizar fuera del contexto principal) |

### Librería (`sprites_lib/`) — por módulo
| Archivo | Qué hace |
|---|---|
| `MAPA.md` | Índice autogenerado de toda la librería (firmas, componentes, anclas, estilos) — leer primero, no editar a mano |
| `mapa.py` | Genera MAPA.md parseando el código con `ast` (docstrings + firmas) |
| `escala.py` | Escala del juego: clases de altura, `alto_objetivo_px`, `celda` estándar por estilo con pivote (pies) fijo |
| `paleta.py` | Hex→RGB, derivación de 3 tonos por estilo con corrimiento de tono, emisivos, variantes `_b`/`mano`, reducción de paleta en Lab |
| `estilos.py` | Perfiles de estilo (vista, direcciones, render, proporciones, tonos, ojos, referencia) + `crear_camara()`; `ACTIVOS` y `VERIFICACION` |
| `cuerpo.py` | Esqueleto base humano: vocabulario de anclas/segmentos, `anatomia()`, `posar()`, trampas de cara/cabeza (`centro_cara`, `sobre_caja`, `giro_cabeza`, `desvio_cabeza`) |
| `poses.py` | Poses clave como datos (`neutra`, `quieto`) + helpers `cuadros()`, `fps()`, `loop()`, `offset_y()`, `ancho()` |
| `ciclos.py` | Ciclos de movimiento reutilizables en el rig lateral (CORRER, QUIETO, CAMINAR, CAMINAR_LPC, SALTAR, AGACHAR, GOLPEAR) |
| `rig.py` | IK de 2 huesos en 2D (`ik(a,b,l1,l2,bend)`) |
| `render3d.py` | Motor 3D: `Camara` (iso), `CamaraCenital`, `CamaraLateral`, `Escena` (primitivas + render con z-buffer, tonos, contornos, buffers), `ik_sagital`/`ik_3d`, `sombra()`, `piso_iso()` |
| `armado.py` | Ficha → specs de componentes → `render_cuadro()` / `render_todo()` → `Cuadro`; `pivote()` |
| `ficha.py` | Carga y valida fichas YAML (esquema, anclas, componentes, estilos, colores, créditos); errores claros con sugerencia |
| `tests_personaje.py` | Tests de consistencia por personaje (visibilidad, ausentes, anclas, líneas guía, paleta, tamaño, recorte, cara, simetría, distinto del elenco) + `informe_md()` |
| `hoja_modelo.py` | Imagen de hoja de modelo con líneas guía, paleta, componentes con su porqué y resultados de tests |
| `fotos_control.py` | Congela y compara poses aprobadas (versión en git); imagen antes/después con los píxeles cambiados en rojo |
| `exportar.py` | Exportación genérica: PNG tira + JSON estilo Aseprite/TexturePacker (frames, meta: cell/fps/loop/pivot/offset_y/animations) + GIF + `_revision.png`; `exportar_direcciones()` arma hoja por dirección |
| `referencia.py` | Separa sheets: `paneles` (fondo y divisorias), `detectar` (componentes conectados + pegado de piezas chicas → boxes.json + hoja numerada), `cortar` (anims alineadas por los pies) |
| `analizar.py` | Mide una tira de cuadros: paleta, bbox, rebote, apoyos, apertura → `medidas.json` + `grilla_XX.png` |
| `pixel2d.py` | Sprites 2D planos: `Lienzo` (capas, trazos `seg`, `puntos`), `contorno()` por capa, `apilar()` |
| `lado_a_lado.py` | Comparación visual ×14 de referencia y propio intercalados, para revisar con Read |
| `comparar_estilo.py` | Métricas objetivas de estilo contra referencia + diagnóstico (ver truco 24) |
| `comparar_plantilla.py` | Compara un ciclo contra su referencia: silueta (IoU) y error de huesos por cuadro |
| `skins.py` | Sistema de skins Minecraft-style (32×32): `Skin`, `cargar`, `u_de`, `desde_colores`, `plantilla_zonas`, `ficha`, `guia`, `demo`, `salida_juego` |
| `muneco.py` | Muñeco base sin skin para probar ciclos/poses: `demo`, `ancho_necesario`, `grilla` de zonas |
| `zonas.py` | Zonas del cuerpo por cuadro (clasifica píxeles por buffers del render) → alertas + informe texto para LLM + falsas conocidas marcadas |
| `pulido.py` | Modo pulido: movimiento (recorridos vs LPC, oposición mano-pie, simetría), limpieza (píxel suelto, manchas, parpadeo), espejo — mide lo que hace la animación BONITA |
| `componentes/` | Registro de componentes (`Componente`, `registrar`, `Contexto`, `entrar`) + `humano.py`, `mago.py`, `robot.py`, `ropa.py`, `skin.py` |

### Personajes y salidas
| Ruta | Qué es |
|---|---|
| `personajes/generar.py` | CLI: `boceto`, `validar`, `hoja`, `tests`, `aprobar` (códigos de salida 0/1/2) |
| `personajes/fichas/mago.yaml`, `clast.yaml` | Fichas ejemplo (Clast: cyborg con prótesis, muñón con cables, paleta con `por_que`) |
| `personajes/mago_*.py` | Versiones anteriores sin ficha (lateral, iso, stardew) — plantillas, no base |
| `personajes/aprobados/` | Fotos de control versionadas |
| `salida/<personaje>/<anim>/` | Salidas (ignoradas por git) |
| `output/` | Entrega del juego (LEEME.md documenta el formato para el motor) |
| `skins/` | `pintar_clast.py`, `pintar_mago.py`, `guia.png`, `zonas.png` |
| `sprites_x/` | Mega Man X separado en 14 animaciones (detección + cortes) — ejemplo del flujo de referencia |
| `referencias/` | Sheets descargados: LPC, Stardew, FFT, Isometric Hero, 8dir (Witch, TheNess, Fry) |
| `mago/`, `el_llamado/`, `prueba/` | Experimentos anteriores (no usar como base) |
| `docs/superpowers/` | Spec y plan de SDD (diseño de fichas de personaje) |
| `.superpowers/sdd/` | Ledger de ejecución del plan con "Rulings" por tarea |
| `tests/` | 16 archivos (~1055 líneas): test_escala_paleta, test_render3d, test_cuerpo_poses, test_armado, test_ficha, test_generar, test_componentes_*, test_zonas, test_pulido, test_skins, test_comparar_plantilla, test_animaciones_juego, test_mapa |

---

## 6. Detalle: sistema de revisión por números (zonas → pulido)

Flujo en dos etapas:

1. **`zonas`** (¿está BIEN CONSTRUIDA?): clasifica cada píxel por zona del cuerpo usando los buffers del render. Produce alertas con severidad (ALTA = casi seguro error: ojo visible de espaldas, pivote que se mueve, lado cruzado; MEDIA = mirar: salto de centro > 1 px, ojo pegado al borde, separación de ojos fuera de rango, cabeza que cambia de tamaño; baja = normal en muchos ciclos). Reglas de falsas conocidas con motivo y lección (ej.: una zona diminuta que alterna cada 2 cuadros con el ritmo del rebote es parpadeo REAL, no cuantización). Umbrales escalables por alto del personaje.

2. **`pulido`** (¿se ve BONITA?): recién cuando zonas no tiene alertas ALTA/MEDIA por revisar, y siempre con el personaje real (skin). Mide movimiento (recorrido de mano/pie normalizado por el alto contra LPC, oposición mano-pie por correlación, simetría p↔p+n/2, cierre del loop, quiebres de 1 cuadro), limpieza (píxel suelto, rasgo que sobresale = ojo/boca con ≥2 lados en contorno, manchas llamativas, parpadeo de color, paleta por dirección) y espejo (E↔W, SE↔SW…; regla comprobada: x' = 2·pivote_x − x, cuadro (p + desfase) % n).

Ambos informes son texto compacto para un LLM; mirar una imagen solo al final, para juzgar "se ve bien" (eso no lo mide ningún número).

---

## 7. Motor de videos pixel art (`pixel-art-video/`)

Skill separada con su propio mini-engine (`scripts/pixelvid.py`, ~134 funciones/clases), para **películas** pixel art (no sprites de juego):
- Cada cuadro es una **función pura del tiempo** → se pueden renderizar stop-frames en cualquier momento sin correr todo el film.
- Canvas chico (320×180) con paleta fija → upscale entero sin suavizado → MP4 + **chipmusic sintetizada** (square/triangle/batería/sfx; `Song`, `note_freq`, osciladores, lowpass).
- Helpers: `humanoid`, sprites ASCII (`Sprite.from_ascii`), clima (rain/snow/stars/clouds/sea/fire/lightning), scroll (mountains/hills/city), texto pixelado con font que soporta cirílico, `keys`/`seg` para timings, easing, dithering como única "transparencia".
- CLI por película: `preview` (12 stop-frames), `stills 3.5,7.2`, `render`, `gif`. Revisión de stop-frames OBLIGATORIA antes de render.
- Referencias: `story.md` (cómo inventar el guion: logline, beats, tabla de escenas, "género → paleta → música"), `craft.md` (reglas de pixel art + checklist de review), `api.md` (notación de música y funciones).
- Ejemplos completos: `lighthouse.py` (faro con tormenta), `star_cat.py`, `super_pixel.py` (plataformero NES con cámara y HUD); y en el proyecto `el_llamado/film.py` (caballero que se arma pieza por pieza) y `prueba/lighthouse.mp4`.

---

## 8. Lecciones de proceso más valiosas (resumen de CRITERIOS_ANIMACION.md)

- **Medir la referencia antes de suponer**: la intuición "Stardew tiene menos ruido que mi render" era al revés.
- **Corregir la causa, no el síntoma**; en Stardew hicieron falta 6 vueltas de autoanálisis.
- **Revisar las 4/8 direcciones antes de exportar**, no solo la vista principal (un error de brazo equivocado llegó a `output/`).
- **Para poses con pierna muy doblada, juzgar sobre el personaje vestido**, no sobre el muñeco desnudo (el contorno de cápsulas superpuestas parece garabato aunque la geometría esté bien).
- **Al cambiar la forma de una pieza, revisar todo lo que se ancla a su superficie** (girar la caja de la cabeza dejó los ojos en el borde).
- **Los accesorios chicos necesitan ≥ 2–3 px** para leerse a esta escala (radio ~1.5, no 2: una hombrera de radio 2 parece globo).
- **Contraste entre capas**: extremidad cercana más clara, lejana más oscura.
- **Movimiento secundario** (pelo, capa, faldón) con 1 cuadro de retraso (`lag_faldon`, `bob_prev`).
- **Anotar todo**: cada lección vuelve al catálogo de patrones de `sprite-revisar` o a `CRITERIOS_ANIMACION.md`, para que la próxima animación salga revisada contra todo lo aprendido.
