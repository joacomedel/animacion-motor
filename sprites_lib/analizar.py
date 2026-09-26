"""Medir una animación de referencia píxel por píxel.

Uso:
  .venv/bin/python -m sprites_lib.analizar <tira.png> <ancho_celda> <alto_celda> <carpeta_salida>

Imprime: paleta (colores y cantidad), por cuadro el bounding box, borde superior (→ rebote),
píxeles del pie más bajo (→ apoyos) y ancho (→ apertura). Genera en <carpeta_salida>:
  grilla_XX.png  cuadros ampliados ×12 con grilla (líneas cada 1 px, amarillas cada 5) para leer
                 coordenadas de articulaciones a ojo (cabeza, hombro, codo, mano, cadera, rodilla, tobillo).
  medidas.json   todo lo medido, para copiar a sprites_lib/ciclos.py.
"""
import json
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw


def analizar(ruta, cw, ch, carpeta):
    im = Image.open(ruta).convert("RGBA")
    a = np.array(im)
    n = im.width // cw
    op = a[..., 3] > 0
    cols = Counter(map(tuple, a[op][:, :3]))
    print(f"{n} cuadros de {cw}x{ch} | {len(cols)} colores")
    for c, k in cols.most_common():
        print(f"  #{c[0]:02x}{c[1]:02x}{c[2]:02x}  {k}")
    cuadros = []
    for i in range(n):
        f = op[:ch, i * cw:(i + 1) * cw]
        ys, xs = np.where(f)
        pie = xs[ys == ys.max()]
        c = dict(cuadro=i, x0=int(xs.min()), x1=int(xs.max()), y0=int(ys.min()), y1=int(ys.max()),
                 ancho=int(xs.max() - xs.min() + 1), alto=int(ys.max() - ys.min() + 1),
                 pie_bajo=[int(pie.min()), int(pie.max())], pixeles=int(f.sum()))
        cuadros.append(c)
        print(f"  cuadro {i}: bbox x{c['x0']}-{c['x1']} y{c['y0']}-{c['y1']}  ancho {c['ancho']}  alto {c['alto']}"
              f"  pie más bajo x{c['pie_bajo'][0]}-{c['pie_bajo'][1]}")
    rebote = [c["y0"] - min(q["y0"] for q in cuadros) for c in cuadros]
    print("rebote (borde superior relativo):", rebote)
    os.makedirs(carpeta, exist_ok=True)
    S = 12
    grillas = []
    for i in range(n):
        fr = im.crop((i * cw, 0, (i + 1) * cw, ch))
        g = Image.new("RGB", (cw * S + 30, ch * S + 30), (20, 20, 28))
        big = fr.resize((cw * S, ch * S), Image.NEAREST)
        g.paste(big, (30, 30), big)
        d = ImageDraw.Draw(g)
        for k in range(ch + 1):
            d.line([(30, 30 + k * S), (30 + cw * S, 30 + k * S)], fill=(200, 200, 60) if k % 5 == 0 else (45, 45, 55))
            if k % 5 == 0:
                d.text((2, 30 + k * S - 5), str(k), fill=(255, 255, 0))
        for k in range(cw + 1):
            d.line([(30 + k * S, 30), (30 + k * S, 30 + ch * S)], fill=(200, 200, 60) if k % 5 == 0 else (45, 45, 55))
            if k % 5 == 0:
                d.text((30 + k * S - 3, 10), str(k), fill=(255, 255, 0))
        d.text((34, 34), f"#{i}", fill=(255, 120, 120))
        grillas.append(g)
    for j in range(0, n, 5):                      # 5 cuadros por imagen
        grupo = grillas[j:j + 5]
        w, h = grupo[0].size
        o = Image.new("RGB", (w * len(grupo), h))
        for k, g in enumerate(grupo):
            o.paste(g, (k * w, 0))
        o.save(os.path.join(carpeta, f"grilla_{j:02d}.png"))
    with open(os.path.join(carpeta, "medidas.json"), "w") as fh:
        json.dump({"cuadros": cuadros, "rebote": rebote,
                   "paleta": [["#%02x%02x%02x" % c, k] for c, k in cols.most_common()]}, fh, indent=1)
    print("grillas y medidas en", carpeta)


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(__doc__); sys.exit(0)
    analizar(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
