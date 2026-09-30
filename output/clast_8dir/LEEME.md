# Clast — paquete completo (8 direcciones)

Pixel art estilo Stardew Valley (cenital 3/4), fondo transparente, sin antialiasing. 8 direcciones (S, SE, E, NE, N, NW, W, SW),
todas dibujadas (no espejadas: Clast es asimétrico, brazo derecho de metal). Cada animación tiene el ancho de celda que necesita.

| Animación | Archivos | Celda | Cuadros por dirección | FPS | Loop | Pivote (pies) |
|---|---|---|---|---|---|---|
| caminar_lpc | `caminar_lpc.png` + `caminar_lpc.json` | 20×32 | 8 | 10 | sí | 10,30 |
| agachar | `agachar.png` + `agachar.json` | 18×32 | 4 | 8 | no | 9,30 |
| saltar | `saltar.png` + `saltar.json` | 18×32 | 6 | 10 | no | 9,30 |
| golpear | `golpear.png` + `golpear.json` | 24×32 | 6 | 12 | no | 12,30 |

- `clast.json`: índice con todo lo anterior (y `offset_y` de saltar).
- Cada `<anim>.png` es la hoja con **todos los cuadros**: una fila por dirección (orden S, SE, E, NE, N, NW, W, SW) y una columna por cuadro.
- Cada `<anim>.json` (formato tipo Aseprite/TexturePacker): `frames` con el rect y la duración (ms) de cada cuadro, y `meta`
  con `cell`, `fps`, `loop`, `pivot` y `animations[<dirección>]` = lista de cuadros de esa dirección.
- `saltar`: el sprite salta en el lugar; el motor aplica `meta.offset_y` (px por cuadro, negativo = arriba).
- `agachar`, `saltar` y `golpear` no se repiten (`loop: false`); en `agachar` el último cuadro se sostiene mientras dure la acción.
- `golpear` pega con el brazo de metal (derecho): se ve de perfil (E/NE y W/SW); de frente y de espaldas casi no se nota.
