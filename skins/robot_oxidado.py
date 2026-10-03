"""Skin del robot oxidado (32×32) pintada por código.

Robot con placas metálicas grises y remera naranja, con óxido marrón/rojizo
en bordes, juntas y zonas de desgaste. Pintado simétrico (col c == col w-1-c
en cada zona): la costura de la espalda cierra sola.

Regenerar:  .venv/bin/python -m skins.robot_oxidado
"""

import numpy as np
from PIL import Image

from sprites_lib import skins

C = {
    k: tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))
    for k, h in dict(
        metal="#9a9a90",
        metal_b="#7a7a72",
        metal_l="#b8b8b0",
        pelo="#6f6f66",
        remera="#b45a2a",
        remera_b="#8a4420",
        pantalon="#5a5a55",
        pantalon_b="#464642",
        calzado="#3a3a38",
        oxido="#8a4a24",
        oxido_b="#6b3a1f",
        oxido_l="#a05a2c",
        iris="#ff5a2a",
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


# Cabeza (24×10; col 12 = frente, 0/23 = nuca; fila 0 = coronilla):
# placas metálicas con óxido en bordes y juntas.
llenar("cabeza", "metal")
llenar("cabeza", "metal_b", filas=[0])  # coronilla oscura
llenar("cabeza", "metal_b", cols=[0])  # nuca
llenar("cabeza", "metal_l", filas=[1], cols=[10, 11, 12, 13])  # brillo frente
llenar("cabeza", "oxido", filas=[8, 9])  # óxido en la base (mandíbula)
llenar(
    "cabeza",
    "oxido_b",
    filas=[9],
    cols=[4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
)  # óxido oscuro base
llenar("cabeza", "oxido", filas=[2], cols=[2, 3])  # óxido en placa lateral
llenar("cabeza", "oxido_l", filas=[3], cols=[1])  # veta de óxido

# Torso (16×10; col 8 = frente; filas 0-6 pecho, 7-9 faldón):
# remera naranja con óxido en bordes y placa metálica en el pecho.
llenar("torso", "remera")
llenar("torso", "remera_b", cols=[0])  # espalda oscura
llenar("torso", "remera_b", filas=[9])  # borde inferior
llenar("torso", "metal", filas=range(1, 5), cols=[6, 7])  # placa pectoral
llenar("torso", "metal_b", filas=[4], cols=[6, 7])  # borde placa
llenar("torso", "oxido", filas=[0])  # óxido en hombros
llenar("torso", "oxido_b", filas=[0], cols=[2, 3, 4, 5])  # óxido oscuro hombros
llenar("torso", "oxido", filas=[7, 8], cols=[1, 2, 3, 4])  # óxido bajo placa
llenar("torso", "oxido_l", filas=[6], cols=[5])  # veta óxido

# Brazos (8×8; col 4 = frente, 0/7 = costura trasera):
# manga de remera, antebrazo metálico con óxido en la unión.
for lado, lado_m in (("derecho", "derecha"), ("izquierdo", "izquierda")):
    z = f"brazo_{lado}"
    llenar(z, "remera", filas=range(0, 4))
    llenar(z, "remera_b", cols=[0])  # costura trasera
    llenar(z, "metal", filas=range(4, 8))
    llenar(z, "metal_b", filas=[7])  # puño oscuro
    llenar(z, "oxido", filas=[3])  # óxido en la unión manga-metal
    llenar(z, "oxido_b", filas=[3], cols=[1, 2])  # óxido oscuro unión
    llenar(z, "oxido_l", filas=[5], cols=[3])  # veta óxido antebrazo
    llenar(f"mano_{lado_m}", "metal_b")

# Piernas (8×10; col 4 = frente, 0/7 = costura trasera):
# pantalón gris con óxido en rodilla y bota.
for lado, lado_p in (("derecha", "derecho"), ("izquierda", "izquierdo")):
    z = f"pierna_{lado}"
    llenar(z, "pantalon")
    llenar(z, "pantalon_b", cols=[0])  # costura trasera
    llenar(z, "pantalon_b", filas=[4])  # rodilla
    llenar(z, "oxido", filas=[3], cols=[2, 3])  # óxido en rodilla
    llenar(z, "oxido_b", filas=[5], cols=[1, 2])  # óxido bajo rodilla
    llenar(z, "calzado", filas=range(6, 10))
    llenar(z, "oxido", filas=[6])  # óxido en el borde del pantalón
    llenar(f"pie_{lado_p}", "calzado")
    llenar(f"pie_{lado_p}", "oxido_b", filas=[2])  # suela oxidada

llenar("iris", "iris")

# Simetría izquierda/derecha: la mitad izquierda de cada zona define la derecha.
# Implica costura trasera cerrada (col 0 == col w-1).
for zona, (x0, y0, w, h) in skins.ZONAS.items():
    for c in range(w // 2):
        a[y0 : y0 + h, x0 + w - 1 - c] = a[y0 : y0 + h, x0 + c]

ruta = "skins/robot_oxidado.png"
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
