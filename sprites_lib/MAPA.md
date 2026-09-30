# Mapa de sprites_lib (generado: `.venv/bin/python -m sprites_lib.mapa`, no editar a mano)

Flujo: ficha YAML → `ficha.cargar` → `armado.render_cuadro` (cuerpo base + componentes → `cuerpo.posar` → `render3d.Escena`) → `Cuadro` (img + buffers) → tests / hoja / exportar.

## Estilos
| estilo | vista | direcciones | adulto px | celda | activo |
|---|---|---|---|---|---|
| volumen | iso | SE E NE N NW W SW S | 36 | 56×60 | no |
| stardew | cenital | S E N W | 26 | 16×32 | sí |
| lateral | lateral | E W | 33 | 40×40 | sí |
| lpc | lateral | E W | 43 | 64×64 | no |

## Anclas
antebrazo_derecho, antebrazo_izquierdo, brazo_derecho, brazo_izquierdo, cabeza, cadera_derecha, cadera_izquierda, cara, cintura, codo_derecho, codo_izquierdo, coronilla, cuello, frente, hombro_derecho, hombro_izquierdo, mano_derecha, mano_izquierda, muneca_derecha, muneca_izquierda, nuca, ojo_derecho, ojo_izquierdo, pecho, pie_derecho, pie_izquierdo, pierna_derecha, pierna_izquierda, rodilla_derecha, rodilla_izquierda, sien_derecha, sien_izquierda, suelo, tobillo_derecho, tobillo_izquierdo, torso

## Componentes (tipo · anclas · material por defecto · parámetros)
- `botas` · pie_derecho, pie_izquierdo · bota · suela=None
- `brazo_humano` · brazo_derecho, brazo_izquierdo · piel · —
- `brazo_robotico` · brazo_derecho, brazo_izquierdo · metal · juntas=None, rayas=None, mano='pinza_3_dedos'
- `brazo_robotico_amputado` · brazo_derecho, brazo_izquierdo · metal · termina_en=None, juntas=None
- `brazo_skin` · brazo_derecho, brazo_izquierdo · — · skin=None
- `cabeza_humana` · cabeza · piel · cabello='corto'
- `cabeza_skin` · cabeza · — · skin=None
- `cables_nuca` · nuca · cable · cables=2, luz_en_punta=None, largo='corto'
- `cinturon` · cintura · cuero · hebilla=None
- `munon_cables` · codo_derecho, codo_izquierdo, rodilla_derecha, rodilla_izquierda · cable · cables=3, largo_px=2, chispa=None, chispa_cada_cuadros=3
- `ojos` · cara · — · solo=None, iris=None
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
- `celda(estilo, clase='adulto')`

### `paleta` — Paleta de un personaje por estilo: la ficha da solo el tono base de cada material; el estilo deriva
- `hex_rgb(h)`
- `tonos(base, regla, emisivo=False)` (sombra, base, luz). Los emisivos (runas, visor) no se oscurecen: brillan igual en todos lados.
- `paleta_estilo(paleta_ficha, estilo)` {material: (sombra, base, luz)}. Agrega '<material>_b' (variante un poco más oscura para texturas:

### `estilos` — Perfiles de estilo: cómo se "ve" un sprite, independiente de qué personaje es y de cómo se mueve.
- `uz(estilo)` Cuántos px de pantalla ocupa 1 unidad de altura del mundo en ese estilo.
- `crear_camara(estilo, mira, celda)` Cámara del estilo para una dirección y una celda (ver escala.celda).

### `cuerpo` — Esqueleto base humano: proporciones por estilo y clase, vocabulario fijo de anclas y pose → posiciones 3D.
- `lado_de(ancla)`
- `masc(lado)`
- clase `Anatomia`
- `anatomia(estilo, clase='adulto', complexion='normal')`
- `centro_cara(cam_local, fuerza=0.9)` Trampa de Stardew: la cara se corre hacia la cámara. De frente queda adelante; de perfil, sobre el costado
- `anclas_ausentes(lista)` Anclas que no existen: las nombradas y, para un segmento, todo menos su raíz (sin antebrazo queda el codo).
- `posar(anat, ps, cam_local)` Posiciones 3D (ejes locales) de todas las anclas para una pose (formato de ciclos.pose / poses.cuadros).

### `poses` — Poses clave como datos (mismo formato que los ciclos: rig lateral, piso y=34, cadera x=18).
- `cuadros(nombre)`
- `fps(nombre)`

### `ciclos` — Ciclos de movimiento reutilizables, en coordenadas del "rig lateral".
- `mano(ciclo, p)` Posición de la mano del brazo A en el cuadro p (coordenadas del rig lateral).
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
- `render_cuadro(ficha, estilo, pose, p, mira)`
- `render_todo(ficha, estilo, poses=('neutra', 'quieto'))`

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

### `comparar_estilo` — Comparar el estilo de un sprite propio contra una referencia con métricas objetivas.
- `metricas_cuadro(a)`
- `metricas(ruta, celda, recorte=None)`
- `comparar(ref, mio)`

### `hoja_modelo` — Hoja de modelo: todas las direcciones alineadas por pose, con líneas guía (coronilla, ojos, hombros, cintura,
- `hoja(ficha, estilo, todo, resultados, ruta)`

### `fotos_control` — Fotos de control: las poses aprobadas por el usuario quedan congeladas (versionadas en git). Si un cambio
- `carpeta(nombre, estilo)`
- `guardar(nombre, estilo, todo)`
- `comparar(nombre, estilo, todo, carpeta_dif)`

### `exportar` — Exportación genérica de animaciones (sirve para cualquier motor).
- `revision(frames, ruta, zoom=5, columnas=5)`
- `exportar(frames, nombre, carpeta, fps=12, pivote=None, zoom=4, extra=None)`
- `exportar_direcciones(por_dir, nombre, carpeta, fps=12, pivote=None, zoom=3)` por_dir: {"SE": [frames], "E": [...], ...} → hoja con una fila por dirección + JSON + GIF por dirección.

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
- `desde_colores(colores, ruta)` Skin simple a partir de colores (como la skin por defecto de Minecraft): pelo arriba y atrás, remera con
- `ficha(ruta, nombre=None)` Ficha mínima para renderizar una skin con el pipeline de siempre (render_cuadro, tests, exportar).
- `guia(ruta, zoom=16)` PNG ampliado con cada zona rotulada y el frente marcado: la plantilla para pintar una skin a mano.
- `demo(ruta, anim='caminar_lpc', estilo='stardew')`

### `componentes` — Biblioteca de componentes: cada pieza de un personaje (cabeza, brazo robótico, pulsera...) sabe dibujarse
- clase `Componente`  · métodos: dibujar
- `registrar(cls)`
- clase `Contexto`  · métodos: ausente, escala
- `entrar(esc, ctx, spec, k=0)` Marca lo que se dibuje a continuación como parte de este componente y de su pieza k.
- `perpendicular(eje)` Un vector unitario perpendicular a eje (si el eje es vertical, usa el lateral).
