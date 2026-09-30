"""Skins tipo Minecraft: el muñeco base y sus animaciones son siempre los mismos; un personaje es solo un PNG de
32×32 con cada parte del cuerpo "desenrollada" (centro = frente, bordes = espalda, arriba = la punta de la parte).

Cada punto del muñeco 3D sabe en qué zona cae y en qué (u, v) de la zona: toma ese color. Sombras, luces y contorno
los pone el estilo, así que la skin se pinta con colores planos. La cara (ojos, boca) no se pinta: a 6 px no se lee;
la dibuja el componente `ojos` con el iris de la skin.

Uso:  .venv/bin/python -m sprites_lib.skins guia                     → skins/guia.png (zonas rotuladas, para pintar)
      .venv/bin/python -m sprites_lib.skins demo [skin.png] [--anim caminar_lpc]  → salida/skins/<nombre>/
"""
import functools
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

LADO = 32
ZONAS = {                      # nombre: (x, y, ancho, alto) en el PNG
    "cabeza": (0, 0, 24, 10),
    "torso": (0, 10, 16, 10),
    "brazo_derecho": (16, 10, 4, 8), "brazo_izquierdo": (20, 10, 4, 8),
    "mano_derecha": (24, 10, 4, 2), "mano_izquierda": (28, 10, 4, 2),
    "iris": (24, 12, 1, 1),
    "pierna_derecha": (0, 20, 8, 10), "pierna_izquierda": (8, 20, 8, 10),
    "pie_derecho": (16, 20, 4, 3), "pie_izquierdo": (20, 20, 4, 3),
}
CARA = (12, 6)                 # texel de piel de la cara (color de la ficha para 'piel')
PELO = (12, 0)                 # texel de la coronilla (color para 'pelo': cejas)


def _hex(c):
    return "#%02x%02x%02x" % tuple(int(x) for x in c[:3])


def material(c):
    return "sk_" + _hex(c)[1:]


class Skin:
    def __init__(self, img):
        a = np.array(img.convert("RGBA"))
        if a.shape[:2] != (LADO, LADO):
            raise ValueError(f"la skin tiene que medir {LADO}×{LADO} (mide {a.shape[1]}×{a.shape[0]})")
        self.a = a
        cara = a[CARA[1], CARA[0]]
        self.nombres = np.empty((LADO, LADO), dtype=object)
        for y in range(LADO):
            for x in range(LADO):
                px = a[y, x] if a[y, x, 3] else cara           # transparente = piel
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
        for clave, (x, y) in (("piel", CARA), ("pelo", PELO), ("iris", ZONAS["iris"][:2])):
            pal[clave] = {"base": _hex(self.color(x, y))}
        return pal


@functools.lru_cache(maxsize=32)
def _cargar(ruta, _mtime):
    return Skin(Image.open(ruta))


def cargar(ruta):
    return _cargar(ruta, os.path.getmtime(ruta))


def u_de(d, ref=0.0):
    """Ángulo alrededor del eje vertical → u (0.5 = hacia ref, que por defecto es adelante)."""
    return (np.arctan2(d[..., 1], d[..., 0]) - ref) / (2 * math.pi) + .5


def desde_colores(colores, ruta):
    """Skin simple a partir de colores (como la skin por defecto de Minecraft): pelo arriba y atrás, remera con
    mangas, pantalón y calzado. Claves: piel, pelo, remera, pantalon, calzado, iris, mangas ('cortas'|'largas')."""
    c = {k: tuple(int(colores[k][i:i + 2], 16) for i in (1, 3, 5)) for k in
         ("piel", "pelo", "remera", "pantalon", "calzado", "iris")}
    a = np.zeros((LADO, LADO, 4), np.uint8)

    def pintar(zona, col, filas=None, cols=None):
        x0, y0, w, h = ZONAS[zona]
        for yy in range(h) if filas is None else filas:
            for xx in range(w) if cols is None else cols:
                a[y0 + yy, x0 + xx] = (*col, 255)
    pintar("cabeza", c["piel"])
    pintar("cabeza", c["pelo"], filas=range(0, 3))                          # coronilla
    pintar("cabeza", c["pelo"], filas=range(3, 8), cols=[*range(0, 6), *range(18, 24)])   # nuca y costados atrás
    pintar("cabeza", c["pelo"], filas=[3], cols=range(6, 18))               # flequillo
    pintar("torso", c["remera"])
    for lado in ("derecho", "izquierdo"):
        pintar(f"brazo_{lado}", c["piel"])
        pintar(f"brazo_{lado}", c["remera"], filas=range(0, 8 if colores.get("mangas") == "largas" else 3))
        pintar(f"pie_{lado}", c["calzado"])
    for lado in ("derecha", "izquierda"):
        pintar(f"mano_{lado}", c["piel"])
        pintar(f"pierna_{lado}", c["pantalon"])
    pintar("iris", c["iris"])
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    Image.fromarray(a, "RGBA").save(ruta)
    return ruta


def ficha(ruta, nombre=None):
    """Ficha mínima para renderizar una skin con el pipeline de siempre (render_cuadro, tests, exportar)."""
    return {"identidad": {"nombre": nombre or os.path.splitext(os.path.basename(ruta))[0]},
            "cuerpo": {"base": "skin", "skin": ruta, "clase_altura": "adulto", "complexion": "normal"},
            "paleta": cargar(ruta).paleta(), "componentes": []}


def guia(ruta, zoom=16):
    """PNG ampliado con cada zona rotulada y el frente marcado: la plantilla para pintar una skin a mano."""
    im = Image.new("RGB", (LADO * zoom, LADO * zoom), (40, 40, 48))
    dr = ImageDraw.Draw(im)
    for i, (nombre, (x, y, w, h)) in enumerate(ZONAS.items()):
        col = tuple(int(90 + 120 * f) for f in ((i * .37) % 1, (i * .61) % 1, (i * .83) % 1))
        dr.rectangle([x * zoom, y * zoom, (x + w) * zoom - 1, (y + h) * zoom - 1], fill=col, outline=(0, 0, 0))
        dr.line([((x + w / 2) * zoom, y * zoom), ((x + w / 2) * zoom, (y + h) * zoom - 1)], fill=(255, 255, 255))
        dr.text((x * zoom + 3, y * zoom + 3), nombre.replace("_", "\n"), fill=(0, 0, 0))
    dr.text((4, LADO * zoom - 28), "línea blanca = frente; bordes = espalda; arriba = punta de la parte (hombro, cadera)",
            fill=(255, 255, 255))
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    im.save(ruta)
    return ruta


def demo(ruta, anim="caminar_lpc", estilo="stardew"):
    from .armado import render_cuadro
    from .estilos import ESTILOS
    from .exportar import exportar_direcciones
    from .poses import POSES, fps
    f = ficha(ruta)
    n = POSES[anim]["n"]
    por_dir = {m: [render_cuadro(f, estilo, anim, p, m).img for p in range(n)] for m in ESTILOS[estilo]["direcciones"]}
    carpeta = os.path.join("salida", "skins", f["identidad"]["nombre"])
    exportar_direcciones(por_dir, anim, carpeta, fps=fps(anim), zoom=6)
    return carpeta


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["guia"]:
        print("→", guia("skins/guia.png"))
    elif args[:1] == ["demo"]:
        anim = args[args.index("--anim") + 1] if "--anim" in args else "caminar_lpc"
        rutas = [a for a in args[1:] if a.endswith(".png")]
        print("→", demo(rutas[0] if rutas else "skins/mago.png", anim))
    else:
        print(__doc__)
