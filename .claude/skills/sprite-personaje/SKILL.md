---
name: sprite-personaje
description: Crear un personaje nuevo del juego de forma consistente y con feedback frecuente del usuario — entrevista corta, ficha YAML con el porqué de cada decisión, boceto rápido para opinar, hoja de modelo con tests automáticos y fotos de control, y recién después animaciones. Usar siempre que el usuario describa un personaje ("quiero un robot con...", "haceme una bruja que..."), pida un personaje nuevo, quiera cambiar uno existente, o hable de fichas, hoja de modelo o consistencia de personajes, aunque no diga "skill".
---

# Personaje nuevo: entrevista → ficha → boceto → hoja → animaciones

El usuario quiere **ver algo rápido y opinar seguido**. No avanzar varias etapas solo: cada etapa termina
mostrándole algo y esperando su OK. Fichas de ejemplo: `personajes/fichas/mago.yaml`, `personajes/fichas/clast.yaml`.
Estilos por defecto: stardew (y lateral si hace falta perfil); volumen solo si lo pide.

## 1. Entrevista (corta)
Reflejar lo que ya dijo y preguntar **solo lo que falta**, en 1–2 tandas de `AskUserQuestion` (opciones cortas, una
recomendada). Temas: identidad/rol · silueta clave · cuerpo (clase de altura, complexión, piel, cabello) · ropa y
accesorios con su porqué · color identitario · estilos · referencias.
Objetar con conocimiento del kit: **escala** (en stardew la cara mide ~6 px y el ancho 16: accesorios de ≥2 px, ~3
legibles), **oclusión** (qué se tapa de perfil o de espaldas → `excepciones` con motivo), **elenco** (el color
identitario se tiene que distinguir de las fichas existentes), **componentes que no existen** (avisar que son trabajo nuevo).

## 2. Ficha
Escribir `personajes/fichas/<nombre>.yaml` y validar con `.venv/bin/python -m personajes.generar validar <nombre>`.
Resumen en una tabla corta → **pausa: OK del usuario**.

## 3. Boceto (rápido, antes de afinar nada)
`.venv/bin/python -m personajes.generar boceto <nombre>` → 1 imagen (frente y perfil, <1 s). Abrirla con `xdg-open`
y **preguntar qué cambiaría** antes de seguir. Si hacen falta componentes nuevos, primero una versión simple que
alcance para el boceto; el detalle viene después, con el feedback.
Iterar boceto ↔ feedback hasta que diga que le gusta la plantilla.

## 4. Hoja de modelo + tests
`.venv/bin/python -m personajes.generar hoja <nombre> --estilo stardew` (o el estilo pedido). Leer el resumen de la
consola y `informe.md`. Corregir la causa de cada ✗, pero **como máximo 2 vueltas propias**: si sigue fallando,
mostrarle el estado y las opciones (excepción documentada, cambio de diseño, seguir afinando) y que decida él.
Mostrar la hoja con `xdg-open` → **aprobación** → `.venv/bin/python -m personajes.generar aprobar <nombre> --estilo ...`
y commitear `personajes/aprobados/`.

## 5. Animaciones
Recién con la hoja aprobada (fase 2 del diseño: poses clave medidas en referencias con `sprite-analizar`).

## Ahorro de tokens
- Números antes que imágenes: leer el resumen de la consola; abrir una imagen con Read solo antes de mostrarla o
  cuando un número no alcanza para entender el problema.
- Un estilo por vez (`--estilo stardew`), no `todos`, mientras se itera.
- Tests del archivo tocado (`.venv/bin/python -m pytest tests/<archivo> -q`) y la suite completa solo al cerrar.
- Ajuste fino largo (muchas vueltas de métricas) → delegarlo a un subagente con modelo barato y un criterio claro de
  terminado; al contexto principal vuelve solo el resultado.
- Redirigir salidas largas a un archivo y leer la cola.

## Anotar
Lecciones nuevas → `CRITERIOS_ANIMACION.md` (breve).
