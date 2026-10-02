"""Skin del mago (32×32) pintada por código.

Mismo diseño que la skin v1 del mago, pero con dos arreglos para las 8 direcciones:

- el frente queda simétrico (col c == col w-1-c en cada zona), así las diagonales SE/SW y NE/NW se espejan;
- al ser simétrico, la costura de la espalda cierra sola (col 0 == col w-1), el check de `proceso_skin`.

Regenerar:  .venv/bin/python -m skins.pintar_mago
"""

import numpy as np
from PIL import Image

from sprites_lib import skins

C = {
    k: tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))
    for k, h in dict(
        piel="#8c5638",
        pelo="#e2e2f0",
        pelo_b="#b4b4d2",
        pelo_l="#ffffff",
        tunica="#5c2c96",
        tunica_b="#46207a",
        camisa="#362e62",
        oro="#e2aa34",
        runa="#5af0e6",
        pantalon="#42366e",
        pantalon_b="#342a58",
        bota="#62392a",
        bota_b="#46281e",
        cuero="#3a2418",
        iris="#5af0e6",
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


# Cabeza (24×10; col 12 = frente, 0/23 = nuca; fila 0 = coronilla): pelo largo con vetas, flequillo y vincha.
llenar("cabeza", "piel")
for x in range(12):
    veta = "pelo_b" if x % 3 == 1 else "pelo"
    llenar("cabeza", veta, filas=range(0, 3), cols=[x])
    if x <= 5:
        llenar("cabeza", veta, filas=range(3, 10), cols=[x])  # nuca/patilla larga
llenar("cabeza", "pelo", filas=[3], cols=[6, 7, 8])  # flequillo (se espeja a 17,16,15)
p("cabeza", 5, 0, "pelo_l")  # brillo en la coronilla
llenar("cabeza", "oro", filas=[2], cols=range(6, 12))
p("cabeza", 11, 2, "runa")  # vincha con gema

# Torso (16×10; col 8 = frente; filas 0-6 pecho, 7-9 faldón): túnica abierta, camisa, ribete, cinturón.
llenar("torso", "tunica")
llenar("torso", "tunica_b", cols=[0])  # espalda más oscura
llenar("torso", "camisa", cols=[6, 7])  # apertura (se espeja a 8, 9)
llenar("torso", "oro", cols=[5])  # ribete (se espeja a 10)
llenar("torso", "cuero", filas=[6])
llenar("torso", "oro", filas=[6], cols=[6, 7])  # cinturón + hebilla
p("torso", 2, 3, "runa")  # runa en la espalda (se espeja a 13)
llenar("torso", "tunica_b", filas=[9], cols=[2, 3])  # pliegues del faldón

# Brazos (4×8; col 2 = frente, 0/3 = costura trasera): manga de túnica, puño dorado y antebrazo a la vista.
for lado in ("derecho", "izquierdo"):
    z = f"brazo_{lado}"
    llenar(z, "tunica", filas=range(0, 6))
    llenar(
        z, "tunica_b", filas=range(0, 6), cols=[0]
    )  # costura trasera (se espeja a 3)
    llenar(z, "oro", filas=[5])
    llenar(z, "piel", filas=[6, 7])
    p(z, 1, 6, "runa")  # tatuaje rúnico (se espeja a 2)
    llenar(f"pie_{lado}", "bota")
    llenar(f"pie_{lado}", "bota_b", filas=[2])  # suela

for lado in ("derecha", "izquierda"):
    llenar(f"mano_{lado}", "piel")

# Piernas (8×10; col 4 = frente, 0/7 = costura trasera): pantalón, rodilla, caña de bota con hebilla.
for lado in ("derecha", "izquierda"):
    z = f"pierna_{lado}"
    llenar(z, "pantalon")
    llenar(z, "pantalon_b", cols=[0])  # costura trasera (se espeja a 7)
    llenar(z, "pantalon_b", filas=[4])  # rodilla
    llenar(z, "bota", filas=range(6, 10))
    llenar(z, "bota_b", filas=[6])
    p(z, 3, 7, "oro")  # hebilla (se espeja a 4)

llenar("iris", "iris")

# Simetría izquierda/derecha: la mitad izquierda de cada zona define la derecha. Implica costura trasera cerrada.
for zona, (x0, y0, w, h) in skins.ZONAS.items():
    for c in range(w // 2):
        a[y0 : y0 + h, x0 + w - 1 - c] = a[y0 : y0 + h, x0 + c]

ruta = "skins/mago.png"
Image.fromarray(a, "RGBA").save(ruta)
malas = skins.continuidad(ruta)
print(
    f"→ {ruta}"
    + (
        f"  ¡costura abierta en {malas}!"
        if malas
        else "  (costura de la espalda cerrada)"
    )
)
