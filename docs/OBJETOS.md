# Objetos sostenidos y puente de referencias

Roadmap de las ideas nuevas. Fase 1 implementada y testeada; fases 2 y 3 diseñadas, pendientes de aprobación.

## Fase 1 — Objetos con materiales (HECHO)

Componente `objeto` (`sprites_lib/componentes/objetos.py`): se engancha a `mano_derecha` / `mano_izquierda` y se
orienta con el antebrazo (`codo → mano`). Como la mano es un ancla que ya mueven **todos** los ciclos, el objeto
sigue la animación sin tocar el motor: blandir = reusar `golpear` sobre el brazo que lo sostiene.

Formas: `espada`, `hacha`, `antorcha`, `escudo`, `baston`.
Parámetros: `forma`, `largo`, `angulo`, `agarre` (`antebrazo` | `vertical`), y materiales opcionales
`mango`, `pomo`, `guarda`, `detalle`. `forma` y `agarre` se validan con `params_opciones` (nuevo en `Componente`).

Tests: `tests/test_componentes_objetos.py`. Ficha sintética: `apoyo.espadachin()`.

**Limitación observada:** de frente (`S`) el objeto colgado del brazo en reposo apunta hacia abajo y queda chico;
para un idle de arma hace falta una pose de "sostener" (brazo levantado) o un `angulo`. Es lo próximo a afinar.

## Fase 2 — Objetos con skin (DISEÑO)

La skin del objeto es **cilíndrica**, igual que el cuerpo envuelve un miembro: `x` del PNG = vuelta alrededor del
eje (`u`, 0.5 = frente), `y` = largo (`v`, 0 = base/mano, 1 = punta). El motor ya entrega `mat(dirs, t)` a las
cápsulas, así que el cuerpo principal de cada forma muestrea la skin directo.

Piezas a tocar:

1. `sprites_lib/skins_objeto.py` (nuevo): clase `SkinObjeto` con `zona(u, v)` y `paleta()` (nombres `sk_<hex>`,
   reusa `skins.material`).
2. `Componente.paleta_extra(spec)` (hook nuevo, default `None`): cada componente puede aportar materiales a la
   paleta. `armado.render_cuadro` mergea esos materiales en `ficha["paleta"]` **antes** de `paleta_estilo`, así
   la skin del objeto también recibe sombra/luz/contorno.
3. `Componente.validar(spec, materiales)` (hook nuevo, default `[]`): `Objeto` exige `skin` **o** `material`.
4. `Objeto.dibujar`: si hay `skin`, el cuerpo principal usa `mat(d, t)` de la skin; las partes auxiliares
   (guarda, pomo, mango) usan sus materiales o el color base de la skin.
5. Tests: la skin cambia los colores del objeto, el PNG de 16×16 se valida, y el objeto sigue enganchado.

## Fase 3 — Puente referencias → ciclos (DISEÑO)

Hoy el flujo es: descargar (`sprite-referencia`) → medir (`sprite-analizar`) → **cargar los números a mano** en
`ciclos.py` → gates. Lo que falta es el puente automático y el catálogo:

1. `analizar` → borrador de ciclo en el formato de `ciclos.py` (bob, pie, pie_ang, mano) a partir de la medición
   de huesos por cuadro. Ahorra la parte tediosa y deja el ciclo listo para `proceso_anim smoke`.
2. Catálogo de referencias con procedencia y licencia (LPC CC-BY-SA, OpenGameArt, itch.io, Sprite Database) para
   no mezclar material con copyright. Extiende el campo `creditos` de las fichas.
3. `proceso_referencia`: encadena descargar → separar → medir → borrador → `comparar_plantilla` → gates, con el
   mismo patrón VERDE/ROJO de `proceso_anim`.

El techo 3D (rotación de columna, multi-articulación) es un cuarto proyecto aparte: extender el modelo de pose
(poses 2D → frame por hueso) o importar keyframes de Blender/glTF. No entra en estas fases.
