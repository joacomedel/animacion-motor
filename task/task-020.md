# task-020 — Iluminación dinámica real en el motor (luces puntuales/radiales sobre las normales)

**Estado:** pendiente
**Origen:** análisis del proyecto (2026-10-03). Extiende/supera task-013.

## Contexto

La "iluminación en tiempo real" de task-013 (`motor/renderer.py:capa_ambiente`) es un **tinte plano
de pantalla**: un `Surface.fill(color_con_alfa)` sobre toda la vista. No usa la normal, ni la distancia
a una fuente, ni deja sombras: no distingue una cara que da a la luz de una que no.

El kit ya trae normal por píxel (una vez hecha task-019) y el motor tiene una antorcha con material
emisivo (`motor/equipo.py:ITEMS["antorcha"]`) que hoy **no ilumina** el entorno.

## Criterio de aceptación

- Una luz con **posición, color, radio e intensidad** ilumina por píxel usando el buffer de normal del
  frame cacheado: `factor = max(0, N·L) * caida(distancia)`, multiplicado sobre el color del sprite.
- No se re-renderiza 3D por frame: se re-ilumina sobre los buffers cacheados (task-019).
- Demo en `motor/main.py`: una antorcha que ilumina su alrededor y se mueve con el personaje.
- Medir FPS: la re-iluminación no debe romper el objetivo de fluidez (comparar contra el tinte plano).

## Depende de

- task-019 (buffer de normal por frame).

## Notas

- El tinte plano puede quedar como caso barato (ambiente global) y las luces puntuales sumarse encima.
- `motor/*.py` estaba con cambios sin commitear al escribir esta task: coordinar antes de tocar.
