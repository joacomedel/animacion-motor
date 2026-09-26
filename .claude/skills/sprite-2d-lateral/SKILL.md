---
name: sprite-2d-lateral
description: Crear personajes y animaciones pixel art 2D planos en vista lateral (perfil, estilo plataformas tipo Mega Man/Metroid) con esqueleto e IK, reutilizando ciclos de movimiento medidos (correr, quieto, etc.), y exportarlos como PNG + JSON + GIF para cualquier motor. Usar siempre que el usuario pida un sprite, personaje o animación "de costado", "de perfil", "lateral", "2D plano", "tipo plataformas" o "como Mega Man", o una animación nueva para un personaje lateral existente.
---

# Personaje 2D lateral

Antes de empezar, leer `CRITERIOS_ANIMACION.md`. El movimiento sale de `sprites_lib/ciclos.py`; el diseño del
personaje es un archivo propio en `personajes/`.

## Plantilla
`personajes/mago_lateral.py` es la plantilla funcional (mago de rastas blancas y runas). Para un personaje nuevo:
1. Copiarla como `personajes/<nombre>_lateral.py` y cambiar `NOMBRE`.
2. **Celda**: `Lienzo(cw, ch, ox)`. El rig usa piso y=34 y cadera x=18; `ox` corre el personaje dentro de la
   celda (dejar lugar atrás para pelo o capa).
3. **Colores**: ~15 en total. Para cada material, base + sombra (más fría) + luz (más cálida); un color de
   contorno oscuro; un tono de "mano" más claro que la piel.
4. **Cabeza**: bloque ASCII (~12×12) mirando a la derecha, con leyenda char→color. La cabeza ocupa casi la mitad
   del alto (estilo chibi, ~2,2 cabezas) y así la cara se lee en ~35 px.
5. **Partes**: `pierna()`, `brazo()` (devuelve brazo y puño por separado), `cuerpo()`, `cabeza()`. Cada una
   dibuja en su capa (`L.capa()`) y termina con `contorno()`.
6. Orden de apilado: brazo lejano, puño lejano, pierna lejana, cuerpo, pierna cercana, cabeza, brazo cercano,
   puño cercano.

## Generar
```bash
.venv/bin/python -m personajes.<nombre>_lateral --anim correr
```
Sale en `salida/<nombre>_lateral/<anim>/`: `<anim>.png` (tira transparente), `.json` (celda, pivote en los pies,
fps y rect por cuadro), `.gif` y `_revision.png`.

## Revisar (siempre, antes de entregar)
Abrir `_revision.png` con Read y verificar:
- ¿Parece sentado? → la cadera está baja respecto de muslo+canilla; subirla o alargar las piernas.
- ¿Los brazos forman una barra horizontal? → la mano queda demasiado lejos del hombro; los codos tienen que
  quedar doblados (~90°).
- ¿Se distingue el puño del antebrazo? → puño en capa propia, 3×3 px, tono más claro y brillo en los nudillos.
- ¿Pierna o brazo cercano se confunden con el torso? → la extremidad cercana va más clara y la lejana más oscura.
- ¿Pelo o capa parecen un casco o un bloque? → separar mechones con un tono oscuro y darles 1 cuadro de retraso.
Corregir, regenerar y volver a mirar (suelen hacer falta 2 o 3 vueltas). Después abrir el GIF con `xdg-open`.

## Animaciones nuevas
Si el ciclo no existe en `CICLOS`, primero medirlo sobre una referencia con `sprite-analizar`. En perfil se puede
reflejar medio ciclo (la pierna A es la cercana en la primera mitad); en isométrico no.

## Entregar y anotar
Informar archivos, comandos y qué se corrigió en cada vuelta. Anotar en `CRITERIOS_ANIMACION.md` cualquier
lección nueva.
