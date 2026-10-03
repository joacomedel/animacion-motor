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
from motor.equipo import Equipo
from motor.mundo import Mundo
from motor.camara import Camara

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

    # Mundo 2D (más grande que la pantalla) y cámara que sigue al personaje
    mundo = Mundo(ancho=80, alto=50, tile=16)
    camara = Camara(SCREEN_WIDTH, SCREEN_HEIGHT, mundo)
    print(f"Mundo: {mundo.ancho_px}×{mundo.alto_px} px")

    equipo = Equipo()

    def toggle(item):
        equipo.alternar(item)
        renderer.set_equipo(equipo.items)

    # Estado inicial: el personaje en el centro del mundo.
    # logica.estado es su propio estado (game_loop.iniciar no lo toca): sin esto el
    # personaje arranca en (0,0), la esquina, y se ve cortado contra el borde.
    estado_inicial = Estado(
        x=mundo.ancho_px // 2,
        y=mundo.alto_px // 2,
        z=0,
        animacion="idle",
        direccion="S",
        frame=0,
    )
    logica.estado = estado_inicial
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
                elif event.key == pygame.K_q:
                    toggle("espada")
                elif event.key == pygame.K_e:
                    toggle("antorcha")
                elif event.key == pygame.K_r:
                    toggle("sombrero")
                elif event.key == pygame.K_f:
                    toggle("armadura_malla")
                elif event.key == pygame.K_c:
                    toggle("guante_cuero")
                elif event.key == pygame.K_h:
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
            # Renderizar el personaje primero: su tamaño define el margen con el que se
            # clampea al mundo. Sin esto, en el borde lateral la cámara se clampea y el
            # sprite se corta contra la pantalla al moverse al costado.
            personaje = renderer.renderizar(estado_interpolado)
            px, py = renderer.pies()
            w, h = personaje.get_width(), personaje.get_height()

            # Posición clampeada dejando que el sprite entero entre en pantalla
            char_px = min(max(estado_interpolado.x, px), mundo.ancho_px - (w - px))
            char_py = min(max(estado_interpolado.y, py), mundo.alto_px - (h - py))

            # cámara que sigue al personaje
            cam_x, cam_y = camara.seguir(char_px, char_py)
            screen.blit(mundo.superficie(), (-cam_x, -cam_y))

            # personaje: los pies en su posición del mundo, levantado por z (salto)
            sombra = renderer.sombra()
            screen.blit(
                sombra,
                (
                    int(char_px - cam_x - sombra.get_width() // 2),
                    int(char_py - cam_y - sombra.get_height() // 2 - estado_interpolado.z),
                ),
            )

            screen.blit(
                personaje,
                (
                    int(char_px - cam_x - px),
                    int(char_py - cam_y - py - estado_interpolado.z),
                ),
            )

            # Iluminación en tiempo real: capa de tinte sobre la escena
            capa = renderer.capa_ambiente(SCREEN_WIDTH, SCREEN_HEIGHT)
            if capa is not None:
                screen.blit(capa, (0, 0))
        except Exception as e:
            print(f"Error renderizando: {e}")

        # HUD: FPS y estado
        fps = clock.get_fps()
        skin = renderer.skin_ruta.split("/")[-1].replace(".png", "")
        equipo_txt = ",".join(equipo.items) or "-"
        hud = (
            f"{fps:4.0f} FPS  {estado_interpolado.animacion} {estado_interpolado.direccion} "
            f"f={estado_interpolado.frame}  skin={skin} equipo=[{equipo_txt}] "
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
