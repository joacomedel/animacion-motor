# Clast — sprites

Pixel art estilo cenital 3/4, 4 direcciones (S, E, N, W). Fondo transparente, sin antialiasing.

| Animación | Hoja | Celda | Cuadros por dirección | FPS | Loop |
|---|---|---|---|---|---|
| caminar | `caminar/caminar.png` | 16×32 | 8 | 10 | sí |
| saltar | `saltar/saltar.png` | 16×32 | 6 | 10 | no |
| agachar | `agachar/agachar.png` | 16×32 | 4 | 8 | no (el último cuadro se sostiene) |
| golpear | `golpear/golpear.png` | 16×32 | 6 | 12 | no |

## Formato
- Cada hoja tiene una fila por dirección, en orden S, E, N, W.
- El `.json` sigue el formato hash de Aseprite/TexturePacker: posición y duración (ms) de cada cuadro, y en `meta.animations`
  la lista de cuadros por dirección.
- `meta.pivot`: punto de apoyo de los pies dentro de la celda (x=8, y=30). Es el mismo en todas las animaciones.
- `agachar/` y `golpear/` traen además `cuadros/<anim>_<dir>_<n>.png`: un PNG por cuadro (nombres iguales a los del JSON).
- Los `.gif` son solo para previsualizar.

## Salto
El sprite salta **en el lugar**: cambia la pose pero no sube dentro de la celda. La altura la aplica el motor con
`meta.offset_y` (px por cuadro, negativo = arriba): `[0, -4, -8, -4, 0, 0]`. Se puede escalar para un salto más alto.

## Golpear
Puñetazo con el brazo de metal (el izquierdo del personaje). Se ve mejor mirando al oeste (W); mirando al este (E) el brazo de metal queda del lado lejano y el torso lo tapa casi todo.

## Versión de 8 direcciones (`*_8dir/`) — estilo stardew8
Mismo look que las animaciones de arriba (cenital 3/4 estilo Stardew) pero con **8 direcciones**: S, SE, E, NE, N, NW, W, SW
(en el JSON, `meta.animations` las lista en ese orden; la hoja tiene una fila por dirección). No están espejadas: las 8 se
dibujan, porque Clast es asimétrico (brazo derecho de metal, izquierdo humano).
| Animación | Carpeta | Celda | Cuadros | FPS | Loop |
|---|---|---|---|---|---|
| caminar | `caminar_lpc_8dir/` | 20×32 | 8 | 10 | sí |
| agachar | `agachar_8dir/` | 18×32 | 4 | 8 | no (el último cuadro se sostiene) |
| saltar | `saltar_8dir/` | 18×32 | 6 | 10 | no (`meta.offset_y` para el motor) |
| golpear | `golpear_8dir/` | 24×32 | 6 | 12 | no |
Cada animación tiene el ancho de celda que necesita, por eso no son todas iguales; el pivote (`meta.pivot`) es propio de cada
una y está en el JSON. Cada carpeta trae además `cuadros/<anim>_<dir>_<n>.png` (un PNG por cuadro).
`golpear` pega con el brazo de metal (el derecho): se ve de perfil en E/NE (y en W/SW hacia el otro lado); de frente o de
espaldas el puño va hacia/desde la cámara y casi no se nota.
