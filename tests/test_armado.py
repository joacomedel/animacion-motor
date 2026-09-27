import numpy as np

from sprites_lib.armado import expandir, render_cuadro
from sprites_lib.componentes import REGISTRO
from sprites_lib.escala import celda
from sprites_lib.estilos import ESTILOS

FICHA = {
    "identidad": {"nombre": "Prueba", "concepto": "humano de prueba", "silueta_clave": "ninguna"},
    "cuerpo": {"base": "humano", "clase_altura": "adulto", "cabello": "corto"},
    "paleta": {"piel": {"base": "#c89070"}, "pelo": {"base": "#302018"}},
    "componentes": [],
}


def pix(c, comp_id):
    from sprites_lib.tests_personaje import mascara      # incluye las partes ('ojos@cara#ojo_izquierdo')
    return int(mascara(c, comp_id).sum())


def test_registro_tiene_el_cuerpo_base():
    for t in ("cabeza_humana", "ojos", "torso_humano", "brazo_humano", "pierna_humana"):
        assert t in REGISTRO


def test_expandir_agrega_el_cuerpo_base():
    specs = expandir(FICHA)
    ids = {s["id"] for s in specs}
    assert len(specs) == 7
    assert {"brazo_humano@brazo_derecho", "pierna_humana@pierna_izquierda", "ojos@cara"} <= ids
    assert len({s["pieza_base"] for s in specs}) == 7


def test_componente_propio_reemplaza_al_base():
    f = dict(FICHA, componentes=[{"tipo": "pierna_humana", "ancla": ["pierna_izquierda", "pierna_derecha"],
                                  "material": "pelo", "por_que": "pantalón oscuro"}])
    specs = expandir(f)
    piernas = [s for s in specs if s["tipo"] == "pierna_humana"]
    assert len(specs) == 7 and len(piernas) == 2 and all(s["material"] == "pelo" for s in piernas)


def test_sustitucion_quita_el_componente_base():
    f = dict(FICHA, cuerpo=dict(FICHA["cuerpo"], sustituciones={"brazo_derecho": "brazo_humano"}),
             componentes=[{"tipo": "brazo_humano", "ancla": "brazo_derecho", "material": "pelo", "por_que": "x"}])
    brazos = [s for s in expandir(f) if s["ancla"] == "brazo_derecho"]
    assert len(brazos) == 1 and brazos[0]["material"] == "pelo"


def test_render_en_los_tres_estilos_y_todas_las_direcciones():
    for est in ("stardew", "volumen", "lateral"):
        for mira in ESTILOS[est]["direcciones"]:
            c = render_cuadro(FICHA, est, "quieto", 0, mira)
            assert c.img.size == (celda(est)["cw"], celda(est)["ch"])
            assert pix(c, "torso_humano@torso") > 0 and pix(c, "cabeza_humana@cabeza") > 0, (est, mira)


def test_de_frente_se_ven_brazos_piernas_y_ojos():
    c = render_cuadro(FICHA, "stardew", "quieto", 0, "S")
    for i in ("brazo_humano@brazo_derecho", "brazo_humano@brazo_izquierdo",
              "pierna_humana@pierna_derecha", "pierna_humana@pierna_izquierda", "ojos@cara"):
        assert pix(c, i) > 0, i


def test_el_puno_es_pieza_propia():
    c = render_cuadro(FICHA, "volumen", "quieto", 0, "S")
    n = c.buf["comp_nombres"]
    m = c.buf["comp"] == n.index("brazo_humano@brazo_derecho")
    assert len(set(c.buf["pieza"][m].tolist())) >= 2      # brazo y puño con contorno entre ellos


def test_antebrazo_ausente_no_se_dibuja():
    f = dict(FICHA, cuerpo=dict(FICHA["cuerpo"], ausentes=["antebrazo_derecho"]))
    c = render_cuadro(f, "stardew", "quieto", 0, "S")
    n = c.buf["comp_nombres"]
    ys = np.nonzero(c.buf["comp"] == n.index("brazo_humano@brazo_derecho"))[0]
    assert ys.max() <= c.anclas_px["codo_derecho"][1] + 2.5


def test_clase_grande_usa_su_celda():
    f = dict(FICHA, cuerpo=dict(FICHA["cuerpo"], clase_altura="grande"))
    c = render_cuadro(f, "stardew", "quieto", 0, "S")
    assert c.img.size == (32, 48)
    alto = celda("stardew", "grande")["gy"] - c.anclas_px["coronilla"][1]
    assert abs(alto - c.anat.alto_px) <= 1


def test_cabeza_rapada_marca_la_zona_del_pelo():
    """Sin material 'pelo', el rapado usa un tono de piel más oscuro (con 'pelo' usa ese color: otro test)."""
    f = dict(FICHA, cuerpo=dict(FICHA["cuerpo"], cabello="rapado"), paleta={"piel": FICHA["paleta"]["piel"]})
    c = render_cuadro(f, "stardew", "quieto", 0, "N")          # de espaldas: casi todo es cuero cabelludo
    a = np.array(c.img)
    n = c.buf["comp_nombres"]
    m = c.buf["comp"] == n.index("cabeza_humana@cabeza")
    from sprites_lib.paleta import paleta_estilo
    rapado = set(paleta_estilo(f["paleta"], ESTILOS["stardew"])["piel_b"])
    colores = {tuple(int(x) for x in p) for p in a[m][:, :3]}
    assert colores & rapado                                    # la zona del pelo corto tiene su propio tono


def test_rapado_usa_el_color_de_pelo_si_existe():
    from sprites_lib.paleta import paleta_estilo
    f = dict(FICHA, cuerpo=dict(FICHA["cuerpo"], cabello="rapado"))
    c = render_cuadro(f, "stardew", "quieto", 0, "N")
    m = c.buf["comp"] == c.buf["comp_nombres"].index("cabeza_humana@cabeza")
    colores = {tuple(int(x) for x in p) for p in np.array(c.img)[m][:, :3]}
    assert colores & set(paleta_estilo(f["paleta"], ESTILOS["stardew"])["pelo"])


def test_la_cabeza_tiene_orejas():
    c = render_cuadro(FICHA, "stardew", "quieto", 0, "S")
    m = c.buf["comp"] == c.buf["comp_nombres"].index("cabeza_humana@cabeza")
    assert len(set(c.buf["pieza"][m].tolist())) >= 2          # cabeza y orejas con contorno propio
