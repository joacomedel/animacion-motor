# Estructura de carpetas de salidas

Referencia para no errarle al layout. Lo usan `render_skins.sh`, `render_armas.sh`, `sprites_lib.skins`,
`sprites_lib.proceso_skin` y el `visor/`.

## Regla base

```
<raíz>/<personaje>/<estilo>/<animación>/
```

- `<raíz>` = `salida/` (trabajo, ignorada por git) o `output/` (entrega del juego).
- `<personaje>` = **nombre de la skin** (ej. `caballero_carmesi`). Nunca se le agrega sufijo de arma, versión ni nada:
  el personaje es siempre el mismo.
- `<estilo>` = capa intermedia de render: `stardew` (4 dir), `stardew8` (8 dir), `lateral`, `volumen`.
- `<animación>` = nombre del ciclo/pose (`neutra`, `quieto`, `caminar_lpc`, `saltar`, `agachar`, `golpear`).

## Archivos dentro de la carpeta de animación

```
<raíz>/<personaje>/<estilo>/<anim>/
    <anim>.png            hoja (una fila por dirección, una columna por cuadro)
    <anim>.json           metadatos: frames (atlas) + meta (celda, fps, loop, pivote, animations)
    <anim>_todas.gif      GIF de todas las direcciones
    <anim>_<DIR>.gif      un GIF por dirección (S, E, N, W / + diagonales en stardew8)
```

El **prefijo de los archivos es igual al nombre de la carpeta de animación** (`golpear/` → `golpear_*`).
El visor descubre una animación válida si existe `<prefijo>_todas.gif` o `<prefijo>.png`.

## Variante con arma (objeto sostenido)

El arma es una **variante de animación del mismo personaje**, no un personaje nuevo:

```
salida/caballero_carmesi/stardew/golpear_espada/
    golpear_espada.png
    golpear_espada.json
    golpear_espada_todas.gif
    golpear_espada_S.gif  ... golpear_espada_W.gif
salida/caballero_carmesi/stardew8/caminar_lpc_espada/
    ...
```

Regla: `<anim>_<arma>` como nombre de carpeta y como prefijo de archivos; el `<personaje>` y el `<estilo>` no cambian.
Así el visor la lista como una animación más del mismo estilo (`estilo` = `stardew`, animación = `golpear_espada`).

## Cómo se genera

- Skin sin arma: `./render_skins.sh [--estilo stardew8] [--anim todas] [--entrega]`.
- Skin con arma: `./render_armas.sh [--arma espada] [--estilo stardew8] [--anim todas] [--entrega]`.
- Un solo caso: `python -m sprites_lib.skins juego <skin.png> --anim <anim> --estilo <estilo>` (sin arma)
  o `python -m sprites_lib.skins arma <skin.png> --arma <arma> --anim <anim> --estilo <estilo>` (con arma).

Ambos scripts son idempotentes: si la salida existe y es más nueva que el PNG de la skin, la saltean.

## Lo que NO se hace

- No crear carpetas de personaje tipo `<personaje>_<algo>` (ej. `caballero_carmesi_espada`): rompe el visor y la
  convención de "un personaje = una skin".
- No meter el arma en el nombre del personaje ni en el estilo.
- No escribir archivos sueltos en la raíz de `<personaje>/`: siempre dentro de `<estilo>/<anim>/`.
