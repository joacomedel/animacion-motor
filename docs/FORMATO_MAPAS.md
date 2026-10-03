# Formato de mapas de superficie (normal map + material map)

Por animación, además de la tira PNG, la exportación genera dos mapas alineados (mismas celdas y pivote):

- `<nombre>_normal.png` — normal map RGBA. RGB codifica la normal en ejes de mundo: `N ∈ [−1,1] → [0,255]`
  (`pixel = (N + 1) × 127.5`). Alpha 0 donde no hay superficie (fondo transparente del sprite).
- `<nombre>_material.png` — material map RGBA. RGB es un color determinista por id de material.
  Alpha 0 donde no hay superficie.

Para `exportar_direcciones`, los mapas se generan por dirección: `<nombre>_<dir>_normal.png` y
`<nombre>_<dir>_material.png`.

## JSON

El JSON de metadatos incluye campos extra (retrocompatibles: el formato anterior sigue siendo válido):

- `meta.normal_map` — ruta del normal map (string en `exportar`, dict por dirección en `exportar_direcciones`).
- `meta.material_map` — ruta del material map (mismo formato).
- `meta.materiales` — mapa `id → nombre de material` (string de id como clave, nombre como valor).

## Uso

Los buffers provienen de `Escena.render(buffers=True)` (task-019) y se pasan a `exportar` /
`exportar_direcciones` mediante el parámetro `buffers` (lista por frame, o dict por dirección → lista por frame).
