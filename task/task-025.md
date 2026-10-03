# task-025 — Paleta fija por rampa de material (en vez de snap píxel a píxel)

**Estado:** pendiente
**Origen:** discusión posterior a task-017 (2026-10-03).

## Contexto

Task-017 aplica la paleta fija con `ajustar_paleta`, que mapea **cada píxel** al color más cercano en
Lab. Eso da coherencia entre sprites del mismo estilo, pero es **cuantización, no interpolación**:
bandea degradados, mata dithering y puede mandar los tres tonos de un material (sombra/base/luz) a
rampas distintas o a colores de otro material, aplanando el volumen (sobre todo en `volumen`).

La ganancia real no es "acercar cada píxel", sino que la paleta fija defina **rampas por material**: a
cada material del estilo le corresponde una terna (sombra, base, luz) dentro de la lista.

## Criterio de aceptación

- Asignar cada material del estilo a una **rampa de 3 colores** de la paleta fija (sombra/base/luz),
  preservando la estructura de 3 tonos y sin mezclar materiales.
- Dos personajes del mismo estilo comparten las rampas (misma propiedad de task-017).
- Comparación contra el snap actual (task-017) en `stardew` y `volumen`: menos bandeo, volumen
  preservado, misma cantidad o menos de colores.
- Decisión documentada de cómo se elige la rampa (por tono base del material, por nombre, declarada en
  el estilo).

## Relaciona

- task-017 (implementación actual), task-018 (aplicación en el motor).
