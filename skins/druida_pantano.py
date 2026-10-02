import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sprites_lib import skins

skins.desde_colores(
    {
        "piel": "#8a9a5a",
        "pelo": "#2f4a2a",
        "remera": "#4a6a2a",
        "pantalon": "#3a3020",
        "calzado": "#5a4a28",
        "iris": "#a0d040",
        "mangas": "cortas",
    },
    "skins/druida_pantano.png",
)
