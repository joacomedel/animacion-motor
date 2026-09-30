from sprites_lib import gates
from sprites_lib.tests_personaje import Resultado


def test_veredicto_verde_solo_si_todos_ok():
    v = gates.correr([lambda: Resultado("a", True), lambda: Resultado("b", True)])
    assert v.verde and "VERDE" in gates.informe(v)
    v = gates.correr([lambda: Resultado("a", True), lambda: Resultado("b", False, "falló")])
    assert not v.verde and "ROJO" in gates.informe(v)


def test_excepcion_es_rojo_con_detalle():
    def boom():
        raise ValueError("explosión")
    v = gates.correr([boom])
    assert not v.verde and "explosión" in v.checks[0].detalle


def test_guardar_json(tmp_path):
    v = gates.correr([lambda: Resultado("a", True)])
    ruta = gates.guardar(v, str(tmp_path / "g.json"))
    assert "VERDE" in open(ruta).read()
