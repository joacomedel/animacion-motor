"""Paleta fija en el motor en vivo y luces/bloom (task-018 + task-021/023).

Regla: todo lo que ve el motor (sprite, luz dinámica, ambiente) usa colores de la paleta fija del
estilo. La iluminación no inventa colores: mueve cada píxel a otro color de la misma paleta.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import numpy as np  # noqa: E402
import pygame  # noqa: E402

from motor.estado import Estado  # noqa: E402
from motor.renderer import Renderer  # noqa: E402
from sprites_lib.estilos import ESTILOS  # noqa: E402
from sprites_lib.paleta import hex_rgb, snap_rgb  # noqa: E402

SKIN = "skins/caballero_carmesi.png"


def setup_module(module):
    pygame.init()
    pygame.display.set_mode((64, 64))


def _colores(surface):
    a = pygame.surfarray.array3d(surface)
    al = pygame.surfarray.array_alpha(surface)
    return {tuple(int(x) for x in c) for c in a[al > 0]}


def _paleta(estilo="stardew8"):
    return {hex_rgb(c) for c in ESTILOS[estilo]["render"]["paleta_fija"]}


def test_snap_rgb_mapea_al_mas_cercano():
    arr = np.array([[[20, 20, 20], [250, 5, 5], [0, 0, 0]]], np.uint8)
    out = snap_rgb(arr, ["#000000", "#ffffff", "#ff0000"])
    assert tuple(out[0, 0]) == (0, 0, 0)
    assert tuple(out[0, 1]) == (255, 0, 0)
    assert tuple(out[0, 2]) == (0, 0, 0)


def test_motor_sprite_cae_en_la_paleta_fija():
    r = Renderer("stardew8", SKIN, zoom=2)
    sup = r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    ok = _paleta()
    assert r.paleta_fija is not None
    assert _colores(sup) <= ok


def test_motor_luz_dinamica_no_sale_de_paleta():
    r = Renderer("stardew8", SKIN, zoom=2)
    sup = r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    normal = r.buffer_normal()
    ilu = r.iluminar(
        sup, normal, (sup.get_width() - 8, sup.get_height() // 3), (255, 180, 80), 120, 1.5
    )
    assert _colores(ilu) <= _paleta()


def test_motor_ambiente_remapea_dentro_de_paleta():
    r = Renderer("stardew8", SKIN, zoom=2)
    sup = r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    r.set_ambiente("noche")
    noche = r.ambientar(sup)
    assert _colores(noche) <= _paleta()
    # y efectivamente cambia respecto de día
    assert not np.array_equal(
        pygame.surfarray.array3d(sup), pygame.surfarray.array3d(noche)
    )


def test_motor_luces_cambian_el_render():
    r = Renderer("stardew8", SKIN, zoom=2)
    apagado = pygame.surfarray.array3d(
        r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    )
    r.set_luces(True)
    encendido = pygame.surfarray.array3d(
        r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    )
    assert not np.array_equal(apagado, encendido)
    assert _colores(r.renderizar(Estado(animacion="idle", direccion="S", frame=0))) <= _paleta()


def test_motor_bloom_cambia_el_render():
    r = Renderer("stardew8", SKIN, zoom=2)
    r.set_equipo(["antorcha"])
    sin = pygame.surfarray.array3d(
        r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    )
    r.set_bloom(True)
    con = pygame.surfarray.array3d(
        r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    )
    assert not np.array_equal(sin, con)


def test_toggles_limpian_la_cache():
    r = Renderer("stardew8", SKIN, zoom=2)
    r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    assert len(r._cache) == 1
    r.set_luces(True)
    assert len(r._cache) == 0 and r.luces is not None
    r.set_bloom(True)
    assert len(r._cache) == 0 and r.bloom is True


def test_render_cuadro_acepta_luces_override():
    from sprites_lib import armado, skins

    f = skins.ficha(SKIN)
    sin = armado.render_cuadro(f, "stardew", "quieto", 0, "S")
    luces = dict(
        activas=True,
        fill=dict(dir=(0.5, -0.3, 0.4), color=(180, 160, 200), intensidad=0.35),
        rim=dict(dir=(0.3, -0.6, 0.5), color=(255, 250, 230), intensidad=0.5),
        ao_contacto=dict(activo=True, factor=0.6),
    )
    con = armado.render_cuadro(f, "stardew", "quieto", 0, "S", luces=luces)
    assert not np.array_equal(np.array(sin.img), np.array(con.img))
