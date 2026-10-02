---
name: sprite-revisar
description: Revisar una animación de sprites cuadro por cuadro leyendo números en vez de imágenes — extrae la posición de cada zona del cuerpo (cabeza, cada ojo, brazos, piernas...) con sprites_lib.zonas, marca inconsistencias y las explica con un catálogo de patrones feos (ojos en el borde, cabeza que cambia de tamaño, zonas que parpadean, desvío asimétrico...) con su causa probable y el arreglo que funcionó. Usar siempre después de generar o cambiar una animación o un estilo (sobre todo stardew8 / 8 direcciones), cuando el usuario diga "se ve raro", "hay inconsistencias", "revisá frame por frame", o antes de exportar a output/.
---

# Revisar sprites con zonas (texto en vez de imágenes)

Una imagen ampliada cuesta muchos tokens, se reenvía en cada turno y los detalles de 1 px se pierden al achicarla.
Esta revisión lee **texto/JSON**: dónde está cada zona en cada cuadro y cómo cambia al siguiente. Miramos una imagen
solo al final, para juzgar si "se ve bien" (eso no lo mide ningún número).

## 1. Correr
```bash
.venv/bin/python -m sprites_lib.zonas --anim caminar_lpc --estilo stardew8            # todas las direcciones
.venv/bin/python -m sprites_lib.zonas --anim caminar_lpc --estilo stardew8 --dirs SE,SW --completo
.venv/bin/python -m sprites_lib.zonas --anim golpear --estilo stardew8 --skin skins/clast.png   # con un personaje
```
Escribe `salida/zonas/<estilo>/<anim>.json` y `.md`. Leer primero el `.md` (empieza con las ALERTAS de cada dirección);
el JSON es para consultar un número puntual. Una animación de 8×8 tarda ~1 s.

## 2. Formato del JSON
`direcciones[<dir>].cuadros[<n>]` = `{cuadro, pivote, celda, contorno, zonas}` y `zonas[<zona>]` = `null` (ausente) o
`{px, bbox:[x0,y0,x1,y1], centro:[x,y]}` (x→derecha, y→abajo, en px de la celda). `alertas` = lista de
`{sev (3 alta, 2 media, 1 baja), dir, cuadro, zona, tipo, valor, umbral, texto}`; `umbrales` = los límites usados
(se cambian en `sprites_lib/zonas.py`, dict `UMBRALES`).
Zonas: cabeza_frente, cabeza_resto, oreja_der/izq, ojo_der/izq, ceja_der/izq, boca_nariz, cuello, torso_frente,
torso_espalda, brazo/mano/pierna/pie derecho e izquierdo, otro (debe ser vacío).

## 3. Cómo leer el informe
1. Mirar `otro` (píxeles sin zona): si no es 0, la herramienta está clasificando mal; no fiarse de lo demás.
2. Leer las alertas ALTA/MEDIA de cada dirección y buscarlas en el catálogo de abajo. Cruzar direcciones: un defecto
   que aparece solo en las diagonales suele ser de cámara/rotación; en todas, de la pose o del ciclo.
3. Para cada alerta real: decir qué es, la causa probable y proponer el arreglo del catálogo. Cambiar UNA cosa, volver
   a correr y comparar la cantidad de alertas antes/después.
4. Antes de dar por bueno: mirar UNA sola imagen (una dirección ampliada) y preguntar al usuario.

## 4. Catálogo de patrones feos
Cada uno: **firma** (qué se ve en los números) → **cómo se ve** → **causa** → **arreglo que funcionó**.

### Cara
- **Ojo pegado al borde de la silueta.** `ojo_*` con 0 px de cabeza entre el ojo y el borde (alerta MEDIA
  "entre el ojo y el borde"). Se ve como un ojo flotando en el contorno, un ojo en cada costado. Causa: los anclas
  `cara`/`ojo_*` se calculan para la caja de cabeza SIN girar/angostar (`cuerpo.posar`) y la caja real es otra.
  Arreglo: `cuerpo.sobre_caja` (apoya cara y ojos en la caja real); en diagonales, `cara_diagonal` y
  `sep_ojos_diagonal` (stardew8: .45 y .45). **Falso positivo**: en E/W de perfil el ojo cercano está en el borde
  por diseño; solo importa en diagonales y de frente.
- **Ojos pegados / iguales (3/4 aplastado).** Distancia horizontal entre centros de ojo < ~3,5 px en diagonal, o los dos
  ojos del mismo tamaño en SE/SW. Se ve como una cara de frente pegada a un cuerpo de costado. Causa: fuerza de cara
  de los perfiles (`cara_hacia_camara` .55) usada en la diagonal; separación fija .31. Arreglo: `sep_ojos_diagonal`
  ↑ (.45 → ~3,7 px) y `cara_diagonal` ↑ para que el ojo cercano no se vaya al borde (se compensan).
- **Ojo en una dirección donde no hay cara.** `ojo_*` con px > 0 en N, NE o NW (alerta ALTA "visible de espaldas").
  Causa: el ojo queda en la silueta aunque mire casi de canto. Arreglo: `ojos_umbral` (.05): no se dibuja el ojo
  cuyo normal · dirección de cámara sea menor (en stardew8: NW ojo izq .01, NE ojo der .01; los reales > .3).
- **Ojos que parpadean.** El `px` de un ojo cambia entre cuadros consecutivos sin que la cabeza se mueva más de 1 px.
  Causa: el rebote (`bob*.9*esc`) no cae en píxeles enteros y la pestaña/ceja cambian de fila según la fracción.
  Arreglo pendiente (ver plan): rebote entero (`bob_px`) o `1/uz` en `humano.py`.
- **Píxel verde/de color en el borde de la cabeza en NE/NW.** No es un ojo: es la punta de los cables de la nuca
  (Clast). Comprobarlo con la zona (`otro` o cables), no tocar.

- **Ojos como puntos sueltos en un personaje grande (fry8, ~54 px).** Cada ojo mide 3 px sueltos y los dos ojos no tienen el
  mismo `px` en S/N (3 vs 2). Causa: ojos de stardew (1 px por parte) + separación .31 con cabeza angosta. Arreglo: `ojos: "fry"`
  (2×2), `sep_ojos` en S/N, ojo lejano de 1 px en diagonales, `sep_ojos_diagonal` .33. Un ojo de 2 px de ancho en diagonal
  toca el borde de la cabeza: por eso el lejano va de 1 px.
- **Umbrales en px con personajes de otra escala.** Con fry8 (×2.08) los saltos de 1-2 px eran falsas alarmas: `zonas` escala
  `ESCALABLES` por alto (`res["escala_umbral"]`).

### Cabeza y cuerpo
- **Cabeza que cambia de tamaño entre direcciones.** bbox de `cabeza_*` (ancho o alto) varía > ±2 px entre direcciones
  (alerta de tamaño). Causa: la caja gira con la cámara y muestra la esquina. Arreglo: `cabeza_pantalla`
  (`giro_cabeza`) alinea la caja a la pantalla. Referencias (Witch, TheNess, Fry): la cabeza se **angosta ~2 px en
  diagonal** (stardew8: 13 de frente/espalda → 10–11 en diagonal con `cabeza_diagonal` .85).
- **Desvío cabeza–torso asimétrico.** Diferencia de centro x entre cabeza y torso distinta en SE vs NE o SW vs NW
  (deberían ser ≈ simétricas, ~±0,7 px hacia donde mira). Arreglo: `cabeza_desvio` por diagonal (medir con la
  herramienta, no a ojo).
- **Zona que se cae del borde de la celda.** Píxel opaco tocando el borde (alerta) o `bbox` en x=0 / x=ancho−1.
  Causa: celda angosta. Arreglo: ancho por animación (`ciclos.<CICLO>["ancho"]`, medirlo con
  `python -m sprites_lib.muneco ancho --anim X --estilo stardew8`). Caminar 20, agachar/saltar/quieto 18, golpear 24.
- **Pivote que se mueve.** `pivote` distinto entre cuadros/direcciones. Causa: pivote calculado con otra celda. Se
  calcula por animación (`armado.pivote(estilo, pose=anim)`).

### Movimiento
- **Zona que aparece/desaparece entre cuadros consecutivos** (alerta ALTA "aparece"/"desaparece"). Mirar la zona:
  - `torso_frente`/`torso_espalda` en diagonales o perfiles: casi siempre **el brazo la tapa** al pasar; falso
    positivo si el `px` del torso completo (frente+espalda) casi no cambia.
  - una mano, un pie o un ojo: real. Revisar la pose.
- **Salto de centro** > ~1 px en cabeza/torso entre cuadros. Rebote esperado: `bob` de 1 px (~0,9–1,5 px en el
  centro de `cabeza_resto`, alterna ±). Más que eso → real (pose mal cargada). Las extremidades pueden saltar hasta 4.
- **Extremidad equivocada** (golpe con el brazo que no es). En animaciones asimétricas, comparar en el cuadro de
  extensión cuál `brazo_*`/`mano_*` tiene el mayor desplazamiento y confrontarlo con la ficha (Clast: golpea el
  izquierdo, de metal; el derecho está amputado). En E el brazo lejano queda tapado por el torso: su `px` baja.
- **Izquierda/derecha cruzadas** (alerta "cambia de lado"): la misma extremidad física salta de lado sin motivo.
  Cercano/lejano SÍ cambia solo al caminar (en S el pie cercano pasa de L a R): no es error.

### Pierna doblada (no se ve en números, revisar imagen)
- **Rodilla de garabato** en el muñeco desnudo cuando la pierna se dobla mucho (agachar): no es una falla de
  geometría; sobre el personaje vestido se lee bien. Juzgar siempre sobre el personaje real. `bob` final de agachar: 7.

## 5. Valores de referencia (stardew8, adulto, celda 16×32 base)
Cabeza 13×12 px de frente/espalda, 10–11 en diagonal; torso −15 % en diagonal (13→11); separación de ojos ~3,7 px en
diagonal; desvío cabeza–torso ±0,7 px hacia donde mira; alto total del personaje constante entre direcciones; cara
visible en S/SE/E/SW/W, ninguna en N/NE/NW.

## 6. Falsas conocidas: la herramienta las MARCA (no las borra)
Cada alerta trae `fp` (None = por revisar; texto = falsa conocida). El informe cuenta aparte "por revisar" y "falsas
conocidas" y en cada dirección lista las falsas agrupadas por motivo. Reglas (`zonas.FALSAS`, `marcar_falsas`), cada una
salió de mirar datos de `caminar_lpc` en stardew8:
- `diminuta`: zona de ≤ 6 px que aparece/desaparece (torso_espalda/frente de 3 px en diagonales): cuantización.
  CUIDADO: esta regla escondió un defecto real: el **cuello** asomaba 3 px en los cuadros pares y no en los impares
  (rebote fraccionario). Se arregló con `bob_px` (rebote en px enteros, stardew8). Si una zona diminuta alterna
  cada 2 cuadros con el ritmo del rebote, es parpadeo real: revisarla antes de darla por falsa.
- `perfil`: ojo a 0 px del borde en E/W (el ojo cercano queda en el borde frontal a propósito). En E/W se ve **un solo**
  ojo: `cara_perfil=.5` apoya la cara al frente y el ojo lejano se culla en `componentes/humano.py`. Si en E/W aparecen los
  **dos** ojos, o un píxel claro afuera de la cabeza, es un defecto real (no un falso positivo). El `cara_perfil=.9` viejo
  corría la cara de frente y volvía a mostrar los dos ojos (ver CRITERIOS_ANIMACION.md, 2026-10-02).
- `area_visible`: salto de centro o cambio de px del torso cuando el torso visible (frente+espalda) cambió ≥ 15 % de px
  (el brazo lo tapa/destapa), o de otra zona cuando su propio px cambió > 25 %.
- `extremidad_en_movimiento`: cambio de px de brazo/mano/pierna/pie al caminar (se giran y se tapan).
- `tapada_por_su_par`: mano o pie que desaparece donde está su par (≤ 3,5 px): lo tapa la otra pierna/brazo.
- `cambio_minimo`: cambio de ≤ 2 px absolutos (orejas de 4 ↔ 6 px por el rebote).
- `pie_al_piso`: contorno del pie tocando el borde de abajo (el pivote está a 2 px del borde).
Además el salto de cabeza/torso se mide **relativo al movimiento de su ancla** (el rebote del cuerpo no cuenta).
Resultado en `caminar_lpc`/stardew8/muñeco: 297 alertas → **10 por revisar (0 altas, 0 medias)** + 265 falsas marcadas.
Regla para agregar una falsa nueva: comprobar en los números que no es un defecto, agregarla a `FALSAS`/`marcar_falsas`
con su motivo y anotarla acá. Nunca subir un umbral "para que dé verde" sin haber mirado qué era.

### Por revisar que quedaron (a investigar, todavía sin explicación)
- Orejas y `torso_espalda` con ±36–38 % de px en E/W (puede ser el borde frente/espalda del torso moviéndose).
- Pie a 5 px de salto en SE/SW (cruce de pasos en perspectiva) y un pie/mano que desaparece sin par cerca.
- Con la ficha `clast.yaml` (componentes, con cresta) en stardew8: la cabeza toca el borde SUPERIOR de la celda en
  S/NE/NW (alertas ALTA `borde_arriba`). La skin `skins/clast.png` (la que se exporta) deja ≥ 2 px de margen. Si se usa
  la ficha vieja en stardew8, subir la celda o bajar la cresta.

## 7. Pulido (después de que las alertas de construcción estén limpias)
`zonas` dice si la animación está bien CONSTRUIDA; `pulido` mide lo que la hace verse BONITA. Correrlo recién cuando
zonas no tenga alertas ALTA/MEDIA por revisar (si las hay, el informe lo avisa arriba), y siempre con el personaje real:
```bash
.venv/bin/python -m sprites_lib.pulido --anim caminar_lpc --estilo stardew8 --skin skins/clast.png
```
→ `salida/zonas/<estilo>/<anim>_<skin>_pulido.md` (y `.json`). Cómo leerlo:
1. **Resumen de pulido**: una nota por familia (movimiento / limpieza / espejo = OK, REVISAR o MAL) y los 3 hallazgos
   más importantes (uno por tipo y zona). Empezar por ahí; cada hallazgo trae dir, cuadro, píxel `@x,y`, valor, umbral
   y qué significa para el ojo.
2. **Medidas**: números de referencia (recorrido de manos/pies, correlación mano-pie, coronilla por cuadro, colores por
   dirección, diferencia de alfa del espejo por cuadro). Sirven para comparar antes/después de un cambio.
3. Hallazgos por familia; **MAL** casi seguro se ve (un ojo afuera de la cara, un píxel flotando, mano y pie del mismo
   lado yendo juntos); **REVISAR** mirar el cuadro ampliado una vez (mancha sobre la cabeza, boca en el contorno,
   espejo que no coincide); **leve** solo si coincide con lo que el usuario vio (detalles de la skin en las piernas).
4. Falsas conocidas (`fp`, motivos en `pulido.FALSAS_PULIDO`): `punta_de_contorno`, `rasgo_de_cara`, `tono_intermedio`,
   `oclusion`, `desvio_de_estilo`, `asimetria_declarada`, `animacion_asimetrica`, `extremidad_en_movimiento`,
   `tono_vecino`, `tono_de_material`, `pie_al_piso`, `ya_en_zonas`. Salieron de mirar caminar_lpc/stardew8 con Clast y
   con el muñeco; misma regla que arriba para agregar una nueva.
Firmas nuevas del catálogo: **ojo que sobresale** = `rasgo_fuera` MAL en E/W (la falsa `perfil` de zonas NO lo cubre);
ya no se reproduce con `cara_perfil=.5` + cull del ojo lejano (ver 2026-10-02), pero sigue siendo la firma a buscar si
alguien vuelve a subir la fuerza de cara; **luz suelta sobre el pelo** = `mancha` REVISAR en `cabeza_resto` (E y NE con
la luz de la sien).

## 8. Mantener el catálogo
Cada vez que el usuario diga que algo se ve feo (o aparezca una alerta nueva y real): (1) buscar la firma en el
JSON/informe, (2) agregar un patrón acá con firma → cómo se ve → causa → arreglo, (3) si es medible y no hay alerta,
agregarla en `sprites_lib/zonas.py` (y un test en `tests/test_zonas.py`). El objetivo es que la próxima animación salga
revisada contra todo lo aprendido. Los números "buenos" que se ajusten van también a `CRITERIOS_ANIMACION.md`.
