import numpy as np
import pytest
from PIL import Image

import sprites_lib.componentes as comps
from sprites_lib import tests_personaje as tp
from sprites_lib.armado import render_todo
from sprites_lib.ficha import cargar
from sprites_lib.render3d import v


@pytest.fixture(scope="module")
def mago():
    return cargar("mago")


@pytest.fixture(scope="module")
def todo_mago(mago):
    return render_todo(mago, "stardew")


def test_sano_tamano_recorte_paleta(mago, todo_mago):
    for r in (tp.t_tamano(mago, "stardew", todo_mago), tp.t_recorte(todo_mago),
              tp.t_paleta(mago, "stardew", todo_mago)):
        assert r.ok, (r.regla, r.evidencia)


def test_detecta_pulsera_que_desaparece_en_una_direccion(mago, monkeypatch):
    orig = comps.REGISTRO["pulsera"].dibujar
    monkeypatch.setattr(comps.REGISTRO["pulsera"], "dibujar",
                        lambda esc, ctx, spec: None if ctx.mira == "E" else orig(esc, ctx, spec))
    r = tp.t_visibilidad(mago, render_todo(mago, "stardew"))
    assert not r.ok and any("pulsera@muneca_derecha" in e and "/E/" in e for e in r.evidencia)


def test_detecta_ojos_corridos_2px(mago, monkeypatch):
    orig = comps.REGISTRO["ojos"].dibujar

    def corridos(esc, ctx, spec):
        if ctx.mira == "S":
            ctx.a = dict(ctx.a, ojo_izquierdo=ctx.a["ojo_izquierdo"] + v(0, 0, 2.2),
                         ojo_derecho=ctx.a["ojo_derecho"] + v(0, 0, 2.2), cara=ctx.a["cara"] + v(0, 0, 2.2))
        orig(esc, ctx, spec)

    monkeypatch.setattr(comps.REGISTRO["ojos"], "dibujar", corridos)
    r = tp.t_lineas_guia(mago, render_todo(mago, "stardew"))
    assert not r.ok and any("ojos@cara" in e for e in r.evidencia)


def test_detecta_recorte(todo_mago):
    c = todo_mago[("quieto", "S")][0]
    a = np.array(c.img); a[0, 8] = (255, 0, 0, 255)
    roto = {("quieto", "S"): [type(c)(**{**c.__dict__, "img": Image.fromarray(a, "RGBA")})]}
    assert not tp.t_recorte(roto).ok


def test_detecta_tamano_incorrecto(mago, monkeypatch):
    import sprites_lib.armado as armado
    orig = armado.anatomia
    monkeypatch.setattr(armado, "anatomia", lambda e, c="adulto", x="normal": orig(e, "grande", x))
    r = tp.t_tamano(mago, "stardew", render_todo(mago, "stardew", poses=("neutra",)))
    assert not r.ok


def test_detecta_color_fuera_de_paleta(mago, todo_mago):
    c = todo_mago[("quieto", "S")][0]
    a = np.array(c.img); ys, xs = np.nonzero(a[..., 3]); a[ys[0], xs[0]] = (1, 254, 3, 255)
    roto = {("quieto", "S"): [type(c)(**{**c.__dict__, "img": Image.fromarray(a, "RGBA")})]}
    r = tp.t_paleta(mago, "stardew", roto)
    assert not r.ok and "(1, 254, 3)" in r.detalle


def test_cara_sin_ojos_falla(mago, monkeypatch):
    monkeypatch.setattr(comps.REGISTRO["ojos"], "dibujar", lambda esc, ctx, spec: None)
    assert not tp.t_cara(mago, "stardew", render_todo(mago, "stardew", poses=("quieto",))).ok


def test_distinto_del_elenco(mago):
    assert tp.t_distinto(mago).ok
    parecido = dict(mago, reglas_globales=[{"distinto_de": ["mago"]}])
    assert not tp.t_distinto(parecido).ok             # contra sí mismo: todo igual


def test_informe(mago, todo_mago, tmp_path):
    res = tp.correr_tests(mago, "stardew", todo_mago, str(tmp_path))
    md = tp.informe_md(mago, "stardew", res)
    assert md.startswith("# Informe de consistencia") and "| Regla | Estado | Detalle |" in md
    assert {r.regla for r in res} >= {"visibilidad de componentes", "líneas guía", "paleta", "tamaño y pivote",
                                     "recorte", "cara visible", "simetría", "distinto del elenco",
                                     "estilo vs referencia", "partes ausentes"}
