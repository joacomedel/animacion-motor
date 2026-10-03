"""Capturas imágenes del motor (mundo 2D + personaje) sin abrir ventana.

Uso:
    SDL_VIDEODRIVER=dummy .venv/bin/python -m motor.debug
"""

import pygame

from motor.config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_FONDO
from motor.estado import Estado
from motor.renderer import Renderer
from motor.mundo import Mundo
from motor.camara import Camara


def escena(renderer, mundo, camara, estado, screen):
    """Compone una vista: región visible del mundo + personaje en su posición."""
    char_px = min(max(estado.x, mundo.tile), mundo.ancho_px - mundo.tile)
    char_py = min(max(estado.y, mundo.tile), mundo.alto_px - mundo.tile)
    cam_x, cam_y = camara.seguir(char_px, char_py)

    screen.fill(COLOR_FONDO)
    screen.blit(mundo.superficie(), (-cam_x, -cam_y))

    personaje = renderer.renderizar(estado)
    px, py = renderer.pies()
    screen.blit(
        personaje, (int(char_px - cam_x - px), int(char_py - cam_y - py - estado.z))
    )
    return screen


def main():
    """Captura imágenes del renderizado para debug."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    renderer = Renderer("stardew8", skin="skins/caballero_carmesi.png", zoom=4)
    mundo = Mundo(ancho=80, alto=50, tile=16)
    camara = Camara(SCREEN_WIDTH, SCREEN_HEIGHT, mundo)

    cx, cy = mundo.ancho_px // 2, mundo.alto_px // 2
    casos = [
        (
            Estado(x=cx, y=cy, z=0, animacion="idle", direccion="S", frame=0),
            "idle centro",
        ),
        (
            Estado(x=cx, y=cy, z=0, animacion="idle", direccion="E", frame=0),
            "idle centro E",
        ),
        (
            Estado(x=cx + 200, y=cy, z=0, animacion="run", direccion="S", frame=2),
            "run +200px",
        ),
        (
            Estado(x=cx, y=cy + 150, z=0, animacion="run", direccion="S", frame=5),
            "run +150py",
        ),
        (Estado(x=cx, y=cy, z=40, animacion="jump", direccion="S", frame=2), "jump"),
        (
            Estado(
                x=mundo.tile,
                y=mundo.tile,
                z=0,
                animacion="idle",
                direccion="S",
                frame=0,
            ),
            "esquina",
        ),
    ]

    for i, (estado, desc) in enumerate(casos):
        escena(renderer, mundo, camara, estado, screen)
        pygame.image.save(screen, f"debug_frame_{i}.png")
        print(f"Frame {i}: {desc}")

    pygame.quit()
    print("\nImágenes guardadas como debug_frame_*.png")


if __name__ == "__main__":
    main()
