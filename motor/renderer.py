"""Renderizador 3D→2D en tiempo real usando el kit de sprites.

Cada cuadro del personaje se arma con `armado.render_cuadro` (ficha de skin →
componentes → escena 3D de primitivas → pixel art) y se cachea por
(animación, dirección, frame): el motor no pre-genera PNGs, pero tampoco
re-renderiza 3D lo que no cambió (task-011).

El piso isométrico se dibuja aparte y se desplaza con la posición del mundo,
para que el movimiento se perciba (task-010).
"""

import numpy as np
import pygame
import pygame.surfarray
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

    def __init__(self, estilo="stardew8", skin=SKIN_DEFECTO, zoom=4, bloom=False):
        if estilo not in ESTILOS:
            raise ValueError(
                f"estilo desconocido {estilo!r}; disponibles: {', '.join(ESTILOS)}"
            )
        if zoom < 1:
            raise ValueError("zoom debe ser >= 1")
        self.estilo = estilo
        self.zoom = int(zoom)
        self.bloom = bloom
        self.skin_ruta = skin
        self.arma = None
        self.dano = False
        self.equipo = []
        self.ambiente = "dia"
        self.ficha_base = skins.ficha(skin)
        self.ficha = self._construir_ficha()
        self.pivote = armado.pivote(estilo)
        self._cache = {}
        self._cache_normal = {}
        self._ultima_normal = None
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
        from .equipo import MATERIALES

        if self.arma:
            f = skins.ficha_con_arma(self.skin_ruta, self.arma)
        else:
            f = self.ficha_base
        # materiales estándar de equipamiento siempre disponibles (p. ej. 'fuego' para la antorcha)
        f = {**f, "paleta": {**MATERIALES, **f["paleta"]}}
        if self.dano:
            f = {**f, "paleta": _paleta_con_dano(f["paleta"])}
        if self.equipo:
            from .equipo import ficha_con_equipo

            f = ficha_con_equipo(f, self.equipo)
        return f

    def _limpiar(self):
        self._cache.clear()
        self._cache_normal.clear()
        self._ultima_normal = None

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
                    self._superficie(anim, d, f)  # noqa: B018 (cachea normal)

    def _pose(self, anim: str) -> str:
        """Traduce la animación del motor al nombre de pose del kit."""
        return ANIM_A_POSE.get(anim, "quieto")

    def n_cuadros(self, anim: str) -> int:
        """Cuántos cuadros tiene la animación (según el kit)."""
        return len(cuadros(self._pose(anim)))

    def _superficie(self, anim: str, direccion: str, frame: int):
        """Superficie y buffer de normal cacheados de (animación, dirección, frame).

        Returns:
            (pygame.Surface, np.ndarray | None): superficie escalada y normal
            (h, w, 3) uint8 con ejes de mundo [-1,1]→[0,255], o None si el
            cuadro no tiene normal.
        """
        pose = self._pose(anim)
        n = len(cuadros(pose))
        p = int(frame) % n
        if direccion not in ESTILOS[self.estilo]["direcciones"]:
            direccion = ESTILOS[self.estilo]["direcciones"][0]
        clave = (pose, direccion, p)
        if clave in self._cache:
            return self._cache[clave], self._cache_normal.get(clave)
        cuadro = armado.render_cuadro(self.ficha, self.estilo, pose, p, direccion, bloom=self.bloom)
        img = cuadro.img.convert("RGBA")
        if self.zoom != 1:
            img = img.resize(
                (img.width * self.zoom, img.height * self.zoom), Image.NEAREST
            )
        sup = _superficie(img)
        # normal (ch, cw, 3) -> transponer a (h, w, 3) para coincidir con array3d
        normal = cuadro.buf.get("normal")
        if normal is not None:
            normal = (
                normal.transpose(1, 0, 2) if normal.shape[0] != img.height else normal
            )
        self._cache[clave] = sup
        self._cache_normal[clave] = normal
        return sup, normal

    def renderizar(self, estado) -> pygame.Surface:
        """Superficie del personaje para el estado dado, ya escalada."""
        sup, normal = self._superficie(estado.animacion, estado.direccion, estado.frame)
        self._ultima_normal = normal
        return sup

    def buffer_normal(self):
        """Buffer de normal (h, w, 3) uint8 del último cuadro renderizado.

        Las normales están en ejes de mundo: [-1,1]→[0,255] por canal.
        """
        if self._ultima_normal is None:
            raise RuntimeError(
                "No hay cuadro renderizado. Llamá a renderizar() primero."
            )
        return self._ultima_normal

    def iluminar(self, surface, normal, luz_pos, luz_color, luz_radio, intensidad):
        """Ilumina una superficie con una luz puntual por píxel (task-020).

        Aplica factor = max(0, N·L) * caida(distancia) sobre el color del sprite,
        sin re-renderizar 3D. Los píxeles transparentes no se modifican.

        Args:
            surface: pygame.Surface RGBA a iluminar.
            normal: np.ndarray (h, w, 3) uint8 con normales en ejes de mundo.
            luz_pos: (x, y) en px de pantalla.
            luz_color: (r, g, b) color de la luz.
            luz_radio: radio de la luz en px.
            intensidad: factor de intensidad (>= 0).

        Returns:
            Nueva pygame.Surface iluminada (la original no se modifica).
        """
        w, h = surface.get_width(), surface.get_height()
        nh, nw = normal.shape[:2]

        # Escalar normal al tamaño de la surface si hace falta
        if (nw, nh) != (w, h):
            normal_surf = pygame.surfarray.make_surface(normal.transpose(1, 0, 2))
            normal_surf = pygame.transform.scale(normal_surf, (w, h))
            normal = pygame.surfarray.array3d(normal_surf).transpose(1, 0, 2)

        arr = pygame.surfarray.array3d(surface).astype(np.float32)  # (w, h, 3)
        alpha = pygame.surfarray.array_alpha(surface)  # (w, h)

        # Normales en [-1, 1]
        n = normal.astype(np.float32) / 127.5 - 1.0  # (h, w, 3)

        # Distancia y caída
        yy, xx = np.mgrid[0:h, 0:w]  # (h, w)
        dx = xx - luz_pos[0]
        dy = yy - luz_pos[1]
        dist = np.sqrt(dx**2 + dy**2)
        caida = np.clip(1.0 - dist / luz_radio, 0.0, 1.0) ** 2  # (h, w)

        # Vector luz normalizado (con altura sobre el plano)
        dist_safe = np.where(dist == 0, 1.0, dist)
        lx = -dx / dist_safe
        ly = -dy / dist_safe
        lz = 0.6
        L = np.stack([lx, ly, np.full_like(lx, lz)], axis=-1)  # (h, w, 3)
        L_norm = np.sqrt(lx**2 + ly**2 + lz**2)
        L = L / L_norm[..., None]

        # N·L
        NdotL = np.clip((n * L).sum(axis=-1), 0.0, 1.0)  # (h, w)

        # Factor final
        factor = NdotL * caida * intensidad  # (h, w)

        # Color de la luz normalizado
        luz = np.array(luz_color, dtype=np.float32) / 255.0  # (3,)

        # Iluminación aditiva: arr + factor * luz * 255
        factor_w = factor.T[..., None]  # (w, h, 1)
        arr_ilu = arr + factor_w * luz * 255.0

        # Solo píxeles opacos
        alpha_w = alpha[..., None] / 255.0  # (w, h, 1)
        arr_ilu = arr * (1.0 - alpha_w) + arr_ilu * alpha_w

        arr_ilu = np.clip(arr_ilu, 0, 255).astype(np.uint8)
        result = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.surfarray.pixels3d(result)[:] = arr_ilu
        pygame.surfarray.pixels_alpha(result)[:] = alpha
        return result

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
