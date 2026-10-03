"""Cámara 2D: sigue un punto y se clampea a los bordes del mundo."""


class Camara:
    """Devuelve el offset (x, y) de la región visible según el punto que sigue.

    Attributes:
        vx, vy: tamaño de la vista (px)
        mundo: el Mundo cuyos límites se respetan
    """

    def __init__(self, vx, vy, mundo):
        self.vx = vx
        self.vy = vy
        self.mundo = mundo

    def seguir(self, px, py):
        """Offset de cámara para que (px, py) quede centrado, sin salir del mundo."""
        max_x = max(self.mundo.ancho_px - self.vx, 0)
        max_y = max(self.mundo.alto_px - self.vy, 0)
        x = min(max(px - self.vx // 2, 0), max_x)
        y = min(max(py - self.vy // 2, 0), max_y)
        return x, y
