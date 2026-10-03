"""Entry point del motor visual 3D→2D en tiempo real.

Uso:
    python -m motor.main
"""

import sys
import time
import pygame
from motor.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLOR_FONDO
from motor.estado import Estado
from motor.logica import LogicaSimulada
from motor.game_loop import GameLoop
from motor.renderer import LUCES_MOTOR, Renderer
from motor.input_handler import InputHandler
from motor.equipo import Equipo
from motor.mundo import Mundo, ARBOL
from motor.camara import Camara


def elementos_ordenados(mundo, cam_x, cam_y, vx, vy, char_y):
    """Elementos a dibujar ordenados por Y: árboles y personaje.

    Returns:
        Lista de tuplas ("arbol", tx, ty) y ("personaje", None),
        ordenadas por Y del mundo en píxeles (ty*tile para árboles, char_y para personaje).
    """
    arboles = mundo.arboles_visibles(cam_x, cam_y, vx, vy)
    elementos = [("arbol", tx, ty) for (tx, ty) in arboles]
    elementos.append(("personaje", None))
    # ordenar por Y en píxeles: árboles por ty * tile, personaje por char_y
    elementos.sort(key=lambda e: e[2] * mundo.tile if e[0] == "arbol" else char_y)
    return elementos


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
    renderer = Renderer(
        estilo="stardew8",
        skin="skins/caballero_carmesi.png",
        zoom=4,
        bloom=True,
        luces=LUCES_MOTOR,
    )
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
                elif event.key == pygame.K_g:
                    renderer.set_luces(renderer.luces is None)
                elif event.key == pygame.K_b:
                    renderer.set_bloom(not renderer.bloom)
                elif event.key == pygame.K_l:
                    i = (AMBIENTES.index(renderer.ambiente) + 1) % len(AMBIENTES)
                    renderer.set_ambiente(AMBIENTES[i])

        # Input
        input = input_handler.actualizar()

        # Lógica
        logica.procesar_input(input)
        nuevo_estado = logica.actualizar(1.0 / FPS)

        # Colisión: no entrar a tiles MURO (usando punto de los pies + radio chico)
        if mundo.colisiona(nuevo_estado.x, nuevo_estado.y, radio=4):
            # revertir al estado anterior (no mover al personaje)
            nuevo_estado = Estado(
                x=logica.estado.x - logica.vel_x * (1.0 / FPS) * 60,
                y=logica.estado.y - logica.vel_y * (1.0 / FPS) * 60,
                z=nuevo_estado.z,
                animacion=nuevo_estado.animacion,
                direccion=nuevo_estado.direccion,
                frame=nuevo_estado.frame,
            )
            logica.estado.x = nuevo_estado.x
            logica.estado.y = nuevo_estado.y

        # Game loop (interpolación)
        game_loop.actualizar(nuevo_estado)
        estado_interpolado = game_loop.obtener_estado_interpolado()

        # Renderizar
        screen.fill(COLOR_FONDO)
        tiempo_ilum = 0.0

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

            # Depth-sorting: piso (con muros), luego arboles y personaje ordenados por Y
            # El ambiente se aplica como remapeo dentro de la paleta (no como tinte de pantalla).
            screen.blit(renderer.ambientar(mundo.superficie_piso()), (-cam_x, -cam_y))

            # Iluminacion dinamica (task-020): antorcha por pixel sobre normales cacheadas
            if "antorcha" in equipo.items:
                normal = renderer.buffer_normal()
                if normal is not None:
                    t0 = time.perf_counter()
                    luz_x = personaje.get_width() - 8
                    luz_y = personaje.get_height() // 3
                    personaje = renderer.iluminar(
                        personaje, normal, (luz_x, luz_y), (255, 180, 80), 120, 1.5
                    )
                    tiempo_ilum = (time.perf_counter() - t0) * 1000

            elementos = elementos_ordenados(
                mundo, cam_x, cam_y, SCREEN_WIDTH, SCREEN_HEIGHT, char_py
            )
            for elem in elementos:
                if elem[0] == "arbol":
                    tx, ty = elem[1], elem[2]
                    arbol_sup = renderer.ambientar(mundo._render_arbol(tx, ty))
                    screen.blit(
                        arbol_sup, (tx * mundo.tile - cam_x, ty * mundo.tile - cam_y)
                    )
                else:  # personaje
                    # sombra de contacto
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

            # Iluminación en tiempo real: el ambiente ya se aplicó por remapeo de paleta (arriba).
        except Exception as e:
            print(f"Error renderizando: {e}")

        # HUD: FPS y estado
        fps = clock.get_fps()
        skin = renderer.skin_ruta.split("/")[-1].replace(".png", "")
        equipo_txt = ",".join(equipo.items) or "-"
        ilum_txt = f" ilum={tiempo_ilum:.2f}ms" if "antorcha" in equipo.items else ""
        hud = (
            f"{fps:4.0f} FPS  {estado_interpolado.animacion} {estado_interpolado.direccion} "
            f"f={estado_interpolado.frame}  skin={skin} equipo=[{equipo_txt}] "
            f"dano={'SI' if renderer.dano else 'no'} amb={renderer.ambiente} "
            f"luces={'on' if renderer.luces else 'off'} bloom={'on' if renderer.bloom else 'off'}"
            f"{ilum_txt}"
        )
        screen.blit(fuente.render(hud, True, (230, 230, 240)), (8, 8))

        # Actualizar pantalla
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
