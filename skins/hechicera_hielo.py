"""Skin pixel art 32x32 de la Hechicera del hielo (estilo Minecraft), con mangas largas.

Generada con la API simple `skins.desde_colores` (pelo, remera, pantalon, calzado, iris).
Salida: skins/hechicera_hielo.png
"""

from sprites_lib import skins

RUTA = "skins/hechicera_hielo.png"

COLORES = {
    "piel": "#e8d0c0",
    "pelo": "#bfe6ff",
    "remera": "#2e6f9e",
    "pantalon": "#24455f",
    "calzado": "#cfe9ff",
    "iris": "#8fe0ff",
    "mangas": "largas",
}

if __name__ == "__main__":
    skins.desde_colores(COLORES, RUTA)
    print(f"skin escrita en {RUTA}")
