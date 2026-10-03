"""Motorcito de lógica simulada.

Simula la física básica del juego (gravedad, movimiento, salto) y manda
estado al motor visual. Está diseñado para ser fácilmente reemplazable
por un servidor real.

Para desacoplar: reemplazar `LogicaSimulada` por `LogicaServidor` que
reciba estado por WebSocket en lugar de simularlo.
"""

import math
from motor.estado import Estado


class LogicaSimulada:
    """Simula la lógica del juego (física, input, estado).

    En el futuro, esta clase será reemplazada por un cliente que reciba
    estado de un servidor real por WebSocket.
    """

    def __init__(self):
        self.estado = Estado()
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.vel_z = 0.0
        self.en_el_piso = True
        self.frame_actual = 0
        self.tiempo_animacion = 0.0

        # Configuración de física
        self.gravedad = 0.5
        self.velocidad_movimiento = 3.0
        self.velocidad_salto = 8.0

        # Animaciones disponibles (frames, fps, loop)
        self.animaciones = {
            "idle": {"n": 4, "fps": 4, "loop": True},
            "run": {"n": 10, "fps": 12, "loop": True},
            "jump": {"n": 6, "fps": 10, "loop": False},
            "crouch": {"n": 4, "fps": 8, "loop": False},
        }

    def procesar_input(self, input: dict) -> None:
        """Procesa input del teclado y actualiza velocidades.

        Args:
            input: dict con keys "up", "down", "left", "right", "jump", "crouch"
        """
        # Movimiento horizontal
        self.vel_x = 0.0
        self.vel_y = 0.0

        if input.get("up"):
            self.vel_y = -self.velocidad_movimiento
        if input.get("down"):
            self.vel_y = self.velocidad_movimiento
        if input.get("left"):
            self.vel_x = -self.velocidad_movimiento
        if input.get("right"):
            self.vel_x = self.velocidad_movimiento

        # Salto
        if input.get("jump") and self.en_el_piso:
            self.vel_z = self.velocidad_salto
            self.en_el_piso = False

        # Agacharse
        if input.get("crouch") and self.en_el_piso:
            self.estado.animacion = "crouch"
            self.frame_actual = min(self.frame_actual + 1, 3)
        elif self.estado.animacion == "crouch" and not input.get("crouch"):
            self.estado.animacion = "idle"
            self.frame_actual = 0

    def actualizar(self, dt: float) -> Estado:
        """Actualiza la física y devuelve el nuevo estado.

        Args:
            dt: delta time en segundos

        Returns:
            Estado actualizado
        """
        # Aplicar gravedad
        if not self.en_el_piso:
            self.vel_z -= self.gravedad
            self.estado.z += self.vel_z * dt * 60

            # Si toca el piso
            if self.estado.z <= 0:
                self.estado.z = 0
                self.vel_z = 0
                self.en_el_piso = True
                self.estado.animacion = "idle"
                self.frame_actual = 0

        # Movimiento horizontal
        self.estado.x += self.vel_x * dt * 60
        self.estado.y += self.vel_y * dt * 60

        # Determinar animación
        if not self.en_el_piso:
            self.estado.animacion = "jump"
        elif abs(self.vel_x) > 0.1 or abs(self.vel_y) > 0.1:
            self.estado.animacion = "run"
        elif self.estado.animacion != "crouch":
            self.estado.animacion = "idle"

        # Actualizar frame de animación
        self.tiempo_animacion += dt
        anim = self.animaciones.get(self.estado.animacion, self.animaciones["idle"])
        duracion_frame = 1.0 / anim["fps"]

        if self.tiempo_animacion >= duracion_frame:
            self.tiempo_animacion -= duracion_frame
            self.frame_actual += 1

            if self.frame_actual >= anim["n"]:
                if anim["loop"]:
                    self.frame_actual = 0
                else:
                    self.frame_actual = anim["n"] - 1

        self.estado.frame = self.frame_actual

        # Determinar dirección (8 direcciones)
        if abs(self.vel_x) > 0.1 or abs(self.vel_y) > 0.1:
            self.estado.direccion = self._calcular_direccion(self.vel_x, self.vel_y)

        return self.estado

    def _calcular_direccion(self, vx: float, vy: float) -> str:
        """Calcula la dirección (8 direcciones) según velocidad.

        Args:
            vx: velocidad X
            vy: velocidad Y

        Returns:
            Dirección ("S", "SE", "E", "NE", "N", "NW", "W", "SW")
        """
        angulo = math.degrees(math.atan2(vy, vx))
        if angulo < 0:
            angulo += 360

        # 8 direcciones: S=0, SE=45, E=90, NE=135, N=180, NW=225, W=270, SW=315
        direcciones = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
        indice = round(angulo / 45) % 8
        return direcciones[indice]
