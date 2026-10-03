# task-022 — Materiales con propiedades (specular, translúcido, rugoso) y texturas procedurales

**Estado:** pendiente
**Origen:** análisis del proyecto (2026-10-03).

## Contexto

Un material hoy es solo `{base}` + `emisivo`; `tonos(base, regla)` deriva sombra/base/luz y listo. No
hay forma de decir que el **oro/metal** refleja (specular), que el **cristal/agua** es translúcido, o
que la **tela/cuero/madera** tiene trama. El único aporte de textura es `_b` (un tono más oscuro) y la
veta del pelo en `componentes/humano.py`.

Además, `motor/equipo.py:MATERIALES` (cuero, metal, oro, tela, madera, fuego) está **desconectado del
kit**: duplica el concepto de material en vez de extenderlo.

## Criterio de aceptación

- Campos nuevos por material (default Neutro): `brillo`/`especular` (0..1), `transmision` (0..1),
  `textura` (nombre de patrón) o `rugosidad`.
- En el render: los metales dibujan un **highlight especular de 1 px** (usando la normal de task-019);
  los translúcidos mezclan con el fondo; la `textura` modula el material sin romper los 3 tonos.
- Unificar el catálogo: `motor/equipo.MATERIALES` extiende el del kit, no lo duplica.
- Test: un material con `brillo` alto gana píxeles más claros en la zona de reflexión; el número de
  colores sigue dentro de la paleta fija del estilo.

## Notas

- Reusar `Escena` (ya pasa `mat(dirs, t)` a las primitivas): la textura puede ser función `(dirs,t)`.
- Ver docs/OBJETOS.md fase 2 (skin de objeto) por si conviene absorberlo acá.
