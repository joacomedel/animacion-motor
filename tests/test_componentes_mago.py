import pytest

from sprites_lib.armado import render_todo
from sprites_lib.ficha import cargar


def pix(c, i):
    n = c.buf["comp_nombres"]
    return int((c.buf["comp"] == n.index(i)).sum()) if i in n else 0


@pytest.fixture(scope="module")
def mago():
    return cargar("mago")


def test_ficha_del_mago_es_valida(mago):
    assert mago["_nombre"] == "mago"


@pytest.mark.parametrize("estilo", ["stardew", "volumen", "lateral"])
def test_cada_componente_se_ve_en_alguna_direccion(mago, estilo):
    todo = render_todo(mago, estilo, poses=("quieto",))
    specs = next(iter(todo.values()))[0].specs
    for s in specs:
        total = sum(pix(c, s["id"]) for frs in todo.values() for c in frs)
        assert total > 0, (estilo, s["id"])


def test_pulsera_se_ve_de_frente_en_stardew(mago):
    c = render_todo(mago, "stardew", poses=("quieto",))[("quieto", "S")][0]
    assert pix(c, "pulsera@muneca_derecha") >= 1
