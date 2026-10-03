"""Renderizador 3D→2D en tiempo real.

Usa el motor render3d.py (de referencias/) para renderizar un personaje
en 8 direcciones con estilo pixel art (stardew8).
"""

import numpy as np
from PIL import Image
import pygame
import io
import base64

from sprites_lib.render3d import CamaraCenital, Escena
from sprites_lib.estilos import ESTILOS
from sprites_lib import paleta as paleta_mod
from sprites_lib import ciclos


class Renderer:
    """Renderiza un personaje 3D como imagen 2D pixel art.

    Attributes:
        estilo: perfil de estilo (stardew8)
        camara: cámara isométrica
        paleta: colores del personaje
    """

    def __init__(self, estilo="stardew8"):
        self.estilo = ESTILOS[estilo]
        self.camara = None
        self.paleta = None
        self._cache_camara = {}
        self._frame_counter = 0

    def _obtener_camara(self, direccion: str):
        """Obtiene o crea la cámara para una dirección.

        Args:
            direccion: dirección ("S", "SE", "E", "NE", "N", "NW", "W", "SW")

        Returns:
            CamaraCenital para esa dirección
        """
        if direccion not in self._cache_camara:
            celda = self.estilo["celda"]
            self._cache_camara[direccion] = CamaraCenital(
                mira=direccion,
                cw=celda["cw"],
                ch=celda["ch"],
                gx=celda["gx"],
                gy=celda["gy"],
                ky=self.estilo["proporciones"].get("paso", 0.5),
                kz=0.92,
                luz=self.estilo["proporciones"]["luz"],
            )
        return self._cache_camara[direccion]

    def renderizar(self, estado) -> pygame.Surface:
        """Renderiza un estado y devuelve una superficie de Pygame.

        Args:
            estado: Estado del personaje (x, y, z, animacion, direccion, frame)

        Returns:
            pygame.Surface con el personaje renderizado
        """
        # Obtener cámara para la dirección
        camara = self._obtener_camara(estado.direccion)

        # Crear escena
        escena = Escena(camara, self._crear_paleta())

        # Agregar piso isométrico
        self._agregar_piso(escena, estado)

        # Agregar personaje a la escena
        self._agregar_personaje(escena, estado)

        # Renderizar
        img = escena.render(
            estilo=self.estilo["render"],
            buffers=False,
        )

        # Convertir PIL Image a superficie de Pygame
        img = img.convert("RGBA")
        self._frame_counter += 1
        return pygame.image.fromstring(img.tobytes(), img.size, "RGBA")

    def _crear_paleta(self):
        """Crea la paleta de colores para el renderizado.

        Returns:
            dict con colores {nombre: (sombra, base, luz)}
        """
        # Paleta básica de prueba con formato (sombra, base, luz)
        return {
            "piel": ((180, 140, 110), (255, 220, 180), (255, 240, 220)),
            "ropa": ((60, 90, 140), (100, 150, 200), (140, 190, 240)),
            "pelo": ((50, 30, 15), (80, 50, 30), (120, 90, 60)),
            "pantalon": ((40, 40, 55), (60, 60, 80), (90, 90, 110)),
            "bota": ((25, 18, 12), (40, 30, 25), (60, 45, 35)),
            "piso_claro": ((60, 90, 60), (80, 120, 80), (100, 140, 100)),
            "piso_oscuro": ((50, 80, 50), (70, 110, 70), (90, 130, 90)),
        }

    def _agregar_personaje(self, escena: Escena, estado) -> None:
        """Agrega el personaje a la escena 3D usando las animaciones reales.

        Args:
            escena: escena 3D
            estado: estado del personaje
        """
        # Obtener la animación correspondiente
        animacion = self._obtener_animacion(estado.animacion)
        if animacion is None:
            return

        # Obtener el frame de la animación
        frame = estado.frame % animacion["n"]
        bob = animacion["bob"][frame] if frame < len(animacion["bob"]) else 0

        # Posición base del personaje (relativa a la cámara)
        # La cámara sigue al personaje, así que el personaje siempre está en el centro
        x, y, z = 0, 0, estado.z

        # Crear cuerpo usando las animaciones reales
        # Cabeza (con bob)
        cabeza_z = z + 20 + bob
        escena.esfera((x, y, cabeza_z), 6, "piel")

        # Torso (cápsula vertical)
        escena.capsula((x, y, z + 8), (x, y, z + 18), 4, "ropa")

        # Brazos (usando la animación)
        mano = animacion.get("mano", {})
        if "xy" in mano:
            # Animación con posiciones de mano específicas
            xy = mano["xy"]
            if frame < len(xy):
                mx, my = xy[frame]
                # Convertir coordenadas del rig a coordenadas 3D
                escena.capsula(
                    (x - 5, y, z + 16), (x - 8 + mx, y, z + 8 + my), 2, "piel"
                )
                escena.capsula(
                    (x + 5, y, z + 16), (x + 8 + mx, y, z + 8 + my), 2, "piel"
                )
        else:
            # Animación con parámetros de movimiento
            cx, ax = mano.get("cx", 20), mano.get("ax", 7)
            y0, ay = mano.get("y0", 21), mano.get("ay", 7)
            fase = mano.get("fase", 0)
            # Calcular posición de la mano
            import math

            mx = cx + ax * math.sin((frame + fase) * math.pi * 2 / animacion["n"])
            my = y0 + ay * math.sin((frame + fase) * math.pi * 2 / animacion["n"])
            escena.capsula((x - 5, y, z + 16), (x - 8 + mx, y, z + 8 + my), 2, "piel")
            escena.capsula((x + 5, y, z + 16), (x + 8 + mx, y, z + 8 + my), 2, "piel")

        # Piernas (usando la animación)
        pie = animacion.get("pie", [])
        if frame < len(pie):
            px, py = pie[frame]
            # Convertir coordenadas del rig a coordenadas 3D
            escena.capsula((x - 3, y, z + 8), (x - 4 + px, y, z + py), 2, "pantalon")
            escena.capsula((x + 3, y, z + 8), (x + 4 + px, y, z + py), 2, "pantalon")

            # Pies
            escena.esfera((x - 4 + px, y, z + py), 2, "bota")
            escena.esfera((x + 4 + px, y, z + py), 2, "bota")

    def _obtener_animacion(self, nombre: str):
        """Obtiene la animación por nombre.

        Args:
            nombre: nombre de la animación ("idle", "run", "jump", "crouch")

        Returns:
            dict con la animación o None
        """
        animaciones = {
            "idle": ciclos.QUIETO,
            "run": ciclos.CORRER,
            "jump": ciclos.SALTAR,
            "crouch": ciclos.AGACHAR,
        }
        return animaciones.get(nombre)

    def _agregar_piso(self, escena: Escena, estado) -> None:
        """Agrega el piso isométrico a la escena.

        Args:
            escena: escena 3D
            estado: estado del personaje
        """
        # Piso centrado en el personaje (que está en 0,0)
        # Dibujar un área de 7x7 tiles alrededor del personaje
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                # Color alternado para efecto de cuadrícula
                color = "piso_claro" if (dx + dy) % 2 == 0 else "piso_oscuro"
                # Dibujar tile como una caja plana
                escena.caja((dx * 16, dy * 16, -1), (8, 8, 1), color, n=2)

    def obtener_imagen_debug(self, estado) -> str:
        """Obtiene una imagen del renderizado en base64 para debug.

        Args:
            estado: estado del personaje

        Returns:
            String base64 con la imagen PNG
        """
        camara = self._obtener_camara(estado.direccion)
        escena = Escena(camara, self._crear_paleta())
        self._agregar_piso(escena, estado)
        self._agregar_personaje(escena, estado)

        img = escena.render(
            estilo=self.estilo["render"],
            buffers=False,
        )

        # Convertir a base64
        img = img.convert("RGBA")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
