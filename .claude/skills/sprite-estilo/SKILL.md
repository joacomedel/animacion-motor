---
name: sprite-estilo
description: Analizar el ESTILO visual de un juego de referencia (Stardew Valley, Zelda, Hyper Light Drifter, Octopath, etc.) — resolución y tamaño de celda, vista (isométrica o cenital 3/4), proporciones, cantidad de colores, tipo de contorno (negro o de color/selout), sombreado (plano o con volumen), cuadros por animación — convertirlo en un perfil reutilizable en sprites_lib/estilos.py y generar personajes con ese estilo. Usar siempre que el usuario diga "en el estilo de <juego>", "que se vea como <juego>", "menos 3D", "más plano", "más pixel art", pase un juego como referencia de look, o quiera armar/cambiar estilos para su juego.
---

# Estilos: analizar el look de un juego y aplicarlo

Estilo ≠ movimiento ≠ personaje. El **personaje** (qué es) vive en `personajes/`, el **movimiento** en
`sprites_lib/ciclos.py` y el **estilo** (cómo se ve) en `sprites_lib/estilos.py`. Esta skill trabaja la
tercera capa. Antes de empezar, leer `CRITERIOS_ANIMACION.md` (sección de estilos).

## 1. Conseguir referencias del juego
Con la skill `sprite-referencia`: 2 hojas de personajes del mismo juego (así se separa lo que es del estilo de lo
que es del personaje) y, si hay, uno parecido al que se va a crear. En The Spriters Resource, las hojas de NPCs
suelen venir completas. Guardarlas en `referencias/<juego>/`.

## 2. Medir el estilo (con números, no a ojo)
Recortar el bloque de caminata (celda × cuadros × direcciones), ampliarlo ×8 y mirarlo con Read. Después medir
con un script de PIL/numpy:
- **Celda y figura**: tamaño de celda, alto real de la figura, ancho.
- **Vista**: ¿piso de rombos (isométrico, 8 direcciones) o de grilla cuadrada vista desde arriba en 3/4
  (cenital, 4 direcciones: abajo, derecha, arriba, izquierda)? Stardew, Zelda y Pokémon son cenitales, no
  isométricos.
- **Proporciones**: cabeza/alto y piernas/alto.
- **Colores**: por cuadro y en total; tonos por material; ¿hay corrimiento de tono en sombras y luces?
- **Contorno**: colores del borde exterior (píxeles opacos junto a transparencia). Calcular qué porcentaje es
  casi negro (<30). Bajo = contorno de color (selout); alto = contorno negro.
- **Sombreado**: ¿casi todo en tono base (plano) o con 3 tonos marcados por volumen? ¿Hay dithering?
- **Animación**: cuadros por dirección, rebote (alto por cuadro), qué se mueve.
- **Trampas del estilo**: por ejemplo, Stardew dibuja la cara casi de frente aunque la cámara mire desde arriba.

## 3. Escribir el perfil
Agregar una entrada en `ESTILOS` (`sprites_lib/estilos.py`) siguiendo el formato de `stardew`:
- `vista` ('iso' o 'cenital') y `celda`;
- `render` → parámetros de `Escena.render(estilo=...)`:
  - `umbrales` (t1, t2) de los 3 tonos: separados (.28, .66) = volumen; extremos (.12, .82) = plano;
  - `contorno` 'negro' | 'color';
  - `interior` 'negro' | 'color' | 'ninguno';
  - `oscurecer` (qué tan oscuro es el contorno de color);
- `proporciones`, reglas de `paleta` y `ciclos` recomendados.
Si el estilo necesita otro movimiento (por ejemplo 4 cuadros en vez de 10), agregar el ciclo en `ciclos.py`
(como `CAMINAR`).

## 4. Crear el personaje en ese estilo
Tomar como base `personajes/mago_stardew.py` (vista cenital) o `personajes/mago_iso.py` (isométrica) y adaptar:
ANATOMIA a las proporciones del estilo (en chibi, las trayectorias del rig se escalan con
`ESCALA = piernas / 14`), PALETA con las reglas del estilo, detalles al tamaño de la celda (ojos de 2 px, runas
de 1 px) y luz (más frontal = más plano). Generar con `--comparar`: la referencia queda arriba y el personaje
abajo, en las mismas direcciones y cuadros.

## 5. Autoanálisis contra la referencia (obligatorio, antes de mostrarle nada al usuario)
El usuario no debería tener que decir "se ve 3D", "está cortado" o "no se ve la cara": hay que detectarlo antes.
Repetir este ciclo hasta que pase:
1. **Métricas objetivas**:
   ```bash
   .venv/bin/python -m sprites_lib.comparar_estilo <ref.png> 16x32 <mio.png> 16x32 --ref-recorte x0,y0,x1,y1
   ```
   Mide colores, borde negro, planitud, tonos por material, degradé (R²), píxeles huérfanos, tamaño de los grupos
   de color, bandas, recorte, rectitud de la silueta y ancho de la cabeza. Imprime el diagnóstico con la corrección.
   Las métricas "informativas" dependen del personaje (ropa negra, pelo largo) y no bloquean.
   **Calibrar primero con un control**: comparar dos sprites reales del mismo juego entre sí. Una métrica que
   falla en el control no discrimina estilo; no hay que perseguirla.
2. **Comparación visual ×14** de frente, perfil y espalda, referencia y propio intercalados:
   ```bash
   .venv/bin/python -m sprites_lib.lado_a_lado <salida.png> <ref.png>:x,y,w,h <mio.png>:x,y,w,h ...
   ```
   Mirarla con Read y responder este checklist por escrito:
   - **Silueta**: ¿lados rectos y formas cuadradas como la referencia, o curvas perfectas (esferas → se ve 3D)?
   - **Superficies**: ¿hay detalle dibujado (mechones, pliegues, capas de ropa, ribetes) o manchas lisas grandes?
   - **Tamaño y proporción**: ¿mismo alto de figura, ancho de cabeza y tamaño de cara que la referencia?
   - **Cara**: ¿se lee de frente **y de perfil**? ¿ojos del mismo tamaño y construcción (pestaña, blanco, iris)?
   - **Contorno**: ¿mismo tipo (negro o de color)? ¿alguna línea rara en los bordes de la celda?
   - **Recorte**: ¿algo toca el borde superior?
   - **Sombreado**: ¿igual de plano? ¿la luz y la sombra forman figuras definidas o degradés?
3. Corregir la causa (no el síntoma) y volver al paso 1. En Stardew hicieron falta 6 vueltas. Solo cuando pase
   todo, mostrarlo y abrir `_todas.gif` con `xdg-open`.

Herramientas del motor para corregir el "look 3D":
- `esc.caja(c, radios, mat, n=3)`: superelipsoide con lados rectos en vez de esfera;
- materiales con textura: funciones de la dirección que alternan dos tonos por franjas (mechones, pliegues);
  `faldon(..., mat=fn(d, t))`;
- `render(estilo={"sombreado": "borde"})`: base plana, luz en el borde superior-izquierdo de cada pieza y sombra
  en el inferior-derecho, como lo haría un artista;
- trampas de vista: ubicar la cara hacia la cámara (`centro_cara` en `personajes/mago_stardew.py`).

## 6. Anotar
En `CRITERIOS_ANIMACION.md`, sección "Estilo <juego>": medidas, perfil elegido, trampas del estilo y errores
corregidos.
