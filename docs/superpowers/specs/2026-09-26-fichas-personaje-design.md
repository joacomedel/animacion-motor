# Diseño: personajes consistentes con fichas, poses clave y tests

Fecha: 2026-09-26 · Estado: borrador para revisión · Rama: `diseno/fichas-personaje`

## 1. Objetivo

Que el kit genere **sprites buenos, predecibles y consistentes**, capaces de basarse en animaciones de la web y de
autoverificarse. Concretamente:

- **Mismo personaje, siempre igual**: en todas las direcciones, poses, animaciones y cuadros (misma cara, mismos
  colores, mismo tamaño, mismos accesorios).
- **Resultados predecibles**: la calidad no depende de que el agente improvise ni de que "se acuerde" de las correcciones;
  las lecciones aprendidas viven en el código.
- **Decisiones explicadas**: cada rasgo y accesorio tiene un "por qué" en una ficha legible.
- **Verificación automática**: tests que confirman que las reglas se cumplen antes de entregar.
- **Tamaños consistentes** entre todos los personajes del juego.
- **Basarse en la web**: movimiento y estilo medidos desde referencias (skills existentes `sprite-referencia`,
  `sprite-analizar`, `sprite-estilo`).

### Lo que pidió el usuario (literal) vs. supuestos

| Pidió | Supuesto de diseño |
|---|---|
| Resultados predecibles; mismo personaje siempre igual | Una ficha es la única fuente de verdad; el código se genera desde ella |
| "Si tiene una pulsera, que se le vea siempre" | = siempre que su ancla (muñeca) sea visible; el test distingue oclusión por pose de omisión |
| Decisiones como explicación de personaje, no solo píxeles | Cada componente y color de la ficha lleva `por_que` |
| Confirmación/testeo de las especificaciones | Tests automáticos + informe ✓/✗; si falla, no se entrega |
| Modelar poses básicas primero como base de las animaciones | Flujo pose a pose; fase 1 = **neutra + quieto** |
| Incluir 2D lateral | Fase 1 cubre lateral, cenital (Stardew) e iso (volumen) |
| Consistente con el tamaño de los sprites | Escala única por estilo, clases de altura, celdas estándar, pivote en los pies, con tests |
| La ficha la armo yo desde su descripción; la aprueba antes de generar | Paso de aprobación explícito de la ficha y de la hoja de modelo |

## 2. Ideas tomadas de la investigación

- **Hojas de modelo de animación** (turnaround / model sheet): vistas alineadas con **líneas guía** (ojos, hombros,
  cintura a la misma altura); "on-model" vs "off-model" (las desviaciones solo valen si son intencionales).
  → hoja de modelo generada + test de líneas guía + excepciones declaradas.
- **Universal LPC Spritesheet Generator**: definiciones JSON por pieza con capa, tipos de cuerpo y animaciones
  soportadas; créditos/licencia obligatorios; la generación falla si falta algo; validación en CI.
  → validador de fichas, compatibilidad declarada por componente, créditos obligatorios de referencias.
- **Spine** (esqueleto + slots + skins): separar esqueleto de accesorios; los sistemas se rompen sin **convención de
  nombres estricta**. → vocabulario fijo de anclas; variantes como capas sobre la ficha.
- **Animación pose a pose**: poses clave aprobadas → intermedias → relleno. → hoja de poses y "fotos de control".
- Descartado: generadores por IA/GAN (no garantizan consistencia entre cuadros).

## 3. Arquitectura

Un sprite = **ficha** (qué es y qué lleva) + **pose/animación** (cómo se mueve) + **estilo** (cómo se dibuja).

```
descripción del usuario
   → ficha YAML (la escribe el agente) ──validar──► error claro si algo no cierra
   → [APROBACIÓN 1: ficha]
   → hoja de modelo: poses neutra + quieto × todas las direcciones del estilo, con líneas guía, paleta y notas
   → tests de consistencia ──falla──► corregir y repetir (no se muestra)
   → [APROBACIÓN 2: hoja de modelo] → se congelan las "fotos de control"
   → (fase 2+) animaciones pose a pose → tests → exportación
```

### 3.1 Unidades (archivos nuevos o modificados)

| Unidad | Responsabilidad | Depende de |
|---|---|---|
| `personajes/fichas/<nombre>.yaml` | Identidad, cuerpo, paleta, componentes, reglas, créditos | — |
| `sprites_lib/ficha.py` | Cargar y **validar** la ficha (esquema, anclas, componentes, estilos, colores, créditos) | `cuerpo`, `componentes` |
| `sprites_lib/escala.py` | **Escala del juego**: px por unidad por estilo, clases de altura, celdas estándar, pivote | `estilos` |
| `sprites_lib/cuerpo.py` | Esqueleto base humano, **vocabulario fijo de anclas** y su posición según la pose | `rig`, `escala` |
| `sprites_lib/poses.py` | Poses como datos (posición de articulaciones en el rig): `neutra`, `quieto` | `ciclos` (formato) |
| `sprites_lib/componentes/*.py` | Un archivo por componente (`ojos`, `rastas`, `vincha`, `pulsera`, `tatuaje_runas`, `tunica_abierta`, `botas`, `manos`…); cada uno dibuja con primitivas en su ancla, declara estilos soportados y **marca sus píxeles** | `render3d` |
| `sprites_lib/render3d.py` | Motor único; se agrega `CamaraLateral` y un **buffer de componente** (qué componente pintó cada píxel) | — |
| `sprites_lib/hoja_modelo.py` | Genera hoja de modelo y hoja de poses con líneas guía, muestras de paleta y notas de la ficha | todo lo anterior |
| `sprites_lib/tests_personaje.py` | Tests de consistencia + informe `informe.md` | render, ficha, escala |
| `sprites_lib/fotos_control.py` | Guardar/comparar las poses aprobadas; imagen antes/después si cambian | — |
| `personajes/generar.py` | CLI: `validar`, `hoja`, `tests`, `aprobar`, `exportar` para cualquier ficha | todo |
| Skill nueva `sprite-personaje` | Flujo completo descripción → ficha → hoja → tests → aprobación | — |

Los archivos `personajes/mago_*.py` actuales quedan como referencia hasta que la ficha del mago los reemplace.
`pixel2d.py` queda como respaldo (ver 3.3).

### 3.2 La ficha (formato)

```yaml
identidad:
  nombre: Mago de las runas
  concepto: "Hechicero viajero que mezcla magia antigua con tecnología rúnica…"
  rol: jugable
  silueta_clave: "rastas blancas largas + túnica abierta"
cuerpo:
  base: humano
  clase_altura: adulto          # ver 3.4: define el tamaño en TODOS los estilos
  piel: morena
paleta:                         # solo tono base; el estilo deriva sombra/luz con su regla de corrimiento de tono
  piel:   {base: "#8c5638", por_que: "tez morena"}
  runa:   {base: "#5af0e6", emisivo: true, por_que: "energía rúnica: el único color que brilla"}
componentes:
  - {tipo: pulsera, ancla: muneca_derecha, material: oro,
     por_que: "regalo de su maestro; nunca se la saca", reglas: [visible_si_ancla_visible]}
reglas_globales: [paleta_identica_entre_direcciones, lineas_guia, nada_recortado, cara_visible_en: [S, E, W]]
excepciones: []                 # desviaciones "off-model" intencionales, con motivo
creditos: [{referencia: "Stardew Valley (estilo)", fuente: "spriters-resource…", uso: "solo referencia"}]
```

El validador rechaza: anclas fuera del vocabulario, componentes inexistentes o incompatibles con el estilo pedido,
materiales usados pero no definidos, colores inválidos, reglas desconocidas, falta de `por_que` en componentes y
falta de créditos cuando la ficha declara referencias.

### 3.3 Vistas: un solo motor para las tres

- `Camara` (iso 2:1, 8 direcciones) y `CamaraCenital` (3/4, 4 direcciones) ya existen.
- **Nuevo `CamaraLateral`**: proyección ortográfica de costado (x = adelante, y = −arriba), direcciones `E` y `W`.
- **Decisión**: el lateral se genera con el mismo motor 3D y los mismos componentes. Así la pulsera, las rastas o los
  ojos se programan una vez y son consistentes en todas las vistas por construcción.
- **Riesgo**: perder la calidad "dibujada" que tiene hoy `pixel2d`. **Mitigación**: estilo lateral con sombreado por
  bordes y formas cuadradas, validado con `comparar_estilo` contra Mega Man X. Si no alcanza la calidad, se usa
  `pixel2d` como renderer alternativo por componente (cada componente puede aportar además un dibujo 2D).

### 3.4 Tamaños consistentes (`escala.py`)

- **Clases de altura** del mundo en unidades del rig: `nino` 0.75, `adulto` 1.0, `grande` 1.25, `gigante` 1.6
  (ajustables). Todos los personajes de la misma clase miden lo mismo; entre clases, la proporción es fija.
- **Por estilo**: tamaño de celda estándar, **px de alto de un adulto** y pivote. Ejemplos: stardew 16×32, adulto 26 px,
  pivote en (8, 30); volumen 56×60, adulto ~45 px, pivote (26, 52); lateral 40×40, adulto 34 px (medido en
  Mega Man X: 33–35 px en celda 34×35; se agranda la celda a 40 para pelo/capas), pivote (18, 38).
  Un "grande" en stardew puede usar una celda estándar mayor (p. ej. 32×48), declarada en el estilo.
- **Pivote siempre en los pies**, en la misma posición de la celda para todos los personajes del estilo.
- Tests de tamaño: alto de la figura = alto de su clase ±1 px en todas las direcciones; pivote correcto; nada fuera de
  la celda; misma celda para todos los personajes de la misma clase.

### 3.5 Componentes

Cada componente es una clase chica con: `tipo`, `anclas_validas`, `estilos` soportados, `parametros` con valores por
defecto, y `dibujar(escena, cuerpo, pose, params)`. Al dibujar, asigna `escena.componente = <id>` para que cada píxel
quede marcado. **Las lecciones de `CRITERIOS_ANIMACION.md` se codifican aquí**, por ejemplo:
- `manos`: pieza propia, radio mayor que el antebrazo, tono más claro, brillo en nudillos.
- `ojos`: centro de cara hacia la cámara (trampa de perfil), variante por estilo (2 px Stardew).
- `rastas`: nacen fuera del volumen de la cabeza, retraso de 1 cuadro.
- cabeza como caja redondeada en estilos no volumétricos.

### 3.6 Poses (fase 1)

- `neutra`: pose A (brazos levemente abiertos, piernas juntas) para verificar construcción y anclas.
- `quieto`: reposo con respiración (4 cuadros; rebote 0,0,1,1).
Las poses se expresan como posiciones de articulaciones en el rig lateral (mismo formato que `ciclos.py`) para que en
la fase 2 las animaciones sean secuencias de poses clave.

### 3.7 Tests de consistencia (`tests_personaje.py`)

| Test | Cómo se verifica |
|---|---|
| Validez de ficha | validador (3.2) |
| Accesorio visible | con el buffer de componente: si el ancla tiene píxeles visibles, el componente debe tener ≥1 píxel visible; si el ancla está tapada, se omite |
| Líneas guía | altura en pantalla de ojos, hombros y cinturón (desde las anclas proyectadas) igual entre direcciones ±1 px, salvo el rebote de la pose |
| Paleta | colores de cada material idénticos entre direcciones/cuadros; ningún color fuera de la paleta derivada |
| Tamaño y pivote | 3.4 |
| Recorte | nada en la fila superior ni fuera de la celda |
| Cara visible | en las direcciones declaradas, píxeles de `ojos` visibles |
| Simetría | componentes `simetrico` presentes en ambos lados cuando ambos son visibles |
| Estilo | `comparar_estilo` contra la referencia del estilo (métricas no informativas deben pasar) |
| Fotos de control | tras aprobar, los PNG deben coincidir píxel a píxel; si no, informe con antes/después |

Salida: `salida/<personaje>/<estilo>/informe.md` con ✓/✗ por regla y la evidencia (dirección, cuadro, píxeles).

### 3.8 CLI

```bash
.venv/bin/python -m personajes.generar validar mago
.venv/bin/python -m personajes.generar hoja mago --estilo stardew     # hoja de modelo + tests + informe
.venv/bin/python -m personajes.generar aprobar mago --estilo stardew  # congela fotos de control
.venv/bin/python -m personajes.generar tests mago --estilo todos
```

## 4. Fases

1. **Fase 1 (este diseño)**: ficha + validador + escala + cuerpo/anclas + componentes del mago + `CamaraLateral` +
   poses neutra/quieto + hoja de modelo + tests + fotos de control + skill `sprite-personaje`, en estilos **stardew,
   volumen y lateral**.
2. **Fase 2**: animaciones pose a pose (caminar, correr) a partir de poses clave **medidas en referencias de la web**;
   fotos de control en los cuadros clave.
3. **Fase 3**: análisis de imágenes más fuerte: extracción semiautomática de articulaciones y poses desde sprites de
   referencia (siluetas, colores por parte y grilla), para cargar poses sin leerlas a ojo.
4. **Fase 4**: acciones (hechizo, ataque), expresiones y variantes/skins.

## 5. Criterios de éxito de la fase 1

- El mago, migrado a ficha, genera su hoja de modelo en **stardew, volumen y lateral** y **pasa todos los tests sin
  retoques a mano**.
- Un segundo personaje de prueba (p. ej. un caballero con capa y escudo) se crea **solo escribiendo su ficha**, sin
  código nuevo salvo componentes que no existan, y pasa los tests con el mismo tamaño de celda y alto que el mago.
- Romper a propósito una regla (quitar la pulsera en una dirección, subir los ojos 2 px, recortar la cabeza) hace
  fallar el test correspondiente con un mensaje claro.
- El lateral pasa `comparar_estilo` contra Mega Man X en las métricas no informativas.

## 6. Fuera de alcance (fase 1)

Animaciones en movimiento, acciones, expresiones, variantes, exportación a motores específicos, migración de
`el_llamado/` y `mago/` (experimentos).

## 7. Riesgos

- **Lateral con motor 3D menos "dibujado"** → mitigación en 3.3.
- **Visibilidad de accesorios chicos** (1 px) puede fallar por redondeo → el componente define un tamaño mínimo por
  estilo; el test reporta el cuadro exacto.
- **Paleta derivada distinta por estilo** → la paleta de la ficha es por material; cada estilo deriva sus tonos, y el
  test de paleta compara dentro de un mismo estilo.
