# task-013 — Iluminación en tiempo real (feature opcional)

**Estado:** pendiente
**Origen:** pedido original del motor (2026-10-02); "posible feature".

## Contexto

El usuario pidió agregar como posible feature iluminación en tiempo real. Hoy la luz es estática
(`kz`, `luz` del estilo). La librería tiene `ik`/`Escena` con normales, así que una luz dinámica
es viable, pero encarece el render (choca con la caché de task-011).

## Criterio de aceptación

Decidir si entra al MVP o queda detrás de un flag; si entra, demostrar el efecto sin romper los FPS.
