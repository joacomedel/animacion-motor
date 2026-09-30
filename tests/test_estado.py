import os
from sprites_lib import estado


def test_hash_obj_estable_y_sensible():
    assert estado.hash_obj({"a": [1, 2], "b": "x"}) == estado.hash_obj({"b": "x", "a": [1, 2]})
    assert estado.hash_obj({"a": 1}) != estado.hash_obj({"a": 2})


def test_deriva_detecta_cambio():
    est = {"fuentes": {"ciclo": "sha256:aaa", "perfil": "sha256:bbb"}}
    assert estado.deriva(est, {"ciclo": "sha256:aaa", "perfil": "sha256:bbb"}) == []
    assert estado.deriva(est, {"ciclo": "sha256:nuevo", "perfil": "sha256:bbb"}) == ["ciclo"]
    assert estado.deriva({"fuentes": {"a": "sha256:1", "b": "sha256:2"}}, {"a": "sha256:1"}) == ["b"]


def test_escribir_y_leer_ida_vuelta(tmp_path):
    carpeta = str(tmp_path / "art")
    estado.escribir(carpeta, "anim/saltar/stardew", {"ciclo": "sha256:abc"}, "metricas.json")
    e = estado.leer(carpeta)
    assert e["artefacto"] == "anim/saltar/stardew"
    assert e["fuentes"]["ciclo"] == "sha256:abc"
    assert e["aprobado_por"] == "usuario" and e["fecha"]
    assert estado.leer(str(tmp_path / "no_existe")) is None


def test_listar_encuentra_artefactos(tmp_path):
    a = tmp_path / "aprobados" / "animaciones" / "quieto" / "stardew"
    estado.escribir(str(a), "anim/quieto/stardew", {"ciclo": "sha256:x"}, "metricas.json")
    encontrados = estado.listar(str(tmp_path / "aprobados" / "animaciones"))
    assert [(x["nombre"], x["estilo"]) for x in encontrados] == [("quieto", "stardew")]
    assert os.path.exists(encontrados[0]["carpeta"])
