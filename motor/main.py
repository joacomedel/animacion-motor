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

# skins que se pueden cambiar en caliente (teclas 1-4)
SKINS = [
    "skins/aldeano_bosque.png",
    "skins/caballero_carmesi.png",
    "skins/mago.png",
    "skins/vampira.png",
]
AMBIENTES = ["dia", "tarde", "noche"]


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
    renderer = Renderer(estilo="stardew8", skin="skins/caballero_carmesi.png", zoom=4)
    input_handler = InputHandler()
    fuente = pygame.font.Font(None, 24)

    # Pre-calentar la caché: ningún frame en vivo paga el costo del render 3D
    print("Pre-calentando caché del renderer...")
    renderer.precalentar()
    print(f"Caché lista: {len(renderer._cache)} cuadros")

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
                elif event.key == pygame.K_1:
                    renderer.set_skin(SKINS[0])
                elif event.key == pygame.K_2:
                    renderer.set_skin(SKINS[1])
                elif event.key == pygame.K_3:
                    renderer.set_skin(SKINS[2])
                elif event.key == pygame.K_4:
                    renderer.set_skin(SKINS[3])
                elif event.key == pygame.K_g:
                    renderer.set_arma(None if renderer.arma else "espada")
                elif event.key == pygame.K_d:
                    renderer.set_dano(not renderer.dano)
                elif event.key == pygame.K_l:
                    i = (AMBIENTES.index(renderer.ambiente) + 1) % len(AMBIENTES)
                    renderer.set_ambiente(AMBIENTES[i])

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
            # Piso: se desplaza con la posición del mundo (el movimiento se ve)
            piso, pos_piso = renderer.piso(
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                (estado_interpolado.x, estado_interpolado.y),
            )
            screen.blit(piso, pos_piso)

            # Personaje: los pies en el centro-bajo, levantado por z (salto)
            personaje = renderer.renderizar(estado_interpolado)
            px, py = renderer.pies()
            destino = (
                SCREEN_WIDTH // 2 - px,
                int(SCREEN_HEIGHT * 0.68) - py - int(estado_interpolado.z),
            )
            screen.blit(personaje, destino)

            # Iluminación en tiempo real: capa de tinte sobre la escena
            capa = renderer.capa_ambiente(SCREEN_WIDTH, SCREEN_HEIGHT)
            if capa is not None:
                screen.blit(capa, (0, 0))
        except Exception as e:
            print(f"Error renderizando: {e}")

        # HUD: FPS y estado
        fps = clock.get_fps()
        skin = renderer.skin_ruta.split("/")[-1].replace(".png", "")
        hud = (
            f"{fps:4.0f} FPS  {estado_interpolado.animacion} {estado_interpolado.direccion} "
            f"f={estado_interpolado.frame}  skin={skin} arma={renderer.arma or '-'} "
            f"dano={'SI' if renderer.dano else 'no'} amb={renderer.ambiente}"
        )
        screen.blit(fuente.render(hud, True, (230, 230, 240)), (8, 8))

        # Actualizar pantalla
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
