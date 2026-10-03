# task-012 — Skins en tiempo real (daño, guante, arma)

**Estado:** completada (2026-10-03)
**Origen:** pedido original del motor (2026-10-02); confirmado en la revisión.

## Contexto

El objetivo del motor es alterar las skins en tiempo real sin pre-generar imágenes: representar
daño, poner una skin de guante sobre la mano, agregar armas. Con el renderer real (task-009) y la
caché (task-011), esto debería ser recomponer componentes sobre el muñeco y invalidar la caché de
las combinaciones afectadas.

## Criterio de aceptación

Cambiar una skin/componente en runtime se refleja en el render sin regenerar PNGs.
