---
name: sprite-isometrico
description: Crear personajes y animaciones pixel art isométricos con volumen real en 8 direcciones (SE, E, NE, N, NW, W, SW, S), construidos como muñeco 3D de primitivas (esferas, cápsulas, elipsoides, faldones) "fotografiado" a resolución de pixel art, con luz, 3 tonos por material, contorno por pieza y exportación PNG + JSON + GIF. Usar siempre que el usuario pida un sprite o animación "isométrico", "iso", "en diagonal", "tipo Diablo/FFT/Baldur's Gate", "en 8 (o 4) direcciones", "con perspectiva", o diga que un sprite isométrico se ve plano.
---

# Personaje isométrico con volumen

Antes de empezar, leer `CRITERIOS_ANIMACION.md` (secciones de isométrico, volumen y manos). La idea es la de los
sprites pre-renderizados de Diablo II: se modela en 3D con volúmenes simples y se "fotografía" desde el ángulo
isométrico (proyección 2:1). Dibujar líneas y polígonos 2D proyectados queda **plano**; no hacerlo así.

## Motor (`sprites_lib/render3d.py`)
- `Camara(mira, cw, ch, gx, gy)`: `mira` es una de las 8 direcciones. La cámara y la luz son fijas en el mundo, así
  la iluminación queda coherente entre direcciones. `cam_local` es el vector "hacia la cámara" en ejes del
  personaje (sirve para poner detalles del lado visible).
- `Escena(camara, paleta)`: ejes locales f = adelante, l = izquierda del personaje, u = arriba (≈ px).
  Primitivas: `esfera`, `elipsoide`, `capsula`, `faldon` (cono abierto adelante), `detalle` (1 px visible).
  El material puede ser un nombre o una función de la dirección (p. ej. cara/pelo/vincha sobre la cabeza).
  **Asignar `esc.pieza` antes de cada parte**: da contorno entre piezas distintas (puño y antebrazo, brazo y torso).
- `ik_sagital()` resuelve rodillas y codos; `sombra()`; `piso_iso()` sirve para el GIF de escena.

## Plantilla
`personajes/mago_iso.py`. Para un personaje nuevo, copiarla como `personajes/<nombre>_iso.py` y cambiar:
1. `ANATOMIA`: ~3–3,5 cabezas (cabeza grande para que la cara se lea), cadera al ~45% del alto, muslo = canilla,
   brazo ≈ antebrazo. Generar primero `--plantilla` y revisarla con el usuario.
2. `PALETA`: material → (sombra, base, luz). La mano tiene que ser un tono más clara que la piel, y los colores
   oscuros (pantalón, botas) no pueden estar cerca del contorno.
3. `construir(esc, ps)`: qué primitivas forman el cuerpo. Recetas:
   - casco o capucha = función de material sobre la esfera de la cabeza;
   - capa = `faldon` desde los hombros con `conservar=lambda d: d[...,0] < -.2` (solo atrás);
   - arma = `capsula` desde la mano en la dirección del antebrazo, con pieza propia;
   - pelo largo o rastas = cadenas de cápsulas con retraso (`ps["bob_prev"]`).
   Las extremidades conservan su lado (derecha l<0, izquierda l>0). En isométrico no se refleja medio ciclo.

## Generar
```bash
.venv/bin/python -m personajes.<nombre>_iso --plantilla             # anatomía
.venv/bin/python -m personajes.<nombre>_iso --anim correr --dir SE  # una dirección
.venv/bin/python -m personajes.<nombre>_iso --anim correr --dir todas
```
Sale en `salida/<nombre>_iso/<anim>/`: hoja PNG (una fila por dirección), JSON con `animations` por dirección y
pivote en los pies, GIF por dirección, `_todas.gif` y `escena_<dir>.gif` (corriendo sobre baldosas).

## Revisar (siempre, antes de entregar)
Ampliar cuadros clave (0, apertura máxima, cruce) ×10 y mirarlos con Read:
- ¿Se ve plano? → faltan volúmenes o los 3 tonos no se distinguen; revisar luz y paleta.
- ¿La cara está en sombra? → la luz tiene que venir del frente del personaje (en la dirección principal).
- ¿Se leen las manos? → pieza propia, radio mayor que el antebrazo, brazalete en la muñeca, brillo en los
  nudillos; en iso los puños no suben a la altura de la cara.
- ¿Los dos pasos son idénticos? → se intercambiaron las piernas; cada una tiene que conservar su lado.
- ¿Algún accesorio parece un globo? → a esta escala, radio ~1,5 alcanza.
Revisar también las 8 direcciones juntas (de frente, de espaldas y de costado). Abrir `escena_SE.gif` con
`xdg-open`.

## Entregar y anotar
Informar archivos, comandos y correcciones. Anotar lecciones nuevas en `CRITERIOS_ANIMACION.md`.
