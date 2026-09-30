import numpy as np
import pytest
from PIL import Image

import sprites_lib.componentes as comps
from sprites_lib import tests_personaje as tp
from sprites_lib.armado import render_todo
from sprites_lib.ficha import cargar
from sprites_lib.render3d import v
from tests import apoyo


@pytest.fixture(scope="module")
def heroe():
    return apoyo.heroe()


@pytest.fixture(scope="module")
def todo_heroe(heroe):
    return render_todo(heroe, "stardew")


def test_sano_tamano_recorte_paleta(heroe, todo_heroe):
    for r in (
        tp.t_tamano(heroe, "stardew", todo_heroe),
        tp.t_recorte(todo_heroe),
        tp.t_paleta(heroe, "stardew", todo_heroe),
    ):
        assert r.ok, (r.regla, r.evidencia)


def test_detecta_pulsera_que_desaparece_en_una_direccion(heroe, monkeypatch):
    orig = comps.REGISTRO["pulsera"].dibujar
    monkeypatch.setattr(
        comps.REGISTRO["pulsera"],
        "dibujar",
        lambda esc, ctx, spec: None if ctx.mira == "E" else orig(esc, ctx, spec),
    )
    r = tp.t_visibilidad(heroe, render_todo(heroe, "stardew"))
    assert not r.ok and any(
        "pulsera@muneca_derecha" in e and "/E/" in e for e in r.evidencia
    )


def test_detecta_ojos_corridos_2px(heroe, monkeypatch):
    orig = comps.REGISTRO["ojos"].dibujar

    def corridos(esc, ctx, spec):
        if ctx.mira == "S":
            ctx.a = dict(
                ctx.a,
                ojo_izquierdo=ctx.a["ojo_izquierdo"] + v(0, 0, 2.2),
                ojo_derecho=ctx.a["ojo_derecho"] + v(0, 0, 2.2),
                cara=ctx.a["cara"] + v(0, 0, 2.2),
            )
        orig(esc, ctx, spec)

    monkeypatch.setattr(comps.REGISTRO["ojos"], "dibujar", corridos)
    r = tp.t_lineas_guia(heroe, render_todo(heroe, "stardew"))
    assert not r.ok and any("ojos@cara" in e for e in r.evidencia)


def test_detecta_recorte(todo_heroe):
    c = todo_heroe[("quieto", "S")][0]
    a = np.array(c.img)
    a[0, 8] = (255, 0, 0, 255)
    roto = {
        ("quieto", "S"): [type(c)(**{**c.__dict__, "img": Image.fromarray(a, "RGBA")})]
    }
    assert not tp.t_recorte(roto).ok


def test_detecta_tamano_incorrecto(heroe, monkeypatch):
    import sprites_lib.armado as armado

    orig = armado.anatomia
    monkeypatch.setattr(
        armado, "anatomia", lambda e, c="adulto", x="normal": orig(e, "grande", x)
    )
    r = tp.t_tamano(heroe, "stardew", render_todo(heroe, "stardew", poses=("neutra",)))
    assert not r.ok


def test_detecta_color_fuera_de_paleta(heroe, todo_heroe):
    c = todo_heroe[("quieto", "S")][0]
    a = np.array(c.img)
    ys, xs = np.nonzero(a[..., 3])
    a[ys[0], xs[0]] = (1, 254, 3, 255)
    roto = {
        ("quieto", "S"): [type(c)(**{**c.__dict__, "img": Image.fromarray(a, "RGBA")})]
    }
    r = tp.t_paleta(heroe, "stardew", roto)
    assert not r.ok and "(1, 254, 3)" in r.detalle


def test_cara_sin_ojos_falla(heroe, monkeypatch):
    monkeypatch.setattr(comps.REGISTRO["ojos"], "dibujar", lambda esc, ctx, spec: None)
    assert not tp.t_cara(
        heroe, "stardew", render_todo(heroe, "stardew", poses=("quieto",))
    ).ok


def test_distinto_del_elenco(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    carpeta = apoyo.fichas_dir(tmp_path)
    apoyo.guardar_ficha(carpeta, apoyo.vecino(), "vecino")
    f = apoyo.heroe()
    f["reglas_globales"] = f["reglas_globales"] + [{"distinto_de": ["vecino"]}]
    apoyo.guardar_ficha(carpeta, f, "heroe")
    cargado = cargar("heroe")
    assert tp.t_distinto(cargado).ok
    parecido = dict(cargado, reglas_globales=[{"distinto_de": ["heroe"]}])
    assert not tp.t_distinto(parecido).ok  # contra sí mismo: todo igual


def test_informe(heroe, todo_heroe, tmp_path):
    res = tp.correr_tests(heroe, "stardew", todo_heroe, str(tmp_path))
    md = tp.informe_md(heroe, "stardew", res)
    assert (
        md.startswith("# Informe de consistencia")
        and "| Regla | Estado | Detalle |" in md
    )
    assert {r.regla for r in res} >= {
        "visibilidad de componentes",
        "líneas guía",
        "paleta",
        "tamaño y pivote",
        "recorte",
        "cara visible",
        "simetría",
        "distinto del elenco",
        "estilo vs referencia",
        "partes ausentes",
    }


def test_tatuaje_tapado_por_las_rastas_de_espaldas_no_es_falla(heroe, todo_heroe):
    r = tp.t_visibilidad(heroe, todo_heroe)
    assert not any("tatuaje_runas" in e and "/N/" in e for e in r.evidencia), (
        r.evidencia
    )


@pytest.mark.lento
def test_pies_en_iso_pueden_quedar_a_distinta_altura(heroe):
    r = tp.t_tamano(heroe, "volumen", render_todo(heroe, "volumen", poses=("quieto",)))
    assert r.ok, r.evidencia


def test_estilo_sin_calibrar_advierte_pero_no_bloquea(heroe, monkeypatch, tmp_path):
    from sprites_lib.estilos import ESTILOS

    ref = dict(ESTILOS["lateral"]["referencia"], calibrada=False)
    monkeypatch.setitem(ESTILOS["lateral"], "referencia", ref)
    r = tp.t_estilo(
        heroe,
        "lateral",
        render_todo(heroe, "lateral", poses=("quieto",)),
        str(tmp_path / "cmp"),
    )
    if r.omitido:
        pytest.skip("sin referencia local")
    assert r.ok and "sin calibrar" in r.detalle and r.evidencia


def test_lineas_guia_ignoran_anclas_que_no_se_ven():
    robot = apoyo.robot()
    r = tp.t_lineas_guia(robot, render_todo(robot, "stardew"))
    assert not any("munon_cables" in e for e in r.evidencia), r.evidencia


@pytest.mark.lento
def test_lineas_guia_en_iso_descuentan_la_profundidad():
    robot = apoyo.robot()
    r = tp.t_lineas_guia(robot, render_todo(robot, "volumen", poses=("quieto",)))
    assert r.ok, r.evidencia


def test_mascara_incluye_las_partes_del_componente(todo_heroe):
    c = todo_heroe[("quieto", "S")][0]
    partes = [n for n in c.buf["comp_nombres"] if n.startswith("ojos@cara#")]
    assert len(partes) == 2 and tp.mascara(c, "ojos@cara").sum() >= sum(
        tp.mascara(c, p).sum() for p in partes
    )
