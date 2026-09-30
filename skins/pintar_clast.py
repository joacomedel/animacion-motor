"""Skin de Clast (cyborg) pintada por código. Regenerar: .venv/bin/python -m skins.pintar_clast"""
import numpy as np
from PIL import Image

from sprites_lib.skins import LADO, ZONAS

C = {k: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for k, h in dict(
    piel="#e8b894", pelo="#3a302a", pelo_b="#2a2218", cresta="#5a4a3e",
    metal="#8a929c", metal_b="#6a7280", metal_raya="#c4ccd4",
    luz="#5cf07a", ropa="#9c4a3c", ropa_b="#6a3428", cuero="#5a3a28", iris="#5cf07a").items()}
a = np.zeros((LADO, LADO, 4), np.uint8)


def p(zona, x, y, col):
    x0, y0, w, h = ZONAS[zona]
    a[y0 + y, x0 + x % w] = (*C[col], 255)


def llenar(zona, col, filas=None, cols=None):
    x0, y0, w, h = ZONAS[zona]
    for y in filas if filas is not None else range(h):
        for x in cols if cols is not None else range(w):
            p(zona, x, y, col)


# cabeza (24×10; col 12 = frente, 0/24 = nuca; fila 0 = coronilla)
llenar("cabeza", "piel")
# coronilla y parte de arriba (filas 0-3)
for fila in range(0, 3):  # filas 0-2: todas columnas
    llenar("cabeza", "pelo", filas=[fila])
# fila 3: todas excepto columnas 9-15 (cara)
for x in range(24):
    if not (9 <= x <= 15):
        p("cabeza", x, 3, "pelo")
# costados y nuca rapados (filas 4-6), alternando pelos cada 2 columnas
for fila in range(4, 7):
    for x in range(0, 8):  # lado izquierdo
        color = "pelo" if (x // 2) % 2 == 0 else "pelo_b"
        p("cabeza", x, fila, color)
    for x in range(17, 24):  # lado derecho
        color = "pelo" if ((x - 17) // 2) % 2 == 0 else "pelo_b"
        p("cabeza", x, fila, color)
# franja central cresta más clara
llenar("cabeza", "cresta", filas=range(0, 2), cols=range(10, 15))
llenar("cabeza", "cresta", filas=range(0, 3), cols=[0, 1, 22, 23])
# luz en sien derecha (lado derecho del personaje = columnas 3-8, fila 4)
p("cabeza", 5, 4, "luz")

# torso (16×10; col 8 = frente; filas 0-6 pecho, 7-9 cadera): remera rojo ladrillo gastada
llenar("torso", "ropa")
llenar("torso", "ropa_b", cols=[0, 1, 15])  # espalda más oscura
# desgaste: algunos texels ropa_b aleatorio y borde abajo irregular
for x in [2, 5, 11, 14]:
    p("torso", x, 3, "ropa_b")  # desgaste aleatorio
for x in [1, 3, 4, 7, 9, 12, 13, 15]:  # borde abajo (fila 9) irregular
    p("torso", x, 9, "ropa_b")
# cinturón en fila 6 con hebilla metal_raya en el frente (col 8)
llenar("torso", "cuero", filas=[6])
p("torso", 8, 6, "metal_raya")

# brazos (4×8; fila 0 = hombro): metal completo con juntas de codo y rayas de desgaste
for lado in ("derecho", "izquierdo"):
    z = f"brazo_{lado}"
    llenar(z, "metal")
    llenar(z, "metal_b", cols=[0])  # espalda más oscura
    # junta de codo en fila 5 (aproximadamente a la mitad)
    p(z, 2, 5, "luz")
    # rayas de desgaste (1 texel)
    for y, x in [(1, 3), (3, 1), (6, 2)]:
        p(z, x, y, "metal_raya")

# manos: metal
for lado in ("derecha", "izquierda"):
    llenar(f"mano_{lado}", "metal")
    llenar(f"mano_{lado}", "metal_b", cols=[0])

# piernas (8×10; filas 0-5 muslo, 6-9 pantorrilla+pie): metal completo con juntas de rodilla
for lado in ("derecha", "izquierda"):
    z = f"pierna_{lado}"
    llenar(z, "metal")
    llenar(z, "metal_b", cols=[0, 7])  # espalda oscura
    # junta/rodilla en fila 5 (más oscura)
    llenar(z, "metal_b", filas=[5])
    # luz en rodilla
    p(z, 4, 5, "luz")
    # rayas de desgaste (1 texel)
    for y, x in [(1, 2), (3, 6), (7, 1), (8, 5)]:
        p(z, x, y, "metal_raya")

# pies: metal (heredan metal del personaje base, pero asegurar consistencia)
for lado in ("derecho", "izquierdo"):
    llenar(f"pie_{lado}", "metal")
    llenar(f"pie_{lado}", "metal_b", filas=[2])  # suela oscura

llenar("iris", "iris")
Image.fromarray(a, "RGBA").save("skins/clast.png")
print("→ skins/clast.png")
