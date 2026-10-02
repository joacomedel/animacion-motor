from sprites_lib import skins

skins.desde_colores(
    {
        "piel": "#c89860",
        "pelo": "#3a3028",
        "remera": "#d8c090",
        "pantalon": "#8a6a40",
        "calzado": "#5a4020",
        "iris": "#6a4a20",
        "mangas": "largas",
    },
    "skins/explorador_desierto.png",
)

# Simetría para cerrar costura de la espalda (igual que pintar_mago.py)
import numpy as np
from PIL import Image

a = np.array(Image.open("skins/explorador_desierto.png").convert("RGBA"))
for zona, (x0, y0, w, h) in skins.ZONAS.items():
    for c in range(w // 2):
        a[y0 : y0 + h, x0 + w - 1 - c] = a[y0 : y0 + h, x0 + c]
Image.fromarray(a, "RGBA").save("skins/explorador_desierto.png")
malas = skins.continuidad("skins/explorador_desierto.png")
print("Costura:", malas)
