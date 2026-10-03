# task-017 — Paleta fija compartida por estilo

**Estado:** pendiente
**Origen:** pedido del usuario (2026-10-03): "tener paleta de colores y que los colores que salgan siempre
correspondan a esa paleta". Alcance elegido: **por estilo, compartida** (cada estilo tiene su lista y todo
sprite de ese estilo sale de ahí).

## Contexto

Hoy la paleta se **deriva por personaje**:

- `paleta.paleta_estilo` (`paleta.py:32`) toma el color base de cada material en la ficha y aplica el
  corrimiento de tonos del estilo → 3 tonos por material, distintos en cada personaje.
- `paleta.reducir_paleta(por_dir, n)` (`paleta.py:57`) **cuantiza una hoja** a ≤ `n` colores uniendo los
  pares más parecidos en Lab, pero **conservando el más usado: nunca inventa**. El tope sale de
  `render.paleta_max` (stardew8=28, fry8=16) y se aplica por animación en `skins.py` y `proceso_skin.py`.
- `tests_personaje.t_paleta` valida que todo color renderizado pertenezca a la paleta *del personaje*.

Consecuencia: dos personajes del mismo estilo **no comparten RGBs exactos**, y la reducción por animación
puede dejar paletas levemente distintas entre animaciones del mismo personaje.

## Fix propuesto

1. Lista fija por estilo: `ESTILOS[estilo]["render"]["paleta_fija"] = ["#rrggbb", ...]` (opcional; si falta,
   todo sigue como hoy).
2. `paleta.ajustar_paleta(por_dir, colores)`: mapea cada píxel opaco al color más cercano de `colores`
   (distancia Lab, reusando `_lab`). A diferencia de `reducir_paleta`, el mapeo es por píxel contra una lista
   fija → determinista e idéntico sin importar cómo se agrupen animaciones/direcciones.
3. Aplicarla en el camino de exportación (`skins.salida_juego`, `proceso_skin`) cuando hay `paleta_fija`,
   idealmente antes o en lugar de `reducir_paleta`.
4. Extender `t_paleta` para que, con `paleta_fija`, exija pertenencia a esa lista (test que falla si no).
5. Opcional: derivar/afinar los tonos de la ficha hacia la paleta (snap del base) para evitar banding.

## Decisiones

- **De dónde salen los colores**: buscados por internet (pedido del usuario). Stardew no tiene paleta global
  oficial (cada sprite usa la suya), así que se usan paletas curadas de Lospec que emulan ese look:
  - `stardew` / `stardew8` → **PLOT50** (top-down cozy, rampas ordenadas), 50 colores.
  - `volumen` → **Resurrect 64** (dark fantasy RPG, Kerrie Lake), 64 colores.
  - `fry8` → los **14 colores medidos** de `referencias/8dir/fry_40x64` (coincide con el criterio).

## Implementación (2026-10-03)

- `estilos.py`: constantes `PALETA_PLOT50` / `PALETA_RESURRECT64` / `PALETA_FRY14` y `render.paleta_fija`
  en cada estilo (stardew8 hereda de stardew; fry8 la sobreescribe).
- `paleta.ajustar_paleta(por_dir, colores)`: mapeo por píxel al color más cercano en Lab, con caché.
- `skins.ajustar_a_paleta_fija(por_dir, estilo)`: si hay `paleta_fija` ajusta y no reduce; si no, reduce
  por `paleta_max` como antes. Lo usan `skins._por_dir_ficha` y `proceso_skin._por_dir_quieto`.
- Test: `tests/test_paleta_fija.py` (8 casos). Suite completa: 277 passed.
- Evidencia visual (aldeano, stardew quieto S/E): 42 colores derivados → 17 de PLOT50, todos dentro de la lista.

## Criterio de aceptación

- [x] Test que falla sin el mecanismo y pasa con él: con `paleta_fija` todo color opaco ∈ lista.
- [x] Dos personajes distintos del mismo estilo comparten la misma paleta.
- [x] Con `paleta_fija` ausente, el comportamiento no cambia (suite verde).
- [ ] PR (pendiente). Ver task-018 para el motor en vivo, que hoy no aplica la paleta fija.
