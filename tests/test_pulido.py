import copy
import json

import numpy as np
import pytest
from PIL import Image

from sprites_lib import pulido as P
from sprites_lib import skins
from tests import apoyo


@pytest.fixture(scope="module")
def skin(tmp_path_factory):
    return apoyo.skin_prueba(tmp_path_factory.mktemp("skins") / "prueba.png")


@pytest.fixture(scope="module")
def analisis(skin):
    return P.analizar("caminar_lpc", "stardew8", None, skins.ficha(skin))


def _reales(pul, **kw):
    return [
        h
        for h in pul["hallazgos"]
        if not h["fp"] and all(h[k] == v for k, v in kw.items())
    ]


def test_estado_actual_sin_hallazgos_graves(analisis):
    assert not _reales(analisis, sev=3)
    assert (
        analisis["resumen"]["notas"]["movimiento"] == "OK"
        and analisis["resumen"]["notas"]["espejo"] == "OK"
    )
    assert all("fp" in h for h in analisis["hallazgos"]) and any(
        h["fp"] for h in analisis["hallazgos"]
    )


def test_regla_de_espejo_con_desfase(analisis):
    m = analisis["medidas"]["espejo"]
    assert (
        max(m["E-W"]["dif_px_por_cuadro"]) <= 1
        and max(m["S-S"]["dif_px_por_cuadro"]) == 0
    )
    # las diagonales difieren solo en la cabeza (cabeza_desvio del estilo) y quedan marcadas, no borradas
    diag = [
        h
        for h in analisis["hallazgos"]
        if h["familia"] == "espejo" and h["dir"] in ("SE", "NE")
    ]
    assert diag and all(h["fp"] == "desvio_de_estilo" for h in diag)


def test_movimiento_medido_contra_lpc(analisis):
    mm = analisis["medidas"]["movimiento"]
    assert mm["ciclo_de_paso"] and 0.15 < mm["lpc"]["mano"] < 0.3
    assert mm["E"]["oposicion_derecha"] < -0.8  # mano opuesta a su pierna
    assert (
        mm["E"]["coronilla_y"][:4] == mm["E"]["coronilla_y"][4:]
    )  # los dos pasos rebotan igual


def test_perfil_e_w_sin_rasgo_afuera(skin):
    """Defecto que vio el usuario: en E/W la cabeza se leía de frente y el ojo lejano quedaba pegado al borde de la
    silueta. Ahora el perfil culla el ojo lejano y apoya los rasgos en la caja: ningún rasgo afuera y limpieza sin MAL.

    (El test viejo forzaba `cara_perfil=.55` para que la herramienta DETECTARA el ojo afuera; con el arreglo ese caso
    ya no existe, así que ahora custodia el resultado: ver también `test_zonas.test_en_perfil_se_ve_un_solo_ojo`.)"""
    pul = P.analizar("caminar_lpc", "stardew8", ["E", "W"], skins.ficha(skin))
    assert not _reales(pul, tipo="rasgo_fuera", sev=3)
    assert pul["resumen"]["notas"]["limpieza"] != "MAL"


def test_luz_verde_suelta_sobre_el_pelo(skin, tmp_path):
    """Defecto que vio el usuario: la luz verde de la sien (texel suelto en la skin) queda sobre el pelo en E y NE."""
    a = np.array(Image.open(skin).convert("RGBA"))
    x0, y0, _, _ = skins.ZONAS["cabeza"]
    a[y0 + 4, x0 + 5] = (0x5C, 0xF0, 0x7A, 255)
    ruta = tmp_path / "prueba_luz.png"
    Image.fromarray(a).save(ruta)
    pul = P.analizar("caminar_lpc", "stardew8", ["NE", "E"], skins.ficha(str(ruta)))
    h = [
        x
        for x in _reales(pul, tipo="mancha", sev=2)
        if x["zona"] == "cabeza_resto"
        and x["dir"] in ("NE", "E")
        and x["texto"].split("px ")[1][:4] in ("#5cf", "#8df")
    ]
    assert {x["dir"] for x in h} == {"NE", "E"}


def test_pixel_suelto_y_agujero_sinteticos(analisis, skin):
    res = analisis["_zonas"]
    r2 = {**res, "_extra": dict(res["_extra"])}
    e = dict(r2["_extra"][("S", 0)])
    img = e["img"].copy()
    img[0, 0] = (255, 0, 0, 255)  # mota suelta en una esquina vacía
    ys, xs = np.nonzero(e["solido"])
    y, x = int(np.median(ys)), int(np.median(xs))
    img[y, x, 3] = 0  # agujero en medio del torso
    e["img"] = img
    r2["_extra"][("S", 0)] = e
    h, _ = P.limpieza(r2, skins.ficha(skin), "stardew8", res["alertas"])
    assert any(a["tipo"] == "suelto" and a["px"] == [0, 0] and a["sev"] == 3 for a in h)
    assert any(a["tipo"] == "agujero" and a["px"] == [x, y] for a in h)


def test_movimiento_sintetico_ambladura_y_temblor(analisis):
    res = copy.deepcopy({k: v for k, v in analisis["_zonas"].items() if k != "_extra"})
    res["_extra"] = analisis["_zonas"]["_extra"]
    cs = res["direcciones"]["E"]["cuadros"]
    # la mano derecha copia la trayectoria de su pie → van juntos (camina como robot)
    for c in cs:
        c["zonas"]["mano_derecha"]["centro"][0] = c["zonas"]["pie_derecho"]["centro"][0]
    # la cabeza tiembla un cuadro: +2 px en y en c3
    cs[3]["zonas"]["cabeza_resto"]["centro"][1] += 2
    h, _ = P.movimiento(res, [], 4)
    assert any(
        a["tipo"] == "oposicion" and a["sev"] == 3 and a["dir"] == "E" for a in h
    )
    assert any(
        a["tipo"] == "quiebre" and a["zona"] == "cabeza_resto" and a["cuadro"] == 3
        for a in h
    )


def test_cli_json_e_informe(tmp_path):
    ruta = tmp_path / "p.json"
    P.main(["--dirs", "E,W", "--salida", str(ruta)])
    js = json.loads(ruta.read_text())
    assert {"hallazgos", "medidas", "resumen", "umbrales"} <= set(js)
    h = js["hallazgos"][0]
    assert {
        "familia",
        "sev",
        "dir",
        "cuadro",
        "zona",
        "px",
        "tipo",
        "valor",
        "umbral",
        "texto",
        "fp",
    } <= set(h)
    md = (tmp_path / "p.md").read_text()
    assert (
        md.startswith("# pulido")
        and "MUÑECO DE ZONAS" in md
        and "## Resumen de pulido" in md
    )
