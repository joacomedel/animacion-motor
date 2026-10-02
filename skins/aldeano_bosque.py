"""Skin del aldeano del bosque (32×32): remera verde de mangas largas, chaleco de cuero, vincha con hoja.

Base con `skins.desde_colores` (simétrica por construcción: cada zona de un color plano) + detalles
pintados con el patrón de `skins/pintar_mago.py`: se pinta la mitad izquierda de cada zona y un loop
final espeja a la derecha, así la costura de la espalda cierra (lo verifica `skins.continuidad`).

Regenerar:  .venv/bin/python -m skins.aldeano_bosque
"""

import numpy as np
from PIL import Image

from sprites_lib import skins

skins.desde_colores(
    {
        "piel": "#d8a06a",
        "pelo": "#6b4a2b",
        "remera": "#5b7a3a",
        "pantalon": "#4a4030",
        "calzado": "#3a2a1c",
        "iris": "#3d5a2a",
        "mangas": "largas",
    },
    "skins/aldeano_bosque.png",
)

# Detalles (la base ya es simétrica; estos se espejan con el loop final, igual que en pintar_mago.py).
C = {
    k: tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))
    for k, h in dict(
        cuero="#5a3d24",
        cuero_b="#46301f",
        bordo="#6b8f3d",
        parche="#7a6a4f",
        suela="#2e2115",
        hebilla="#8a8578",
    ).items()
}

a = np.array(Image.open("skins/aldeano_bosque.png").convert("RGBA"))


def p(zona, x, y, col):
    x0, y0, w, h = skins.ZONAS[zona]
    a[y0 + y, x0 + x % w] = (*C[col], 255)


def llenar(zona, col, filas=None, cols=None):
    x0, y0, w, h = skins.ZONAS[zona]
    for y in filas if filas is not None else range(h):
        for x in cols if cols is not None else range(w):
            p(zona, x, y, col)


# Cabeza: vincha de cuero con una hoja (el loop espeja la hoja al otro lado).
llenar("cabeza", "cuero", filas=[2], cols=range(6, 12))
p("cabeza", 8, 2, "bordo")
p("cabeza", 8, 1, "bordo")

# Torso: chaleco de cuero con ribete, cinturón con hebilla y bordado de hoja.
llenar("torso", "cuero", cols=[7, 8])
llenar("torso", "cuero_b", cols=[6, 9])
llenar("torso", "cuero", filas=[6])
llenar("torso", "hebilla", filas=[6], cols=[7, 8])
p("torso", 5, 3, "bordo")

# Brazos: ribete de puño y franja bordada en la manga.
for lado in ("derecho", "izquierdo"):
    z = f"brazo_{lado}"
    llenar(z, "cuero_b", filas=[7])
    llenar(z, "bordo", filas=[4], cols=[2, 3])

# Piernas: parche en la rodilla y ruedo oscuro.
for lado in ("derecha", "izquierda"):
    z = f"pierna_{lado}"
    llenar(z, "parche", filas=[4, 5], cols=[3, 4])
    llenar(z, "cuero_b", filas=[9])

# Pies: suela.
for lado in ("derecho", "izquierdo"):
    llenar(f"pie_{lado}", "suela", filas=[2])

# Simetría izquierda/derecha: la mitad izquierda de cada zona define la derecha. Implica costura cerrada.
for zona, (x0, y0, w, h) in skins.ZONAS.items():
    for c in range(w // 2):
        a[y0 : y0 + h, x0 + w - 1 - c] = a[y0 : y0 + h, x0 + c]

Image.fromarray(a, "RGBA").save("skins/aldeano_bosque.png")
malas = skins.continuidad("skins/aldeano_bosque.png")
print(
    "→ skins/aldeano_bosque.png"
    + (
        f"  ¡costura abierta en {malas}!"
        if malas
        else "  (costura de la espalda cerrada)"
    )
)
