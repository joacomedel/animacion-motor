"""Skins tipo Minecraft: el muñeco base y sus animaciones son siempre los mismos; un personaje es solo un PNG de
32×32 con cada parte del cuerpo "desenrollada" (centro = frente, bordes = espalda, arriba = la punta de la parte).

Cada punto del muñeco 3D sabe en qué zona cae y en qué (u, v) de la zona: toma ese color. Sombras, luces y contorno
los pone el estilo, así que la skin se pinta con colores planos. La cara (ojos, boca) no se pinta: a 6 px no se lee;
la dibuja el componente `ojos` con el iris de la skin.

Uso:  .venv/bin/python -m sprites_lib.skins guia                     → skins/guia.png (zonas rotuladas, para pintar)
      .venv/bin/python -m sprites_lib.skins demo  [skin.png] [--anim caminar_lpc]  → docs/diagnostico/skins/<nombre>/ (vista previa)
      .venv/bin/python -m sprites_lib.skins juego [skin.png] [--anim caminar_lpc]  → <raíz>/<nombre>/<estilo>/<anim>/ (salida del juego)
      .venv/bin/python -m sprites_lib.skins arma  [skin.png] [--arma espada] [--anim golpear] [--estilo stardew]
                                                                                     → <personaje>/<estilo>/<anim>_<arma>/
"""

import functools
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

LADO = 32
ZONAS = {  # nombre: (x, y, ancho, alto) en el PNG
    "cabeza": (0, 0, 24, 10),
    "torso": (0, 10, 16, 10),
    # brazos y pies de 8 de ancho: con 4 texeles las 8 direcciones colapsaban en 4 columnas y las
    # mangas/puños/hebillas saltaban de a dos direcciones (u da la vuelta en el ancho de la zona)
    "brazo_derecho": (16, 10, 8, 8),
    "brazo_izquierdo": (24, 10, 8, 8),
    "mano_derecha": (16, 18, 4, 2),
    "mano_izquierda": (20, 18, 4, 2),
    "iris": (24, 18, 1, 1),
    "pierna_derecha": (0, 20, 8, 10),
    "pierna_izquierda": (8, 20, 8, 10),
    "pie_derecho": (16, 20, 8, 3),
    "pie_izquierdo": (24, 20, 8, 3),
}
CARA = (12, 6)  # texel de piel de la cara (color de la ficha para 'piel')
PELO = (12, 0)  # texel de la coronilla (color para 'pelo': cejas)


def _hex(c):
    return "#%02x%02x%02x" % tuple(int(x) for x in c[:3])


def material(c):
    return "sk_" + _hex(c)[1:]


class Skin:
    def __init__(self, img):
        a = np.array(img.convert("RGBA"))
        if a.shape[:2] != (LADO, LADO):
            raise ValueError(
                f"la skin tiene que medir {LADO}×{LADO} (mide {a.shape[1]}×{a.shape[0]})"
            )
        self.a = a
        cara = a[CARA[1], CARA[0]]
        self.nombres = np.empty((LADO, LADO), dtype=object)
        for y in range(LADO):
            for x in range(LADO):
                px = a[y, x] if a[y, x, 3] else cara  # transparente = piel
                self.nombres[y, x] = material(px)

    def color(self, x, y):
        return tuple(int(c) for c in self.a[y, x, :3])

    def zona(self, nombre, u, v):
        """Nombres de material para arrays u∈[0,1) (0.5 = frente) y v∈[0,1] (0 = arriba)."""
        x0, y0, w, h = ZONAS[nombre]
        xi = x0 + np.clip(np.floor(np.asarray(u) % 1.0 * w), 0, w - 1).astype(int)
        yi = y0 + np.clip(np.floor(np.asarray(v) * h), 0, h - 1).astype(int)
        return self.nombres[yi, xi]

    def paleta(self):
        """Paleta de ficha: un material por color usado, más 'piel', 'pelo' e 'iris' (los usa el componente ojos)."""
        vistos = {tuple(c) for c in self.a[..., :3][self.a[..., 3] > 0].tolist()}
        pal = {material(c): {"base": _hex(c)} for c in sorted(vistos)}
        for clave, (x, y) in (
            ("piel", CARA),
            ("pelo", PELO),
            ("iris", ZONAS["iris"][:2]),
        ):
            pal[clave] = {"base": _hex(self.color(x, y))}
        return pal


@functools.lru_cache(maxsize=32)
def _cargar(ruta, _mtime):
    return Skin(Image.open(ruta))


def cargar(ruta):
    return _cargar(ruta, os.path.getmtime(ruta))


def u_de(d, ref=0.0):
    """Ángulo alrededor del eje vertical → u (0.5 = hacia ref, que por defecto es adelante)."""
    return (np.arctan2(d[..., 1], d[..., 0]) - ref) / (2 * math.pi) + 0.5


def continuidad(ruta_o_skin):
    """Zonas cuya costura trasera no cierra. La columna 0 y la última de una zona son el mismo punto del cuerpo
    (u da la vuelta en la espalda), así que tienen que coincidir fila a fila: si no, en las vistas de espalda
    (N/NE/NW) aparece una costura. Devuelve `[(zona, filas_que_no_cierran), ...]` (vacío = cierra)."""
    sk = ruta_o_skin if isinstance(ruta_o_skin, Skin) else cargar(ruta_o_skin)
    a = sk.a
    malas = []
    for nombre, (x0, y0, w, h) in ZONAS.items():
        borde0, borde1 = a[y0 : y0 + h, x0], a[y0 : y0 + h, x0 + w - 1]
        n = int((borde0 != borde1).any(axis=1).sum())
        if n:
            malas.append((nombre, n))
    return malas


def columnas_por_direccion(estilo):
    """Columna (0..w-1) que muestrea cada dirección del estilo en cada zona de la skin. El cuerpo gira alrededor
    del eje vertical (`u_de` con ref=0); la cabeza usa la cara corrida hacia la cámara (`centro_cara` + fuerza de
    su estilo), igual que `CabezaSkin`. Permite pintar la skin sabiendo dónde cae cada dirección."""
    from .cuerpo import centro_cara, fuerza_cara
    from .escala import celda
    from .estilos import ESTILOS, crear_camara
    from .poses import ancho as _ancho

    e = ESTILOS[estilo]
    prop = e["proporciones"]
    cols = {}
    for mira in e["direcciones"]:
        cam = crear_camara(
            estilo, mira, celda(estilo, "adulto", _ancho("quieto", estilo))
        )
        cl = np.asarray(cam.cam_local, float)
        d = np.array([cl[0], cl[1], 0.0])
        n = np.linalg.norm(d)
        d = d / n if n > 1e-9 else d
        c = centro_cara(cl, fuerza_cara(prop, cl))
        ref = math.atan2(c[1], c[0])
        cols[mira] = {}
        for nombre, (x0, y0, w, h) in ZONAS.items():
            u = u_de(d, ref) if nombre == "cabeza" else u_de(d)
            cols[mira][nombre] = int(
                np.clip(np.floor(np.asarray(u) % 1.0 * w), 0, w - 1)
            )
    return cols


def desde_colores(colores, ruta):
    """Skin simple a partir de colores (como la skin por defecto de Minecraft): pelo arriba y atrás, remera con
    mangas, pantalón y calzado. Claves: piel, pelo, remera, pantalon, calzado, iris, mangas ('cortas'|'largas')."""
    c = {
        k: tuple(int(colores[k][i : i + 2], 16) for i in (1, 3, 5))
        for k in ("piel", "pelo", "remera", "pantalon", "calzado", "iris")
    }
    a = np.zeros((LADO, LADO, 4), np.uint8)

    def pintar(zona, col, filas=None, cols=None):
        x0, y0, w, h = ZONAS[zona]
        for yy in range(h) if filas is None else filas:
            for xx in range(w) if cols is None else cols:
                a[y0 + yy, x0 + xx] = (*col, 255)

    pintar("cabeza", c["piel"])
    pintar("cabeza", c["pelo"], filas=range(0, 3))  # coronilla
    pintar(
        "cabeza", c["pelo"], filas=range(3, 8), cols=[*range(0, 6), *range(18, 24)]
    )  # nuca y costados atrás
    pintar("cabeza", c["pelo"], filas=[3], cols=range(6, 18))  # flequillo
    pintar("torso", c["remera"])
    for lado in ("derecho", "izquierdo"):
        pintar(f"brazo_{lado}", c["piel"])
        pintar(
            f"brazo_{lado}",
            c["remera"],
            filas=range(0, 8 if colores.get("mangas") == "largas" else 3),
        )
        pintar(f"pie_{lado}", c["calzado"])
    for lado in ("derecha", "izquierda"):
        pintar(f"mano_{lado}", c["piel"])
        pintar(f"pierna_{lado}", c["pantalon"])
    pintar("iris", c["iris"])
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    Image.fromarray(a, "RGBA").save(ruta)
    return ruta


# Plantilla de depuración: un color plano por zona (derecha cálidos, izquierda fríos) para ver qué se mueve dónde.
COLORES_ZONAS = {
    "cabeza_frente": "#ffe0b2",
    "cabeza_resto": "#6d4c41",
    "torso_frente": "#fafafa",
    "torso_espalda": "#546e7a",
    "brazo_derecho": "#e53935",
    "mano_derecha": "#ff9800",
    "pierna_derecha": "#ad1457",
    "pie_derecho": "#fdd835",
    "brazo_izquierdo": "#1e88e5",
    "mano_izquierda": "#00bcd4",
    "pierna_izquierda": "#3949ab",
    "pie_izquierdo": "#43a047",
    "iris": "#000000",
}


def plantilla_zonas(ruta="skins/zonas.png"):
    """Skin de zonas: cada parte del cuerpo de un color distinto (la cara y el frente del torso, aparte)."""
    a = np.zeros((LADO, LADO, 4), np.uint8)

    def pintar(zona, clave, cols=None):
        x0, y0, w, h = ZONAS[zona]
        col = tuple(int(COLORES_ZONAS[clave][i : i + 2], 16) for i in (1, 3, 5))
        for xx in range(w) if cols is None else cols:
            a[y0 : y0 + h, x0 + xx] = (*col, 255)

    pintar("cabeza", "cabeza_resto")
    pintar("cabeza", "cabeza_frente", range(6, 18))
    pintar("torso", "torso_espalda")
    pintar("torso", "torso_frente", range(4, 12))
    for z in (
        "brazo_derecho",
        "mano_derecha",
        "pierna_derecha",
        "pie_derecho",
        "brazo_izquierdo",
        "mano_izquierda",
        "pierna_izquierda",
        "pie_izquierdo",
        "iris",
    ):
        pintar(z, z)
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    Image.fromarray(a, "RGBA").save(ruta)
    return ruta


# Brazo con el que el personaje ataca en las animaciones asimétricas (golpear): el de metal / el fuerte.
BRAZO_ACTIVO = {}

# Armas del componente `objeto`: materiales que se suman a la paleta de la skin (el arma no está en el PNG de 32×32)
# y parámetros por forma. La skin no cambia: el arma es una capa aparte que sigue la mano.
MATERIALES_ARMA = {
    "arma_metal": {"base": "#cdd6e0"},
    "arma_cuero": {"base": "#5a3a28"},
    "arma_oro": {"base": "#e2aa34"},
    "arma_brillo": {"base": "#fff1a8", "emisivo": True},
}
ARMAS = {
    "espada": {"mango": "arma_cuero", "pomo": "arma_oro", "detalle": "arma_brillo"},
    "hacha": {"mango": "arma_cuero", "detalle": "arma_brillo"},
    "antorcha": {"mango": "arma_cuero", "detalle": "arma_brillo"},
    "escudo": {"detalle": "arma_oro"},
    "baston": {"mango": "arma_cuero", "detalle": "arma_brillo"},
}


def ficha_con_arma(ruta, arma="espada", nombre=None, ancla="mano_derecha"):
    """Ficha de una skin con un arma en la mano: la misma skin y las mismas animaciones, más el componente `objeto`.
    El personaje conserva su nombre (el arma es una variante, no un personaje nuevo). El arma sigue la mano en
    cualquier ciclo (blandir = `golpear`)."""
    if arma not in ARMAS:
        raise ValueError(f"arma desconocida {arma!r}; disponibles: {', '.join(ARMAS)}")
    f = ficha(ruta, nombre)
    f["paleta"].update(MATERIALES_ARMA)
    f["componentes"] = list(f.get("componentes", [])) + [
        {
            "tipo": "objeto",
            "ancla": ancla,
            "material": "arma_metal",
            "parametros": {"forma": arma, **ARMAS[arma]},
            "por_que": f"arma ({arma}) en {ancla}",
        }
    ]
    return f


def ficha(ruta, nombre=None):
    """Ficha mínima para renderizar una skin con el pipeline de siempre (render_cuadro, tests, exportar)."""
    return {
        "identidad": {"nombre": nombre or os.path.splitext(os.path.basename(ruta))[0]},
        "cuerpo": {
            "base": "skin",
            "skin": ruta,
            "clase_altura": "adulto",
            "complexion": "normal",
            **(
                {
                    "brazo_activo": BRAZO_ACTIVO[
                        os.path.splitext(os.path.basename(ruta))[0]
                    ]
                }
                if os.path.splitext(os.path.basename(ruta))[0] in BRAZO_ACTIVO
                else {}
            ),
        },
        "paleta": cargar(ruta).paleta(),
        "componentes": [],
    }


def guia(ruta, zoom=16, estilo="stardew8"):
    """PNG ampliado con cada zona rotulada, el frente marcado y la columna que muestrea cada dirección del estilo
    (la cabeza usa la cara corrida hacia la cámara). Es la plantilla para pintar una skin que cierre en todas las
    direcciones: la columna 0 y la última de cada zona son la misma (la espalda). Leyenda al pie."""
    from .estilos import ESTILOS

    dirs = ESTILOS[estilo]["direcciones"]
    cols = columnas_por_direccion(estilo)
    colores = {}
    for i, d in enumerate(dirs):
        colores[d] = tuple(
            int(70 + 185 * f) for f in ((i * 0.37) % 1, (i * 0.61) % 1, (i * 0.83) % 1)
        )
    alto_leyenda = 34
    im = Image.new("RGB", (LADO * zoom, LADO * zoom + alto_leyenda), (28, 28, 34))
    dr = ImageDraw.Draw(im)
    for i, (nombre, (x, y, w, h)) in enumerate(ZONAS.items()):
        col = tuple(
            int(60 + 40 * f) for f in ((i * 0.37) % 1, (i * 0.61) % 1, (i * 0.83) % 1)
        )
        dr.rectangle(
            [x * zoom, y * zoom, (x + w) * zoom - 1, (y + h) * zoom - 1],
            fill=col,
            outline=(90, 90, 100),
        )
        for d in dirs:
            c = cols[d][nombre]
            xl = (x + c) * zoom + zoom // 2
            dr.line(
                [(xl, y * zoom + 1), (xl, (y + h) * zoom - 2)], fill=colores[d], width=2
            )
        dr.line(
            [((x + w / 2) * zoom, y * zoom), ((x + w / 2) * zoom, (y + h) * zoom - 1)],
            fill=(255, 255, 255),
        )
        dr.text(
            (x * zoom + 3, y * zoom + 3), nombre.replace("_", "\n"), fill=(20, 20, 20)
        )
    y0 = LADO * zoom + 4
    dr.text(
        (4, y0),
        "línea blanca = frente · col 0 y última = espalda (mismo texel)",
        fill=(230, 230, 230),
    )
    ancho = 46
    for i, d in enumerate(dirs):
        xi = 4 + i * ancho
        dr.rectangle(
            [xi, y0 + 13, xi + 10, y0 + 23], fill=colores[d], outline=(0, 0, 0)
        )
        dr.text((xi + 13, y0 + 13), d, fill=colores[d])
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    im.save(ruta)
    return ruta


def _por_dir(ruta, anim, estilo):
    return _por_dir_ficha(ficha(ruta), anim, estilo)


def _por_dir_ficha(f, anim, estilo):
    from .armado import render_cuadro
    from .estilos import ESTILOS
    from .poses import POSES

    n = POSES[anim]["n"]
    por_dir = {
        m: [render_cuadro(f, estilo, anim, p, m).img for p in range(n)]
        for m in ESTILOS[estilo]["direcciones"]
    }
    ajustar_a_paleta_fija(por_dir, estilo)
    return f, por_dir


def ajustar_a_paleta_fija(por_dir, estilo):
    """Si el estilo declara `render.paleta_fija`, mapea todo el render a esa lista (y no reduce más, porque
    reducir después rompería la pertenencia); si no, aplica la reducción de siempre por `paleta_max`."""
    from .estilos import ESTILOS

    render = ESTILOS[estilo]["render"]
    fija = render.get("paleta_fija")
    if fija:
        from .paleta import ajustar_paleta

        ajustar_paleta(por_dir, fija)
        return
    tope = render.get("paleta_max")
    if tope:
        from .paleta import reducir_paleta

        reducir_paleta(por_dir, tope)


def _exportar(f, por_dir, anim, estilo, carpeta, zoom, cuadros=False, nombre=None):
    from .armado import pivote
    from .exportar import exportar_direcciones
    from .poses import fps, loop, offset_y

    oy = offset_y(anim)
    exportar_direcciones(
        por_dir,
        nombre or anim,
        carpeta,
        fps=fps(anim),
        zoom=zoom,
        pivote=pivote(estilo, pose=anim),
        loop=loop(anim),
        extra={"offset_y": oy} if oy else None,
        cuadros=cuadros,
    )
    return carpeta


def demo(ruta, anim="caminar_lpc", estilo="stardew"):
    """Vista previa rápida (una skin cualquiera): docs/diagnostico/skins/<nombre>/<anim>*"""
    f, por_dir = _por_dir(ruta, anim, estilo)
    carpeta = os.path.join("docs", "diagnostico", "skins", f["identidad"]["nombre"])
    return _exportar(f, por_dir, anim, estilo, carpeta, zoom=6)


def salida_juego(
    ruta, anim="caminar_lpc", estilo="stardew", raiz="salida", cuadros=False
):
    """Salida final del juego (convención del proyecto): <raíz>/<personaje>/<estilo>/<anim>/<anim>*.
    El estilo (`stardew` 4 direcciones, `stardew8` 8 direcciones) es la capa intermedia, así que
    los archivos que empiezan con el nombre de la animación no colisionan entre estilos. Sirve para
    cualquier skin (las que vengan): mismo comando, cambiando el PNG y/o --anim."""
    f, por_dir = _por_dir(ruta, anim, estilo)
    carpeta = os.path.join(raiz, f["identidad"]["nombre"], estilo, anim)
    return _exportar(f, por_dir, anim, estilo, carpeta, zoom=4, cuadros=cuadros)


def salida_arma(
    ruta,
    arma="espada",
    anim="golpear",
    estilo="stardew",
    raiz="salida",
    cuadros=False,
    ancla="mano_derecha",
):
    """Salida de una skin con un arma en la mano: el personaje conserva su nombre, el estilo sigue siendo la capa
    intermedia, y la animación con arma es una variante `<anim>_<arma>`:
    `<raíz>/<personaje>/<estilo>/<anim>_<arma>/<anim>_<arma>*`."""
    f = ficha_con_arma(ruta, arma, ancla=ancla)
    nombre_anim = f"{anim}_{arma}"
    f, por_dir = _por_dir_ficha(f, anim, estilo)
    carpeta = os.path.join(raiz, f["identidad"]["nombre"], estilo, nombre_anim)
    return _exportar(
        f, por_dir, anim, estilo, carpeta, zoom=4, cuadros=cuadros, nombre=nombre_anim
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["guia"]:
        print("→", guia("skins/guia.png"))
    elif args[:1] in (["demo"], ["juego"]):
        anim = args[args.index("--anim") + 1] if "--anim" in args else "caminar_lpc"
        rutas = [a for a in args[1:] if a.endswith(".png")]
        ruta = rutas[0] if rutas else "skins/zonas.png"
        estilo = args[args.index("--estilo") + 1] if "--estilo" in args else "stardew"
        if args[0] == "demo":
            print("→", demo(ruta, anim, estilo))
        else:  # --output: carpeta de entrega (output/) con un PNG por cuadro además de la hoja y el JSON
            ent = "--output" in args
            print(
                "→",
                salida_juego(
                    ruta, anim, estilo, raiz="output" if ent else "salida", cuadros=ent
                ),
            )
    elif args[:1] == ["arma"]:
        anim = args[args.index("--anim") + 1] if "--anim" in args else "golpear"
        estilo = args[args.index("--estilo") + 1] if "--estilo" in args else "stardew"
        arma = args[args.index("--arma") + 1] if "--arma" in args else "espada"
        rutas = [a for a in args[1:] if a.endswith(".png")]
        ruta = rutas[0] if rutas else "skins/zonas.png"
        ent = "--output" in args
        print(
            "→",
            salida_arma(
                ruta,
                arma,
                anim,
                estilo,
                raiz="output" if ent else "salida",
                cuadros=ent,
            ),
        )
    else:
        print(__doc__)
