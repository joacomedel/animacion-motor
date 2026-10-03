"""Tests de materiales con propiedades: Material, highlight especular, translúcido, textura."""

import numpy as np
import pytest

from sprites_lib.estilos import ESTILOS, crear_camara
from sprites_lib.paleta import MATERIALES_BASE, Material, paleta_estilo
from sprites_lib.render3d import Camara, Escena, v


def test_material_es_tuple_con_props():
    """Material es un tuple (sombra, base, luz) con atributos extra."""
    m = Material(
        ((10, 10, 10), (50, 50, 50), (100, 100, 100)), especular=0.8, transmision=0.3
    )
    assert isinstance(m, tuple)
    assert len(m) == 3
    assert m[0] == (10, 10, 10)
    assert m[1] == (50, 50, 50)
    assert m[2] == (100, 100, 100)
    assert m.especular == 0.8
    assert m.transmision == 0.3
    assert m.textura is None
    assert m.rugosidad == 0.5


def test_material_default_neutro():
    """Sin props, un material es neutro: especular=0, transmision=0, textura=None, rugosidad=0.5."""
    m = Material(((1, 2, 3), (4, 5, 6), (7, 8, 9)))
    assert m.especular == 0.0
    assert m.transmision == 0.0
    assert m.textura is None
    assert m.rugosidad == 0.5


def test_paleta_estilo_devuelve_material():
    """paleta_estilo devuelve Material objects con props de MATERIALES_BASE."""
    p = paleta_estilo(
        {"metal": {"base": "#9aa0a8"}, "tela": {"base": "#4a6fa5"}}, ESTILOS["stardew"]
    )
    assert isinstance(p["metal"], Material)
    assert p["metal"].especular == MATERIALES_BASE["metal"]["especular"]
    assert p["metal"].rugosidad == MATERIALES_BASE["metal"]["rugosidad"]
    assert p["tela"].especular == MATERIALES_BASE["tela"]["especular"]


def test_paleta_estilo_variantes_heredan_props():
    """Las variantes _b y mano heredan las props del material base."""
    p = paleta_estilo(
        {"metal": {"base": "#9aa0a8"}, "piel": {"base": "#8c5638"}}, ESTILOS["stardew"]
    )
    assert isinstance(p["metal_b"], Material)
    assert p["metal_b"].especular == p["metal"].especular
    assert isinstance(p["mano"], Material)
    assert p["mano"].especular == p["piel"].especular


def test_materias_base_tienen_base_y_props():
    """MATERIALES_BASE tiene los materiales estándar con base y props válidas."""
    for nombre in ("cuero", "metal", "oro", "tela", "madera", "fuego"):
        assert nombre in MATERIALES_BASE, f"{nombre} falta en MATERIALES_BASE"
        m = MATERIALES_BASE[nombre]
        assert "base" in m, f"{nombre} sin base"
        assert m["especular"] >= 0.0 and m["especular"] <= 1.0, (
            f"{nombre} especular fuera de rango"
        )
        assert m["rugosidad"] >= 0.0 and m["rugosidad"] <= 1.0, (
            f"{nombre} rugosidad fuera de rango"
        )


def test_materias_base_metal_especular():
    """El metal tiene especular alto; la tela, bajo."""
    assert MATERIALES_BASE["metal"]["especular"] > 0.5
    assert MATERIALES_BASE["tela"]["especular"] < 0.2


def test_materias_base_transmision():
    """Agua y cristal tienen transmision > 0; cuero y metal, 0."""
    assert MATERIALES_BASE["agua"]["transmision"] > 0.0
    assert MATERIALES_BASE["cristal"]["transmision"] > 0.0
    assert MATERIALES_BASE["cuero"]["transmision"] == 0.0
    assert MATERIALES_BASE["metal"]["transmision"] == 0.0


def test_render_con_especular():
    """Un material con especular > 0 produce píxeles más brillantes que sin especular."""
    cam = Camara("SE", cw=20, ch=20, gx=10, gy=10)
    # sin especular
    esc1 = Escena(cam, {"a": ((50, 50, 50), (100, 100, 100), (200, 200, 200))})
    esc1.esfera(v(0, 0, 10), 3, "a")
    img1 = np.array(esc1.render())
    # con especular
    esc2 = Escena(
        cam,
        {
            "a": Material(
                ((50, 50, 50), (100, 100, 100), (200, 200, 200)), especular=0.9
            )
        },
    )
    esc2.esfera(v(0, 0, 10), 3, "a")
    img2 = np.array(esc2.render())
    # el especular debe aumentar el brillo de algunos píxeles
    assert img2[..., :3].sum() > img1[..., :3].sum()


def test_render_con_transmision():
    """Un material con transmision > 0 produce píxeles con alpha < 255."""
    cam = Camara("SE", cw=20, ch=20, gx=10, gy=10)
    esc = Escena(
        cam,
        {
            "a": Material(
                ((50, 50, 50), (100, 100, 100), (200, 200, 200)), transmision=0.5
            )
        },
    )
    esc.esfera(v(0, 0, 10), 3, "a")
    img = np.array(esc.render())
    solido = img[..., 3] > 0
    assert solido.any()
    assert (img[solido, 3] < 255).any(), "transmision debe reducir alpha"


def test_render_con_textura():
    """Un material con textura modula el color pero mantiene 3 tonos."""
    cam = Camara("SE", cw=20, ch=20, gx=10, gy=10)
    esc = Escena(
        cam,
        {
            "a": Material(
                ((50, 50, 50), (100, 100, 100), (200, 200, 200)), textura="ruido"
            )
        },
    )
    esc.esfera(v(0, 0, 10), 3, "a")
    img = np.array(esc.render())
    solido = img[..., 3] > 0
    colores = set(tuple(c) for c in img[solido][:, :3])
    # la textura modula pero no rompe los 3 tonos base
    assert len(colores) >= 3


def test_render_sin_props_no_cambia():
    """Un material sin props (tuple plano) renderiza igual que antes."""
    cam = Camara("SE", cw=20, ch=20, gx=10, gy=10)
    esc = Escena(cam, {"a": ((50, 50, 50), (100, 100, 100), (200, 200, 200))})
    esc.esfera(v(0, 0, 10), 3, "a")
    img = np.array(esc.render())
    solido = img[..., 3] > 0
    assert solido.any()
    assert (img[solido, 3] == 255).all()


def test_equipo_importa_de_paleta():
    """motor.equipo.MATERIALES es el mismo objeto que sprites_lib.paleta.MATERIALES_BASE."""
    from motor.equipo import MATERIALES

    assert MATERIALES is MATERIALES_BASE


def test_ficha_con_equipo_con_props():
    """ficha_con_equipo funciona con materiales con props."""
    from motor.equipo import ficha_con_equipo
    from sprites_lib import skins

    f = ficha_con_equipo(skins.ficha("skins/caballero_carmesi.png"), ["armadura_malla"])
    assert "metal" in f["paleta"]
    assert f["componentes"][-1]["material"] == "metal"
