"""Objetos sostenidos: el componente `objeto` se engancha a una mano, se orienta con el antebrazo y sigue la
mano en todos los ciclos existentes (blandir = reusar `golpear` sobre el brazo). Materiales planos por ahora."""

import numpy as np
import pytest

from sprites_lib.armado import render_cuadro
from sprites_lib.ficha import validar
from sprites_lib.tests_personaje import mascara
from tests import apoyo


def _mask(c, i):
    return mascara(c, i)


def _centro(m):
    ys, xs = np.nonzero(m)
    return float(xs.mean()), float(ys.mean())


def _dist_min_a(m, punto):
    ys, xs = np.nonzero(m)
    return float(np.min(np.hypot(xs - punto[0], ys - punto[1])))


def test_ficha_con_objetos_es_valida():
    assert not validar(apoyo.espadachin())


def test_forma_desconocida_falla_con_opciones():
    f = apoyo.espadachin()
    f["componentes"][-2]["parametros"]["forma"] = "sable_laser"
    errs = validar(f)
    assert any("forma" in e and "opciones" in e for e in errs), errs


def test_espada_y_escudo_se_ven_en_alguna_direccion():
    f = apoyo.espadachin()
    c = render_cuadro(f, "stardew", "quieto", 0, "S")
    assert _mask(c, "objeto@mano_derecha").sum() > 0, "espada de frente"
    assert _mask(c, "objeto@mano_izquierda").sum() > 0, "escudo de frente"
    for mira in (
        "E",
        "W",
    ):  # de perfil la mano lejana queda oculta: alcanza con la espada (mano cercana)
        c = render_cuadro(f, "stardew", "quieto", 0, mira)
        assert _mask(c, "objeto@mano_derecha").sum() > 0, ("espada", mira)


def test_el_objeto_esta_enganchado_a_la_mano():
    """En todos los cuadros de `golpear` la espada tiene un píxel pegado a la mano (se mueve con ella)."""
    f = apoyo.espadachin()
    n = 6
    for p in range(n):
        c = render_cuadro(f, "lateral", "golpear", p, "E")
        m = _mask(c, "objeto@mano_derecha")
        assert m.sum() > 0, p
        assert _dist_min_a(m, c.anclas_px["mano_derecha"]) < 3.0 * c.escala + 1.5, p


def test_la_espada_acompana_el_movimiento_del_brazo():
    """La posición de la espada cambia cuadro a cuadro (no es un adorno fijo)."""
    f = apoyo.espadachin()
    centros = [
        _centro(
            _mask(render_cuadro(f, "lateral", "golpear", p, "E"), "objeto@mano_derecha")
        )
        for p in range(6)
    ]
    xs = [c[0] for c in centros]
    assert max(xs) - min(xs) > 2.0, xs


@pytest.mark.parametrize("forma", ["hacha", "antorcha", "baston"])
def test_otras_formas_se_ven(forma):
    f = apoyo.espadachin()
    f["componentes"][-2]["parametros"]["forma"] = forma
    c = render_cuadro(f, "lateral", "quieto", 0, "E")
    assert _mask(c, "objeto@mano_derecha").sum() > 0, forma


def test_mas_largo_mas_pixeles():
    f = apoyo.espadachin()
    f["componentes"][-2]["parametros"]["forma"] = "espada"
    f["componentes"][-2]["parametros"]["largo"] = 4.0
    chico = render_cuadro(f, "volumen", "quieto", 0, "S")
    f2 = apoyo.espadachin()
    f2["componentes"][-2]["parametros"]["forma"] = "espada"
    f2["componentes"][-2]["parametros"]["largo"] = 12.0
    grande = render_cuadro(f2, "volumen", "quieto", 0, "S")
    assert (
        _mask(grande, "objeto@mano_derecha").sum()
        > _mask(chico, "objeto@mano_derecha").sum()
    )


def test_objeto_visible_es_por_cuadro():
    """El objeto puede no estar en ciertos cuadros (desenvainar: la espada aparece de golpe)."""
    from sprites_lib import ciclos

    c = {
        "n": 2,
        "desfase": 0,
        "bob": [0, 0],
        "pie": [(18, 32)] * 2,
        "pie_ang": [0, 0],
        "mano": dict(cx=19.5, ax=0, y0=27, ay=0),
        "lag_faldon": 1,
        "objeto_visible": [False, True],
    }
    assert ciclos.pose(c, 0)["objeto_visible"] is False
    assert ciclos.pose(c, 1)["objeto_visible"] is True
    c2 = {k: v for k, v in c.items() if k != "objeto_visible"}
    assert ciclos.pose(c2, 0)["objeto_visible"] is True


def test_muneco_objetos_genera_la_grilla(tmp_path):
    """El comando `muneco objetos` arma la comparación misma-animación/distintos-objetos."""
    from PIL import Image

    from sprites_lib import muneco

    ruta = muneco.objetos(
        "quieto",
        "stardew",
        formas=("espada", "escudo"),
        ruta=str(tmp_path / "o.png"),
        zoom=2,
    )
    im = Image.open(ruta)
    assert im.width > 0 and im.height > 0
