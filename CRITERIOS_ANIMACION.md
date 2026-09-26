# Criterios de animación

Notas prácticas que se van acumulando al estudiar animaciones existentes.
**Regla:** cada vez que me base en una animación existente, la analizo píxel por píxel
y anoto acá lo útil (proporciones, tiempos, trayectorias, errores que cometí y cómo los corregí).

---

## Ciclo de correr — Mega Man X (SNES), `sprites_x/animaciones/04_correr.png`

Analizado el 2026-09-26. Aplicado en `mago/mago_correr.py`.

### Formato
- **10 cuadros**, celda de **34×35 px**, personaje mirando a la derecha, piso en y=34.
- **15 colores** en total, incluido el contorno `#181818`, que es el color más usado (1883 px).
  La armadura usa una rampa de 5 azules, del oscuro `#203080` al claro `#78d8f0`. La piel tiene
  3 tonos, los guantes 2 grises y hay acentos puntuales en amarillo y rojo.
- **Contorno oscuro también por dentro**: separa brazo, torso y pierna aunque se superpongan.
  Por eso conviene dibujar cada parte en su propia capa, con su propio contorno.

### Proporciones (estilo chibi, ~2,2 cabezas)
| Parte | Medida aprox. |
|---|---|
| Alto total | 33–35 px |
| Cabeza (casco + cara) | ~16 px de alto × ~12 de ancho → **casi la mitad del cuerpo** |
| Torso | ~10 px (hombro y≈15 → cadera y≈24) |
| Pierna (cadera → tobillo) | ~10–11 px; muslo ≈ canilla |
| Brazo (hombro → puño) | ~10 px; brazo ≈ antebrazo; puño 3–4 px |
| Ancho | 20 px (cruce) → 34 px (máxima apertura) |

### Tiempos y estructura
- **10 cuadros = 2 pasos.** Los cuadros 5–9 son los 0–4 con piernas y brazos intercambiados.
  Alcanza con diseñar medio ciclo y reflejarlo.
- Fases de cada paso: 0 cruce (piernas juntas bajo el cuerpo) → 1 despegue → 2 impulso atrás →
  **3 vuelo, máxima apertura** (ningún pie apoyado del todo) → 4 aterrizaje.
- **Rebote vertical**, medido en el borde superior de la cabeza: `1, 0, 1, 2, 2` por paso.
  Queda más alto en el despegue y más bajo en vuelo y aterrizaje. Son solo 2 px, pero sin eso
  el personaje parece deslizarse.
- Velocidad de reproducción sugerida: ~12 fps.

### Trayectorias medidas (coordenadas de la celda 34×35)
- **Tobillo de una pierna** a lo largo de las 10 fases:
  `(17,32) (13,32) (6,32) (4,22) (5,25) (11,28) (18,27) (24,26) (26,31) (22,32)`.
  Va para atrás pegado al piso, sube alto detrás (hasta y≈22), pasa por debajo con la rodilla
  arriba y vuelve a apoyarse adelante. La otra pierna es la misma curva desfasada 5 cuadros.
- **Puños**: el de adelante sube hasta ≈(28,15), cerca de la cara. El de atrás llega a ≈(8,13).
  En el cruce quedan a la altura de la cadera, ≈(20,20).
- **Brazos opuestos a las piernas**: cuando la pierna cercana va adelante, el brazo cercano va atrás.
- La cabeza casi no se mueve en x (≈17–27): todo el movimiento lo hacen las extremidades.

### Lecciones al replicarlo (errores que cometí y cómo los corregí)
1. **Codos siempre doblados (~90°).** Si la mano queda lejos del hombro, el brazo se estira y
   se ve como una barra horizontal cruzando el pecho. Conviene centrar la trayectoria de la mano
   cerca del hombro (±7 px en x) y subir el puño adelantado.
2. **Cadera alta.** Si la distancia cadera–piso es mucho menor que muslo + canilla, las rodillas
   se doblan demasiado y el personaje parece sentado. Conviene que la pierna casi estirada llegue al piso.
3. **Contraste entre capas.** La pierna y el brazo cercanos van más claros y los lejanos más oscuros.
   Si no, en 35 px se confunden con el torso.
4. **Pelo largo o capas**: si se dibujan como una masa sólida quedan como un casco. Hay que separar
   mechones con un tono más oscuro y darles un retraso de 1 cuadro respecto del rebote
   (movimiento secundario).
5. **IK de dos huesos** (cadera → rodilla → tobillo): define la pose con solo la cadera y el pie.
   La rodilla siempre se dobla hacia adelante y el codo hacia atrás.

### Checklist para un ciclo de correr nuevo
- [ ] Número par de cuadros; medio ciclo reflejado.
- [ ] Rebote de 1–2 px sincronizado con los apoyos.
- [ ] Cuadro de máxima apertura sin pies apoyados del todo.
- [ ] Brazos opuestos a las piernas y codos doblados.
- [ ] Capas cercanas más claras que las lejanas; contorno por capa.
- [ ] Movimiento secundario (pelo, capa, faldón) con 1 cuadro de retraso.

---

## Isométrico: correr hacia el sudeste (derecha-abajo)

Analizado el 2026-09-26. Referencias: `referencias/fft_ramza.png` (Final Fantasy Tactics) y
`referencias/isometric_hero/` (Isometric Hero de Clint Bellanger, CC-BY 3.0, 8 direcciones, 8 cuadros de correr,
celdas de 128×128, figura de ~50 px, baldosas de 64×32). Aplicado en `mago/mago_iso.py`.

### Qué cambia respecto de la vista lateral
- **"Hacia la derecha" en isométrico = sudeste** (diagonal abajo-derecha, se ve la cara) o noreste
  (arriba-derecha, se ve la espalda). El sudeste es el más común para mostrar al personaje.
- **Proyección 2:1**: avanzar 1 en el piso = 2 px a la derecha y 1 px abajo en pantalla. La profundidad se
  acorta (usé ×0.78 sobre el eje de avance) y el "arriba" sigue siendo vertical puro.
- **Vista 3/4 (FFT)**: se ven los dos hombros y los dos ojos. El torso se ve más ancho que de perfil y el pelo o
  la capa quedan hacia arriba-izquierda (noroeste), que es "atrás".
- **Cada extremidad conserva su lado**: la derecha queda más cerca de cámara (abajo-izquierda en pantalla y más clara)
  y la izquierda más lejos (arriba-derecha, más oscura). **No se puede reflejar medio ciclo como en perfil**: los
  cuadros 5–9 son distintos de los 0–4. Si se intercambian las piernas, los dos pasos salen idénticos (fue mi error).
- **La rodilla sube en vertical** en pantalla, mientras que el pie viaja por la diagonal.
- **Sombra en el piso**: una elipse aplastada 2:1 bajo la cadera, con dithering. Ancla visualmente al personaje
  mientras está en el aire.
- Método que funcionó: reutilizar el rig lateral (f = x, u = altura), agregar un eje lateral l por extremidad y
  proyectar. Las IK se resuelven en el plano lateral y después se proyecta.

### Volumen en isométrico (segunda versión: `mago/mago_iso3d.py`)
El primer intento (líneas y polígonos 2D proyectados) quedó **plano**. Lo que lo resolvió:
- **Construir con volúmenes, no con líneas** (Pixel Parmesan: meter cada parte en su "caja" isométrica).
  Usé esferas (cabeza, articulaciones), cápsulas (extremidades, rastas), elipsoides (torso, pelvis) y un
  tronco de cono abierto adelante (faldón). Es la técnica de Diablo II / sprites pre-renderizados, pero
  "fotografiada" directamente a resolución de pixel art con z-buffer.
- **Luz arriba + un costado**: cada cara del volumen recibe un tono distinto (3 tonos por material).
  Si la luz viene de atrás respecto de hacia dónde mira el personaje, la cara queda en sombra. Hay que
  mover la luz hacia el frente del personaje (usé L ≈ (f .4, l −.45, u .8)).
- **Contorno interior por salto de profundidad**: donde un píxel está >3 unidades detrás de su vecino
  se pinta de oscuro. Separa brazo, torso y pierna sin dibujar líneas a mano.
- **Detalles de 1 px al final** (ojos, runas, gemas, suelas), solo si el punto 3D es visible (z-buffer).
- **Accesorios chicos**: a esta escala, una hombrera de radio 2 ya parece un globo; con 1.5 alcanza.
  Los colores del pantalón no pueden estar cerca del contorno o la pierna desaparece.
- Plantilla usada (`mago/plantilla_anatomia.png`): ~3.3 cabezas, cadera al 45% de la altura,
  hombros 10.8 / caderas 4.6, muslo = canilla, brazo ≈ antebrazo.

### Manos (corrección del 2026-09-26)
Problema: las manos no se leían, porque brazo y mano formaban una sola mancha marrón. Causas y soluciones:
- **Cada pieza del cuerpo es una "parte" con contorno propio** (puño, antebrazo, torso, pierna, bota, cabeza,
  rastas). Donde dos partes distintas se tocan, se oscurece el píxel de la que queda detrás, aunque la
  diferencia de profundidad sea chica (> 0.8). Es lo que hace X: el puño tiene contorno aunque esté pegado al brazo.
  El contorno por salto de profundidad (> 3.2) solo no alcanza.
- **Mano = pieza separada, un poco más grande que el antebrazo** (radio 1.95 contra 1.35) y **un tono más
  clara**. A esta escala un puño necesita ~3–4 px para leerse (X usa guantes blancos de 3–4 px por el mismo motivo).
- **Algo que marque la muñeca**: un brazalete (acá dorado) pegado a la mano separa visualmente mano y antebrazo.
- **1 px de brillo en los nudillos** (el tono más claro, del lado de la cámara) define la forma del puño.
- **En isométrico no subir el puño a la altura de la cara** (en perfil sí, como X): la cara está en la misma
  diagonal y el puño la tapa. Bajé los puños ~2.5 px y los separé ~1 px del cuerpo hacia afuera.
- Checklist de manos: ¿se distingue el puño del antebrazo? ¿tiene contorno? ¿se ve en los cuadros de
  máxima apertura? ¿tapa la cara en algún cuadro?

### 8 direcciones (kit `sprites_lib/render3d.py`, 2026-09-26)
- Cámara y luz **fijas en el mundo**; lo que rota es el personaje (f, l dentro del piso). Así las 8 direcciones
  quedan iluminadas de forma coherente entre sí, como en un juego: de espaldas (N) el personaje queda más oscuro,
  y eso está bien.
- Orden de la hoja: SE, E, NE, N, NW, W, SW, S (una fila por dirección). El JSON trae `animations` por dirección.
- Con el modelo 3D, las direcciones nuevas no requieren redibujar: solo cambia `Camara(mira=...)`.

---

## Estilos (capa separada de personaje y movimiento)

Un sprite = **personaje** (`personajes/`) + **movimiento** (`sprites_lib/ciclos.py`) + **estilo**
(`sprites_lib/estilos.py`). El mismo muñeco 3D puede verse "pre-renderizado" o "Stardew" cambiando solo el estilo.

### Estilo Stardew Valley (analizado el 2026-09-26)
Referencias: `referencias/stardew/abigail.png` y `wizard.png` (The Spriters Resource, subidos por blargsnarf).
Aplicado en `personajes/mago_stardew.py` con el perfil `ESTILOS["stardew"]`.
- **No es isométrico**: es **cenital 3/4** (piso de grilla cuadrada, cámara arriba y adelante), 4 direcciones.
  Orden de la hoja: abajo (S), derecha (E), arriba (N), izquierda (W).
- **Celda 16×32**; figura de 26–27 px de alto, 14–16 de ancho.
- **Chibi**: cabeza ≈ 44% del alto, piernas ≈ 25%.
- **Contorno de color (selout)**: en Abigail, 0% del borde es negro. Usa el tono más oscuro de cada material
  (violeta oscuro para el pelo, marrón para las botas). El Wizard tiene borde oscuro porque su ropa es negra.
- **Sombreado plano**: casi todo en tono base, luz solo arriba-izquierda, sombra en pocos píxeles. Sin dithering.
  En el render: `umbrales=(.12, .82)` + luz más frontal. Con los umbrales de "volumen" (.28, .66) queda muy 3D.
- **Colores**: 20–30 por cuadro, saturados; sombras corridas a violeta y luces a amarillo.
- **Caminata de 4 cuadros**: neutro, paso, neutro, paso. En los pasos el cuerpo baja 1 px (alto 27, 26, 27, 26).
  Brazos con balanceo mínimo. ~7 fps.
- **Trampa del estilo**: la cara se dibuja casi de frente y grande aunque la cámara mire desde arriba. En el modelo
  3D eso se consigue agrandando la zona de "cara" sobre la esfera. Ojos de 2 px (blanco + iris de color).
- **Errores que corregí**:
  1. Cabeza = cúpula blanca sin cara → la región de piel era chica para una cámara que mira desde arriba.
  2. Rastas invisibles de frente → nacían adentro de la esfera de la cabeza. Tienen que arrancar por fuera
     del radio.
  3. Parecía pelado con vincha → falta pelo arriba: la vincha va fina sobre la frente y el pelo cubre la parte
     superior.
  4. Cara con volumen de "pelota" → luz más frontal y umbrales extremos.

### Por qué "se ve 3D" y cómo detectarlo solo (2026-09-26)
El usuario tuvo que decirme dos veces que se veía voluminoso. Ahora hay un protocolo (skill `sprite-estilo`, paso 5)
con métricas (`sprites_lib/comparar_estilo.py`) y una comparación visual ×14 (`sprites_lib/lado_a_lado.py`).
- **Lo que hace que un sprite "parezca 3D" no es tanto el sombreado sino**:
  1. **siluetas con curvas perfectas** (una esfera de cabeza se ve como pelota). Hay que usar cajas redondeadas;
  2. **superficies lisas sin detalle dibujado**. La referencia tiene más micro-detalle, no menos: grupos de color de
     1.9 px de media contra 3.4 en mi versión lisa, y 36 bandas cada 100 px contra 23;
  3. **tamaños de cara y cabeza que no son los del estilo**.
- **Mi intuición inicial era errónea**: pensé que Stardew tendría menos "ruido" que el render, y es al revés. Por
  eso conviene medir la referencia antes de suponer.
- **Calibrar métricas con un control** (dos sprites reales del mismo juego): la rectitud de la silueta y el ancho de
  la cabeza no discriminaban; el detalle (huérfanos, grupos de color, bandas) sí.
- **Bug encontrado gracias a la métrica "recorte"**: `np.roll` "da la vuelta" y el contorno de los pies (fila de
  abajo) aparecía en la fila de arriba. Se reemplazó por un desplazamiento sin vuelta en `render3d` y `pixel2d`.
- **Trampa de perfil**: de costado, la cara queda de canto y solo se ve pelo. Stardew corre la cara hacia el lado
  visible. Implementado: centro de la cara = normalizar(adelante + 0.9·hacia_cámara).
