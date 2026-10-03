# task-021 — Modelo de luces key/fill/rim + oclusión de contacto por estilo

**Estado:** pendiente
**Origen:** análisis del proyecto (2026-10-03).

## Contexto

Hoy hay **un solo término difuso** (`lam`, un único `luz` fijo por estilo) o, en stardew, un bevel de
pantalla sin normal (`sombreado="borde"`). Consecuencias:

- Todo lo que no da a la luz cae al **único tono sombra**: las formas se leen planas o sucias.
- No hay **rim/contraluz** para separar el personaje del fondo.
- No hay **oclusión de contacto**: el personaje no "apoya" sobre el piso ni sobre sí mismo.

## Criterio de aceptación

- El estilo puede declarar varias luces (mínimo: **key**, **fill**, **rim**) con dirección, color e
  intensidad; el sombreado las combina.
- **Rim**: un borde de 1 px del lado opuesto a la key, con el tono de luz, que separa del fondo.
- **Fill**: evita que todo lo no iluminado quede en el tono sombra.
- **AO de contacto**: oscurece donde dos piezas se tocan o donde el cuerpo toca el piso.
- Comparación antes/después por estilo (`stardew` y `volumen`) con capturas.

## Depende de

- task-019 (normal por píxel).

## Notas

- Mantener el look: cada estilo decide cuánto pesa cada luz; `stardew` debe seguir leyéndose plano.
- No cambiar el número de colores fuera de la paleta fija del estilo (task-017).
