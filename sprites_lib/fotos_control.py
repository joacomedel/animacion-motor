"""Fotos de control: las poses aprobadas por el usuario quedan congeladas (versionadas en git). Si un cambio
del motor o de un componente altera aunque sea un píxel, el test lo reporta con una imagen antes/después."""
import os

import numpy as np
from PIL import Image

from .tests_personaje import Resultado

DIR = os.path.join("personajes", "aprobados")


def carpeta(nombre, estilo, raiz=None):
    """Carpeta de las fotos de control: `<raiz>/<nombre>/<estilo>`; con `raiz=None` usa `DIR`
    (`personajes/aprobados`); las animaciones pasan `raiz="aprobados/animaciones"`."""
    return os.path.join(DIR if raiz is None else raiz, nombre, estilo)


def _archivo(c):
    return f"{c.pose}_{c.mira}_{c.indice}.png"


def guardar(nombre, estilo, todo, raiz=None):
    out = carpeta(nombre, estilo, raiz)
    os.makedirs(out, exist_ok=True)
    for frs in todo.values():
        for c in frs:
            c.img.save(os.path.join(out, _archivo(c)))
    return out


def _diferencia(antes, ahora, ruta, zoom=6):
    h, w = antes.shape[:2]
    m = np.any(antes != ahora, axis=2)
    marca = np.zeros_like(ahora); marca[m] = (255, 40, 40, 255)
    hoja = Image.new("RGBA", (w * 3 * zoom + 8, h * zoom), (60, 58, 80, 255))
    for i, arr in enumerate((antes, ahora, marca)):
        im = Image.fromarray(arr, "RGBA").resize((w * zoom, h * zoom), Image.NEAREST)
        hoja.paste(im, (i * (w * zoom + 4), 0), im)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    hoja.save(ruta)


def comparar(nombre, estilo, todo, carpeta_dif, raiz=None):
    """Compara los cuadros con los congelados en `raiz`; sin carpeta aprobada queda omitido."""
    base = carpeta(nombre, estilo, raiz)
    if not os.path.isdir(base):
        return Resultado("fotos de control", True, "todavía no hay poses aprobadas: omitido", omitido=True)
    fallas = []
    for frs in todo.values():
        for c in frs:
            f = os.path.join(base, _archivo(c))
            if not os.path.exists(f):
                fallas.append(f"{_archivo(c)}: no estaba aprobado")
                continue
            antes, ahora = np.array(Image.open(f).convert("RGBA")), np.array(c.img)
            if antes.shape != ahora.shape:
                fallas.append(f"{_archivo(c)}: cambió el tamaño {antes.shape[:2]} → {ahora.shape[:2]}")
            elif (antes != ahora).any():
                n = int(np.any(antes != ahora, axis=2).sum())
                _diferencia(antes, ahora, os.path.join(carpeta_dif, _archivo(c)))
                fallas.append(f"{_archivo(c)}: {n} píxeles distintos (ver {os.path.join(carpeta_dif, _archivo(c))})")
    return Resultado("fotos de control", not fallas, f"{len(fallas)} cuadros cambiaron" if fallas
                     else "idéntico a lo aprobado", fallas[:25])
