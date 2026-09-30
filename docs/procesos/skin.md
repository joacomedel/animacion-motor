# Proceso de skin

Diseño: `docs/superpowers/specs/2026-09-29-procesos-estilo-animacion-skin-design.md` (§6).

## Cuándo usarlo

- Personaje nuevo pintado como PNG 32×32 (o heredado de otra skin), sobre animaciones ya aprobadas.

## Pasos

1. Pintar `skins/pintar_<nombre>.py` sobre `skins/guia.png` (o editar `skins/<nombre>.png` directamente).
2. Humo en `quieto` (la pose simple genérica): `.venv/bin/python -m sprites_lib.proceso_skin smoke <nombre>`
   (opcional `--anim X --estilo Y`; el default es `quieto`/`stardew`). Gate: el PNG carga y mide 32×32, más
   `zonas` y `pulido` de su ficha en esa pose y determinismo del render.
3. Iterar en autonomía hasta VERDE: **tope 3 vueltas propias**; si no converge, consultar con el estado y las
   opciones.
4. Aprobar: `.venv/bin/python -m sprites_lib.proceso_skin aprobar <nombre>` (ROJO no congela; excepcionalmente
   `--excepcion "motivo"`; una skin que no carga no se congela ni con excepción).
5. Lote: `.venv/bin/python -m sprites_lib.proceso_skin lote <nombre>` → recorre las animaciones aprobadas del
   estilo y les corre `zonas`, `pulido` y deriva del ciclo. Una animación ROJA no corta el lote: queda listada
   sin exportar y el exit es 1.

## Qué congela

- `aprobados/skins/<nombre>/`: hoja, `smoke.gif` (todas las direcciones de `quieto`), `metricas.json` y
  `estado.json` (último).
- El lote exporta a `output/<nombre>/<anim>/` y escribe el informe `salida/zonas/lote_<nombre>.md`
  (`--raiz` cambia la raíz de entrega).

Elenco: mismo pipeline por ficha + componentes, con el gate extra `tests_personaje`.
