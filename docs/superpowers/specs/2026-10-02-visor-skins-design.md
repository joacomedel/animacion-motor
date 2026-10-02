# Visor de skins y animaciones — diseño

- **Fecha:** 2026-10-02
- **Estado:** diseño aprobado en chat; listo para implementar
- **Origen:** pedido del usuario — una app que lea la carpeta de salidas y permita rotar entre
  personajes y animaciones mostrando el GIF, sin pedírselo al LLM.

## Problema y objetivo

Hoy, para ver una animación hay que abrir el archivo a mano
(`xdg-open salida/<personaje>/<anim>/<anim>_todas.gif`) o pedirle al agente que la muestre en el chat.
Se quiere un visor local que liste lo que hay en `salida/`, permita cambiar de personaje y de
animación, y muestre el GIF (y la hoja) al instante.

**Éxito:** con un solo comando y en el navegador, elegir entre todos los personajes y animaciones
renderizadas, ver el GIF animado, rotar con el teclado, y que los renders nuevos aparezcan al
recargar (sin reiniciar la app).

## Alcance

- Solo lectura: no renderiza, no edita, no borra, no sube nada.
- Lee una o más raíces: `salida/` por defecto; `output/` es opcional vía `--raiz`.
- App local: bind solo a `127.0.0.1`.

## No-goals

- No genera skins ni animaciones (para eso está `render_skins.sh`).
- **Fuera de alcance el pipeline de ficha** (`personajes/generar.py`), que escribe
  `salida/<personaje>/<estilo>/<pose>.*` (carpeta = estilo, archivos = pose). El visor solo lee el
  pipeline de skin (`skins.salida_juego`).
- Sin autenticación, sin multiusuario, sin deploy.
- **Sin dependencias nuevas**: solo stdlib de Python.
- Sin persistencia de estado.

## Datos de entrada

Hay **dos convenciones mezcladas en `salida/`**; el visor solo entiende la primera:

```
salida/
  aldeano_bosque/               # pipeline de skin (lo que muestra el visor)
    caminar_lpc/                # 4 direcciones (estilo stardew)
      caminar_lpc_todas.gif     # la animación completa (una fila por dirección)
      caminar_lpc_S.gif  ... caminar_lpc_W.gif
      caminar_lpc.png           # hoja: una fila por dirección, una columna por cuadro
      caminar_lpc.json
    caminar_lpc_8dir/           # la MISMA animación en 8 dirs (estilo stardew8):
      caminar_lpc_todas.gif     # el sufijo _8dir va en la CARPETA; los archivos adentro
      caminar_lpc_SE.gif ...    # conservan el prefijo base (caminar_lpc)
      caminar_lpc.png
      caminar_lpc.json
  mago/
    neutra/  quieto/  caminar_lpc/  saltar/  agachar/  golpear/
  aldeano/                      # pipeline de ficha: FUERA DE ALCANCE
    stardew8/                   # (carpeta = estilo, archivos = pose)
      quieto.png  quieto_todas.gif  quieto_SE.gif ...
  _review/                      # copias para revisión humana: IGNORAR
  skins/mago/                   # layout viejo que no matchea: IGNORAR
  zonas/stardew8/               # informes de zonas (sin animaciones): IGNORAR
```

El JSON trae `frames` (atlas) y `meta` con los datos útiles:

```json
{
  "frames": [{"filename": "caminar_lpc_S_0", "frame": {"x":0,"y":0,"w":16,"h":32}, "duration": 100}],
  "meta": {
    "image": "caminar_lpc.png",
    "size": {"w": 128, "h": 128},
    "cell": {"w": 16, "h": 32},
    "fps": 10,
    "loop": true,
    "pivot": {"x": 8, "y": 30},
    "animations": {"S": ["caminar_lpc_S_0", "..."], "E": [], "N": [], "W": []}
  }
}
```

## Decisiones de diseño

1. **Web local con Python stdlib**: `visor.py` con `http.server`, HTML+CSS+JS embebido como string
   (sin build, sin archivos sueltos que se puedan perder). Se abre en el navegador.
2. **Descubrimiento por convención (solo pipeline de skin)**: una carpeta de animación es válida si:
   - `nombre_carpeta == prefijo`, donde `prefijo` sale de sus archivos (`<prefijo>_todas.gif` o
     `<prefijo>.png`), o
   - `nombre_carpeta == prefijo + "_8dir"`.

   La animación se nombra por el **prefijo de archivos**, no por la carpeta: `caminar_lpc/` y
   `caminar_lpc_8dir/` son dos entradas distintas (4 y 8 direcciones) y las dos se llaman
   `caminar_lpc`. Las carpetas del pipeline de ficha (`stardew8/` con `quieto.png`), `skins/` y
   `zonas/` no matchean y se ignoran. Tolerante a faltantes: si no hay `_todas.gif` se usa la hoja;
   si no hay JSON, se muestra igual sin metadatos.
3. **Re-escaneo por request**: `/api/personajes` relee el disco en cada llamada, así los renders
   nuevos aparecen con recargar la página; no hay caché de descubrimiento.
4. **Servir archivos con guard**: el endpoint de archivos solo permite `.gif`, `.png` y `.json`
   dentro de las raíces configuradas (anti path-traversal).

## Archivos a tocar

| Archivo | Acción |
|---|---|
| `visor.py` | nuevo |
| `tests/test_visor.py` | nuevo |

Nada más: **no tocar `sprites_lib/` ni `render_skins.sh`**.

## API y funciones

### `descubrir(raiz: Path) -> list[dict]`

Devuelve los personajes bajo `raiz`, orden alfabético. Personaje válido = carpeta con al menos una
animación válida. Animación válida = carpeta cuyo nombre es el prefijo de archivos (`<prefijo>/` con
`<prefijo>_todas.gif` o `<prefijo>.png`) o ese prefijo + `_8dir` (`<prefijo>_8dir/` con
`<prefijo>_todas.gif`). El nombre de la animación es el **prefijo de archivos** (`caminar_lpc`), no
el de la carpeta (`caminar_lpc_8dir`). Se ignoran las carpetas que empiezan con `_` y todo lo que no
matchee (pipeline de ficha, `salida/skins/`, `salida/zonas/`).

```python
{
  "nombre": "aldeano_bosque",
  "raiz": "salida",
  "animaciones": [
    {
      "nombre": "caminar_lpc",     # prefijo de los archivos
      "carpeta": "caminar_lpc",    # carpeta real: "caminar_lpc" o "caminar_lpc_8dir"
      "cuadros": 8,
      "fps": 10,
      "loop": True,
      "celda": {"w": 16, "h": 32},
      "direcciones": ["S", "E", "N", "W"],
      "gif": "salida/aldeano_bosque/caminar_lpc/caminar_lpc_todas.gif",   # o None
      "hoja": "salida/aldeano_bosque/caminar_lpc/caminar_lpc.png",       # o None
      "json": "salida/aldeano_bosque/caminar_lpc/caminar_lpc.json",      # o None
      "por_direccion": {"S": "salida/.../caminar_lpc_S.gif", "...": "..."}
    }
  ]
}
```

- `cuadros`: int por cuadro de la primera dirección en `meta.animations`; si no hay JSON, `None`.
- `fps` / `loop` / `celda`: de `meta`; `None` si no hay JSON.
- `direcciones`: claves de `meta.animations` (4 u 8 según el caso), en orden cenital
  (`S E N W` / `S SE E NE N NW W SW`); si no hay JSON, se derivan de los archivos `<prefijo>_<D>.gif`.
- Orden de animaciones: el de `sprites_lib.poses.POSES`
  (`neutra, quieto, caminar_lpc, saltar, agachar, golpear`); las desconocidas van al final,
  alfabéticas. La base va antes que su `_8dir`.

### Rutas HTTP

- `GET /` → HTML del visor.
- `GET /api/personajes` → `{"raices": ["salida"], "personajes": [ ... ]}`. En esta respuesta, cada
  path (`gif`, `hoja`, `json` y cada valor de `por_direccion`) viene ya como URL
  `/archivo/<ruta-relativa>` para que la UI las use directo.
- `GET /archivo/<ruta>` → sirve el archivo pedido (solo `.gif|.png|.json`, solo dentro de las
  raíces), `Cache-Control: no-store`. Fuera de las raíces o extensión no permitida → `404`.
- Cualquier otra ruta → `404`.

### CLI

```
.venv/bin/python visor.py [--raiz salida] [--raiz output] [--puerto 8765] [--no-abrir]
```

Por defecto: raíz `salida`, puerto `8765`, abre el navegador (`webbrowser.open`).
Si una raíz no existe, no es un error: se informa y se sigue con las demás. Si no hay nada para
mostrar, la UI lo dice con el comando sugerido (`./render_skins.sh`).

## UI

- Encabezado con `select` de **personaje** y `select` de **animación**, con contador `x/N`. Si hay
  versión de 4 y de 8 direcciones, se listan como dos opciones (indicando `4 dir` / `8 dir`).
- GIF grande centrado, sobre fondo a cuadros (para ver bien el pixel art).
- Vistas: `todas` (default) · por dirección (botones con las claves de `direcciones`) · hoja PNG
  completa.
- Línea de datos: `n` cuadros, `n` direcciones, fps, loop sí/no, celda `16×32`, ruta en disco.
- Teclado: `←/→` personaje anterior/siguiente, `↑/↓` animación anterior/siguiente,
  `g` alterna GIF/hoja, `r` recarga.
- Sin frameworks: HTML + CSS + JS vanilla.

## Casos borde

- Raíz vacía o inexistente → lista vacía y mensaje en la UI.
- Animación sin `_todas.gif` → se muestra la hoja.
- Animación sin JSON → se muestra igual, sin metadatos.
- Nombres con espacios o acentos → `encodeURIComponent` del lado del cliente y `unquote` del
  servidor.
- Petición de archivo fuera de las raíces (`/archivo/../../etc/passwd`) → `404`.
- GIF/PNG roto → placeholder sin romper la página.

## Tests (`tests/test_visor.py`, pytest rápido)

1. `descubrir()` con `tmp_path`: layout real de un personaje con `caminar_lpc/` y
   `caminar_lpc_8dir/` → dos animaciones con el mismo `nombre`, `carpeta` distinta y `direcciones`
   de 4 y 8; `cuadros`/`fps`/`loop` correctos.
2. `descubrir()` ignora `_review/`, `skins/`, `zonas/` y carpetas de estilo del pipeline de ficha
   (`stardew8/` con `quieto.png`).
3. `descubrir()` con raíz vacía → `[]`.
4. Animación sin `_todas.gif` → `gif is None` y `hoja` presente.
5. HTTP en puerto efímero (`server.server_port`): `GET /api/personajes` → 200 y el personaje
   esperado; `GET /` → 200.
6. `GET /archivo/../../etc/passwd` y `GET /archivo/<raiz>/x.txt` → 404.
7. `GET /archivo/<raiz>/<personaje>/<anim>/<anim>_todas.gif` → 200 con `Content-Type: image/gif`.

Correr: `.venv/bin/python -m pytest tests/test_visor.py -q`.

## Criterios de aceptación

- [ ] `.venv/bin/python visor.py` levanta y abre `http://127.0.0.1:8765`.
- [ ] Lista todos los personajes de `salida/` (hoy 11) y **no** muestra `_review`, `skins` ni `zonas`.
- [ ] `caminar_lpc` y `caminar_lpc_8dir` aparecen como dos animaciones (4 y 8 direcciones); las
      carpetas de estilo del pipeline de ficha (`aldeano/stardew8/`) no aparecen.
- [ ] Cambiar personaje/animación muestra el GIF correcto (probar las 6 animaciones de `mago`).
- [ ] `g` alterna GIF/hoja; los botones de dirección cambian la vista.
- [ ] `←/→/↑/↓` rotan personaje y animación.
- [ ] Un render nuevo (correr `./render_skins.sh`) aparece al recargar, sin reiniciar.
- [ ] `/archivo/../../etc/passwd` → 404.
- [ ] `pytest tests/test_visor.py -q` en verde.

## Convenciones para quien implemente

- Python siempre desde la raíz del repo: `.venv/bin/python ...`.
- Leer `AGENTS.md` antes de empezar. No agregar dependencias; si hace falta una, pedir aprobación.
- TDD: primero los tests de `descubrir()` y del guard de paths, después la implementación.
- No commitear nada fuera de los dos archivos de la tabla.

## Futuro (fuera de alcance)

- Botón que dispare `render_skins.sh` desde la UI.
- Comparar dos skins lado a lado.
- Grilla de miniaturas de todos los personajes.
- Unificar los dos layouts de `salida/` (pipeline de skin vs pipeline de ficha); hoy el visor solo
  entiende el de skin.
