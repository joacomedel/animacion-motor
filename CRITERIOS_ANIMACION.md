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

## Plantilla de caminar — LPC (medida el 2026-09-27)
Fuente: cuerpo base masculino de LPC (`referencias/caminar/`, CC-BY-SA/GPL: **solo referencia de movimiento**, no se
copian píxeles). Celda 64×64, 9 cuadros (0 parado + 8 de ciclo), filas N W S E, vista 3/4 con cabeza chibi (45 % del
alto, 46 px en total). Marcas por cuadro en `referencias/caminar/lpc_E_huesos.json`; ciclo en `ciclos.CAMINAR_LPC`.

- **Cómo se midió**: cada cuadro pasado a mapa de colores en texto (una letra por color) → coordenadas exactas sin
  gastar imágenes. Cercano/lejano se separan por tono: LPC pinta más oscuras las extremidades lejanas. Rodillas y
  codos no se marcan: salen de la IK, igual que en nuestro muñeco.
- **Estructura**: 8 cuadros, desfase 4 (segunda mitad = primera con las piernas cambiadas). Baja 1 px al apoyar
  (cuadros 0 y 4), pie en el piso 6 de 8 cuadros, levanta ~2 px al cruzar, paso ≈ 0,85 del largo de pierna, mano ±5 px
  opuesta a la pierna. LPC no es simétrico en los cruces: la plantilla promedia las dos mitades.
- **Verificación** (`python -m sprites_lib.comparar_plantilla`, test `test_comparar_plantilla`): el muñeco en el estilo
  `lpc` (solo verificación: mismo alto y celda) se mide contra la referencia: huesos (error medio ≤ 2 px) y silueta
  (IoU, informativa ≥ 0,65; las proporciones son nuestras, más finas que LPC).
- **Errores corregidos al replicarlo**:
  1. La cámara cenital separa verticalmente los lados cercano/lejano (hombros 6 px, caderas 3 px); en el perfil de LPC
     los dos pies pisan la misma línea → para comparar de perfil usar cámara lateral.
  2. El muñeco medía 3 px más que `adulto_px`: el contorno y el pie redondo suman altura bajo el piso y arriba.
     Compensado en el estilo `lpc` (alto 43, pie a 5 px del borde). Revisar si pasa lo mismo en stardew.
  3. La mano no sigue un seno: va rápido hacia atrás en el cruce → mano medida cuadro a cuadro (`mano.xy`).
  4. `escala_rig` no es 1: una unidad del rig mide 0,82 px en `lpc`. Convertir las medidas con ese factor.
- **Trampa de LPC que no copiamos**: el hombro cercano está 4 px atrás del centro del torso y el lejano 4 px adelante,
  por eso el brazo lejano "sale del pecho". Nuestros hombros van en su lugar: la mano lejana queda fuera de la meta.

## Plantilla de salto — Mega Man X (boceto, medido el 2026-09-27)
Fuente: `sprites_x/animaciones/06_saltar.png` (SNES, celda 35×46, piso y=45, solo referencia de movimiento). 6 cuadros,
sin repetición (no es cíclico como caminar/correr). Ciclo en `ciclos.SALTAR`, pose nueva en `poses.POSES["saltar"]`.

- **Cómo se midió**: `python -m sprites_lib.analizar` sobre la tira → bbox y "rebote" (borde superior relativo) por
  cuadro: `[9, 0, 0, 4, 5, 14]`. Confirmado a ojo con `grilla_00.png`/`grilla_05.png`: 0 agachada (anticipación,
  pies en el piso), 1–2 despegue y pico (piernas se recogen, sube el cuerpo entero), 3–4 caída (piernas se abren y
  después se estiran buscando el piso), 5 aterrizaje (agachada más profunda que la de salida: amortigua el golpe).
- **El sprite NO se traslada verticalmente (decisión de diseño, 2026-09-27)**: la altura del salto la pone el
  motor del juego, no el dibujo. `bob` en `SALTAR` nunca es negativo (0 = altura de parado, + = agachado): en el
  aire el cuerpo se dibuja **a la altura de parado**, solo cambia la pose (piernas que se recogen/estiran, brazos
  que suben), como si algo sostuviera al personaje. Solo agachada (cuadro 0) y aterrizaje (cuadro 5) bajan el
  cuerpo de verdad, porque ahí los pies siguen en el piso.
  - Motivo: con `bob` negativo (versión anterior) la cabeza subía por encima de la de parado y en los cuadros de
    pico llegaba a tocar el borde superior de la celda de 32 px (13 px opacos en la fila 0) — cortaba la cabeza.
    Con `bob` acotado a `[0, +∞)` la cabeza de parado es el techo real y siempre queda ≥1 px de margen arriba
    (verificado con `test_animaciones_juego.py`, que corre esto para **todas** las animaciones y estilos activos,
    no solo salto).
  - La sensación de "subir" en el aire la da la pose (piernas recogidas en el pico = cuerpo más chico, se separa
    del piso visualmente) más el `offset_y` que se le pasa al motor (ver abajo), no un desplazamiento del dibujo.
- **`offset_y` (meta del JSON, para el motor)**: cuánto tiene que levantar el motor el sprite completo por cuadro,
  en px de juego, negativo = arriba. Se guarda en `ciclos.SALTAR["offset_y"]` y sale en el JSON exportado
  (`sprites_lib.poses.offset_y(anim)`). Para `saltar`: `[0, -4, -8, -4, 0, 0]` — 0 en los cuadros que tocan el piso
  (agachada y aterrizaje), más negativo en el pico. Caminar/quieto no llevan `offset_y` (el piso no se mueve).
- **`loop` (meta del JSON, por animación, no por estilo)**: caminar/quieto/correr son cíclicos (`loop: true`);
  saltar se juega una sola vez (`loop: false`). Se lee de `ciclos.<CICLO>["loop"]` vía `sprites_lib.poses.loop(anim)`;
  antes `exportar.py` lo tenía fijo en `True` para todo.
- **`pivot` (meta del JSON, por estilo, no por animación)**: punto de los pies dentro de la celda. Sale de
  proyectar el ancla `suelo` (origen del mundo, no se mueve con la pose) con `armado.pivote(estilo)` — da el mismo
  punto para cualquier pose/dirección/personaje de ese estilo (stardew: `(8, 30)` en celda 16×32; lateral: `(20, 38)`
  en celda 40×40). Antes `demo()`/`muneco.demo()` no lo pasaban y quedaba `null` en el JSON.
- **No cíclico → sin desfase**: las dos piernas van juntas (mismo tiempo, sin cruce), así que `desfase=0` y la
  misma `pie`/`mano` sirve para ambas piernas/brazos (antes, en caminar, el desfase corría la misma curva medio
  ciclo para simular la pierna contraria).
- **Verificación (liviana, es un boceto)**: no se armó un comparador de huesos nuevo (eso implicaría un estilo de
  verificación con la proporción y celda exactas de Mega Man X, como se hizo para LPC). En cambio:
  1. Forma de la curva de altura: "rebote" (borde superior relativo) de nuestro propio muñeco vs. el medido en la
     referencia — nuestro `[8, 0, 0, 0, 4, 10]` contra `[9, 0, 0, 4, 5, 14]` (con el `bob` viejo, antes de sacarle
     la traslación del cuerpo; ahora esa forma la debe reproducir `offset_y` + pose, no el render).
  2. `test_animaciones_juego.py::test_ningun_cuadro_toca_el_borde_superior`: ningún cuadro de ninguna
     animación/estilo activo tiene píxeles opacos en la fila 0 de la celda.
- **Errores corregidos al calibrarlo**:
  1. Primer intento: copiar el `bob` medido de la referencia directo en px de la referencia (hasta 14) sin revisar
     la escala del rig → con `pie` cerca del piso en el aterrizaje, la cadera calculada quedaba **por debajo del
     tobillo** (pierna invertida). Se corrigió midiendo la cadera y el tobillo proyectados de nuestro propio
     muñeco (`render_cuadro(...).anclas_px`) para cada `bob`/`pie` candidato y ajustando hasta que
     `tobillo_y - cadera_y` fuera siempre positivo y ≤ muslo + canilla (~9 px en `lateral`).
  2. `bob` y `pie` usan factores de escala distintos (`.9*esc` contra `escala_rig`): no se puede mezclar el mismo
     número de px para los dos sin convertir.
  3. Segundo intento: `bob` negativo en vuelo (para simular la altura del salto en el propio dibujo) cortaba la
     cabeza contra el borde de la celda en stardew (32 px de alto). Se sacó la traslación del cuerpo del ciclo y
     se movió a `offset_y` (responsabilidad del motor, no del sprite).

### Checklist para un salto nuevo
- [ ] `bob` nunca negativo: en el aire, como mucho la altura de parado (0); agachado (+) solo cuando los pies
      tocan el piso.
- [ ] La sensación de altura va en `offset_y` (meta del JSON), no en el dibujo.
- [ ] `pie` sí puede recogerse mucho en el aire (rodillas arriba) sin romper la pierna: verificar cadera por
      encima del tobillo y que no se pase de muslo + canilla.
- [ ] `loop: false` en el ciclo si no se repite; `pivot` sale solo de `armado.pivote(estilo)`.
- [ ] Ningún cuadro exportado toca la fila 0 de la celda (correr `test_animaciones_juego.py`).

## Plantilla de agachar — boceto propio (2026-09-28)
Sin referencia externa: pose diseñada a mano a partir de la agachada de `ciclos.SALTAR` (cuadro 0). Ciclo en
`ciclos.AGACHAR`, pose en `poses.POSES["agachar"]`. 4 cuadros, `loop=False` (se agacha una vez y se queda; el
motor sostiene el último cuadro mientras dure la acción, igual que en `saltar`), sin `offset_y` (los pies no se
despegan del piso).

- **`bob` final 7** (`[0, 3, 6, 7]`): con tope 4 (primera versión) el usuario lo vio "agachado muy poco". Con 7 la
  cabeza baja ~8 px en lateral (40 px de celda) y ~6 en stardew, y sobre Clast (remera larga + piernas robóticas) se
  lee bien. Con 9-11 el torso queda casi sobre los pies y se pierde la pierna. Sobre el muñeco desnudo, ver abajo.
- **Probar primero con el muñeco base (`sprites_lib.muneco`, piel lisa, sin ropa) casi no sirve para juzgar una
  pose con la rodilla muy doblada**: sin una prenda o componente que separe muslo de canilla, el contorno de las
  dos cápsulas superpuestas se ve como un zigzag/garabato aunque la geometría (cadera por encima del tobillo,
  huesos sin estirarse) sea correcta. Con la ficha real (Clast: `remera_larga_rota` tapa la cadera, piernas
  `pierna_robotica` con `juntas` de color en la rodilla) la misma pose se lee bien. **Conclusión: para poses con
  la pierna muy doblada, juzgar la legibilidad sobre un personaje vestido (o con junta marcada), no sobre el
  muñeco desnudo.**
- **El ángulo del pie (`pie_ang`) rompe el dibujo antes que `bob`**: en el muñeco desnudo, con `bob=0` fijo, ya
  con `pie_ang=10` la rotación del pie se superpone visiblemente con la canilla. Mantener `pie_ang` chico (≤10)
  para agachado quieto; ángulos grandes (20-30, como en `saltar`) son para cuadros de paso rápido, no para
  sostener.
- **Verificado en los dos estilos activos** (no solo el que use `--estilo` por defecto de `skins.py`, que es
  `stardew`): en `lateral` se lee el doblez de rodilla de perfil; en `stardew` (cenital) se nota menos pero no
  rompe. `sprites_lib/skins.py juego`/`demo` no tienen `--estilo` en la CLI (queda fijo en `stardew`); para
  otro estilo, llamar `salida_juego(ruta, anim, estilo)` directamente en Python.

### Checklist para un agachado nuevo
- [ ] `bob` final ~7 (4 se ve poco; 9+ aplasta el cuerpo). Medir la fila más alta de cada cuadro para cuantificar.
- [ ] `pie` casi fijo cerca del piso; dejar que la rodilla se doble sola vía IK al bajar la cadera (no achicar
      `pie` en y además de subir `bob`: duplica el efecto).
- [ ] `pie_ang` chico (≤10) si el cuadro se sostiene; ángulos grandes se ven mal sostenidos varios cuadros.
- [ ] Revisar la pose sobre la ficha del personaje real (con ropa/junta), no solo sobre el muñeco desnudo.
- [ ] `loop: false`, sin `offset_y` (no se despega del piso); `test_animaciones_juego.py` en verde.

## Plantilla de golpear — boceto propio (2026-09-28)
`ciclos.GOLPEAR` (6 cuadros, `loop=False`): preparación hacia atrás, golpe, extensión sostenida, retorno. Nuevo: un
ciclo puede llevar `mano_b`, `pie_b` y `pie_ang_b` propios (antes el brazo/pierna B era la misma curva desfasada).

- **Error: pega con el brazo equivocado.** Se asumió por lectura de código que `mano_a` es el brazo izquierdo (el de
  metal de Clast) y no se comprobó en imagen cuál brazo sale en cada dirección. El usuario vio que pegaba con el otro.
  Qué tenía que considerar:
  1. Con una animación asimétrica (un brazo hace algo distinto al otro) **verificar en imagen, por dirección, cuál
     extremidad es cuál** antes de exportar. Cuál es el brazo cercano cambia con la dirección (E/W) y el lado que
     ve la cámara.
  2. El personaje tiene un brazo con rol propio (Clast: izquierdo = prótesis completa, derecho = muñón sin
     antebrazo). Un golpe con el brazo amputado no tiene mano: la ficha manda qué brazo puede golpear.
  3. Revisar las **4 direcciones antes de exportar** (solo miré lateral E y la hoja recién después de escribir en
     `output/`). En E el brazo lejano queda tapado por el torso: elegir dirección de lectura o brazo según eso.
- **Checklist para animaciones asimétricas**: [ ] leer la ficha (qué brazo/pierna tiene qué rol) [ ] hoja de las 4
  direcciones ampliada, con el cuadro de mayor extensión [ ] confirmar el brazo/pierna activo mirando el material
  (metal vs piel) [ ] recién ahí exportar a `output/`.

## Estilo `stardew8` — Stardew en 8 direcciones, sin volumen (2026-09-28)
Mismo perfil que `stardew` (cenital 3/4, sombreado plano, contorno de color, celda 16×32) + las 4 diagonales
(SE, NE, NW, SW), pensado para peleas en plano isométrico. `render3d.DIRECCIONES_CENITAL` ahora incluye las
diagonales (vector ±0,7071). No está en `ACTIVOS`: `stardew` (4 dir.) sigue siendo el de las fichas y `output/`.
- Primera prueba con `caminar_lpc` y la skin de Clast: las 8 direcciones se leen; las diagonales muestran bien
  los dos hombros y la cara de 3/4. Ancho usado: hasta la columna 15 de 16 (SE/NE llegan a la 0): **sin margen**.
  Si se agrega arma o brazo extendido (golpear) habrá que ensanchar la celda a 20-24 px.
- Salida: `output/clast/caminar_lpc_8dir/` (`skins.py juego ... --estilo stardew8 --output`).
- **Correcciones de `stardew8` tras la primera prueba (2026-09-28)**: (1) *Ojos en SE/SW*: con la fuerza de cara de los
  perfiles (.55) la cara queda casi de frente y los dos ojos se ven iguales y las cejas forman una barra; se agregó
  `proporciones["cara_diagonal"]=.2` (`cuerpo.fuerza_cara`): el ojo cercano queda entero y el lejano de costado.
  (2) *Cabeza*: la caja giraba con la cámara y medía distinto por dirección; `cabeza_pantalla` (`cuerpo.giro_cabeza`,
  `Escena.caja(giro=)`) la alinea a la pantalla: 11×12 px en las 8 direcciones (medido con la plantilla de zonas).
  (3) *Ancho por animación*: `ciclos.<CICLO>["ancho"]={"stardew8": N}` (`poses.ancho`); se mide con
  `python -m sprites_lib.muneco ancho --anim X --estilo stardew8` → caminar 20, saltar/agachar/quieto 18, golpear 24.
  El pivote se calcula por animación (`armado.pivote(estilo, pose=anim)`).
- **Plantilla de zonas** (`python -m sprites_lib.muneco zonas --anim X --estilo stardew8` → `salida/muneco/`): el muñeco con
  un color por parte (derecha cálidos, izquierda fríos). Revisar SIEMPRE con ella antes de aplicar una skin.
- **No se espeja**: las 8 direcciones se renderizan (Clast es asimétrico). Para gastar pocos tokens: medir en números
  (bbox de cabeza, ancho necesario) y mirar una sola hoja con las 8 filas × 4 cuadros en vez de imágenes por dirección.
- **Ajuste de diagonales con referencias (2026-09-28)** (`referencias/8dir/`: Witch CC-BY, TheNess CC0, Fry CC0; hoja
  `comparativa.png`): las referencias angostan la cabeza ~2 px en 3/4, corren la cara hacia donde miran y dibujan un solo
  ojo o el lejano de 1 px. En `stardew8`: `cabeza_diagonal=.85` (cabeza 11 px en diagonal contra 13 de frente/espalda,
  medido con ojos y orejas incluidos), `cara_diagonal=0.0`, `cabeza_desvio` por diagonal (SE .9, NE -.2, SW -1.0, NW .1 px) →
  desvío cabeza-torso final SE +.6, NE +.7, NW -.7, SW -.9 (simétrico). Medir con componentes (`tests_personaje.mascara`),
  no por color: los colores cambian con el sombreado y dan anchos falsos.
- El píxel verde en el borde de la cabeza en NE/NW **no es un ojo**: es la punta de los cables de la nuca de Clast.
- **Error de los ojos (el usuario lo vio en captura, 2026-09-28)**: al girar la caja de la cabeza (`cabeza_pantalla`) los
  anclas `cara`/`ojo_*` seguían calculados para la caja SIN girar y quedaban en los bordes de la silueta (un ojo en cada
  costado, y un ojo asomando en NW). Corregido: `cuerpo.sobre_caja` proyecta cara y ojos sobre la caja real (girada y
  angostada). Con eso `cara_diagonal` volvió a 0.0 (con -.3 solo se veía un ojo en el borde). Lección: **al cambiar la
  forma de una pieza, revisar todo lo que se ancla a su superficie**, y **mirar la imagen ampliada de la cara por
  dirección, no solo contar píxeles**: los números daban "bien" mientras los ojos estaban fuera de lugar.
- **Ojos más separados (pedido del usuario, 2026-09-28)**: `sep_ojos_diagonal=.45` (antes .31 fijo) separa los ojos ~1 px más en
  las diagonales (centros a ~3,7 px), y `cara_diagonal=.45` corre el ojo cercano ~1 px hacia adentro, lejos del borde de la
  silueta. Los dos parámetros se compensan: subir la separación empuja el ojo cercano al borde, hay que subir también
  `cara_diagonal`. Medir los centros con `tests_personaje.mascara(cuadro, "ojos@cara#ojo_derecho")`.

## Cómo revisar una animación con zonas (sin mirar imágenes, 2026-09-28)
- Comando: `.venv/bin/python -m sprites_lib.zonas --anim caminar_lpc --estilo stardew8 [--dirs S,E] [--cuadros 0,1]
  [--skin skins/x.png | --ficha nombre] [--json] [--completo] [--png]` → `salida/zonas/<estilo>/<anim>.json` y `.md`
  (el informe también sale por stdout). Por defecto usa el muñeco de zonas; `--png` da la plantilla de colores planos
  por zona (una fila por dirección) solo para revisión humana.
- Quien revisa lee el `.md`: por dirección, `ALERTAS` primero (ALTA > MEDIA > baja; alertas iguales en varios cuadros
  van en una línea con la lista de cuadros y los valores), después la tabla de centros x,y por cuadro con el Δ al
  siguiente (solo si hay alertas MEDIA/ALTA; si no, una línea por zona con Δ máximo y rango de px) y al final el resumen
  entre direcciones (bbox y px por zona, separación de ojos y px de cara entre cada ojo y el borde). El JSON tiene todo
  (px, bbox, centro por zona y cuadro, pivote, celda, alertas con valor y umbral). Umbrales: `zonas.UMBRALES`.
- Cada píxel se clasifica por los buffers del render (componente/pieza/material), no por color: el sombreado y el
  contorno cambian los colores. El contorno exterior va a la pieza vecina (nunca a un ojo o ceja).
- Cómo leer las alertas: **ALTA** = casi seguro un error (ojo visible de espaldas, pivote que se mueve, lado cruzado,
  una parte de la cabeza/torso que aparece o desaparece, algo cortado arriba). **MEDIA** = mirar (salto de centro de
  cabeza/torso > 1 px, ojo pegado al borde de la silueta, separación de ojos fuera de rango, cabeza que cambia de
  tamaño). **baja** = normal en muchos ciclos (extremidades que se tapan entre sí, px de manos/pies que cambian > 35 %,
  contorno del pie tocando el borde de abajo): mirar solo si coincide con otra cosa.
- Los umbrales están pensados para caminar/quieto: en saltar o agachar la cabeza SÍ se mueve más de 1 px en la celda
  (ahí el salto de centro es esperable; lo que importa es que sea suave y que no aparezcan/desaparezcan partes).
- Primera pasada con `caminar_lpc` en `stardew8` (sin corregir, para revisar): ojo izquierdo visible en NW (ALTA, los 8
  cuadros); ojo a 0 px del borde de la cabeza en E, NW y W; torso_espalda/torso_frente que aparecen y desaparecen en
  SE, NE, NW, SW; salto de 1,1-3,4 px de cabeza_resto/cabeza_frente/torso_espalda en SE, E, NE, NW, W; el cuello (3 px)
  se tapa en la mitad de los cuadros con el rebote.
- **Píxeles raros que el usuario vio en el GIF (2026-09-28)**: (1) luz verde de la sien en la skin de Clast: quedaba suelta en NE
  y detrás de la oreja en E → se sacó de `pintar_clast.py`; (2) píxel blanco del ojo sobresaliendo de la silueta en E/W
  (marcado como "falso positivo perfil" por la herramienta, pero SÍ era un defecto visible) → `cara_perfil=.9`
  (`cuerpo.fuerza_cara`). Lección: una falsa "por diseño" hay que confirmarla mirando el GIF, no solo los números.
  Detector de píxeles sueltos: 1 px opaco con 0–1 vecinos opacos (4-conexos); lo que queda son contornos de 1 px en manos/pies
  (normales) y la nariz de perfil (E/W, y 17,10-11).
- **Perfil E/W con los dos ojos y cara de frente (2026-10-02)**: `cara_perfil=.9` corría la cara casi de frente a la cámara
  → en E/W la cara envolvía toda la cabeza (cara 117 px vs pelo 41) y se dibujaban los dos ojos (a 2 px), con la oreja
  a mitad de cara. El culling de `ojos` (`ojos_umbral`) solo cubría diagonales (`len(mira)==2`). Arreglo: `cara_perfil=.5`
  (perfil con pelo atrás, un solo ojo), cull explícito del ojo lejano en E/W (`componentes/humano.py`) y ancla `boca`
  apoyada en la caja (`cuerpo.posar` → `sobre_caja`, offset `-rz·.40`) para que la boca no cruce la silueta. Resultado:
  E/W con un solo ojo, sin `rasgo_fuera` de ojos ni de boca; `zonas` sigue sin alertas alta/media. Solo afecta E/W (las
  diagonales usan `cara_diagonal`). Test: `test_zonas.test_en_perfil_se_ve_un_solo_ojo`.
  - **Lecciones para futuras animaciones**: (1) `cara_perfil` sólo afecta E/W; las diagonales usan `cara_diagonal` (no
    tocar una esperando cambiar la otra). (2) Todo rasgo de cara (ojo, ceja, boca) va apoyado con `cuerpo.sobre_caja`,
    nunca con un offset fijo sobre la dirección de la cara: con la cara corrida, un offset fijo termina fuera de la
    silueta. (3) El culling de ojo "de canto" (`ojos_umbral`) y el "lejano" hay que cubrir TODOS los cardinales y
    diagonales, no sólo diagonales. (4) Antes de "arreglar" subiendo un parámetro (`cara_perfil=.9`), mirar el GIF: ese
    cambio había tapado un defecto (ojo afuera) empeorando otro (perfil de frente, dos ojos). (5) `zonas`+`pulido` ven
    esto sin mirar imágenes: el mapa de zonas por píxel (E c0) fue lo que mostró los dos ojos y la cara dominante.

## Modo pulido: ¿se ve BONITA? (2026-09-28)
- Comando: `.venv/bin/python -m sprites_lib.pulido --anim caminar_lpc --estilo stardew8 --skin skins/clast.png`
  (o `--ficha x`; sin personaje mide el muñeco de zonas y lo avisa) → `salida/zonas/<estilo>/<anim>[_skin]_pulido.json` y `.md`.
  Reusa `zonas.analizar` (mismas zonas por píxel) y mide la imagen del personaje real. Umbrales: `pulido.UMBRALES_PULIDO`.
- Mide tres familias: **movimiento** (recorrido de mano/pie en E/W contra LPC normalizado por el alto: mano 0,22·alto,
  pie 0,26·alto, mano lejana 0,09·alto; oposición mano-pie del mismo lado por correlación; simetría p vs p+n/2 con lados
  cambiados; cierre del loop; quiebres de 1 cuadro y aceleraciones > 1,25 × la máxima de LPC; rebote de la coronilla),
  **limpieza** (píxel suelto, espina, rasgo que sobresale = ojo/boca con ≥2 lados en contorno exterior o fondo, relleno
  que toca el fondo, agujero, mancha llamativa de ≤3 px lejos de TODO su entorno, parpadeo de un color, paleta por
  dirección) y **espejo** (E↔W, SE↔SW, NE↔NW, S y N consigo mismas).
- **Regla de espejo comprobada**: x' = 2·pivote_x − x y cuadro (p + desfase) % n. En caminar_lpc da 0-1 px de diferencia
  de alfa en E↔W, S y N (sin el desfase, 60-70 px). Las diagonales difieren 4-7 px solo en la cabeza porque
  `cabeza_desvio` no es espejo exacto (SE .9 / SW −1.0, NE −.2 / NW .1): falsa `desvio_de_estilo`.
- Criterio de mancha (medido): un tono de transición (pelo→piel, sombreado) queda a ≤ 37 del segmento RGB entre dos
  vecinos; los acentos reales (luz verde, blanco del ojo, raya de metal) a ≥ 88 → `entre_min` 50. Una mancha sobre la
  cabeza o en el borde de la silueta es REVISAR; dentro de brazos/piernas es leve (suele ser un detalle de la skin).
- Los dos defectos que vio el usuario, reproducidos: `cara_perfil` .55 → **MAL** `rasgo_fuera` (el blanco del ojo tiene
  3 de 4 lados en el contorno, E/W todos los cuadros); luz verde en la sien → **REVISAR** `mancha` en E (@5,10, 2 px,
  8/8) y NE (@12,11, 8/8).
- Estado actual (Clast, caminar_lpc, stardew8): movimiento OK, espejo OK, limpieza REVISAR: boca a 2 lados del contorno
  en SE c0/1/4/5 (no en SW: otra vez el `cabeza_desvio` asimétrico), un píxel de pelo oscuro #2a2218 entre canas en NE,
  y la mano lejana en E/W casi no se mueve (0,6 px contra 2,4 de LPC, leve).
- Qué NO mide: si una mancha es un detalle a propósito o una mota (solo la prioriza), la expresión, el "peso" del
  paso ni el timing (fps). El umbral de amplitud (±35 %) es dudoso: LPC es otro cuerpo (46 px, cabeza 45 %).

## Fry (referencia 8dir, CC0) vs nuestro stardew8 — análisis de detalles (2026-09-29)
- **Formato**: `referencias/8dir/fry_40x64/player_full_animation.png` = 240×448, celdas 40×64, 6 cuadros × 7 filas:
  0 caminar S, 1 caminar lado, 2 caminar N, 3 giros (S→lado→N), 4-6 quieto S/lado/N. **Solo 3 vistas dibujadas (S, lado, N)**;
  no trae diagonales (el resto se espeja): no sirve para medir 3/4, sí para detalle y proporciones.
- **Tamaño**: Fry ocupa 63 px de alto × 38 de ancho (con capa) en celda 40×64; nosotros 29 × 15 en celda 20×32.
  Fry es ~2.2× más alto y ~4.5× más área. Cabeza de Fry ~14 px de ancho (≈3 cabezas de alto, hombros 26-36 px de
  ancho = 2-2.6× la cabeza); la nuestra 13 px de ancho en 29 de alto (≈2.2 cabezas, torso 9-11 px < cabeza: chibi extremo).
  Si se compara, escalar Fry por 0.46 (no ×0.5 exacto) y ojo: a 20×32 no entran sus detalles finos.
- **Paleta**: Fry usa **14 colores en total** (rampas de 3 tonos por material, brillos saturados en amarillo, contorno de
  color oscuro tipo selout, nada de negro). Nuestro render tiene **70 colores** en 8 direcciones → más "ruido" que Fry.
- **Sombra en el piso**: elipse semitransparente (alfa 153) bajo los pies. Nosotros no tenemos (alfa solo 0/255).
- **Silueta**: el pelo sale en picos y rompe el óvalo de la cabeza; la capa es una masa grande con vetas de 2 tonos;
  brillos puntuales en botas y hombreras. Nuestra cabeza es un bloque liso con contorno parejo.
- **Rebote**: en caminar S el borde superior cambia 1 px entre cuadros (0/1).
- **Anatomía de Fry por vista (idle, celda 40×64, medida por color)**:
  | | S (frente) | Lado | N (espalda) |
  |---|---|---|---|
  | Cabeza (pelo+cara) | x14-27 (14 px), y0-18 (~19 px = 30% del alto) | x10-27 (**18 px**), y0-19 | x13-27 (15 px), y0-15: solo pelo, sin cara ni cuello |
  | Cara | pelo y0-9, visor/piel y10-18: la cara es la mitad de abajo de la cabeza | cara pegada al frente (x10-21), el pelo sobresale 6 px hacia atrás | ninguna |
  | Cuerpo (ancho total) | 38 px: capa a los costados + brazos azules por fuera (x3-36) | 27-33 px: la capa cae por detrás | 39 px: la capa lo tapa todo, del brazo solo asoman las puntas (y17-27) |
  | Piernas | ~16 px visibles (y45-60), botas separadas | botas en fila, una tapando la otra | casi ocultas por la capa (y54-56) |
  Conclusión: al girar, **cambia cuánto se ve de cada parte** (frente: cara + brazos + botas; lado: cabeza más ancha
  por el pelo, cuerpo más angosto; espalda: solo pelo + masa de tela), no las proporciones. La cabeza es ~30% del alto
  (la nuestra ~41%), con más de la mitad ocupada por el pelo.
- **Paleta reducida en stardew8 (2026-09-29)**: `estilos.ESTILOS["stardew8"]["render"]["paleta_max"] = 28` y
  `paleta.reducir_paleta` (une colores parecidos en Lab, ponderado por píxeles, conserva siempre el más usado). Clast pasó de 70 a
  28 colores en las 8 direcciones. 28 casi no se distingue; con 20 se apagan los ojos y sube el blanco de la cara en NE. Sin sombra.
- **Paleta fija por estilo (2026-10-03, task-017)**: cada estilo puede declarar `render.paleta_fija` (lista de hex). Si
  está, todo el render se mapea al color más cercano en Lab (`paleta.ajustar_paleta`) y no se reduce más; si falta, sigue
  la derivación por personaje + `reducir_paleta`. Fuentes: stardew/stardew8 → PLOT50 (top-down cozy, 50),
  volumen → Resurrect 64 (dark fantasy RPG, 64), fry8 → los 14 medidos de `referencias/8dir/fry_40x64`. Efecto medido
  en el aldeano (stardew, quieto S/E): 42 colores derivados → 17 de PLOT50, todos dentro de la lista. Dos personajes del
  mismo estilo ahora caen exactamente en la misma paleta.
- **Boceto `fry8` (2026-09-29)**: estilo derivado de stardew8 (`adulto_px=58`, celda 40×64, `cabeza_frac=.30`, `hombros_frac=.16`,
  `piernas_frac=.27`, `paleta_max=16`). Alto real 63 px = igual que Fry, pero la cabeza sale de 23 px de ancho (Fry 14) y el
  cuerpo de 31-34 (Fry 38). La skin de 32×32 estirada ~2× deja los ojos como puntos sueltos: el detalle de cara no sale de ahí.
- **Iteración de `fry8` con números (2026-09-29)**: se corrió `zonas` (con la skin de Clast) y se midió cabeza/torso/brazos por
  dirección en vez de mirar imágenes. Alertas 104 → 16 (0 altas). Cambios y por qué:
  - cabeza 25×24 → 19×21 (Fry: 14 de ancho): `cabeza_ancho .72`; cuerpo "flaco" (torso 17, brazos a 31) → torso 21, brazos 35:
    `cuerpo_ancho 1.3` + `hombros_frac .125` (con .16 los brazos quedaban flotando, separados del torso: medir el hueco
    entre bbox de brazo y torso, tiene que ser ≤ 0).
  - rebote 2 px → 1 px (`bob_escala .5`: el rebote escala con el alto y Fry rebota 1 px); paso `.55` (con el cuerpo más ancho
    los pies cruzaban la línea central en las diagonales: paso ≈ .7 / cuerpo_ancho); celda 48×64 (con 40 las manos tocaban el
    borde) y `adulto_px` 54 (con 58 la cabeza tocaba el borde de arriba).
  - **ojos**: los de stardew (3 píxeles sueltos: pestaña, blanco, iris) a 54 px se ven como puntos. Modo `ojos: "fry"` = 2×2
    (pestaña oscura, blanco afuera, iris adentro), cejas de 3 px seguidos; en diagonales el ojo LEJANO va de 1 px de ancho.
    Separación en S/N `sep_ojos .55` (con .31 los ojos se pegaban: uno de 3 px y otro de 2 px = asimétricos); en diagonales
    `.33` (con .45+ el ojo lejano tocaba el borde; con .40 desaparecía en SE/SW). Detector: los dos ojos con el mismo px en S/N.
  - `zonas`: los umbrales en px (`ESCALABLES`) se escalan por alto del personaje respecto de stardew8 (fry8 ×2.08); stardew8 no cambia.
- **Pendiente en fry8**: las cejas/ojos dejan puntos sueltos en la frente porque la skin de 32×32 se estira ~2×: hace falta skin
  64×64. Quedan 4 alertas MEDIA: salto de 2.4 px del centro de `torso_frente` en S (el brazo tapa y destapa; umbral 2.08).
- **Rebote entero en `stardew` (2026-10-02)**: el perfil `stardew` no tenía `bob_px`, así que el `bob` (~0.8 px de mundo a
  16 px) se redondeaba a 0 y caminar/saltar quedaban sin rebote: `sprites_lib.analizar` daba `rebote [0,0,0,...]` en
  `caminar_lpc` E/W, contra 1 px de la referencia Stardew. Se copió el arreglo que ya tenía `stardew8`
  (`estilos.ESTILOS["stardew"]["proporciones"]["bob_px"] = True`). Ahora `caminar_lpc` E/W da `rebote [1,1,0,0,1,1,0,0]`,
  `golpear` `[0,1,2,2,1,0]`, `saltar` `[3,0,0,0,0,5]`. Efecto colateral aceptado (ya documentado en `stardew8`): con rebote
  entero la cabeza tapa el cuello, así que el torso base queda oculto bajo la ropa; los tests de visibilidad de componentes
  ahora exigen solo los componentes **declarados** (el cuerpo base desnudo lo valida `test_armado`).
- **Objetos sostenidos (2026-10-02)**: componente `objeto` (`forma` espada/hacha/antorcha/escudo/bastón) enganchado a
  `mano_derecha`/`mano_izquierda` y orientado con el antebrazo (`codo→mano`). Sigue la mano en todos los ciclos: blandir =
  reusar `golpear`. Demo de iteración: `python -m sprites_lib.muneco objetos --anim golpear --formas espada,hacha`.
- **Animaciones de espada (2026-10-02)**: `blandir` (6 cuadros, un tajo), `combo` (9, tres tajos encadenados) y
  `desenvainar` (5; la espada aparece de golpe en el cuadro 2). Generadas con 3 subagentes (longcat-2.5-preview-free) en el
  formato de `ciclos.py` + registro en `poses.POSES`, y verificadas. `desenvainar` usa la clave `objeto_visible` (lista de
  n bools, por cuadro): `ciclos.pose` la propaga y el componente `objeto` no se dibuja si es `False`. Las tres son
  one-shot (`loop=False`) y declaran `ancho` para que entre la espada. Demo:
  `docs/diagnostico/objetos/nuevas_espada_stardew8.png`.

## Procesos del kit: estilo → animación → skin (2026-09-29)

Los pasos completos están en `docs/procesos/{estilo,animacion,skin}.md` y el diseño en
`docs/superpowers/specs/2026-09-29-procesos-estilo-animacion-skin-design.md`. Comandos:

- `.venv/bin/python -m sprites_lib.proceso_estilo medir|validar|aprobar <estilo>`
- `.venv/bin/python -m sprites_lib.proceso_anim smoke|validar|aprobar <anim> --estilo <estilo>`
- `.venv/bin/python -m sprites_lib.proceso_skin smoke|aprobar|lote <nombre>`

Cada proceso itera en autonomía hasta que el gate determinista (zonas, pulido, determinismo, deriva, plantilla)
da VERDE (tope 3 vueltas propias); `aprobar` es el único paso humano y congela en `aprobados/`.

## Contrato numérico del muñeco (`proporciones`, calibrado el 2026-09-29)
`proporciones.medir(estilo)` renderiza la ficha mínima (pose `neutra`, todas las direcciones) y mide el cuerpo
(`buf["solido"]`, sin contorno): alto desde el pivote (`suelo`), cabeza, piernas y anchos. `comparar` contrasta
la primera dirección con el perfil del estilo. Valores medidos (alto px / cabezas / piernas% / ancho cabeza px):

| estilo | alto (esp.) | cabezas (esp. 1/frac) | piernas (esp. perfil) | ancho cabeza (esp.) |
|---|---|---|---|---|
| volumen | 37 (36) | 2.64 (3.33) | 48.6% (41%) | 14 (12.8) |
| stardew | 27 (26) | 2.08 (2.78) | 33.3% (29%) | 13 (11.4) |
| lateral | 33 (33) | 2.36 (2.50) | 33.3% (32%) | 14 (15.2) |
| lpc | 43 (43) | 2.15 (2.22) | 27.9% (30%) | 20 (21.4) |
| stardew8 | 27 (26) | 2.08 (2.78) | 33.3% (29%) | 13 (11.4) |
| fry8 | 55 (54) | 2.75 (3.33) | 30.9% (27%) | 17 (18.2) |

- **Hallazgo (por qué `TOL_REL=.35`, no .10)**: en las vistas 3/4 (cenital e iso) la profundidad se proyecta
  sobre la pantalla (`ky=.5`) y la silueta de la cabeza y de las piernas mide 15-25% más que su tamaño vertical;
  el perfil guarda fracciones del mundo (`cabeza_frac`, `piernas_frac`), no de la silueta. En lateral/LPC la
  diferencia es 3-7%. El alto desde el pivote sale consistente (+1 px por redondeo; 0 px de variación entre
  direcciones). Tolerancias elegidas: `TOL_PX=2` (peor desvío 1.6 px) y `TOL_REL=.35` (peor desvío 25.2%, en
  stardew/stardew8). Ningún estilo legítimo queda fuera del doble de la tolerancia.
- **Caso límite del esqueleto**: `saltar` cuadro 2 recoge las piernas en el pico (tobillo **por encima** de la
  cadera; decisión de diseño documentada en la sección de la plantilla de salto). `test_esqueleto` mantiene la
  aserción `cadera > tobillo` y saltea los cuadros en el aire, que el propio ciclo declara con `offset_y != 0`.

## Generación de skins por un LLM: qué decide la calidad (experimento, 2026-10-02)

Experimento: 10 modelos free, prompt idéntico (receta `skins.desde_colores` + detalle opcional copiando
`skins/pintar_mago.py` + candado "detalle solo si `continuidad == []`"), 10 personajes, salida
`caminar_lpc` en `stardew`. Review humana a ciegas de cada GIF.

- **La calidad siguió a una conducta, no al modelo**: los 5 que escribieron un pase de pintado propio
  (100+ líneas, loop de simetría como `pintar_mago`) sacaron 8–9.5; los 5 que quedaron en
  `desde_colores` sacaron 6–7. Correlación perfecta.
- **El prompt constante no discrimina**: el mismo modelo divergió entre corridas (longcat: aldeano
  detallado 8 vs druida base 6; space-bunny: hechicera base vs pescador detallado 8). No es un ranking
  de modelos: es iniciativa + interpretación del personaje + azar de la corrida.
- **El candado jugó en contra**: "detalle solo si `continuidad == []`" hizo que `fledge` (robot) intentara
  óxido, fallara la costura y revirtiera a `desde_colores`. Conviene "corregí hasta que cierre" (loop
  corto) en lugar de revertir: el candado aplana justo a los que intentan.
- **El bug típico del detalle es mapeo columna→dirección**: `caballero_carmesi` pintó `cabeza` cols 0-1
  (nuca) de rojo; al mirar al N se ve la nuca roja. Al encargar una skin hay que pasar el mapa
  (`skins.guia`, `skins.columnas_por_direccion`) y avisar que la col 0 y la última de cada zona son la espalda.
- **Artefacto que no es del skin**: píxel oscuro que "popea" al caminar en `hechicera_hielo` (usó la base,
  sin pintado propio) y `fantasma_cian` → revisar pipeline/GIF/contorno antes de culpar a la skin.

Checklist para encargar una skin a un modelo/LLM:

1. Exigir pase de detalle propio (no opcional) con simetría izquierda-derecha.
2. Pasar `skins.guia` / `columnas_por_direccion` y la regla de la nuca (no pintar cols 0-1 / últimas de `cabeza`).
3. Iterar hasta `continuidad == []` (corregir, no revertir).
4. Cerrar con `zonas`/`pulido` para cazar el píxel que popea antes de mostrar.
