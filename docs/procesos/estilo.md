# Proceso de estilo

Diseño: `docs/superpowers/specs/2026-09-29-procesos-estilo-animacion-skin-design.md` (§4).

## Cuándo usarlo

- Al sumar un estilo nuevo (vista, celda, proporciones, render, tonos) o al ajustar uno existente.
- Antes de animar: las animaciones y las skins se apoyan en el perfil del estilo.

## Pasos

1. Reunir 2+ referencias del mismo juego en `referencias/estilos/<juego>/`.
2. Medir sin escribir: `.venv/bin/python -m sprites_lib.proceso_estilo medir <estilo>`.
   Calibrar la comparación con un control (dos sprites reales entre sí; `sprites_lib/comparar_estilo.py`).
3. Volcar el perfil en `sprites_lib/estilos.py` y las celdas en `sprites_lib/escala.py`.
4. Validar: `.venv/bin/python -m sprites_lib.proceso_estilo validar <estilo>` (exit 0 VERDE / 1 ROJO).
   El gate corre: contrato numérico del muñeco (`proporciones.comparar`), determinismo del render, comparación
   con la referencia calibrada contra el espécimen declarado (`referencia.especimen`, si está) y deriva de las
   fuentes contra la última aprobación.
5. Iterar en autonomía hasta VERDE: **tope 3 vueltas propias**; si no converge, consultar con el estado y las
   opciones (no ajustar umbrales a ciegas).
6. Aprobar (única acción humana): `.venv/bin/python -m sprites_lib.proceso_estilo aprobar <estilo>`.
   Un gate ROJO no congela nada; excepcionalmente `aprobar <estilo> --excepcion "motivo"`.

## Qué congela

- `aprobados/estilos/<estilo>/`: `control.png` (comparativa referencia vs espécimen), `metricas.json` y
  `estado.json` (hash de `estilos.py` + `escala.py`; se escribe último, es la marca del congelado).
- Propone `docs/estilos/<estilo>.md` (medidas, reglas, trampas y umbrales) si todavía no existe.
- Si cambia el perfil o la escala, el hash no coincide y el gate da ROJO: hay que re-validar y volver a aprobar.
