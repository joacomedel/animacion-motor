"""Separar sprite sheets de referencia en animaciones.

Uso (desde la raíz del proyecto):
  .venv/bin/python -m sprites_lib.referencia paneles <sheet.png>
      → color de fondo y líneas divisorias (para ubicar paneles)
  .venv/bin/python -m sprites_lib.referencia detectar <sheet.png> <carpeta> [--panel x0,y0,x1,y1] [--fondo r,g,b]
      → <carpeta>/boxes.json + <carpeta>/hoja_numerada.png (cada sprite con fila F y número)
  .venv/bin/python -m sprites_lib.referencia cortar <carpeta>/cortes.json
      → una animación por entrada: PNG transparente + JSON + GIF (alineadas por los pies)

cortes.json:
  {"boxes": "<carpeta>/boxes.json", "salida": "<carpeta>/animaciones", "fps": 12,
   "animaciones": {"04_correr": [[1, [1,2,3,4,5,6,7,8,9,10]]], "02_quieto": [[0, [7,8,9,10]]]},
   "fps_por_anim": {"02_quieto": 4}}
"""
import json
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from .exportar import exportar


def color_fondo(a):
    return Counter(map(tuple, a.reshape(-1, 3))).most_common(1)[0][0]


def paneles(ruta):
    a = np.array(Image.open(ruta).convert("RGB"))
    print("tamaño", a.shape[1], "x", a.shape[0], "| fondo", color_fondo(a))
    oscuro = a.sum(2) < 90
    print("filas divisorias:", np.where(oscuro.mean(1) > .5)[0].tolist())
    print("columnas divisorias:", np.where(oscuro.mean(0) > .5)[0].tolist())


def detectar(ruta, carpeta, panel=None, fondo=None, area_min=120, pegar=3, tol_fila=14):
    img = Image.open(ruta).convert("RGB")
    panel = panel or (0, 0, img.width, img.height)
    sub = img.crop(panel)
    a = np.array(sub)
    fondo = tuple(fondo) if fondo else color_fondo(a)
    fg = np.any(a != fondo, axis=2)
    # 1) figuras = componentes conectados; 2) piezas chicas (destellos, disparos) se pegan a la figura más cercana
    lab, n = ndimage.label(fg, structure=np.ones((3, 3)))
    areas = ndimage.sum(fg, lab, range(1, n + 1))
    grandes, chicas = [], []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        y, x = sl
        (grandes if areas[i] >= area_min else chicas).append([x.start, y.start, x.stop, y.stop])

    def gap(p, q):
        return max(max(0, max(p[0], q[0]) - min(p[2], q[2])), max(0, max(p[1], q[1]) - min(p[3], q[3])))

    for b in chicas:
        if not grandes:
            break
        j = min(range(len(grandes)), key=lambda k: gap(b, grandes[k]))
        if gap(b, grandes[j]) <= pegar:
            g = grandes[j]
            grandes[j] = [min(g[0], b[0]), min(g[1], b[1]), max(g[2], b[2]), max(g[3], b[3])]
    fusion = True
    while fusion:                                   # cajas muy solapadas = un solo sprite con efecto
        fusion = False
        for i in range(len(grandes)):
            for j in range(i + 1, len(grandes)):
                p, q = grandes[i], grandes[j]
                ix = max(0, min(p[2], q[2]) - max(p[0], q[0])); iy = max(0, min(p[3], q[3]) - max(p[1], q[1]))
                menor = min((p[2] - p[0]) * (p[3] - p[1]), (q[2] - q[0]) * (q[3] - q[1]))
                if ix * iy > .4 * menor:
                    grandes[i] = [min(p[0], q[0]), min(p[1], q[1]), max(p[2], q[2]), max(p[3], q[3])]
                    grandes.pop(j); fusion = True
                    break
            if fusion:
                break
    cajas = sorted(([b[0], b[1], b[2] - b[0], b[3] - b[1]] for b in grandes), key=lambda b: b[1] + b[3] / 2)
    filas = []
    for b in cajas:
        cy = b[1] + b[3] / 2
        if filas and abs(cy - filas[-1]["cy"]) < tol_fila:
            filas[-1]["b"].append(b)
            filas[-1]["cy"] = float(np.mean([q[1] + q[3] / 2 for q in filas[-1]["b"]]))
        else:
            filas.append({"cy": cy, "b": [b]})
    rows = [[[int(v) for v in b] for b in sorted(f["b"], key=lambda q: q[0])] for f in filas]
    os.makedirs(carpeta, exist_ok=True)
    with open(os.path.join(carpeta, "boxes.json"), "w") as fh:
        json.dump({"sheet": os.path.abspath(ruta), "panel": list(panel), "fondo": list(map(int, fondo)), "rows": rows}, fh)
    # hoja numerada, cada fila con su propio ancho de celda
    S = 3
    alto = sum((max(b[3] for b in r) + 14) * S for r in rows)
    ancho = max(sum(b[2] + 6 for b in r) for r in rows) * S + 60
    hoja = Image.new("RGB", (ancho, alto), (30, 30, 30))
    d = ImageDraw.Draw(hoja)
    y = 0
    for ri, r in enumerate(rows):
        d.text((4, y + 10), f"F{ri}", fill=(255, 255, 0))
        x = 60
        for ci, (bx, by, bw, bh) in enumerate(r):
            spr = sub.crop((bx, by, bx + bw, by + bh)).resize((bw * S, bh * S), Image.NEAREST)
            hoja.paste(spr, (x, y + 12))
            d.text((x, y), str(ci), fill=(255, 255, 255))
            x += (bw + 6) * S
        y += (max(b[3] for b in r) + 14) * S
    hoja.save(os.path.join(carpeta, "hoja_numerada.png"))
    print(f"{len(rows)} filas, {sum(len(r) for r in rows)} sprites →", os.path.join(carpeta, "hoja_numerada.png"))
    for ri, r in enumerate(rows):
        print(f"  F{ri}: {len(r)} sprites")


def cortar(ruta_cfg):
    cfg = json.load(open(ruta_cfg))
    bx = json.load(open(cfg["boxes"]))
    sub = Image.open(bx["sheet"]).convert("RGB").crop(bx["panel"])
    fondo = tuple(bx["fondo"])
    for nombre, partes in cfg["animaciones"].items():
        frames = []
        for fila, idxs in partes:
            for i in idxs:
                x, y, w, h = bx["rows"][fila][i]
                a = np.array(sub.crop((x, y, x + w, y + h)))
                alpha = np.where(np.all(a == fondo, axis=2), 0, 255).astype(np.uint8)
                frames.append(Image.fromarray(np.dstack([a, alpha]), "RGBA"))
        cw, ch = max(f.width for f in frames), max(f.height for f in frames)
        celdas = []
        for f in frames:                             # misma celda, alineados abajo al centro (pies)
            c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            c.paste(f, ((cw - f.width) // 2, ch - f.height))
            celdas.append(c)
        fps = cfg.get("fps_por_anim", {}).get(nombre, cfg.get("fps", 12))
        exportar(celdas, nombre, cfg["salida"], fps=fps, pivote=(cw // 2, ch - 1), zoom=3)
        print(f"{nombre:26s} {len(celdas):2d} cuadros  celda {cw}x{ch}")


def _tupla(s):
    return tuple(int(v) for v in s.split(","))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(0)
    cmd = args[0]
    opts = {args[i]: args[i + 1] for i in range(len(args) - 1) if args[i].startswith("--")}
    pos = [a for i, a in enumerate(args[1:], 1) if not a.startswith("--") and not args[i - 1].startswith("--")]
    if cmd == "paneles":
        paneles(pos[0])
    elif cmd == "detectar":
        detectar(pos[0], pos[1], _tupla(opts["--panel"]) if "--panel" in opts else None,
                 _tupla(opts["--fondo"]) if "--fondo" in opts else None)
    elif cmd == "cortar":
        cortar(pos[0])
    else:
        print(__doc__)
