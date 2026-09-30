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
