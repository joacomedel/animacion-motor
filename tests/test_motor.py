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
