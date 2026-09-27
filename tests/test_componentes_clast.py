import numpy as np
import pytest

from sprites_lib.armado import render_cuadro, render_todo
from sprites_lib.ficha import cargar


def mask(c, i):
    from sprites_lib.tests_personaje import mascara      # incluye las partes ('ojos@cara#ojo_izquierdo')
    return mascara(c, i)


@pytest.fixture(scope="module")
def clast():
    return cargar("clast")


def test_ficha_de_clast_es_valida(clast):
    assert clast["identidad"]["nombre"] == "Clast"


@pytest.mark.parametrize("estilo", ["stardew", pytest.param("volumen", marks=pytest.mark.lento), "lateral"])
def test_cada_componente_se_ve_en_alguna_direccion(clast, estilo):
    todo = render_todo(clast, estilo, poses=("quieto",))
    specs = next(iter(todo.values()))[0].specs
    for s in specs:
        assert sum(int(mask(c, s["id"]).sum()) for frs in todo.values() for c in frs) > 0, (estilo, s["id"])


def test_no_tiene_brazos_ni_piernas_humanos(clast):
    ids = {s["id"] for s in render_cuadro(clast, "stardew", "quieto", 0, "S").specs}
    assert not any(i.startswith(("brazo_humano", "pierna_humana")) for i in ids)


def test_brazo_amputado_termina_en_el_codo(clast):
    c = render_cuadro(clast, "lateral", "neutra", 0, "E")
    ys = np.nonzero(mask(c, "brazo_robotico_amputado@brazo_derecho"))[0]
    assert ys.max() <= c.anclas_px["codo_derecho"][1] + 2.6 * c.escala + 1.5


def test_la_chispa_parpadea(clast):
    luz = tuple(int(x) for x in c0_luz(clast))
    brilla = [luz in render_cuadro(clast, "lateral", "quieto", p, "E").buf["colores_detalle"] for p in range(4)]
    assert brilla[0] and not all(brilla)


def c0_luz(clast):
    from sprites_lib.estilos import ESTILOS
    from sprites_lib.paleta import paleta_estilo
    return paleta_estilo(clast["paleta"], ESTILOS["lateral"])["luz"][2]
