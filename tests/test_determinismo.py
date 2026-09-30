from sprites_lib import gates
from sprites_lib.estilos import ACTIVOS


def test_determinismo_por_estilo_activo():
    for estilo in ACTIVOS:
        r = gates.check_determinismo(estilo)
        assert r.ok, r.detalle
