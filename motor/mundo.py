"""Mundo 2D renderizable: un mapa de tiles más grande que la pantalla.

El mundo es una grilla de tiles (piso, muro, árbol) pre-renderizada una sola vez a una superficie
grande; el motor blitea la región visible según la cámara. Así el personaje se mueve por un mundo
real y la cámara lo sigue, en vez de estar siempre centrado en un piso que se desplaza con él.
"""

import random

import pygame
from PIL import Image, ImageDraw

from sprites_lib.render3d import piso_iso

PISO, MURO, ARBOL = 0, 1, 2


class Mundo:
    """Mapa de tiles con su superficie pre-renderizada.

    Attributes:
        ancho, alto: tamaño en tiles
        tile: lado de un tile en px
        mapa: grilla [y][x] de PISO/MURO/ARBOL
    """

    def __init__(self, ancho=80, alto=50, tile=16):
        self.ancho = ancho
        self.alto = alto
        self.tile = tile
        self.mapa = [[PISO] * ancho for _ in range(alto)]
        self._superficie = None
        self._superficie_piso = None
        self._generar()

    def _generar(self):
        """Borde de muro + algunos muros y árboles (determinista)."""
        rng = random.Random(42)
        for x in range(self.ancho):
            self.mapa[0][x] = MURO
            self.mapa[self.alto - 1][x] = MURO
        for y in range(self.alto):
            self.mapa[y][0] = MURO
            self.mapa[y][self.ancho - 1] = MURO
        for _ in range(self.ancho * self.alto // 10):
            x = rng.randrange(1, self.ancho - 1)
            y = rng.randrange(1, self.alto - 1)
            self.mapa[y][x] = rng.choice([MURO, ARBOL])

    @property
    def ancho_px(self):
        return self.ancho * self.tile

    @property
    def alto_px(self):
        return self.alto * self.tile

    def tile_en(self, tx, ty):
        """Tipo de tile en (tx, ty); MURO si está fuera."""
        if 0 <= tx < self.ancho and 0 <= ty < self.alto:
            return self.mapa[ty][tx]
        return MURO

    def colisiona(self, px, py, radio=4):
        """True si el círculo (px, py, radio) toca un tile MURO.

        Usa el punto de los pies + un radio chico, no la celda entera.
        ARBOL no bloquea.
        """
        tx = int(px // self.tile)
        ty = int(py // self.tile)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if self.tile_en(tx + dx, ty + dy) == MURO:
                    # distancia del círculo al tile vecino
                    cx = max((tx + dx) * self.tile, min(px, (tx + dx + 1) * self.tile))
                    cy = max((ty + dy) * self.tile, min(py, (ty + dy + 1) * self.tile))
                    if (px - cx) ** 2 + (py - cy) ** 2 < radio**2:
                        return True
        return False

    def arboles_visibles(self, cam_x, cam_y, vx, vy):
        """Lista de (tx, ty) de árboles visibles, ordenados por Y (para depth-sorting)."""
        tx0 = max(0, cam_x // self.tile)
        ty0 = max(0, cam_y // self.tile)
        tx1 = min(self.ancho - 1, (cam_x + vx) // self.tile)
        ty1 = min(self.alto - 1, (cam_y + vy) // self.tile)
        arboles = []
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if self.mapa[ty][tx] == ARBOL:
                    arboles.append((tx, ty))
        return arboles

    def superficie(self):
        """Superficie del mundo pre-renderizada (se genera una sola vez)."""
        if self._superficie is None:
            img = self._render()
            self._superficie = pygame.image.fromstring(img.tobytes(), img.size, "RGBA")
        return self._superficie

    def superficie_piso(self):
        """Superficie del piso con muros (sin árboles) para depth-sorting."""
        if self._superficie_piso is None:
            img = self._render_piso()
            self._superficie_piso = pygame.image.fromstring(
                img.tobytes(), img.size, "RGBA"
            )
        return self._superficie_piso

    def _render_piso(self):
        img = piso_iso(self.ancho_px, self.alto_px).convert("RGBA")
        d = ImageDraw.Draw(img)
        t = self.tile
        for y in range(self.alto):
            for x in range(self.ancho):
                tipo = self.mapa[y][x]
                cx, cy = x * t, y * t
                if tipo == MURO:
                    d.rectangle(
                        [cx + 1, cy + 1, cx + t - 1, cy + t - 1],
                        fill=(72, 72, 92, 255),
                        outline=(38, 38, 52, 255),
                    )
        return img

    def _render_arbol(self, tx, ty):
        """Renderiza un árbol individual como superficie transparente."""
        t = self.tile
        img = Image.new("RGBA", (t, t), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse(
            [3, 3, t - 3, t - 3],
            fill=(40, 110, 50, 255),
            outline=(18, 58, 28, 255),
        )
        return pygame.image.fromstring(img.tobytes(), img.size, "RGBA")

    def _render(self):
        img = piso_iso(self.ancho_px, self.alto_px).convert("RGBA")
        d = ImageDraw.Draw(img)
        t = self.tile
        for y in range(self.alto):
            for x in range(self.ancho):
                tipo = self.mapa[y][x]
                cx, cy = x * t, y * t
                if tipo == MURO:
                    d.rectangle(
                        [cx + 1, cy + 1, cx + t - 1, cy + t - 1],
                        fill=(72, 72, 92, 255),
                        outline=(38, 38, 52, 255),
                    )
                elif tipo == ARBOL:
                    d.ellipse(
                        [cx + 3, cy + 3, cx + t - 3, cy + t - 3],
                        fill=(40, 110, 50, 255),
                        outline=(18, 58, 28, 255),
                    )
        return img
