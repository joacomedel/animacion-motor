"""Skin del Caballero Carmesí (32×32).

Base con `skins.desde_colores` (mangas largas) y detalles de caballero pintados en la mitad
izquierda de cada zona; al final se espeja la mitad izquierda a la derecha (como
`skins/pintar_mago.py`), así las diagonales SE/SW y NE/NW coinciden y la costura de la
espalda cierra sola (check `skins.continuidad`).

Regenerar:  .venv/bin/python skins/caballero_carmesi.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PIL import Image

from sprites_lib import skins

C = {
    "piel": "#d6a071",
    "pelo": "#3a2a1a",
    "remera": "#a01f28",
    "pantalon": "#2a2a32",
    "calzado": "#4a4a55",
    "iris": "#c8c8d0",
    "mangas": "largas",
}
RUTA = "skins/caballero_carmesi.png"

# Tonos extra (derivados de la paleta): carmesí oscuro para costuras, carmesí claro para la
# pechera y plateado (el del iris) para la cruz y la hebilla.
carmesi_o = (0x7E, 0x16, 0x20)
carmesi_c = (0xC2, 0x3B, 0x44)
plata = (0xC8, 0xC8, 0xD0)

skins.desde_colores(C, RUTA)
a = np.array(Image.open(RUTA).convert("RGBA"))


def p(zona, x, y, col):
    x0, y0, w, h = skins.ZONAS[zona]
    a[y0 + y, x0 + x % w] = (*col, 255)


def llenar(zona, col, filas=None, cols=None):
    x0, y0, w, h = skins.ZONAS[zona]
    for y in filas if filas is not None else range(h):
        for x in cols if cols is not None else range(w):
            p(zona, x, y, col)


# Cabeza: pelo con costados más oscuros y flequillo con vetas (mitad izquierda).
# Ojo: la col 0 de cada zona es la nuca (N); no pintarla con rojo o se ve rojo al mirar al N.
llenar("cabeza", carmesi_o, filas=range(4, 8), cols=[1])
llenar("cabeza", (0x4A, 0x38, 0x26), filas=[0, 1, 2], cols=[3, 7])  # vetas de pelo
llenar("cabeza", (0x4A, 0x38, 0x26), filas=[3], cols=[7])  # flequillo con entrante

# Torso: armadura de tela carmesí con cruz de plata al frente, costuras oscuras y cinturón.
llenar("torso", carmesi_o, cols=[0, 1])  # costados/espalda oscuros
llenar("torso", carmesi_c, cols=[6, 7])  # pechera clara (se espeja a 8, 9)
llenar("torso", plata, filas=[1, 2, 4, 5], cols=[7])  # vertical de la cruz
llenar("torso", plata, filas=[3], cols=[5, 6, 7])  # travesaño de la cruz
llenar("torso", (0x1E, 0x1E, 0x26), filas=[6])  # cinturón
llenar("torso", plata, filas=[6], cols=[6, 7])  # hebilla
llenar("torso", carmesi_o, filas=[9], cols=[2, 3])  # pliegues del faldón

# Brazos: manga larga carmesí con costura trasera oscura y franja frontal clara.
for lado in ("derecho", "izquierdo"):
    z = f"brazo_{lado}"
    llenar(z, carmesi_o, cols=[0])  # costura trasera (se espeja a 7)
    llenar(z, carmesi_c, filas=range(1, 7), cols=[2])  # franja frontal (se espeja a 5)

# Piernas: pantalón oscuro con costura trasera, rótula y caña más clara.
for lado in ("derecha", "izquierda"):
    z = f"pierna_{lado}"
    llenar(z, (0x1C, 0x1C, 0x24), cols=[0])  # costura trasera (se espeja a 7)
    llenar(z, (0x3A, 0x3A, 0x46), filas=[4], cols=[3])  # rótula (se espeja a 4)
    llenar(z, (0x3A, 0x3A, 0x46), filas=range(6, 9), cols=[1, 2])  # caña

# Calzado: bota con suela oscura y puntera clara.
for lado in ("derecho", "izquierdo"):
    z = f"pie_{lado}"
    llenar(z, (0x33, 0x33, 0x3C), filas=[2])  # suela
    llenar(z, (0x5C, 0x5C, 0x6A), filas=[0], cols=[3])  # puntera (se espeja a 4)

# Simetría izquierda/derecha: la mitad izquierda de cada zona define la derecha.
# Implica costura trasera cerrada (col 0 == col w-1 en cada zona).
for zona, (x0, y0, w, h) in skins.ZONAS.items():
    for c in range(w // 2):
        a[y0 : y0 + h, x0 + w - 1 - c] = a[y0 : y0 + h, x0 + c]

Image.fromarray(a, "RGBA").save(RUTA)
malas = skins.continuidad(RUTA)
print(
    f"→ {RUTA}"
    + (
        f"  ¡costura abierta en {malas}!"
        if malas
        else "  (costura de la espalda cerrada)"
    )
)
