"""Skin del fantasma cian (32×32) pintada por código.

Base: `skins.desde_colores` (piel pálida, pelo spectral, remera, pantalón, calzado, mangas largas).
Encima, una pasada de detalles espectrales simétricos: vetas en el pelo, brillo y una gema-alma en el pecho,
costuras del faldón, degradado fantasmal en las piernas y cuffs en los puños.

Al ser todo simétrico (col c == col w-1-c en cada zona), la costura de la espalda cierra sola, que es lo que
exige `skins.continuidad`. Reglas: no tocar (12,0) = pelo ni (12,6) = piel de la cara.

Regenerar:  .venv/bin/python skins/fantasma_cian.py
"""

import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sprites_lib import skins  # noqa: E402

RUTA = "skins/fantasma_cian.png"

BASE = {
    "piel": "#cfe8e0",
    "pelo": "#a0e0d0",
    "remera": "#207a7a",
    "pantalon": "#104a4a",
    "calzado": "#083030",
    "iris": "#d0fff0",
    "mangas": "largas",
}

# Tonos derivados de la paleta base para el detalle (más claro = más brillo espectral).
DET = {
    k: tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))
    for k, h in dict(
        piel_l="#e6f8f2",  # punta del pelo / punta de la cola
        pelo_l="#c4f2e6",  # veta clara del pelo
        pelo_b="#7cc4b6",  # veta oscura del pelo
        remera_l="#2f9a9a",  # brillo de la remera
        remera_b="#175c5c",  # sombra de la remera / espalda
        alma="#d0fff0",  # gema-alma del pecho
        brasa="#7fd8d8",  # costura fantasmal del faldón y cuffs
    ).items()
}

skins.desde_colores(BASE, RUTA)
a = np.array(Image.open(RUTA).convert("RGBA"))

# Todos los colores por nombre (los de la base + los del detalle), para pintar con `llenar(zona, "remera_l", ...)`.
C = {
    **{
        k: tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))
        for k, h in BASE.items()
        if k != "mangas"
    },
    **DET,  # ya son tuplas
}


def p(zona, x, y, col, alpha=255):
    """Pinta un texel de la zona por nombre de color; `x` se espeja al final (izquierda define derecha)."""
    x0, y0, w, h = skins.ZONAS[zona]
    a[y0 + y, x0 + x % w] = (*C[col], alpha)


def llenar(zona, col, filas=None, cols=None, alpha=255):
    x0, y0, w, h = skins.ZONAS[zona]
    for y in filas if filas is not None else range(h):
        for x in cols if cols is not None else range(w):
            p(zona, x, y, col, alpha)


# Cabeza (24×10; col 12 = frente, 0/23 = nuca; fila 0 = coronilla): vetas espectrales y brillo.
for x in range(12):
    veta = "pelo_l" if x % 3 == 0 else ("pelo_b" if x % 3 == 1 else "pelo")
    llenar("cabeza", veta, filas=range(0, 3), cols=[x])
llenar("cabeza", "piel_l", filas=[0], cols=[6])  # brillo en la coronilla
llenar("cabeza", "pelo_b", filas=[3], cols=[4, 5, 6, 7])  # raíz del flequillo

# Torso (16×10; col 8 = frente; filas 0-6 pecho, 7-9 faldón): brillo lateral, espalda oscura,
# gema-alma y faldón con costuras fantasmal.
llenar("torso", "remera_b", cols=[0, 1])
llenar("torso", "remera_l", cols=[5, 6])
llenar("torso", "alma", filas=[3, 4], cols=[8])
llenar("torso", "brasa", filas=[2, 5], cols=[8])  # halo de la gema
llenar("torso", "brasa", filas=[8], cols=[1, 2, 3, 4])  # costuras del faldón
llenar("torso", "remera_b", filas=[9], cols=[5])  # punta del faldón

# Brazos (4×8; col 2 = frente, 0/3 = costura trasera): costura trasera, cuff y punta fantasmal.
for lado in ("derecho", "izquierdo"):
    z = f"brazo_{lado}"
    llenar(z, "remera_b", cols=[0])
    llenar(z, "brasa", filas=[6])  # cuff
    llenar(z, "piel_l", filas=[7])  # se disuelve en luz

for lado in ("derecha", "izquierda"):
    llenar(f"mano_{lado}", "piel_l")  # manos translúcidas

# Piernas (8×10; col 4 = frente, 0/7 = costura trasera): pantalón que se desvanece en cola fantasmal.
for lado in ("derecha", "izquierda"):
    z = f"pierna_{lado}"
    llenar(z, "remera_b", cols=[0])  # costura trasera
    llenar(z, "brasa", filas=[5], cols=[3, 4])  # cintura de luz
    llenar(z, "remera", filas=[6])
    llenar(z, "piel", filas=[7])
    llenar(z, "piel_l", filas=[8, 9])  # punta de la cola

# Pies (8×3; col 4 = frente): calzado oscuro con suela de luz, para que la cola se disuelva.
for lado in ("derecho", "izquierdo"):
    z = f"pie_{lado}"
    llenar(z, "calzado")
    llenar(z, "brasa", filas=[2])  # suela fantasmal

llenar("iris", "iris")

# Simetría izquierda/derecha: la mitad izquierda de cada zona define la derecha. Implica costura trasera cerrada.
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
