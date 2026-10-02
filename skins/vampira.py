"""Skin de la "Vampira elegante" (32×32) pintada por código.

Como `pintar_mago`: frente simétrico (col c == col w-1-c en cada zona), así la costura de la
espalda cierra sola y las diagonales se espejan.

Regenerar:  .venv/bin/python skins/vampira.py
"""

import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sprites_lib import skins  # noqa: E402

C = {
    k: tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))
    for k, h in dict(
        piel="#e8d8e0",
        pelo="#1a1020",
        pelo_v="#3a2a55",
        remera="#4a1030",
        remera_o="#2e0a1e",
        pantalon="#201020",
        pantalon_o="#140a16",
        calzado="#101018",
        calzado_v="#262634",
        suela="#08080f",
        iris="#d02040",
        boton="#c9c9d9",
    ).items()
}
a = np.zeros((skins.LADO, skins.LADO, 4), np.uint8)


def p(zona, x, y, col):
    x0, y0, w, h = skins.ZONAS[zona]
    a[y0 + y, x0 + x % w] = (*C[col], 255)


def llenar(zona, col, filas=None, cols=None):
    x0, y0, w, h = skins.ZONAS[zona]
    for y in filas if filas is not None else range(h):
        for x in cols if cols is not None else range(w):
            p(zona, x, y, col)


# Cabeza (24×10; col 12 = frente, 0/23 = nuca): pelo largo con mechones, vincha roja y flequillo.
llenar("cabeza", "piel")
llenar("cabeza", "pelo", filas=range(0, 3))  # coronilla
for x in (1, 5, 9):
    p("cabeza", x, 1, "pelo_v")  # brillos (se espejan a 22, 18, 14)
llenar(
    "cabeza", "iris", filas=[2], cols=range(6, 12)
)  # vincha roja (se espeja a 12..17)
llenar("cabeza", "pelo", filas=[3], cols=range(6, 12))  # flequillo sobre la frente
llenar("cabeza", "pelo", filas=range(3, 10), cols=range(0, 6))  # pelo largo en la nuca
for x in (1, 4):
    llenar("cabeza", "pelo_v", filas=range(5, 9), cols=[x])  # mechones
llenar(
    "cabeza", "pelo", filas=range(4, 9), cols=[6, 7]
)  # mechones al frente (marcan la cara)

# Torso (16×10; col 8 = frente): remera de noche con solapa, cinturón y saco largo con forro rojo.
llenar("torso", "remera")
llenar("torso", "remera_o", cols=[0])  # espalda más oscura (se espeja a 15)
llenar("torso", "remera_o", filas=range(0, 6), cols=[6])  # solapa (se espeja a 9)
for y in (2, 4):
    p("torso", 7, y, "boton")  # botones plateados al centro (se espejan a 8)
llenar("torso", "calzado", filas=[6])  # cinturón
p("torso", 7, 6, "boton")  # hebilla (se espeja a 8)
llenar("torso", "remera_o", filas=range(7, 10))  # faldón del saco
llenar(
    "torso", "iris", filas=range(7, 10), cols=[7]
)  # forro rojo en la abertura (se espeja a 8)

# Brazos (8×8): mangas largas con puño, costura trasera y muñeca a la vista.
for lado in ("derecho", "izquierdo"):
    z = f"brazo_{lado}"
    llenar(z, "remera")
    llenar(z, "remera_o", cols=[0])  # costura (se espeja a 7)
    llenar(z, "remera_o", filas=[6])  # puño
    llenar(z, "piel", filas=[7])  # muñeca

for lado in ("derecha", "izquierda"):
    llenar(f"mano_{lado}", "piel")

# Piernas (8×10; col 4 = frente): pantalón recto y botas altas.
for lado in ("derecha", "izquierda"):
    z = f"pierna_{lado}"
    llenar(z, "pantalon")
    llenar(z, "pantalon_o", cols=[0])  # costura (se espeja a 7)
    llenar(z, "calzado", filas=range(6, 10))  # botas
    llenar(z, "calzado_v", filas=[6])  # vuelta de la bota

# Zapatos con hebilla plateada y suela.
for lado in ("derecho", "izquierdo"):
    z = f"pie_{lado}"
    llenar(z, "calzado")
    llenar(z, "suela", filas=[2])
    p(z, 3, 0, "boton")  # hebilla al frente (se espeja a 4)

llenar("iris", "iris")

# Simetría izquierda/derecha: la mitad izquierda de cada zona define la derecha.
# Implica costura trasera cerrada (col 0 == col w-1).
for zona, (x0, y0, w, h) in skins.ZONAS.items():
    for c in range(w // 2):
        a[y0 : y0 + h, x0 + w - 1 - c] = a[y0 : y0 + h, x0 + c]

ruta = "skins/vampira.png"
Image.fromarray(a, "RGBA").save(ruta)
malas = skins.continuidad(ruta)
print(
    f"→ {ruta}"
    + (
        f"  ¡costura abierta en {malas}!"
        if malas
        else "  (costura de la espalda cerrada: continuidad = [])"
    )
)
