"""Manejador de input del teclado."""

import pygame


class InputHandler:
    """Captura input del teclado y lo convierte en un dict.

    Attributes:
        teclas: dict con el estado actual de las teclas
    """

    def __init__(self):
        self.teclas = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "jump": False,
            "crouch": False,
        }

    def actualizar(self) -> dict:
        """Actualiza el estado del input.

        Returns:
            dict con el estado actual de las teclas
        """
        keys = pygame.key.get_pressed()

        self.teclas["up"] = keys[pygame.K_w] or keys[pygame.K_UP]
        self.teclas["down"] = keys[pygame.K_s] or keys[pygame.K_DOWN]
        self.teclas["left"] = keys[pygame.K_a] or keys[pygame.K_LEFT]
        self.teclas["right"] = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        self.teclas["jump"] = keys[pygame.K_SPACE]
        self.teclas["crouch"] = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        return self.teclas
