"""Tests del motor 3D→2D (headless, sin ventana)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

from motor.estado import Estado  # noqa: E402
from motor.game_loop import GameLoop  # noqa: E402
from motor.logica import LogicaSimulada  # noqa: E402
from motor.renderer import Renderer  # noqa: E402

SKIN = "skins/caballero_carmesi.png"
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]


def setup_module(module):
    pygame.init()


def test_estado_lerp_interpola_posicion():
    a = Estado(x=0, y=0, z=0)
    b = Estado(x=10, y=20, z=4)
    medio = a.lerp(b, 0.5)
    assert (medio.x, medio.y, medio.z) == (5, 10, 2)


def test_logica_movimiento_y_direccion():
    log = LogicaSimulada()
    log.procesar_input({"right": True})
    estado = log.actualizar(1.0 / 60)
    assert estado.x > 0
    assert estado.animacion == "run"
    assert estado.direccion == "E"


def test_logica_salto_levanta_z():
    log = LogicaSimulada()
    log.procesar_input({"jump": True})
    assert log.vel_z > 0
    estado = log.actualizar(1.0 / 60)
    assert estado.z > 0
    assert estado.animacion == "jump"


def test_logica_agachar_sostiene_animacion():
    log = LogicaSimulada()
    log.procesar_input({"crouch": True})
    log.actualizar(1.0 / 60)
    assert log.estado.animacion == "crouch"


def test_game_loop_actualiza_estado():
    gl = GameLoop()
    gl.iniciar(Estado(x=0))
    for _ in range(5):
        t = gl.actualizar(Estado(x=100))
        assert 0.0 <= t <= 1.0
    assert gl.obtener_estado_interpolado() is not None


def test_renderer_renderiza_todas_las_animaciones_y_direcciones():
    r = Renderer("stardew8", SKIN, zoom=4)
    for anim in ("idle", "run", "jump", "crouch"):
        for d in DIRS:
            sup = r.renderizar(Estado(animacion=anim, direccion=d, frame=0))
            assert isinstance(sup, pygame.Surface)
            assert sup.get_width() > 0 and sup.get_height() > 0


def test_renderer_set_skin_cambia_personaje():
    r = Renderer("stardew8", "skins/caballero_carmesi.png", zoom=4)
    r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    r.set_skin("skins/mago.png")
    assert r.ficha_base["cuerpo"]["skin"] == "skins/mago.png"
    sup = r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    assert isinstance(sup, pygame.Surface) and sup.get_width() > 0


def test_renderer_cachea_mismos_cuadros():
    r = Renderer("stardew8", SKIN, zoom=4)
    e = Estado(animacion="run", direccion="S", frame=2)
    assert r.renderizar(e) is r.renderizar(e)


def test_renderer_mapea_animaciones_al_kit():
    r = Renderer("stardew8", SKIN, zoom=4)
    assert r.n_cuadros("idle") == 4
    assert r.n_cuadros("run") == 8
    assert r.n_cuadros("jump") == 6
    assert r.n_cuadros("crouch") == 4


def test_piso_scrollea_con_el_mundo():
    r = Renderer("stardew8", SKIN, zoom=4)
    _, pos0 = r.piso(800, 600, (0, 0))
    _, pos1 = r.piso(800, 600, (17, 9))
    assert pos0 != pos1


def test_renderer_set_skin_invalida_cache():
    r = Renderer("stardew8", SKIN, zoom=4)
    r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    assert len(r._cache) == 1
    r.set_skin("skins/mago.png")
    assert len(r._cache) == 0
    assert r.skin_ruta == "skins/mago.png"


def test_renderer_set_arma_y_dano():
    r = Renderer("stardew8", SKIN, zoom=4)
    r.set_arma("espada")
    assert r.arma == "espada" and len(r._cache) == 0
    r.set_dano(True)
    assert r.dano and len(r._cache) == 0
    r.set_arma(None)
    assert r.arma is None


def test_renderer_ambiente():
    r = Renderer("stardew8", SKIN, zoom=4)
    assert r.capa_ambiente(800, 600) is None  # día: sin tinte
    r.set_ambiente("noche")
    assert r.capa_ambiente(800, 600) is not None
    with pytest.raises(ValueError):
        r.set_ambiente("espacio")


def test_precalentar_llena_la_cache():
    r = Renderer("stardew8", SKIN, zoom=4)
    r.precalentar()
    esperado = sum(r.n_cuadros(a) for a in ("idle", "run", "jump", "crouch")) * 8
    assert len(r._cache) == esperado


# --- Tests de depth-sorting (task-027) ---


def test_elementos_ordenados_por_y():
    """Los árboles y el personaje se dibujan ordenados por su Y del mundo."""
    from motor.main import elementos_ordenados
    from motor.mundo import Mundo, ARBOL

    m = Mundo(ancho=20, alto=10, tile=16)
    # limpiar y poner árboles conocidos
    for y in range(10):
        for x in range(20):
            m.mapa[y][x] = 0
    m.mapa[2][3] = ARBOL  # y = 2*16 = 32
    m.mapa[7][5] = ARBOL  # y = 7*16 = 112
    m.mapa[4][8] = ARBOL  # y = 4*16 = 64

    # cámara en (0,0), viewport 800x600, personaje en y=80
    elementos = elementos_ordenados(m, 0, 0, 800, 600, char_y=80)
    # debe haber 4 elementos: 3 árboles + 1 personaje
    assert len(elementos) == 4
    # ordenados por Y: árbol y=32, árbol y=64, personaje y=80, árbol y=112
    assert elementos[0] == ("arbol", 3, 2)
    assert elementos[1] == ("arbol", 8, 4)
    assert elementos[2] == ("personaje", None)
    assert elementos[3] == ("arbol", 5, 7)


def test_elementos_ordenados_personaje_por_detras():
    """El personaje con Y mayor que un árbol se dibuja después (encima)."""
    from motor.main import elementos_ordenados
    from motor.mundo import Mundo, ARBOL

    m = Mundo(ancho=20, alto=10, tile=16)
    for y in range(10):
        for x in range(20):
            m.mapa[y][x] = 0
    m.mapa[2][3] = ARBOL  # y = 32

    # personaje abajo del árbol (y mayor)
    elementos = elementos_ordenados(m, 0, 0, 800, 600, char_y=100)
    assert elementos[0] == ("arbol", 3, 2)
    assert elementos[1] == ("personaje", None)


def test_elementos_ordenados_personaje_por_delante():
    """El personaje con Y menor que un árbol se dibuja antes (detrás)."""
    from motor.main import elementos_ordenados
    from motor.mundo import Mundo, ARBOL

    m = Mundo(ancho=20, alto=10, tile=16)
    for y in range(10):
        for x in range(20):
            m.mapa[y][x] = 0
    m.mapa[7][5] = ARBOL  # y = 112

    # personaje arriba del árbol (y menor)
    elementos = elementos_ordenados(m, 0, 0, 800, 600, char_y=50)
    assert elementos[0] == ("personaje", None)
    assert elementos[1] == ("arbol", 5, 7)
