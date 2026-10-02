"""Skin del Pescador del muelle (32×32) pintada por código.

Base: `skins.desde_colores` con la paleta pedida (piel, pelo, remera azul, pantalón claro, botas
marrones, mangas cortas). Encima se agregan detalles de pescador: vetas y brillo en el pelo,
barba corta, rayas y bolsillo de pecho en la remera, cinturón con hebilla, rodilleras y suela en
las botas.

Todo se pinta en la mitad izquierda de cada zona y al final se espeja (igual que `pintar_mago.py`):
- el frente queda simétrico, así las diagonales SE/SW y NE/NW se espejan;
- al ser simétrico, la costura de la espalda cierra sola (col 0 == col w-1).

Regenerar:  .venv/bin/python skins/pescador.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PIL import Image

from sprites_lib import skins

RUTA = "skins/pescador.png"

skins.desde_colores(
    {
        "piel": "#e0b080",
        "pelo": "#2a2a2a",
        "remera": "#3a6a8a",
        "pantalon": "#d8d8c0",
        "calzado": "#4a3a28",
        "iris": "#3a5a7a",
        "mangas": "cortas",
    },
    RUTA,
)

C = {
    k: tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))
    for k, h in dict(
        piel="#e0b080",
        piel_b="#c09068",
        pelo="#2a2a2a",
        pelo_b="#1c1c1c",
        pelo_l="#404040",
        remera="#3a6a8a",
        remera_b="#2c5470",
        remera_l="#4e88ac",
        pantalon="#d8d8c0",
        pantalon_b="#b0b098",
        calzado="#4a3a28",
        calzado_b="#382a1b",
        cuerda="#c8b070",
        laton="#e0c060",
        iris="#3a5a7a",
    ).items()
}
a = np.array(Image.open(RUTA).convert("RGBA"))


def p(zona, x, y, col):
    x0, y0, w, h = skins.ZONAS[zona]
    a[y0 + y, x0 + x % w] = (*C[col], 255)


def llenar(zona, col, filas=None, cols=None):
    x0, y0, w, h = skins.ZONAS[zona]
    for y in filas if filas is not None else range(h):
        for x in cols if cols is not None else range(w):
            p(zona, x, y, col)


# --- Cabeza (24×10; col 12 = frente, 0/23 = nuca, fila 0 = coronilla) ---
# (desde_colores ya puso pelo en coronilla 0-2, costados/nuca 3-7 y flequillo en la fila 3)
llenar(
    "cabeza", "pelo_b", filas=[1], cols=[2, 3, 4, 5]
)  # nuca más oscura (se espeja a 21..18)
llenar(
    "cabeza", "pelo_l", filas=[0], cols=[3, 4, 8, 9]
)  # brillo del pelo (se espeja a 20,19,15,14)
llenar(
    "cabeza", "pelo_b", filas=[2], cols=[0]
)  # costura trasera del pelo (se espeja a 23)
llenar("cabeza", "pelo_b", filas=[6, 7], cols=[5])  # patillas (se espeja a 18)
llenar(
    "cabeza", "pelo", filas=[8, 9], cols=[4, 5, 6]
)  # barba corta (se espeja a 19,18,17)
llenar(
    "cabeza", "piel_b", filas=[8], cols=[7]
)  # sombra bajo el flequillo (se espeja a 16)

# --- Torso (16×10; col 8 = frente, filas 0-6 pecho, 7-9 faldón) ---
llenar("torso", "remera_b", filas=[0])  # hombros más oscuros (se espeja a 15)
llenar("torso", "remera_l", filas=[2])  # raya clara de la remera a rayas
llenar("torso", "remera", filas=[3])
llenar("torso", "remera_l", filas=[4])
llenar("torso", "remera_b", filas=[6])  # cintura bajo la remera
llenar("torso", "cuerda", filas=[7])  # cinturón de lona (se espeja fila a fila)
llenar("torso", "laton", filas=[7], cols=[6, 7])  # hebilla (se espeja a 8, 9)
llenar(
    "torso", "remera_b", filas=[9], cols=[1, 2, 3]
)  # pliegues del faldón (se espeja a 14,13,12)
llenar(
    "torso", "cuerda", filas=[4], cols=[3, 4, 5]
)  # correa del equipo de pesca (se espeja a 12,11,10)

# --- Brazos (8×8; col 4 = frente, 0/7 = costura trasera): manga corta + antebrazo ---
for lado in ("derecho", "izquierdo"):
    z = f"brazo_{lado}"
    llenar(z, "remera_l", filas=[2])  # puño de la manga corta
    llenar(
        z, "remera_b", filas=[2], cols=[0]
    )  # costura trasera del puño (se espeja a 7)
    llenar(z, "piel_b", filas=[5])  # codo con sombra
    llenar(f"pie_{lado}", "calzado")
    llenar(f"pie_{lado}", "calzado_b", filas=[2])  # suela

# --- Manos (4×2) ---
for lado in ("derecha", "izquierda"):
    llenar(f"mano_{lado}", "piel")

# --- Piernas (8×10; col 4 = frente, 0/7 = costura trasera): pantalón claro y botas ---
for lado in ("derecha", "izquierda"):
    z = f"pierna_{lado}"
    llenar(z, "pantalon_b", filas=[0])  # cinturilla (se espeja a 7)
    llenar(z, "pantalon_b", filas=[4])  # rodillera
    llenar(z, "cuerda", filas=[6])  # vuelta del botín
    llenar(z, "calzado", filas=range(7, 10))
    llenar(
        z, "calzado_b", filas=[7]
    )  # 一年内 горутина de la bota (se espeja fila a fila)

llenar("iris", "iris")

# Simetría izquierda/derecha: la mitad izquierda de cada zona define la derecha. Implica costura cerrada.
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
