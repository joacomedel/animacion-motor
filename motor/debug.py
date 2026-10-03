"""Captura imágenes del motor (piso + personaje) sin abrir ventana.

Uso:
    SDL_VIDEODRIVER=dummy .venv/bin/python -m motor.debug
"""

import pygame

from motor.config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_FONDO
from motor.estado import Estado
from motor.renderer import Renderer


def escena(
    renderer: Renderer, estado: Estado, screen: pygame.Surface
) -> pygame.Surface:
    """Compone una vista del motor: piso desplazado por el mundo + personaje."""
    screen.fill(COLOR_FONDO)
    piso, pos_piso = renderer.piso(SCREEN_WIDTH, SCREEN_HEIGHT, (estado.x, estado.y))
    screen.blit(piso, pos_piso)

    personaje = renderer.renderizar(estado)
    px, py = renderer.pies()
    destino = (SCREEN_WIDTH // 2 - px, int(SCREEN_HEIGHT * 0.68) - py - int(estado.z))
    screen.blit(personaje, destino)
    return screen


def main():
    """Captura imágenes del renderizado para debug."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    renderer = Renderer("stardew8", skin="skins/caballero_carmesi.png", zoom=4)

    # (estado, descripción) — incluye dos posiciones de mundo para ver el scroll del piso
    casos = [
        (Estado(x=0, y=0, z=0, animacion="idle", direccion="S", frame=0), "idle S"),
        (Estado(x=0, y=0, z=0, animacion="idle", direccion="E", frame=0), "idle E"),
        (Estado(x=0, y=0, z=0, animacion="run", direccion="S", frame=2), "run S f2"),
        (
            Estado(x=64, y=0, z=0, animacion="run", direccion="S", frame=5),
            "run S f5 (x=64)",
        ),
        (
            Estado(x=0, y=0, z=40, animacion="jump", direccion="S", frame=2),
            "jump S (z=40)",
        ),
        (
            Estado(x=0, y=0, z=0, animacion="crouch", direccion="S", frame=3),
            "crouch S f3",
        ),
    ]

    for i, (estado, desc) in enumerate(casos):
        escena(renderer, estado, screen)
        pygame.image.save(screen, f"debug_frame_{i}.png")
        print(f"Frame {i}: {desc}")

    pygame.quit()
    print("\nImágenes guardadas como debug_frame_*.png")


if __name__ == "__main__":
    main()
