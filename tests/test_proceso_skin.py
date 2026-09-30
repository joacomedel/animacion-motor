import json

from PIL import Image

from sprites_lib import proceso_skin


def test_smoke_skin_existente(capsys):
    assert proceso_skin.main(["smoke", "mago"]) == 0
    assert "VERDE" in capsys.readouterr().out


def test_skin_inexistente_da_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_skin.main(["smoke", "no_existe"]) == 2


def test_skin_de_tamano_incorrecto_da_1(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(proceso_skin, "RAIZ", str(tmp_path))
    (tmp_path / "skins").mkdir()
    Image.new("RGBA", (16, 16)).save(tmp_path / "skins" / "chica.png")
    assert proceso_skin.main(["smoke", "chica"]) == 1
    out = capsys.readouterr().out
    assert "ROJO" in out and "32×32" in out


def test_aprobar_congela(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_skin.main(["aprobar", "mago"]) == 0
    carpeta = tmp_path / "aprobados" / "skins" / "mago"
    assert (carpeta / "estado.json").exists() and (carpeta / "smoke.gif").exists()
    e = json.loads((carpeta / "estado.json").read_text())
    assert e["fuentes"]["skin"].startswith("sha256:")


def test_aprobar_rojo_no_congela(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(proceso_skin, "RAIZ", str(tmp_path))
    (tmp_path / "skins").mkdir()
    Image.new("RGBA", (16, 16)).save(tmp_path / "skins" / "chica.png")
    assert proceso_skin.main(["aprobar", "chica"]) == 1
    assert not (tmp_path / "aprobados" / "skins" / "chica").exists()
    assert "ROJO" in capsys.readouterr().out
    # una excepción no alcanza para congelar una skin que no carga (no hay render posible)
    assert proceso_skin.main(["aprobar", "chica", "--excepcion", "prueba"]) == 1
    assert not (tmp_path / "aprobados" / "skins" / "chica").exists()


def test_lote_sin_aprobadas_avisa_y_da_1(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert proceso_skin.main(["lote", "mago"]) == 1
    assert "no hay animaciones aprobadas" in capsys.readouterr().out.lower()


def test_lote_exporta(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from sprites_lib import estado
    from sprites_lib.poses import POSES
    a = tmp_path / "aprobados" / "animaciones" / "quieto" / "stardew"
    estado.escribir(str(a), "anim/quieto/stardew", {"ciclo": estado.hash_obj(POSES["quieto"])}, "metricas.json")
    assert proceso_skin.main(["lote", "mago", "--raiz", str(tmp_path / "output")]) == 0
    assert (tmp_path / "output" / "mago" / "quieto" / "quieto.png").exists()


def test_lote_skin_rota_avisa_y_da_1(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(proceso_skin, "RAIZ", str(tmp_path))
    (tmp_path / "skins").mkdir()
    Image.new("RGBA", (16, 16)).save(tmp_path / "skins" / "chica.png")
    from sprites_lib import estado
    from sprites_lib.poses import POSES
    estado.escribir(str(tmp_path / "aprobados" / "animaciones" / "quieto" / "stardew"),
                    "anim/quieto/stardew", {"ciclo": estado.hash_obj(POSES["quieto"])}, "metricas.json")
    assert proceso_skin.main(["lote", "chica"]) == 1
    assert "skin inválida" in capsys.readouterr().err


def test_lote_roja_no_corta_y_da_1(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    from sprites_lib import estado
    from sprites_lib.poses import POSES
    fuentes = {"agachar": "sha256:viejo", "neutra": estado.hash_obj(POSES["neutra"])}
    for anim, ciclo in fuentes.items():
        a = tmp_path / "aprobados" / "animaciones" / anim / "stardew"
        estado.escribir(str(a), f"anim/{anim}/stardew", {"ciclo": ciclo}, "metricas.json")
    out = tmp_path / "output"
    assert proceso_skin.main(["lote", "mago", "--raiz", str(out)]) == 1
    salida = capsys.readouterr().out
    assert "agachar: ROJO" in salida and "neutra: VERDE" in salida
    assert not (out / "mago" / "agachar" / "agachar.png").exists()      # ROJA no se exporta
    assert (out / "mago" / "neutra" / "neutra.png").exists()            # y el lote siguió con la otra
    informe = (tmp_path / "salida" / "zonas" / "lote_mago.md").read_text()
    assert "## agachar" in informe and "## neutra" in informe and "deriva" in informe
