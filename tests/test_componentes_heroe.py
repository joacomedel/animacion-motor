import pytest

from sprites_lib.armado import render_todo
from sprites_lib.ficha import validar
from tests import apoyo


def pix(c, i):
    from sprites_lib.tests_personaje import (
        mascara,
    )  # incluye las partes ('ojos@cara#ojo_izquierdo')

    return int(mascara(c, i).sum())


@pytest.fixture(scope="module")
def heroe():
    return apoyo.heroe()


def test_ficha_sintetica_es_valida(heroe):
    assert heroe["identidad"]["nombre"] == "Héroe de prueba"
    assert not validar(heroe)


@pytest.mark.parametrize(
    "estilo", ["stardew", pytest.param("volumen", marks=pytest.mark.lento), "lateral"]
)
def test_cada_componente_se_ve_en_alguna_direccion(heroe, estilo):
    todo = render_todo(heroe, estilo, poses=("quieto",))
    specs = next(iter(todo.values()))[0].specs
    for s in specs:
        total = sum(pix(c, s["id"]) for frs in todo.values() for c in frs)
        assert total > 0, (estilo, s["id"])


def test_pulsera_se_ve_de_frente_en_stardew(heroe):
    c = render_todo(heroe, "stardew", poses=("quieto",))[("quieto", "S")][0]
    assert pix(c, "pulsera@muneca_derecha") >= 1
