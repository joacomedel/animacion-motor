from sprites_lib import gates


def test_deriva_rojo_si_cambio_la_fuente():
    estado_dict = {"fuentes": {"ciclo": "sha256:viejo"}}
    r = gates.check_deriva(estado_dict, {"ciclo": "sha256:nuevo"})
    assert not r.ok and "ciclo" in r.detalle


def test_deriva_omitida_si_no_hay_estado():
    r = gates.check_deriva(None, {"ciclo": "sha256:x"})
    assert r.ok and r.omitido
