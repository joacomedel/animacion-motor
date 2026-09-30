import numpy as np
import pytest
from PIL import Image

from sprites_lib import gates, proceso_anim


def test_smoke_quieto_verde(capsys):
    assert proceso_anim.main(["smoke", "quieto", "--estilo", "stardew"]) == 0
    out = capsys.readouterr().out
    assert "VERDE" in out
    assert (
        "zonas quieto/stardew" in out and "pulido quieto/stardew" in out
    )  # detalle de cada check


def test_anim_desconocida_da_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["smoke", "no_existe", "--estilo", "stardew"]) == 2


def _alerta(tipo="borde_derecha", sev=2, fp=None):
    return {
        "sev": sev,
        "dir": "S",
        "cuadro": 0,
        "zona": "oreja_izquierda",
        "tipo": tipo,
        "valor": 2,
        "umbral": 0,
        "texto": "2 px opacos tocan el borde derecha",
        "fp": fp,
    }


def _hallazgo(sev, fp=None):
    return {
        "familia": "limpieza",
        "sev": sev,
        "dir": "S",
        "cuadro": 0,
        "zona": "cabeza_frente",
        "px": [1, 1],
        "tipo": "mancha",
        "valor": 0,
        "umbral": 0,
        "texto": "prueba",
        "fp": fp,
    }


def _res(alertas, solido):
    return {
        "alertas": alertas,
        "direcciones": {"S": {"cuadros": [{"cuadro": 0}]}},
        "_extra": {("S", 0): {"solido": solido}},
    }


def _solido(borde=False):
    s = np.zeros((4, 4), bool)
    s[1, 1] = True
    if borde:
        s[1, 3] = True
    return s


def test_check_zonas_ignora_borde_de_contorno_exterior(monkeypatch):
    monkeypatch.setattr(
        gates.zonas, "analizar", lambda **kw: _res([_alerta()], _solido())
    )
    r = gates.check_zonas("quieto", "stardew")
    assert r.ok and r.detalle == "0 por revisar"


def test_check_zonas_borde_con_solido_cortado_bloquea(monkeypatch):
    monkeypatch.setattr(
        gates.zonas, "analizar", lambda **kw: _res([_alerta()], _solido(borde=True))
    )
    r = gates.check_zonas("quieto", "stardew")
    assert not r.ok and r.detalle == "1 por revisar" and r.evidencia


def test_check_zonas_media_por_revisar_bloquea(monkeypatch):
    monkeypatch.setattr(
        gates.zonas,
        "analizar",
        lambda **kw: _res(
            [_alerta(tipo="salto"), _alerta(sev=1), _alerta(fp="perfil")], _solido()
        ),
    )
    r = gates.check_zonas("quieto", "stardew")
    assert not r.ok and r.detalle == "1 por revisar"


def test_check_pulido_solo_mal_bloquea(monkeypatch):
    monkeypatch.setattr(
        gates.pulido,
        "analizar",
        lambda **kw: {"hallazgos": [_hallazgo(2), _hallazgo(1)]},
    )
    r = gates.check_pulido("quieto", "stardew")
    assert (
        r.ok
        and r.detalle == "0 MAL · REVISAR: S c0 cabeza_frente/mancha"
        and r.evidencia
    )
    monkeypatch.setattr(
        gates.pulido,
        "analizar",
        lambda **kw: {"hallazgos": [_hallazgo(3), _hallazgo(2)]},
    )
    r = gates.check_pulido("quieto", "stardew")
    assert not r.ok and r.detalle == "1 MAL · REVISAR: S c0 cabeza_frente/mancha"


def test_check_pulido_recorta_los_revisar_del_detalle(monkeypatch):
    monkeypatch.setattr(
        gates.pulido,
        "analizar",
        lambda **kw: {"hallazgos": [_hallazgo(2) for _ in range(8)]},
    )
    r = gates.check_pulido("quieto", "stardew")
    assert (
        r.ok
        and r.detalle
        == "0 MAL · REVISAR: " + ", ".join(["S c0 cabeza_frente/mancha"] * 6) + " +2"
    )


def test_check_pulido_ignora_hallazgos_marcados_como_falsos(monkeypatch):
    monkeypatch.setattr(
        gates.pulido,
        "analizar",
        lambda **kw: {"hallazgos": [_hallazgo(3, fp="rasgo_de_cara")]},
    )
    r = gates.check_pulido("quieto", "stardew")
    assert r.ok and r.detalle == "0 MAL"


def test_detalle_checks_una_linea_por_check():
    v = gates.correr(
        [
            lambda: gates.Resultado("a", True, "detalle a"),
            lambda: gates.Resultado("b", True, "detalle b"),
        ]
    )
    assert proceso_anim.detalle_checks(v) == "- a: detalle a\n- b: detalle b"


def test_aprobar_congela_y_exporta(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["aprobar", "quieto", "--estilo", "stardew"]) == 0
    carpeta = tmp_path / "aprobados" / "animaciones" / "quieto" / "stardew"
    assert (carpeta / "estado.json").exists()
    assert list(carpeta.glob("*.png")), "faltan cuadros de control"
    assert (
        tmp_path / "salida" / "animaciones" / "quieto" / "stardew" / "quieto.png"
    ).exists()


def test_validar_con_control_ok(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["aprobar", "quieto", "--estilo", "stardew"]) == 0
    assert proceso_anim.main(["validar", "quieto", "--estilo", "stardew"]) == 0


def test_validar_sin_control_ok(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["validar", "quieto", "--estilo", "stardew"]) == 0


def test_aprobar_con_control_cambiado_no_congela(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["aprobar", "quieto", "--estilo", "stardew"]) == 0
    carpeta = tmp_path / "aprobados" / "animaciones" / "quieto" / "stardew"
    export = tmp_path / "salida" / "animaciones" / "quieto" / "stardew" / "quieto.png"
    export.unlink()
    original = proceso_anim._todo

    def tocado(anim, estilo, ficha):
        todo = original(anim, estilo, ficha)
        todo["S"][0].img.putpixel(
            (5, 5), (255, 0, 0, 255)
        )  # cambia el render sin tocar el ciclo
        return todo

    monkeypatch.setattr(proceso_anim, "_todo", tocado)
    assert proceso_anim.main(["aprobar", "quieto", "--estilo", "stardew"]) == 1
    assert "fotos de control" in capsys.readouterr().out
    assert not export.exists() and (carpeta / "estado.json").exists()
    assert (
        proceso_anim.main(
            ["aprobar", "quieto", "--estilo", "stardew", "--excepcion", "render nuevo"]
        )
        == 0
    )
    assert export.exists()


def test_nombre_invalido_rechazado(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["aprobar", "../afuera", "--estilo", "stardew"]) == 2
    assert not (tmp_path.parent / "afuera").exists()


@pytest.mark.parametrize("cmd", ["smoke", "validar", "aprobar"])
def test_skin_invalida_da_2_sin_traceback(tmp_path, cmd, capsys):
    chica = tmp_path / "chica.png"
    Image.new("RGBA", (16, 16)).save(chica)
    assert (
        proceso_anim.main([cmd, "quieto", "--estilo", "stardew", "--skin", str(chica)])
        == 2
    )
    err = capsys.readouterr().err
    assert "error: skin inválida" in err and "32×32" in err


def test_skin_que_no_es_imagen_da_2(tmp_path, capsys):
    archivo = tmp_path / "no_es_imagen.png"
    archivo.write_text("esto no es un PNG")
    assert (
        proceso_anim.main(
            ["smoke", "quieto", "--estilo", "stardew", "--skin", str(archivo)]
        )
        == 2
    )
    assert "error: skin inválida" in capsys.readouterr().err
