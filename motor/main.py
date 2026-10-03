"""Entry point del motor visual 3D→2D en tiempo real.

Uso:
    python -m motor.main
"""

import sys
import pygame
from motor.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLOR_FONDO
from motor.estado import Estado
from motor.logica import LogicaSimulada
from motor.game_loop import GameLoop
from motor.renderer import Renderer
from motor.input_handler import InputHandler


def main():
    """Función principal del motor visual."""
    # Inicializar Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Motor Visual 3D→2D")
    clock = pygame.time.Clock()

    # Crear componentes
    logica = LogicaSimulada()
    game_loop = GameLoop()
    renderer = Renderer(estilo="stardew8")
    input_handler = InputHandler()

    # Estado inicial
    estado_inicial = Estado(x=0, y=0, z=0, animacion="idle", direccion="S", frame=0)
    game_loop.iniciar(estado_inicial)

    # Loop principal
    running = True
    while running:
        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Input
        input = input_handler.actualizar()

        # Lógica
        logica.procesar_input(input)
        nuevo_estado = logica.actualizar(1.0 / FPS)

        # Game loop (interpolación)
        game_loop.actualizar(nuevo_estado)
        estado_interpolado = game_loop.obtener_estado_interpolado()

        # Renderizar
        screen.fill(COLOR_FONDO)

        try:
            superficie = renderer.renderizar(estado_interpolado)
            # Centrar en pantalla
            x = (SCREEN_WIDTH - superficie.get_width()) // 2
            y = (SCREEN_HEIGHT - superficie.get_height()) // 2
            screen.blit(superficie, (x, y))
        except Exception as e:
            print(f"Error renderizando: {e}")

        # Actualizar pantalla
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
