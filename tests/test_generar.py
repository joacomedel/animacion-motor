import os

import numpy as np
from PIL import Image

from personajes import generar
from sprites_lib import fotos_control
from sprites_lib.armado import render_todo
from sprites_lib.ficha import cargar
from sprites_lib.tests_personaje import Resultado
from tests import apoyo


def _ficha(tmp_path, nombre="heroe"):
    return apoyo.guardar_ficha(apoyo.fichas_dir(tmp_path), apoyo.heroe(), nombre)


def test_validar_ok(tmp_path, capsys):
    assert generar.main(["validar", _ficha(tmp_path)]) == 0
    assert "válida" in capsys.readouterr().out


def test_ficha_inexistente_codigo_2_sin_traceback(capsys):
    assert generar.main(["validar", "nadie"]) == 2
    err = capsys.readouterr().err
    assert "no existe la ficha" in err and "Traceback" not in err


def test_yaml_roto_codigo_2(tmp_path, capsys):
    ruta = tmp_path / "rota.yaml"
    ruta.write_text("identidad: [", encoding="utf-8")
    assert generar.main(["validar", str(ruta)]) == 2
    assert "YAML mal formado" in capsys.readouterr().err


def test_hoja_genera_archivos(tmp_path, monkeypatch):
    monkeypatch.setattr(generar, "SALIDA", str(tmp_path))
    codigo = generar.main(["hoja", _ficha(tmp_path), "--estilo", "stardew"])
    base = tmp_path / "heroe" / "stardew"
    assert codigo in (0, 1)
    for f in ("hoja_modelo.png", "informe.md", "quieto.png", "quieto.json"):
        assert (base / f).exists(), f


def test_aprobar_se_niega_si_fallan_tests(tmp_path, monkeypatch):
    monkeypatch.setattr(generar, "SALIDA", str(tmp_path))
    monkeypatch.setattr(fotos_control, "DIR", str(tmp_path / "aprobados"))
    monkeypatch.setattr(
        generar, "correr_tests", lambda *a: [Resultado("x", False, "roto")]
    )
    assert generar.main(["aprobar", _ficha(tmp_path), "--estilo", "stardew"]) == 1
    assert not (tmp_path / "aprobados").exists()


def test_fotos_de_control_detectan_cambios(tmp_path, monkeypatch):
    monkeypatch.setattr(fotos_control, "DIR", str(tmp_path / "aprobados"))
    f = cargar(_ficha(tmp_path))
    nombre = f["_nombre"]
    todo = render_todo(f, "stardew", poses=("neutra",))
    assert fotos_control.comparar(
        nombre, "stardew", todo, str(tmp_path / "dif")
    ).omitido
    fotos_control.guardar(nombre, "stardew", todo)
    assert fotos_control.comparar(nombre, "stardew", todo, str(tmp_path / "dif")).ok
    c = todo[("neutra", "S")][0]
    a = np.array(c.img)
    a[5, 5] = (255, 0, 0, 255)
    c.img = Image.fromarray(a, "RGBA")
    r = fotos_control.comparar(nombre, "stardew", todo, str(tmp_path / "dif"))
    assert not r.ok and "neutra_S_0.png" in r.evidencia[0]
    assert os.path.exists(tmp_path / "dif" / "neutra_S_0.png")


def test_boceto_rapido_una_sola_imagen(tmp_path, monkeypatch):
    monkeypatch.setattr(generar, "SALIDA", str(tmp_path))
    assert generar.main(["boceto", _ficha(tmp_path)]) == 0
    img = Image.open(tmp_path / "heroe" / "boceto.png")
    assert img.width > img.height  # frente y perfil lado a lado
    assert not (
        tmp_path / "heroe" / "stardew"
    ).exists()  # no corre la generación completa
