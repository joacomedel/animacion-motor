---
name: sprite-analizar
description: Capturar la anatomía y el movimiento de una animación existente píxel por píxel — paleta, proporciones (cabezas de alto, largo de huesos), rebote, trayectorias de pies y manos, fases del ciclo — y convertirlo en un ciclo reutilizable y en criterios anotados. Usar siempre que el usuario pida "analizar", "entender", "estudiar" o "capturar la anatomía/el movimiento" de un sprite o animación, basarse en cómo se mueve un personaje existente, o hacer algo "similar en movimiento" a una referencia.
---

# Analizar anatomía y movimiento de una referencia

El resultado de esta skill no es un dibujo: son **números y criterios** que después usan `sprite-2d-lateral`
y `sprite-isometrico`. Regla del proyecto: todo lo útil que se aprenda se anota en `CRITERIOS_ANIMACION.md`
(leerlo primero, porque puede que la animación ya esté analizada).

## 1. Medir automáticamente
La animación tiene que estar como tira horizontal de cuadros de igual tamaño (si viene de un sheet, primero usar
`sprite-referencia`).
```bash
.venv/bin/python -m sprites_lib.analizar <tira.png> <ancho_celda> <alto_celda> <carpeta_salida>
```
Imprime la paleta (colores y cantidad; el más usado suele ser el contorno), y por cuadro el bbox, el ancho
(apertura) y el pie más bajo (apoyos). También calcula el **rebote** (borde superior relativo). Guarda
`medidas.json` y `grilla_XX.png` (cuadros ×12 con grilla; las líneas amarillas van cada 5 px).

## 2. Leer articulaciones a ojo
Abrir cada `grilla_XX.png` con Read y anotar por cuadro, en coordenadas de la celda: cabeza (alto y ancho),
hombro, codo, mano o puño, cadera, rodilla, tobillo y punta del pie, para la extremidad cercana y la lejana.
Con eso calcular:
- **Proporciones**: alto total, cabezas de alto, torso, pierna (muslo/canilla), brazo (brazo/antebrazo), ancho.
- **Estructura del ciclo**: cuántos cuadros, cuántos pasos, y si la segunda mitad es la primera con los lados
  intercambiados.
- **Fases**: cruce, impulso, vuelo o máxima apertura, aterrizaje o contacto.
- **Trayectorias**: posición del tobillo por cuadro, extremos del puño adelante/atrás/cruce, rebote.
- **Detalles de estilo**: contorno interior sí/no, rampas de color, tamaño del puño, movimiento secundario.

## 3. Convertirlo en un ciclo reutilizable
Pasar las trayectorias al **rig lateral** del proyecto (x adelante, y abajo, piso y=34, cadera x=18). Si la
celda de la referencia tiene otra escala o posición, escalar y trasladar. Agregar el ciclo a
`sprites_lib/ciclos.py` siguiendo el formato de `CORRER` (`bob`, `pie`, `pie_ang`, `mano`, `desfase`, `n`, `fps`)
y sumarlo a `CICLOS`. Así cualquier personaje (lateral o isométrico) lo puede usar con `--anim <nombre>`.

## 4. Anotar criterios
Agregar una sección a `CRITERIOS_ANIMACION.md` con: fuente y fecha, formato, proporciones (tabla), tiempos y
estructura, trayectorias medidas y, sobre todo, **lecciones al replicarlo** (errores que aparecieron al usarlo
y cómo se corrigieron). Tomar como modelo la sección "Ciclo de correr — Mega Man X".

## 5. Validar
Generar un personaje con el ciclo nuevo y comparar lado a lado con la referencia (una fila arriba, otra
abajo, mismos cuadros, ×4). Revisar con Read que coincidan el ritmo, el rebote y la apertura.
