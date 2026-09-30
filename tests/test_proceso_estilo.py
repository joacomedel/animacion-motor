import json
import os

import pytest

from sprites_lib import proceso_estilo


def test_validar_verde_y_rojo(capsys):
    assert proceso_estilo.main(["validar", "stardew"]) == 0
    assert "VERDE" in capsys.readouterr().out


def test_aprobar_congela_y_deriva(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_estilo.main(["aprobar", "stardew"]) == 0
    carpeta = tmp_path / "aprobados" / "estilos" / "stardew"
    assert (carpeta / "estado.json").exists() and (carpeta / "control.png").exists()
    e = json.loads((carpeta / "estado.json").read_text())
    assert e["fuentes"]["perfil"].startswith("sha256:")
    assert os.path.exists(tmp_path / "docs" / "estilos" / "stardew.md")


def test_aprobar_rojo_no_escribe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from sprites_lib import gates
    monkeypatch.setattr(proceso_estilo, "correr_gate",
                        lambda estilo: gates.correr([lambda: gates.Resultado("test", False, "forzado")]))
    assert proceso_estilo.main(["aprobar", "stardew"]) == 1
    assert not (tmp_path / "aprobados").exists()


def test_estilo_desconocido_da_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_estilo.main(["validar", "no_existe"]) == 2


def test_sin_referencia_calibrada_omite():
    r = proceso_estilo.check_referencia("lpc")
    assert r.ok and r.omitido


def test_referencia_sin_especimen_omite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = proceso_estilo.check_referencia("stardew")
    assert r.ok and r.omitido


def test_referencia_compara_especimen():
    if not os.path.exists("referencias/stardew/abigail.png"):
        pytest.skip("falta referencias/stardew/abigail.png (gitignored): no hay referencia que comparar")
    r = proceso_estilo.check_referencia("stardew")
    assert r.ok and not r.omitido
    assert "espécimen" in r.detalle


def test_especimen_faltante_omite(tmp_path, monkeypatch):
    from sprites_lib import estilos
    ref_real = os.path.abspath("referencias/stardew/abigail.png")     # antes del chdir: la referencia existe
    monkeypatch.chdir(tmp_path)
    ref = dict(estilos.ESTILOS["stardew"]["referencia"], ruta=ref_real)
    monkeypatch.setitem(estilos.ESTILOS["stardew"], "referencia", ref)
    r = proceso_estilo.check_referencia("stardew")
    assert r.ok and r.omitido and "especimen" in r.detalle
