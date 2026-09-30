"""Skin del mago pintada por código (texel a texel). Regenerar: .venv/bin/python -m skins.pintar_mago"""
import numpy as np
from PIL import Image

from sprites_lib.skins import LADO, ZONAS

C = {k: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for k, h in dict(
    piel="#8c5638", pelo="#e2e2f0", pelo_b="#b4b4d2", pelo_l="#ffffff", tunica="#5c2c96", tunica_b="#46207a",
    camisa="#362e62", oro="#e2aa34", runa="#5af0e6", pantalon="#42366e", pantalon_b="#342a58",
    bota="#62392a", bota_b="#46281e", cuero="#3a2418", iris="#5af0e6").items()}
a = np.zeros((LADO, LADO, 4), np.uint8)


def p(zona, x, y, col):
    x0, y0, w, h = ZONAS[zona]
    a[y0 + y, x0 + x % w] = (*C[col], 255)


def llenar(zona, col, filas=None, cols=None):
    x0, y0, w, h = ZONAS[zona]
    for y in filas if filas is not None else range(h):
        for x in cols if cols is not None else range(w):
            p(zona, x, y, col)


# cabeza (24×10; col 12 = frente, 0/24 = nuca; fila 0 = coronilla): pelo largo con vetas, flequillo partido
llenar("cabeza", "piel")
for x in range(24):
    veta = "pelo_b" if x % 3 == 1 else "pelo"
    llenar("cabeza", veta, filas=range(0, 3), cols=[x])
    if not 9 <= x <= 15:
        llenar("cabeza", veta, filas=range(3, 10 if (x <= 5 or x >= 19) else 5), cols=[x])   # nuca larga, patillas
for x in (9, 10, 14, 15):
    p("cabeza", x, 3, "pelo" if x in (10, 14) else "pelo_b")                                # flequillo a los lados
for x in (11, 12, 13):
    p("cabeza", x, 0, "pelo_l")                                                               # brillo en la coronilla
llenar("cabeza", "oro", filas=[2], cols=range(8, 17)); p("cabeza", 12, 2, "runa")             # vincha con gema

# torso (16×10; col 8 = frente; filas 0-6 pecho, 7-9 cadera): túnica abierta, camisa, ribete, cinturón
llenar("torso", "tunica")
llenar("torso", "tunica_b", cols=[0, 1, 15])                                                  # espalda más oscura
llenar("torso", "camisa", filas=range(0, 10), cols=[7, 8, 9])
llenar("torso", "oro", cols=[6, 10])                                                          # ribete de la túnica
llenar("torso", "cuero", filas=[6]); p("torso", 8, 6, "oro")                                  # cinturón + hebilla
p("torso", 3, 3, "runa"); p("torso", 13, 3, "runa")                                           # runas en la espalda
for x in (2, 4, 12, 14):
    p("torso", x, 9, "tunica_b")                                                              # pliegues del faldón

# brazos (4×8; fila 0 = hombro): manga de túnica con puño dorado y antebrazo a la vista
for lado in ("derecho", "izquierdo"):
    z = f"brazo_{lado}"
    llenar(z, "tunica", filas=range(0, 6)); llenar(z, "tunica_b", filas=range(0, 6), cols=[0])
    llenar(z, "oro", filas=[5]); llenar(z, "piel", filas=[6, 7])
    p(z, 2, 6, "runa")                                                                        # tatuaje rúnico
    llenar(f"pie_{lado}", "bota"); llenar(f"pie_{lado}", "bota_b", filas=[2])                 # suela
for lado in ("derecha", "izquierda"):
    llenar(f"mano_{lado}", "piel")
    z = f"pierna_{lado}"
    llenar(z, "pantalon"); llenar(z, "pantalon_b", cols=[0, 7]); llenar(z, "pantalon_b", filas=[4])   # rodilla
    llenar(z, "bota", filas=range(6, 10)); llenar(z, "bota_b", filas=[6]); p(z, 4, 7, "oro")  # caña con hebilla
llenar("iris", "iris")
Image.fromarray(a, "RGBA").save("skins/mago.png")
print("→ skins/mago.png")
