---
name: sprite-referencia
description: Buscar, descargar y separar sprite sheets de referencia en animaciones individuales (PNG transparente + JSON + GIF por animación). Usar siempre que el usuario pida buscar sprites de un juego o personaje (Mega Man, FFT, Metal Slug, etc.), descargar un sprite sheet, "separar", "recortar" o "cortar" un sheet en animaciones, identificar qué animación es cada fila, o conseguir referencias libres (OpenGameArt, Kenney, itch.io) para inspirarse, aunque no diga "skill".
---

# Sprites de referencia: buscar → descargar → separar

Objetivo: tener animaciones de referencia limpias y separadas para después analizarlas
(skill `sprite-analizar`) o inspirarse en ellas. Antes de empezar, leer `CRITERIOS_ANIMACION.md`.

## 1. Buscar y descargar
- Sprites de juegos comerciales: **The Spriters Resource** (spriters-resource.com). Con WebFetch sobre la
  página del asset se obtiene la URL directa del PNG (`/media/assets/<n>/<id>.png`).
- Recursos libres para usar en el juego: **OpenGameArt**, **Kenney.nl** (CC0) e **itch.io** (assets gratis). Revisar la licencia.
- Descargar a `referencias/` con `curl -sSL -A "Mozilla/5.0" -o referencias/<nombre>.png "<url>"`.
  curl requiere permiso del usuario; es normal que lo pida.
- Mostrarle el PNG al usuario con `xdg-open`.
- **Derechos**: los sprites de juegos comerciales se usan solo como referencia de estilo y movimiento; lo que
  se genere tiene que ser un personaje propio. Indicar autor/ripper y fuente al usuario.

## 2. Ubicar paneles
Muchos sheets tienen varios paneles (versiones, juegos, capas sueltas). Conviene usar uno solo:
```bash
.venv/bin/python -m sprites_lib.referencia paneles referencias/<sheet>.png
```
Muestra el color de fondo y las líneas divisorias. Si el sheet es muy grande, recortarlo en partes y mirarlas
con Read para elegir el panel (el más completo, preferentemente el personaje "armado" y no las capas sueltas).

## 3. Detectar sprites y numerarlos
```bash
.venv/bin/python -m sprites_lib.referencia detectar referencias/<sheet>.png referencias/<nombre>_cortes --panel x0,y0,x1,y1
```
Genera `boxes.json` y `hoja_numerada.png`: cada sprite con su fila `F<n>` y su número. Cómo funciona: los píxeles
distintos del fondo forman figuras conectadas; los destellos chicos se pegan a la figura más cercana y las cajas
muy solapadas se fusionan. Si dos sprites quedan unidos, o uno queda partido, ajustar el panel o usar
`--fondo r,g,b`.

## 4. Identificar las animaciones (criterio visual)
Mirar `hoja_numerada.png` con Read. Cada fila suele contener una o dos animaciones seguidas. Para las poses
dudosas, ampliar esos sprites (recortar con PIL y resize ×5) antes de decidir. Nombrarlas con un número y
un verbo en español: `01_teletransporte`, `02_quieto`, `04_correr`, `06_saltar`, `14_danio`. Descartar sprites
con texto de créditos o etiquetas. Si queda alguna duda, decírsela al usuario en vez de inventar.

## 5. Cortar y exportar
Crear `referencias/<nombre>_cortes/cortes.json`:
```json
{"boxes": "referencias/<nombre>_cortes/boxes.json",
 "salida": "referencias/<nombre>_cortes/animaciones", "fps": 12,
 "animaciones": {"02_quieto": [[0, [7, 8, 9, 10]]], "04_correr": [[1, [1,2,3,4,5,6,7,8,9,10]]]},
 "fps_por_anim": {"02_quieto": 4}}
```
Una animación puede juntar sprites de varias filas: `[[5, [1,2,3]], [6, [0]]]`.
```bash
.venv/bin/python -m sprites_lib.referencia cortar referencias/<nombre>_cortes/cortes.json
```
Cada animación sale con los cuadros en una misma celda, **alineados por los pies** (así no "saltan"), con fondo
transparente, JSON de cuadros y GIF. Hacer además un índice visual y abrirlo con `xdg-open`.

## 6. Entregar
Tabla con animaciones y cantidad de cuadros, rutas, dudas de identificación y fuente/licencia.
Ejemplo ya hecho: `sprites_x/` (Mega Man X, 14 animaciones).
