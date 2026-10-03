"""Renderizador 3D→2D en tiempo real usando el kit de sprites.

Cada cuadro del personaje se arma con `armado.render_cuadro` (ficha de skin →
componentes → escena 3D de primitivas → pixel art) y se cachea por
(animación, dirección, frame): el motor no pre-genera PNGs, pero tampoco
re-renderiza 3D lo que no cambió (task-011).

El piso isométrico se dibuja aparte y se desplaza con la posición del mundo,
para que el movimiento se perciba (task-010).
"""

import pygame
from PIL import Image

from sprites_lib import armado, skins
from sprites_lib.estilos import ESTILOS
from sprites_lib.poses import cuadros
from sprites_lib.render3d import piso_iso

# nombre de animación del motor → nombre de pose/ciclo del kit
ANIM_A_POSE = {
    "idle": "quieto",
    "run": "caminar_lpc",
    "jump": "saltar",
    "crouch": "agachar",
}
SKIN_DEFECTO = "skins/caballero_carmesi.png"


def _superficie(img: Image.Image) -> pygame.Surface:
    """Convierte una imagen PIL RGBA a superficie de Pygame."""
    img = img.convert("RGBA")
    return pygame.image.fromstring(img.tobytes(), img.size, "RGBA")


class Renderer:
    """Renderiza el personaje del kit de sprites como pixel art en tiempo real.

    Attributes:
        estilo: perfil de estilo (stardew8)
        zoom: factor de escala entero para ver el pixel art
        ficha: ficha de la skin cargada (personaje base)
        pivote: punto de los pies (suelo) dentro de la celda, en px de celda
    """

    def __init__(self, estilo="stardew8", skin=SKIN_DEFECTO, zoom=4):
        if estilo not in ESTILOS:
            raise ValueError(
                f"estilo desconocido {estilo!r}; disponibles: {', '.join(ESTILOS)}"
            )
        if zoom < 1:
            raise ValueError("zoom debe ser >= 1")
        self.estilo = estilo
        self.zoom = int(zoom)
        self.ficha = skins.ficha(skin)
        self.pivote = armado.pivote(estilo)
        self._cache = {}
        self._piso = None

    def _pose(self, anim: str) -> str:
        """Traduce la animación del motor al nombre de pose del kit."""
        return ANIM_A_POSE.get(anim, "quieto")

    def n_cuadros(self, anim: str) -> int:
        """Cuántos cuadros tiene la animación (según el kit)."""
        return len(cuadros(self._pose(anim)))

    def _superficie(self, anim: str, direccion: str, frame: int) -> pygame.Surface:
        """Superficie cacheada de (animación, dirección, frame)."""
        pose = self._pose(anim)
        n = len(cuadros(pose))
        p = int(frame) % n
        if direccion not in ESTILOS[self.estilo]["direcciones"]:
            direccion = ESTILOS[self.estilo]["direcciones"][0]
        clave = (pose, direccion, p)
        sup = self._cache.get(clave)
        if sup is None:
            cuadro = armado.render_cuadro(self.ficha, self.estilo, pose, p, direccion)
            img = cuadro.img.convert("RGBA")
            if self.zoom != 1:
                img = img.resize(
                    (img.width * self.zoom, img.height * self.zoom), Image.NEAREST
                )
            sup = _superficie(img)
            self._cache[clave] = sup
        return sup

    def renderizar(self, estado) -> pygame.Surface:
        """Superficie del personaje para el estado dado, ya escalada."""
        return self._superficie(estado.animacion, estado.direccion, estado.frame)

    def pies(self) -> tuple:
        """Posición (x, y) de los pies dentro de la superficie renderizada (px de pantalla)."""
        return (self.pivote[0] * self.zoom, self.pivote[1] * self.zoom)

    def piso(self, ancho: int, alto: int, scroll=(0.0, 0.0)):
        """Superficie del piso isométrico cacheada y el offset para scrollear.

        Args:
            ancho, alto: tamaño de la vista
            scroll: (x, y) del mundo: el piso se mueve al revés

        Returns:
            (superficie, (x, y)) listo para `screen.blit`.
        """
        if self._piso is None:
            base = piso_iso(ancho + 32, alto + 16)
            self._piso = _superficie(base)
        ox = int(scroll[0]) % 32
        oy = int(scroll[1]) % 16
        return self._piso, (-ox, -oy)
