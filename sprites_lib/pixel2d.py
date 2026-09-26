"""Herramientas para sprites 2D planos (vista lateral): capas con contorno propio y trazos pixelados."""
import math

import numpy as np
from PIL import Image, ImageDraw


class Lienzo:
    """Tamaño de celda y desplazamiento x del rig lateral dentro de la celda."""

    def __init__(self, cw, ch, ox=0):
        self.cw, self.ch, self.ox = cw, ch, ox

    def capa(self):
        im = Image.new("RGBA", (self.cw, self.ch), (0, 0, 0, 0))
        return im, ImageDraw.Draw(im)

    def P(self, x, y):
        return (int(round(x + self.ox)), int(round(y)))

    def seg(self, d, a, b, col, w):
        """Trazo grueso con puntas redondeadas (hueso de una extremidad)."""
        d.line([self.P(*a), self.P(*b)], fill=col, width=w)
        for q in (a, b):
            x, y = self.P(*q)
            r = w // 2
            d.ellipse([x - r, y - r, x + r - (1 - w % 2), y + r - (1 - w % 2)], fill=col)

    def puntos(self, d, a, b, col, paso=2, off=0):
        """Puntos cada `paso` px a lo largo de un hueso (runas, costuras, remaches)."""
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
        for i in range(off, n, paso):
            t = i / n
            d.point(self.P(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), fill=col)

    def ascii(self, d, filas, x0, y0, leyenda, colores):
        """Dibuja un bloque ASCII ('.' transparente) con la leyenda char→nombre de color."""
        for y, fila in enumerate(filas):
            for x, ch in enumerate(fila):
                if ch != ".":
                    d.point(self.P(x0 + x, y0 + y), fill=colores[leyenda[ch]])


def contorno(im, col):
    """Contorno de 1 px alrededor de todo lo opaco de la capa."""
    a = np.array(im)
    op = a[..., 3] > 0
    pad = np.pad(op, 1)                                  # sin np.roll: no "da la vuelta" por los bordes
    grow = op | pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
    a[grow & ~op] = (*col, 255)
    return Image.fromarray(a, "RGBA")


def apilar(cw, ch, capas):
    """Compone capas de atrás hacia adelante."""
    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    for c in capas:
        out.alpha_composite(c)
    return out
