"""Skins simples de ítems: un PNG chico cuyos colores se vuelven materiales de la paleta.

A diferencia de `skins.Skin` (32×32 con zonas del cuerpo), la skin de un ítem es libre: se usa
como catálogo de colores. El material principal es el color más usado, así que "espada_roja"
es una espada con material `sk_ff0000` y el componente `objeto` la pinta con ese color.
"""

import numpy as np
from PIL import Image

from .skins import material


def paleta_y_material(ruta):
    """(paleta {material: hex}, material principal) a partir del PNG de un ítem.

    Args:
        ruta: PNG del ítem (cualquier tamaño; solo importan los colores opacos)

    Returns:
        (dict material→hex, str material principal = el color más usado)
    """
    a = np.asarray(Image.open(ruta).convert("RGBA")).reshape(-1, 4)
    conteo = {}
    for r, g, b, al in a:
        if al:
            nombre = material((int(r), int(g), int(b)))
            conteo[nombre] = conteo.get(nombre, 0) + 1
    if not conteo:
        raise ValueError(f"la skin del ítem {ruta!r} no tiene píxeles opacos")
    paleta = {nombre: {"base": "#" + nombre[3:]} for nombre in conteo}
    principal = max(conteo, key=conteo.get)
    return paleta, principal
