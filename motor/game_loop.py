"""Game loop a timestep fijo con interpolación.

Corre a 60 Hz fijo, interpola entre estados para suavizar el movimiento.
"""

import time
import pygame
from motor.config import FPS, FIXED_TIMESTEP


class GameLoop:
    """Game loop a timestep fijo.

    Attributes:
        running: si el loop está corriendo
        accumulator: tiempo acumulado para el timestep fijo
    """

    def __init__(self):
        self.running = False
        self.accumulator = 0.0
        self.ultimo_tiempo = 0.0
        self.estado_anterior = None
        self.estado_actual = None

    def iniciar(self, estado_inicial):
        """Inicia el game loop.

        Args:
            estado_inicial: estado inicial del personaje
        """
        self.running = True
        self.ultimo_tiempo = time.time()
        self.estado_anterior = estado_inicial
        self.estado_actual = estado_inicial

    def actualizar(self, nuevo_estado) -> float:
        """Actualiza el loop con un nuevo estado.

        Args:
            nuevo_estado: nuevo estado del servidor/lógica

        Returns:
            Factor de interpolación (0.0-1.0)
        """
        ahora = time.time()
        dt = ahora - self.ultimo_tiempo
        self.ultimo_tiempo = ahora

        # Limitar dt para evitar saltos grandes
        dt = min(dt, 0.1)

        self.accumulator += dt

        # Si pasó un timestep fijo, actualizar estado
        if self.accumulator >= FIXED_TIMESTEP:
            self.estado_anterior = self.estado_actual
            self.estado_actual = nuevo_estado
            self.accumulator -= FIXED_TIMESTEP

        # Factor de interpolación
        return self.accumulator / FIXED_TIMESTEP

    def obtener_estado_interpolado(self) -> float:
        """Devuelve el estado interpolado.

        Returns:
            Estado interpolado entre estado_anterior y estado_actual
        """
        if self.estado_anterior is None or self.estado_actual is None:
            return self.estado_actual

        t = self.accumulator / FIXED_TIMESTEP
        return self.estado_anterior.lerp(self.estado_actual, t)

    def detener(self):
        """Detiene el game loop."""
        self.running = False
