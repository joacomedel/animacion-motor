import numpy as np

from sprites_lib import gates, proceso_anim


def test_smoke_quieto_verde(capsys):
    assert proceso_anim.main(["smoke", "quieto", "--estilo", "stardew", "--skin", "skins/mago.png"]) == 0
    assert "VERDE" in capsys.readouterr().out


def test_anim_desconocida_da_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["smoke", "no_existe", "--estilo", "stardew"]) == 2


def _alerta(tipo="borde_derecha", sev=2, fp=None):
    return {"sev": sev, "dir": "S", "cuadro": 0, "zona": "oreja_izquierda", "tipo": tipo,
            "valor": 2, "umbral": 0, "texto": "2 px opacos tocan el borde derecha", "fp": fp}


def _hallazgo(sev, fp=None):
    return {"familia": "limpieza", "sev": sev, "dir": "S", "cuadro": 0, "zona": "cabeza_frente",
            "px": [1, 1], "tipo": "mancha", "valor": 0, "umbral": 0, "texto": "prueba", "fp": fp}


def _res(alertas, solido):
    return {"alertas": alertas, "direcciones": {"S": {"cuadros": [{"cuadro": 0}]}},
            "_extra": {("S", 0): {"solido": solido}}}


def _solido(borde=False):
    s = np.zeros((4, 4), bool)
    s[1, 1] = True
    if borde:
        s[1, 3] = True
    return s


def test_check_zonas_ignora_borde_de_contorno_exterior(monkeypatch):
    monkeypatch.setattr(gates.zonas, "analizar", lambda **kw: _res([_alerta()], _solido()))
    r = gates.check_zonas("quieto", "stardew")
    assert r.ok and r.detalle == "0 por revisar"


def test_check_zonas_borde_con_solido_cortado_bloquea(monkeypatch):
    monkeypatch.setattr(gates.zonas, "analizar", lambda **kw: _res([_alerta()], _solido(borde=True)))
    r = gates.check_zonas("quieto", "stardew")
    assert not r.ok and r.detalle == "1 por revisar" and r.evidencia


def test_check_zonas_media_por_revisar_bloquea(monkeypatch):
    monkeypatch.setattr(gates.zonas, "analizar",
                        lambda **kw: _res([_alerta(tipo="salto"), _alerta(sev=1), _alerta(fp="perfil")], _solido()))
    r = gates.check_zonas("quieto", "stardew")
    assert not r.ok and r.detalle == "1 por revisar"


def test_check_pulido_solo_mal_bloquea(monkeypatch):
    monkeypatch.setattr(gates.pulido, "analizar", lambda **kw: {"hallazgos": [_hallazgo(2), _hallazgo(1)]})
    r = gates.check_pulido("quieto", "stardew")
    assert r.ok and r.detalle == "0 MAL, 1 REVISAR" and r.evidencia
    monkeypatch.setattr(gates.pulido, "analizar", lambda **kw: {"hallazgos": [_hallazgo(3), _hallazgo(2)]})
    r = gates.check_pulido("quieto", "stardew")
    assert not r.ok and r.detalle == "1 MAL, 1 REVISAR"


def test_check_pulido_ignora_hallazgos_marcados_como_falsos(monkeypatch):
    monkeypatch.setattr(gates.pulido, "analizar", lambda **kw: {"hallazgos": [_hallazgo(3, fp="rasgo_de_cara")]})
    r = gates.check_pulido("quieto", "stardew")
    assert r.ok and r.detalle == "0 MAL, 0 REVISAR"
