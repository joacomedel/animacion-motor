"""Separa el panel "Helmet (X1)" en animaciones: tira PNG transparente + GIF por animación."""
import json
import os

import numpy as np
from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "animaciones")
BG = (50, 96, 166)

# (fila, [cuadros]) según hoja_numerada.png
ANIMS = {
    "01_teletransporte":     [(0, [0, 2, 3, 4, 5, 6])],
    "02_quieto":             [(0, [7, 8, 9, 10])],
    "03_disparo_quieto":     [(0, [11, 12])],
    "04_correr":             [(1, list(range(1, 11)))],
    "05_correr_disparando":  [(2, list(range(0, 10)))],
    "06_saltar":             [(3, list(range(0, 7)))],
    "07_saltar_disparando":  [(3, list(range(7, 14)))],
    "08_pared":              [(4, list(range(0, 5)))],
    "09_pared_disparando":   [(4, list(range(5, 10)))],
    "10_escalera":           [(5, [1, 2, 3, 4, 5]), (6, [0])],
    "11_brillo_victoria":    [(5, list(range(7, 12)))],
    "12_dash":               [(8, [0, 1])],
    "13_dash_disparando":    [(8, [2, 3])],
    "14_danio":              [(8, list(range(4, 10))), (5, [12])],
}
FPS = {"01_teletransporte": 12, "02_quieto": 4, "03_disparo_quieto": 6, "12_dash": 8, "13_dash_disparando": 8,
       "14_danio": 10}

d = json.load(open(os.path.join(AQUI, "boxes.json")))
panel = Image.open(os.path.join(AQUI, "..", "referencias", "megamanx_X_sprites.png")).convert("RGB").crop(d["panel"])


def recorte(r, i):
    x, y, w, h = d["rows"][r][i]
    a = np.array(panel.crop((x, y, x + w, y + h)))
    alpha = np.where(np.all(a == BG, axis=2), 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a, alpha]), "RGBA")


os.makedirs(SALIDA, exist_ok=True)
resumen = []
for nombre, partes in ANIMS.items():
    frames = [recorte(r, i) for r, idxs in partes for i in idxs]
    cw, ch = max(f.width for f in frames), max(f.height for f in frames)
    # todos los cuadros en una celda igual, alineados abajo al centro (pies)
    celdas = []
    for f in frames:
        c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        c.paste(f, ((cw - f.width) // 2, ch - f.height))
        celdas.append(c)
    tira = Image.new("RGBA", (cw * len(celdas), ch), (0, 0, 0, 0))
    for k, c in enumerate(celdas):
        tira.paste(c, (k * cw, 0))
    tira.save(os.path.join(SALIDA, f"{nombre}.png"))
    # GIF ampliado x3 sobre fondo oscuro
    S, fps = 3, FPS.get(nombre, 12)
    gif = []
    for c in celdas:
        g = Image.new("RGB", (cw, ch), (28, 28, 40))
        g.paste(c, (0, 0), c)
        gif.append(g.resize((cw * S, ch * S), Image.NEAREST))
    gif[0].save(os.path.join(SALIDA, f"{nombre}.gif"), save_all=True, append_images=gif[1:],
                loop=0, duration=int(1000 / fps), disposal=1)
    resumen.append((nombre, len(celdas), cw, ch, celdas))
    print(f"{nombre:24s} {len(celdas):2d} cuadros  celda {cw}x{ch}")

# índice visual con todas las animaciones
S = 3
ancho = max(len(c) * (cw + 4) for _, _, cw, _, c in resumen) * S + 200
alto = sum((ch + 8) * S for _, _, _, ch, _ in resumen)
idx = Image.new("RGB", (ancho, alto), (28, 28, 40))
dr = ImageDraw.Draw(idx)
y = 0
for nombre, n, cw, ch, celdas in resumen:
    dr.text((6, y + ch * S // 2), nombre, fill=(255, 220, 90))
    for k, c in enumerate(celdas):
        idx.paste(c.resize((cw * S, ch * S), Image.NEAREST), (200 + k * (cw + 4) * S, y), c.resize((cw * S, ch * S), Image.NEAREST))
    y += (ch + 8) * S
idx.save(os.path.join(AQUI, "indice.png"))
