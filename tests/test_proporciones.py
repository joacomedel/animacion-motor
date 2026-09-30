import pytest
from sprites_lib import proporciones
from sprites_lib.estilos import ESTILOS


@pytest.mark.parametrize("estilo", sorted(ESTILOS))
def test_proporciones_dentro_de_tolerancia(estilo):
    r = proporciones.comparar(estilo)
    assert r.ok, r.detalle


def test_alto_igual_entre_direcciones():
    m = proporciones.medir("stardew")
    altos = [v["alto_px"] for v in m["por_direccion"].values()]
    assert max(altos) - min(altos) <= 2
