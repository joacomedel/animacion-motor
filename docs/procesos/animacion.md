# Proceso de animación

Diseño: `docs/superpowers/specs/2026-09-29-procesos-estilo-animacion-skin-design.md` (§5).

## Cuándo usarlo

- Al sumar o ajustar una animación para un estilo ya aprobado.

## Pasos

1. Definir el movimiento como datos en `sprites_lib/ciclos.py` y registrarlo en `sprites_lib/poses.py`
   (n, fps, desfase, loop, `offset_y`, ancho).
2. Humo en una dirección (por defecto la primera del estilo, con la skin de zonas `skins/zonas.png`):
   `.venv/bin/python -m sprites_lib.proceso_anim smoke <anim> --estilo <estilo>`
   (opcional `--dir D` y `--skin RUTA`). Gate: `zonas` sin ALTA/MEDIA por revisar + `pulido` sin MAL.
3. Completo, todas las direcciones: `.venv/bin/python -m sprites_lib.proceso_anim validar <anim> --estilo <estilo>`.
   Gate completo: zonas, pulido, determinismo, deriva del ciclo, plantilla contra la referencia (si la animación
   la declara en `REFERENCIAS`) y fotos de control congeladas (si ya hay).
4. Iterar en autonomía hasta VERDE: **tope 3 vueltas propias**; si no converge, consultar con el estado y las
   opciones.
5. Aprobar: `.venv/bin/python -m sprites_lib.proceso_anim aprobar <anim> --estilo <estilo>`.
   Un gate ROJO no congela; excepcionalmente `--excepcion "motivo"`.

## Qué congela

- `aprobados/animaciones/<anim>/<estilo>/`: cuadros de control (`<anim>_<dir>_<cuadro>.png`), `metricas.json` y
  `estado.json` (último).
- Exporta la fuente con esa skin a `salida/animaciones/<anim>/<estilo>/` (hoja, JSON y GIF), disponible para el
  lote de skins.
