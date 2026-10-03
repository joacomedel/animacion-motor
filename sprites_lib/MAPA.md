# Mapa de sprites_lib (generado: `.venv/bin/python -m sprites_lib.mapa`, no editar a mano)

Flujo: ficha YAML → `ficha.cargar` → `armado.render_cuadro` (cuerpo base + componentes → `cuerpo.posar` → `render3d.Escena`) → `Cuadro` (img + buffers) → tests / hoja / exportar.

## Estilos
| estilo | vista | direcciones | adulto px | celda | activo |
|---|---|---|---|---|---|
| volumen | iso | SE E NE N NW W SW S | 36 | 56×60 | no |
| stardew | cenital | S E N W | 26 | 16×32 | sí |
| lateral | lateral | E W | 33 | 40×40 | sí |
| lpc | lateral | E W | 43 | 64×64 | no |
| stardew8 | cenital | S SE E NE N NW W SW | 26 | 16×32 | no |
| fry8 | cenital | S SE E NE N NW W SW | 54 | 48×64 | no |

## Anclas
antebrazo_derecho, antebrazo_izquierdo, boca, brazo_derecho, brazo_izquierdo, cabeza, cadera_derecha, cadera_izquierda, cara, cintura, codo_derecho, codo_izquierdo, coronilla, cuello, frente, hombro_derecho, hombro_izquierdo, mano_derecha, mano_izquierda, muneca_derecha, muneca_izquierda, nuca, ojo_derecho, ojo_izquierdo, pecho, pie_derecho, pie_izquierdo, pierna_derecha, pierna_izquierda, rodilla_derecha, rodilla_izquierda, sien_derecha, sien_izquierda, suelo, tobillo_derecho, tobillo_izquierdo, torso

## Componentes (tipo · anclas · material por defecto · parámetros)
- `botas` · pie_derecho, pie_izquierdo · bota · suela=None
- `brazo_humano` · brazo_derecho, brazo_izquierdo · piel · —
- `brazo_robotico` · brazo_derecho, brazo_izquierdo · metal · juntas=None, rayas=None, mano='pinza_3_dedos'
- `brazo_robotico_amputado` · brazo_derecho, brazo_izquierdo · metal · termina_en=None, juntas=None
- `brazo_skin` · brazo_derecho, brazo_izquierdo · — · skin=None
- `cabeza_humana` · cabeza · piel · cabello='corto'
- `cabeza_skin` · cabeza · — · skin=None
- `cables_nuca` · nuca · cable · cables=2, luz_en_punta=None, largo='corto'
- `camisa` · torso · ropa · mangas='cortas'
- `cinturon` · cintura · cuero · hebilla=None
- `munon_cables` · codo_derecho, codo_izquierdo, rodilla_derecha, rodilla_izquierda · cable · cables=3, largo_px=2, chispa=None, chispa_cada_cuadros=3
- `objeto` · mano_derecha, mano_izquierda · metal · forma='espada', largo=8.0, angulo=0.0, agarre='antebrazo', mango=None, pomo=None, guarda=None, detalle=None
- `ojos` · cara · — · solo=None, iris=None
- `pelo_rizado` · cabeza · pelo · filas=2, volumen=1.0
- `pierna_humana` · pierna_derecha, pierna_izquierda · piel · calzado=None
- `pierna_robotica` · pierna_derecha, pierna_izquierda · metal · juntas=None, rodilla='piston', pie='bota_metalica'
- `pierna_skin` · pierna_derecha, pierna_izquierda · — · skin=None
- `placa_sien` · sien_derecha, sien_izquierda · metal · —
- `pulsera` · muneca_derecha, muneca_izquierda · oro · grosor=1.0
- `rastas` · cabeza · pelo · cantidad=6, largo='hombros', cuentas=None
- `remera_larga_rota` · torso · ropa · largo='medio_muslo', jirones=3, sin_mangas=True
- `tatuaje_runas` · brazo_derecho, brazo_izquierdo · runa · puntos_por_segmento=1
- `torso_humano` · torso · piel · —
- `torso_skin` · torso · — · skin=None
- `tunica_abierta` · torso · tunica · interior=None, ribete=None, faldon='hasta_rodilla', mangas=True
- `vincha` · frente · oro · gema=None
- `visor` · ojo_derecho, ojo_izquierdo · metal · lente=None, tamano_min_px=2

## Módulos
### `escala` — Escala del juego: el mismo personaje mide lo mismo en todos los estilos de su clase, y todas las
- clase `EscalaError`
- `alto_objetivo_px(estilo, clase='adulto')`
- `celda(estilo, clase='adulto', ancho=None)` ancho: ancho propio de una animación (ver poses.ancho); el alto y los pies no cambian.

### `paleta` — Paleta de un personaje por estilo: la ficha da solo el tono base de cada material; el estilo deriva
- `hex_rgb(h)`
- `tonos(base, regla, emisivo=False)` (sombra, base, luz). Los emisivos (runas, visor) no se oscurecen: brillan igual en todos lados.
- `paleta_estilo(paleta_ficha, estilo)` {material: (sombra, base, luz)}. Agrega '<material>_b' (variante un poco más oscura para texturas:
- `reducir_paleta(por_dir, n)` Deja a lo sumo `n` colores en TODAS las direcciones y cuadros a la vez ({dir: [imágenes RGBA]}, in situ).

### `estilos` — Perfiles de estilo: cómo se "ve" un sprite, independiente de qué personaje es y de cómo se mueve.
- `uz(estilo)` Cuántos px de pantalla ocupa 1 unidad de altura del mundo en ese estilo.
- `crear_camara(estilo, mira, celda)` Cámara del estilo para una dirección y una celda (ver escala.celda).

### `cuerpo` — Esqueleto base humano: proporciones por estilo y clase, vocabulario fijo de anclas y pose → posiciones 3D.
- `lado_de(ancla)`
- `masc(lado)`
- clase `Anatomia`
- `anatomia(estilo, clase='adulto', complexion='normal')`
- `fuerza_cara(prop, cam_local)` Cuánto se corre la cara hacia la cámara. Los estilos de 8 direcciones pueden dar una fuerza propia a las
- `giro_cabeza(prop, mira)` Ángulo con que se gira la caja de la cabeza para que su silueta mida lo mismo en todas las direcciones
- `radios_cabeza(prop, mira, radios)` Radios de la caja de la cabeza. 'cabeza_diagonal' (< 1) angosta la cabeza en las 4 diagonales, como los juegos
- `desvio_cabeza(prop, mira)` Vector local (adelante, izquierda) que corre la cabeza en pantalla 'cabeza_desvio[mira]' px hacia un costado
- `sobre_caja(hc, d, radios, giro, n=3.2, k=1.02)` Punto de la superficie de la caja de la cabeza (superelipsoide de radios 'radios' girada 'giro' alrededor de la
- `centro_cara(cam_local, fuerza=0.9)` Trampa de Stardew: la cara se corre hacia la cámara. De frente queda adelante; de perfil, sobre el costado
- `anclas_ausentes(lista)` Anclas que no existen: las nombradas y, para un segmento, todo menos su raíz (sin antebrazo queda el codo).
- `posar(anat, ps, cam_local, mira=None)` Posiciones 3D (ejes locales) de todas las anclas para una pose (formato de ciclos.pose / poses.cuadros).

### `poses` — Poses clave como datos (mismo formato que los ciclos: rig lateral, piso y=34, cadera x=18).
- `cuadros(nombre)`
- `fps(nombre)`
- `loop(nombre)` Si la animación se repite (caminar, quieto) o se juega una sola vez (saltar). Depende de la animación,
- `offset_y(nombre)` Cuánto tiene que levantar el motor el sprite por cuadro (px de juego, negativo = arriba) o None si el
- `ancho(nombre, estilo)` Ancho de celda propio de la animación en ese estilo (px) o None si usa el del estilo. Cada animación ocupa lo

### `ciclos` — Ciclos de movimiento reutilizables, en coordenadas del "rig lateral".
- `mano(ciclo, p, clave='mano')` Posición de la mano del brazo A en el cuadro p (coordenadas del rig lateral).
- `pose(ciclo, p)` Todo lo que cambia por cuadro, para las extremidades A (cercana) y B (lejana).

### `rig` — Cinemática inversa de dos huesos (cadera→rodilla→tobillo, hombro→codo→mano).
- `ik(a, b, l1, l2, bend)` Articulación intermedia entre a y b en 2D (y hacia abajo).

### `render3d` — Motor de sprites isométricos con volumen: muñeco 3D de primitivas "fotografiado" en pixel art.
- `v(f, l, u)`
- clase `Camara`  · métodos: a_mundo, proyectar
- clase `CamaraCenital` Vista cenital 3/4 (top-down tipo Stardew Valley/Zelda): piso de grilla cuadrada, 4 direcciones. · métodos: a_mundo, proyectar
- clase `CamaraLateral` Vista de costado ortográfica (plataformas): sin inclinación; x = adelante, y = −arriba.
- clase `Escena` Acumula puntos de superficie (posición, normal, material, pieza, componente) en ejes locales. · métodos: esfera, elipsoide, caja, capsula, faldon, detalle, render
- `ik_sagital(a, b, l1, l2, doblez)` IK en el plano (adelante, arriba) del personaje; l se conserva. doblez=+1 rodilla, -1 codo.
- `ik_3d(a, b, l1, l2, polo)` IK de dos huesos en 3D: la articulación intermedia se dobla hacia 'polo' (p. ej. (1,0,0) rodilla adelante,
- `sombra(camara, rx=10.0, ry=4.6, col=(10, 8, 18, 210))` Sombra 2:1 con dithering bajo el punto de apoyo.
- `piso_iso(w, h, desplazamiento=0.0, direccion='SE')` Piso de baldosas 32x16 que se desplaza en la dirección de avance (para GIF de escena).

### `armado` — Armado: ficha → lista de componentes (cuerpo base + los de la ficha) → escena → cuadros renderizados.
- `expandir(ficha)` Specs finales, una por (tipo, ancla): cuerpo base (salvo sustituciones o componentes propios del mismo
- clase `Cuadro`
- `render_cuadro(ficha, estilo, pose, p, mira, ancho=None)`
- `render_todo(ficha, estilo, poses=('neutra', 'quieto'))`
- `pivote(estilo, clase_altura='adulto', pose='quieto')` Punto de los pies (piso) dentro de la celda: el mismo para cualquier pose/dirección/personaje de ese

### `ficha` — Fichas de personaje: cargar el YAML y validarlo antes de generar nada. Los errores dicen qué está mal y,
- clase `FichaInvalida`
- `validar(f, estilos=None)`
- `cargar(ruta_o_nombre, validar_=True, estilos=None)`

### `tests_personaje` — Tests de consistencia de un personaje sobre todos sus cuadros renderizados (todas las poses y direcciones).
- clase `Resultado`
- `mascara(cuadro, comp_id)` Píxeles del componente, incluidas sus partes ('ojos@cara#ojo_izquierdo' es parte de 'ojos@cara').
- `partes(cuadro, comp_id)` El componente y cada una de sus partes, como 'rasgos' que se miden por separado.
- `ancla_visible(cuadro, ancla, tol=None)` Un ancla está a la vista si en el píxel donde se proyecta se ve la pieza que la contiene (el brazo para el
- `t_visibilidad(ficha, todo)`
- `t_ausentes(ficha, todo)`
- `c_anclas(todo)`
- `t_lineas_guia(ficha, todo, tol=1.5)`
- `colores_permitidos(ficha, estilo)`
- `t_paleta(ficha, estilo, todo)`
- `t_tamano(ficha, estilo, todo)`
- `t_recorte(todo)` Arriba no se toca nunca (ahí se cortan pelo y sombreros). A los costados puede llegar el contorno (Stardew
- `t_cara(ficha, estilo, todo)`
- `t_simetria(ficha, estilo, todo)`
- `t_distinto(ficha)`
- `t_estilo(ficha, estilo, todo, carpeta)`
- `correr_tests(ficha, estilo, todo, carpeta)`
- `informe_md(ficha, estilo, resultados)`

### `proporciones` — Contrato numérico del muñeco por estilo: mide el render real y lo compara con el perfil.
- `medir(estilo, clase='adulto')` Medidas del render real (píxeles) en todas las direcciones: resumen de la primera + `por_direccion`.
- `comparar(estilo, clase='adulto')` Compara el resumen contra el perfil del estilo; `Resultado` con el detalle de cada desvío.

### `comparar_estilo` — Comparar el estilo de un sprite propio contra una referencia con métricas objetivas.
- `metricas_cuadro(a)`
- `metricas(ruta, celda, recorte=None)`
- `comparar_detalle(ref, mio)` Compara las métricas una por una y devuelve la lista estructurada (sin imprimir).
- `comparar(ref, mio)`

### `hoja_modelo` — Hoja de modelo: todas las direcciones alineadas por pose, con líneas guía (coronilla, ojos, hombros, cintura,
- `hoja(ficha, estilo, todo, resultados, ruta)`

### `fotos_control` — Fotos de control: las poses aprobadas por el usuario quedan congeladas (versionadas en git). Si un cambio
- `carpeta(nombre, estilo, raiz=None)` Carpeta de las fotos de control: `<raiz>/<nombre>/<estilo>`; con `raiz=None` usa `DIR`
- `guardar(nombre, estilo, todo, raiz=None)`
- `comparar(nombre, estilo, todo, carpeta_dif, raiz=None)` Compara los cuadros con los congelados en `raiz`; sin carpeta aprobada queda omitido.

### `exportar` — Exportación genérica de animaciones (sirve para cualquier motor).
- `revision(frames, ruta, zoom=5, columnas=5)`
- `exportar(frames, nombre, carpeta, fps=12, pivote=None, zoom=4, extra=None, loop=True)`
- `exportar_direcciones(por_dir, nombre, carpeta, fps=12, pivote=None, zoom=3, loop=True, extra=None, cuadros=False)` por_dir: {"SE": [frames], "E": [...], ...} → hoja con una fila por dirección + JSON + GIF por dirección.

### `referencia` — Separar sprite sheets de referencia en animaciones.
- `color_fondo(a)`
- `paneles(ruta)`
- `detectar(ruta, carpeta, panel=None, fondo=None, area_min=120, pegar=3, tol_fila=14)`
- `cortar(ruta_cfg)`

### `analizar` — Medir una animación de referencia píxel por píxel.
- `analizar(ruta, cw, ch, carpeta)`

### `pixel2d` — Herramientas para sprites 2D planos (vista lateral): capas con contorno propio y trazos pixelados.
- clase `Lienzo` Tamaño de celda y desplazamiento x del rig lateral dentro de la celda. · métodos: capa, P, seg, puntos, ascii
- `contorno(im, col)` Contorno de 1 px alrededor de todo lo opaco de la capa.
- `apilar(cw, ch, capas)` Compone capas de atrás hacia adelante.

### `lado_a_lado` — Comparación visual ampliada: cuadros de referencia y propios intercalados, para revisarlos con Read.
- `lado_a_lado(salida, items, zoom=14)`

### `comparar_plantilla` — Comparar una plantilla de movimiento contra la referencia de la que salió: huesos y silueta, cuadro por cuadro.
- `medir(estilo='lpc', pose='caminar_lpc', mira='E')` Por cuadro: silueta (IoU) y error de cada hueso; el muñeco se corre en x una sola vez para toda la tira.
- `imagen(res, ruta, zoom=6)` Tres filas: LPC, nuestro muñeco y siluetas superpuestas (azul LPC, rojo nuestro, violeta coinciden)
- `resumen(res)`

### `skins` — Skins tipo Minecraft: el muñeco base y sus animaciones son siempre los mismos; un personaje es solo un PNG de
- `material(c)`
- clase `Skin`  · métodos: color, zona, paleta
- `cargar(ruta)`
- `u_de(d, ref=0.0)` Ángulo alrededor del eje vertical → u (0.5 = hacia ref, que por defecto es adelante).
- `continuidad(ruta_o_skin)` Zonas cuya costura trasera no cierra. La columna 0 y la última de una zona son el mismo punto del cuerpo
- `columnas_por_direccion(estilo)` Columna (0..w-1) que muestrea cada dirección del estilo en cada zona de la skin. El cuerpo gira alrededor
- `desde_colores(colores, ruta)` Skin simple a partir de colores (como la skin por defecto de Minecraft): pelo arriba y atrás, remera con
- `plantilla_zonas(ruta='skins/zonas.png')` Skin de zonas: cada parte del cuerpo de un color distinto (la cara y el frente del torso, aparte).
- `ficha_con_arma(ruta, arma='espada', nombre=None, ancla='mano_derecha')` Ficha de una skin con un arma en la mano: la misma skin y las mismas animaciones, más el componente `objeto`.
- `ficha(ruta, nombre=None)` Ficha mínima para renderizar una skin con el pipeline de siempre (render_cuadro, tests, exportar).
- `guia(ruta, zoom=16, estilo='stardew8')` PNG ampliado con cada zona rotulada, el frente marcado y la columna que muestrea cada dirección del estilo
- `demo(ruta, anim='caminar_lpc', estilo='stardew')` Vista previa rápida (una skin cualquiera): docs/diagnostico/skins/<nombre>/<anim>*
- `salida_juego(ruta, anim='caminar_lpc', estilo='stardew', raiz='salida', cuadros=False)` Salida final del juego (convención del proyecto): <raíz>/<personaje>/<estilo>/<anim>/<anim>*.
- `salida_arma(ruta, arma='espada', anim='golpear', estilo='stardew', raiz='salida', cuadros=False, ancla='mano_derecha')` Salida de una skin con un arma en la mano, mismo layout que `salida_juego`:

### `muneco` — Muñeco base: sin skin ni ficha de personaje, solo para ver y probar un ciclo/pose antes de aplicarlo a alguien
- `demo(anim='caminar_lpc', estilo='stardew')`
- `ancho_necesario(anim='caminar_lpc', estilo='stardew8', margen=1)` Ancho de celda (par) que necesita la animación: se renderiza en una celda enorme con el muñeco y se mide cuánto
- `objetos(anim='golpear', estilo='lateral', mira=None, formas=None, ruta=None, zoom=6)` Misma animación, distintas cosas en la mano: una fila por forma, una columna por cuadro. Sirve para
- `grilla(anim='caminar_lpc', estilo='stardew8', ruta=None, zoom=6, cuadros=None)` Plantilla de zonas: una fila por dirección, una columna por cuadro (skins/zonas.png), para revisar a ojo.

### `zonas` — Zonas del cuerpo por cuadro: dónde está cada parte (cabeza, cada ojo, cada brazo...) y cómo cambia de un cuadro
- `ficha_plantilla()`
- `clasificar(cuadro, ficha, estilo, plantilla=None)` Mapa de zonas del cuadro: array (alto, ancho) con el índice en ZONAS (-1 = transparente) y la máscara del
- `medir(zm)` {zona: {px, bbox [x0,y0,x1,y1], centro [x,y]} | None} para todas las ZONAS ('otro' incluido).
- `analizar(anim='caminar_lpc', estilo='stardew8', dirs=None, cuadros=None, ficha=None)` Dict con las zonas por dirección y cuadro, las alertas y los datos del resumen. ficha=None: muñeco de zonas.
- `marcar_falsas(out, res)` Agrega a cada alerta el campo 'fp' (None = por revisar; texto = falsa conocida y por qué). Las falsas NO se
- `alertas(res, extra)`
- `informe(res, completo=False)` Texto compacto para un LLM: por dirección, ALERTAS primero (agrupadas por zona y tipo) y la tabla de centros
- `para_json(res)`
- `imagen(zm, anillo=None)` PNG RGBA de un mapa de zonas: cada zona con su color plano de COLORES (el contorno exterior, más oscuro).
- `png(res, ruta, zoom=6)` Una fila por dirección, una columna por cuadro, con los colores planos de zona.
- `main(argv=None)`

### `pulido` — Modo pulido: lo que hace que una animación se vea BONITA (no solo bien construida), medido en números y texto.
- `referencia_lpc(ruta=REF_LPC)` Amplitud del balanceo en la referencia LPC de perfil (E), relativa al alto del personaje (piso − coronilla):
- `movimiento(res, zres_alertas, desfase)`
- `limpieza(res, ficha, estilo, zres_alertas)`
- `espejo(res, estilo, desfase, asimetrica=False)` asimetrica: la animación mueve distinto los lados A y B (el ciclo trae 'mano_b'/'pie_b', p. ej. golpear): el
- `analizar(anim='caminar_lpc', estilo='stardew8', dirs=None, ficha=None)` Hallazgos de pulido (movimiento, limpieza, espejo) + medidas + resumen. ficha=None: muñeco de zonas.
- `resumen(pul)`
- `informe(pul, max_por_grupo=6, max_leves=3)`
- `para_json(pul)`
- `main(argv=None)`

### `estado` — Estado de artefactos aprobados: hash de la fuente, fecha y detección de deriva.
- `canonico(obj)` Serialización canónica de un objeto (claves ordenadas) para que el hash sea estable.
- `hash_obj(obj)` Hash `sha256:` de un objeto JSON-serializable, independiente del orden de las claves.
- `hash_archivo(ruta)` Hash `sha256:` de los bytes de un archivo; `sha256:falta` si no existe.
- `escribir(carpeta, artefacto, fuentes, metricas, nota=None)` Congela un artefacto aprobado: escribe `<carpeta>/estado.json` y devuelve su ruta.
- `leer(carpeta)` Carga `<carpeta>/estado.json`, o `None` si el artefacto no está aprobado.
- `deriva(estado_dict, fuentes)` Claves con hash distinto o ausentes de cualquiera de los dos lados (simétrico), ordenadas.
- `listar(raiz)` Lista los artefactos aprobados bajo `raiz` (nombre, estilo, carpeta y estado), ordenados.

### `gates` — Motor de gates: corre checks y arma un veredicto VERDE/ROJO con evidencia para el agente.
- clase `Veredicto`
- `correr(checks)` Ejecuta cada check (callable sin argumentos); si uno explota, ese check queda rojo con la excepción.
- `informe(v)` Texto legible: primera línea `VERDE (n/m)` o `ROJO (k fallan)`, y después cada fallo con hasta 5 evidencias.
- `guardar(v, ruta)` Escribe el veredicto en `ruta` como JSON (`verde`, `informe` legible y un objeto por check); devuelve la ruta.
- `check_determinismo(estilo, pose='quieto', mira=None, veces=2, ficha=None)` Renderiza `veces` veces en el mismo (pose, mira) y compara los píxeles entre corridas. La ficha es la del
- `check_deriva(estado_dict, fuentes, regla='deriva')` Compara las fuentes actuales contra las aprobadas; sin aprobación previa el check queda omitido (pasa).
- `check_zonas(anim, estilo, ficha=None, dirs=None)` Gate de zonas: ninguna alerta MEDIA/ALTA por revisar (sin `fp`), contando las de borde solo si el sólido
- `check_pulido(anim, estilo, ficha=None, dirs=None)` Gate de pulido: ningún hallazgo MAL por revisar (sin `fp`) en movimiento, limpieza ni espejo. El detalle

### `proceso_estilo` — Proceso de estilo: medir, validar y congelar el perfil de un estilo.
- `fuentes_actuales(estilo)` Fuentes del estilo para el hash de deriva: perfil completo y escala (hash estable por claves ordenadas).
- `check_referencia(estilo)` Compara la referencia calibrada con el espécimen vestido del estilo (omitido si falta algún dato).
- `correr_gate(estilo)` Veredicto del estilo: contrato del muñeco, determinismo, referencia calibrada y deriva de las fuentes.
- `medir(estilo)` Imprime las métricas de la referencia (si hay) y las del muñeco; no escribe nada.
- `validar(estilo)` Imprime el informe del gate; devuelve 0 si es VERDE y 1 si es ROJO.
- `aprobar(estilo, excepcion=None)` Congela el estilo (control, métricas, doc si falta y `estado.json` último); ROJO sin excepción no escribe.
- `main(argv=None)` CLI del proceso de estilo: devuelve 0 VERDE, 1 ROJO y 2 error de uso o estilo desconocido.

### `proceso_anim` — Proceso de animación: smoke, validar y aprobar una animación sobre una skin, con los gates universales.
- `detalle_checks(v)` Una línea por check con su `detalle`, para ver el estado de cada gate aunque el veredicto sea VERDE.
- `smoke(anim, estilo, direccion=None, skin=SKIN_DEFECTO)` Gate de humo de una animación: una dirección con esa skin; imprime el informe y el detalle de cada check,
- `fuentes_actuales(anim)` Fuentes de la animación para el hash de deriva: el ciclo entero (hash estable por claves ordenadas).
- `check_plantilla(anim)` Compara el ciclo contra su referencia (`REFERENCIAS`): exige error medio de huesos ≤ `TOL_MEDIO` px; el
- `correr_gate(anim, estilo, ficha, todo=None)` Veredicto de la animación: zonas y pulido en todas las direcciones, determinismo, deriva del ciclo,
- `validar(anim, estilo, skin=SKIN_DEFECTO)` Renderiza todas las direcciones y corre el gate completo; imprime informe y detalle; 0 VERDE / 1 ROJO.
- `aprobar(anim, estilo, skin=SKIN_DEFECTO, excepcion=None)` Corre el gate completo (incluida la comparación con los cuadros de control ya congelados: un cambio de
- `main(argv=None)` CLI del proceso de animación: devuelve 0 VERDE, 1 ROJO y 2 error de uso o nombre desconocido.

### `proceso_skin` — Proceso de skin: smoke, aprobar y lote de una skin pintada.
- `check_carga(ruta)` La skin carga con `skins.cargar` y mide 32×32 (la medida la valida el propio cargador); cualquier falla de
- `check_continuidad(ruta)` La espalda de cada zona de la skin cierra: la columna 0 y la última son el mismo texel (u da la vuelta en
- `correr_gate(ruta, anim='quieto', estilo='stardew')` Veredicto de la skin en esa pose: carga 32×32, costura de la espalda, zonas y pulido de su ficha, y
- `smoke(nombre, anim='quieto', estilo='stardew')` Corre el gate de la skin y imprime el informe; devuelve 0 VERDE / 1 ROJO.
- `fuentes_skin(nombre)` Fuentes de la skin para congelar/derivar: el PNG y, si existe, el script que la pinta
- `aprobar(nombre, estilo='stardew', excepcion=None)` Corre el gate de `smoke` y, si está VERDE o hay `excepcion`, congela la skin en `aprobados/skins/<nombre>/`
- `lote(nombre, estilo='stardew', raiz='output')` Exporta en formato del juego todas las animaciones aprobadas del estilo con esta skin.
- `main(argv=None)` CLI del proceso de skin: devuelve 0 VERDE, 1 ROJO y 2 error de uso, nombre inválido o skin inexistente.

### `componentes` — Biblioteca de componentes: cada pieza de un personaje (cabeza, brazo robótico, pulsera...) sabe dibujarse
- clase `Componente`  · métodos: dibujar
- `registrar(cls)`
- clase `Contexto`  · métodos: ausente, escala
- `entrar(esc, ctx, spec, k=0)` Marca lo que se dibuje a continuación como parte de este componente y de su pieza k.
- `perpendicular(eje)` Un vector unitario perpendicular a eje (si el eje es vertical, usa el lateral).
