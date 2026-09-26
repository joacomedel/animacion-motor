"""Detecta cada sprite del panel "Helmet (X1)" y genera una hoja numerada para identificarlos."""
import json
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

AQUI = os.path.dirname(os.path.abspath(__file__))
SHEET = os.path.join(AQUI, "..", "referencias", "megamanx_X_sprites.png")
PANEL = (1, 386, 472, 737)          # x0, y0, x1, y1 (sin la línea del título)
BG = (50, 96, 166)

img = Image.open(SHEET).convert("RGB")
panel = img.crop(PANEL)
a = np.array(panel)
fg = np.any(a != BG, axis=2)

# 1) figuras = componentes conectados sin dilatar; 2) piezas chicas se pegan a la figura más cercana
lab, n = ndimage.label(fg, structure=np.ones((3, 3)))
areas = ndimage.sum(fg, lab, range(1, n + 1))
objs = ndimage.find_objects(lab)
big, small = [], []
for i, sl in enumerate(objs):
    y, x = sl
    b = [x.start, y.start, x.stop, y.stop]
    (big if areas[i] >= 120 else small).append(b)


def gap(a, b):
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    return max(dx, dy)


for b in small:
    j = min(range(len(big)), key=lambda k: gap(b, big[k]), default=None)
    if j is not None and gap(b, big[j]) <= 3:
        g = big[j]
        big[j] = [min(g[0], b[0]), min(g[1], b[1]), max(g[2], b[2]), max(g[3], b[3])]
# fusionar cajas que se solapan mucho (efectos encima del personaje)
merged = True
while merged:
    merged = False
    for i in range(len(big)):
        for j in range(i + 1, len(big)):
            a_, b_ = big[i], big[j]
            ix = max(0, min(a_[2], b_[2]) - max(a_[0], b_[0]))
            iy = max(0, min(a_[3], b_[3]) - max(a_[1], b_[1]))
            small_area = min((a_[2]-a_[0])*(a_[3]-a_[1]), (b_[2]-b_[0])*(b_[3]-b_[1]))
            if ix * iy > .4 * small_area:
                big[i] = [min(a_[0], b_[0]), min(a_[1], b_[1]), max(a_[2], b_[2]), max(a_[3], b_[3])]
                big.pop(j)
                merged = True
                break
        if merged:
            break
boxes = [[b[0], b[1], b[2] - b[0], b[3] - b[1]] for b in big]

# agrupar en filas por el centro vertical
boxes.sort(key=lambda b: b[1] + b[3] / 2)
rows = []
for b in boxes:
    cy = b[1] + b[3] / 2
    if rows and abs(cy - rows[-1]["cy"]) < 14:
        rows[-1]["boxes"].append(b)
        rows[-1]["cy"] = np.mean([bb[1] + bb[3] / 2 for bb in rows[-1]["boxes"]])
    else:
        rows.append({"cy": cy, "boxes": [b]})
out = []
for r in rows:
    r["boxes"].sort(key=lambda b: b[0])
    out.append([[int(v) for v in b] for b in r["boxes"]])

with open(os.path.join(AQUI, "boxes.json"), "w") as f:
    json.dump({"panel": PANEL, "rows": out}, f)

# hoja numerada: cada fila con su índice fila.cuadro, ampliada x3
S = 3
cw = max(b[2] for r in out for b in r) + 6
ch = max(b[3] for r in out for b in r) + 16
cols = max(len(r) for r in out)
sheet = Image.new("RGB", (cols * cw * S // 1 + 60, len(out) * ch * S), (30, 30, 30))
d = ImageDraw.Draw(sheet)
for ri, r in enumerate(out):
    d.text((4, ri * ch * S + 10), f"F{ri}", fill=(255, 255, 0))
    for ci, (x, y, w, h) in enumerate(r):
        spr = panel.crop((x, y, x + w, y + h)).resize((w * S, h * S), Image.NEAREST)
        ox, oy = 60 + ci * cw * S, ri * ch * S
        sheet.paste(spr, (ox, oy + 12 * S // 3 + 12))
        d.text((ox, oy), f"{ci}", fill=(255, 255, 255))
sheet.save(os.path.join(AQUI, "hoja_numerada.png"))
print(len(out), "filas;", sum(len(r) for r in out), "sprites")
for ri, r in enumerate(out):
    print(f"F{ri}: {len(r)} sprites, alto ~{max(b[3] for b in r)}")
