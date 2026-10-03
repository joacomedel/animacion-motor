"""Script de debug para capturar imágenes del renderizado.

Uso:
    python -m motor.debug
"""

import sys
import pygame
from motor.estado import Estado
from motor.renderer import Renderer


def main():
    """Captura imágenes del renderizado para debug."""
    pygame.init()

    renderer = Renderer("stardew8")

    # Probar diferentes estados
    estados = [
        Estado(x=0, y=0, z=0, animacion="idle", direccion="S", frame=0),
        Estado(x=0, y=0, z=0, animacion="idle", direccion="E", frame=0),
        Estado(x=0, y=0, z=0, animacion="run", direccion="S", frame=0),
        Estado(x=0, y=0, z=0, animacion="run", direccion="S", frame=5),
        Estado(x=0, y=0, z=4, animacion="jump", direccion="S", frame=2),
        Estado(x=0, y=0, z=0, animacion="crouch", direccion="S", frame=3),
    ]

    for i, estado in enumerate(estados):
        # Renderizar
        surf = renderer.renderizar(estado)

        # Guardar imagen
        pygame.image.save(surf, f"debug_frame_{i}.png")

        print(f"Frame {i}: {estado.animacion} {estado.direccion} frame={estado.frame}")

    print("\nImágenes guardadas como debug_frame_*.png")


if __name__ == "__main__":
    main()
