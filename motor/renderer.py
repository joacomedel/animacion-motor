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


def _paleta_con_dano(paleta: dict) -> dict:
    """Paleta con la piel teñida de rojo para representar daño (sin regenerar PNGs)."""
    p = {k: dict(v) if isinstance(v, dict) else v for k, v in paleta.items()}
    if isinstance(p.get("piel"), dict):
        p["piel"] = {**p["piel"], "base": "#ff5a5a"}
    return p


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
        self.skin_ruta = skin
        self.arma = None
        self.dano = False
        self.equipo = []
        self.ambiente = "dia"
        self.ficha_base = skins.ficha(skin)
        self.ficha = self._construir_ficha()
        self.pivote = armado.pivote(estilo)
        self._cache = {}
        self._piso = None
        # capas de tinte de iluminación en tiempo real (baratas: no re-renderizan 3D)
        self._ambientes = {
            "dia": None,
            "tarde": (255, 140, 60, 60),
            "noche": (20, 20, 90, 110),
        }
        self._capa_ambiente = {}

    def _construir_ficha(self):
        """Ficha de la skin actual, con arma, daño y equipo si están activos."""
        if self.arma:
            f = skins.ficha_con_arma(self.skin_ruta, self.arma)
        else:
            f = self.ficha_base
        if self.dano:
            f = {**f, "paleta": _paleta_con_dano(f["paleta"])}
        if self.equipo:
            from .equipo import ficha_con_equipo

            f = ficha_con_equipo(f, self.equipo)
        return f

    def _limpiar(self):
        self._cache.clear()

    # --- skins en tiempo real (task-012) ---

    def set_skin(self, ruta: str):
        """Cambia la skin en caliente: se reconstruye la ficha y se invalida la caché."""
        self.skin_ruta = ruta
        self.ficha_base = skins.ficha(ruta)
        self.ficha = self._construir_ficha()
        self._limpiar()

    def set_arma(self, arma):
        """Pone/quita un arma en la mano (espada, hacha, antorcha, escudo, bastón)."""
        self.arma = arma
        self.ficha = self._construir_ficha()
        self._limpiar()

    def set_dano(self, activo: bool):
        """Representa daño: tiñe la piel de rojo sin regenerar PNGs."""
        self.dano = bool(activo)
        self.ficha = self._construir_ficha()
        self._limpiar()

    def set_equipo(self, items):
        """Equipa una lista de ítems (ver `motor.equipo.ITEMS`): reconstruye la ficha y limpia la caché."""
        from .equipo import Equipo

        self.equipo = Equipo(items).items
        self.ficha = self._construir_ficha()
        self._limpiar()

    # --- iluminación en tiempo real (task-013) ---

    def set_ambiente(self, nombre: str):
        if nombre not in self._ambientes:
            raise ValueError(
                f"ambiente desconocido {nombre!r}; disponibles: {', '.join(self._ambientes)}"
            )
        self.ambiente = nombre

    def capa_ambiente(self, ancho: int, alto: int):
        """Capa de tinte para el ambiente actual (None = día, sin tinte)."""
        color = self._ambientes[self.ambiente]
        if color is None:
            return None
        clave = (ancho, alto, self.ambiente)
        capa = self._capa_ambiente.get(clave)
        if capa is None:
            capa = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            capa.fill(color)
            self._capa_ambiente[clave] = capa
        return capa

    # --- caché (task-011 / task-016) ---

    def precalentar(self):
        """Renderiza todas las combinaciones una vez para que ningún frame en vivo page 3D."""
        for anim in ANIM_A_POSE:
            for d in ESTILOS[self.estilo]["direcciones"]:
                for f in range(self.n_cuadros(anim)):
                    self._superficie(anim, d, f)

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
