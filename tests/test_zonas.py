import copy
import json

import numpy as np

from sprites_lib import zonas as Z
from sprites_lib.armado import render_cuadro


def _res(dirs=("S",), cuadros=(0, 1), **kw):
    return Z.analizar("caminar_lpc", "stardew8", list(dirs), list(cuadros), **kw)


def test_cada_zona_de_la_plantilla_aparece():
    r = _res(("S", "N"), (0,))
    s0, n0 = (r["direcciones"][d]["cuadros"][0]["zonas"] for d in ("S", "N"))
    # el cuello ya no aparece: con el rebote en píxeles enteros (bob_px) la cabeza lo tapa siempre; antes asomaban 3 px en
    # los cuadros pares y no en los impares (parpadeo)
    faltan = [
        z for z in Z.ZONAS if z not in ("otro", "cuello") and not s0[z] and not n0[z]
    ]
    assert not faltan
    assert set(z for z in Z.ZONAS if not s0[z]) == {
        "torso_espalda",
        "cuello",
        "otro",
    }  # de frente no se ve la espalda
    # cada ojo por separado, y de frente el derecho queda a la izquierda de la pantalla
    assert s0["ojo_derecho"]["centro"][0] < s0["ojo_izquierdo"]["centro"][0]


def test_en_perfil_se_ve_un_solo_ojo():
    """En E/W la cabeza se lee de perfil: se ve el ojo del lado cercano y el lejano queda tapado.

    Antes se dibujaban los dos (a 2 px), porque el culling de `ojos` solo cubría las diagonales."""
    f = Z.ficha_plantilla()
    for mira, cerca, lejos in (
        ("E", "ojo_derecho", "ojo_izquierdo"),
        ("W", "ojo_izquierdo", "ojo_derecho"),
    ):
        z = _res((mira,), (0,), ficha=f)["direcciones"][mira]["cuadros"][0]["zonas"]
        assert z[cerca], f"en {mira} debería verse {cerca}"
        assert not z[lejos], f"en {mira} no debería verse {lejos}"


def test_cada_pixel_opaco_en_exactamente_una_zona():
    f = Z.ficha_plantilla()
    for mira in ("S", "E", "NW"):
        c = render_cuadro(f, "stardew8", "caminar_lpc", 3, mira)
        zm, anillo = Z.clasificar(c, f, "stardew8")
        alfa = np.array(c.img.convert("RGBA"))[..., 3] > 0
        assert ((zm >= 0) == alfa).all()
        assert not (zm == Z.ZONAS.index("otro")).any()
        assert not np.isin(
            zm[anillo], [Z.ZONAS.index(z) for z in Z.RASGOS]
        ).any()  # los rasgos no se quedan contorno


def test_otra_skin_por_componentes(tmp_path):
    from sprites_lib import skins
    from tests import apoyo

    r = _res(("S",), (0,), ficha=skins.ficha(apoyo.skin_prueba(tmp_path / "otra.png")))
    zz = r["direcciones"]["S"]["cuadros"][0]["zonas"]
    assert r["modo"] == "componentes" and zz["otro"] is None and zz["ojo_izquierdo"]


def test_json_con_la_estructura_pedida(tmp_path):
    ruta = tmp_path / "z.json"
    Z.main(["--dirs", "S,E", "--cuadros", "0,1", "--salida", str(ruta)])
    js = json.loads(ruta.read_text())
    assert set(js["direcciones"]) == {"S", "E"} and js["zonas"] == list(Z.ZONAS)
    c = js["direcciones"]["S"]["cuadros"][0]
    assert c["pivote"] == [10, 30] and c["celda"] == [20, 32]
    cab = c["zonas"]["cabeza_frente"]
    assert (
        set(cab) == {"px", "bbox", "centro"}
        and len(cab["bbox"]) == 4
        and len(cab["centro"]) == 2
    )
    assert c["zonas"]["torso_espalda"] is None
    assert (tmp_path / "z.md").read_text().startswith("# zonas")


def test_alerta_sintetica_de_salto():
    r = _res()
    assert not [
        a for a in r["alertas"] if a["tipo"] == "salto" and a["zona"] == "cabeza_frente"
    ]
    r2 = copy.deepcopy({k: v for k, v in r.items() if k != "_extra"})
    r2["direcciones"]["S"]["cuadros"][1]["zonas"]["cabeza_frente"]["centro"][1] += 3
    al = [
        a
        for a in Z.alertas(r2, r["_extra"])
        if a["tipo"] == "salto" and a["zona"] == "cabeza_frente"
    ]
    assert al and al[0]["sev"] == 2 and al[0]["cuadro"] == 1
    assert "cabeza_frente" in Z.informe({**r2, "alertas": al, "_extra": r["_extra"]})


def test_colores_de_zona_distintos_y_rasgos_con_nombre():
    assert len(set(Z.COLORES.values())) == len(Z.ZONAS) == len(Z.COLORES)
    c = render_cuadro(Z.ficha_plantilla(), "stardew8", "quieto", 0, "S")
    assert {
        "rostro@cara#ceja_izquierda",
        "rostro@cara#ceja_derecha",
        "rostro@cara#boca",
    } <= set(c.buf["comp_nombres"])


def test_las_alertas_falsas_conocidas_se_marcan_no_se_borran():
    from sprites_lib.zonas import analizar

    res = analizar("caminar_lpc", "stardew8", dirs=["E", "SE"])
    assert all("fp" in a for a in res["alertas"])
    assert any(
        a["fp"] == "perfil" for a in res["alertas"]
    )  # ojo cercano en el borde en E
    assert not any(
        a["sev"] == 3 and not a["fp"] for a in res["alertas"]
    )  # y no queda nada grave por revisar
