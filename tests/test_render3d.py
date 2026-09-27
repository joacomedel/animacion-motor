import numpy as np
import pytest

from sprites_lib.escala import celda
from sprites_lib.estilos import crear_camara
from sprites_lib.render3d import Camara, CamaraCenital, CamaraLateral, Escena, v

PAL = {"a": ((50, 50, 50), (100, 100, 100), (200, 200, 200)), "b": ((50, 0, 0), (150, 0, 0), (250, 0, 0))}


def opacos(img):
    return int((np.array(img)[..., 3] > 0).sum())


def test_lateral_mira_derecha():
    cam = CamaraLateral("E", cw=40, ch=40, gx=20, gy=38)
    x0, y0, _ = cam.proyectar(v(0, 0, 0))
    x1, y1, _ = cam.proyectar(v(5, 0, 10))
    assert x1 - x0 == pytest.approx(5) and y0 - y1 == pytest.approx(10)


def test_lateral_oeste_espeja():
    cam = CamaraLateral("W", cw=40, ch=40, gx=20, gy=38)
    x, _, _ = cam.proyectar(v(5, 0, 0))
    assert x == pytest.approx(15)


def test_lateral_lado_derecho_mas_cerca_mirando_al_este():
    cam = CamaraLateral("E", cw=40, ch=40, gx=20, gy=38)
    _, _, d_der = cam.proyectar(v(0, -2, 0))
    _, _, d_izq = cam.proyectar(v(0, 2, 0))
    assert d_der > d_izq


def test_lateral_rechaza_otras_direcciones():
    with pytest.raises(ValueError, match="E o W"):
        CamaraLateral("S")


def test_crear_camara_por_vista():
    assert isinstance(crear_camara("volumen", "SE", celda("volumen")), Camara)
    assert type(crear_camara("stardew", "S", celda("stardew"))) is CamaraCenital
    assert isinstance(crear_camara("lateral", "E", celda("lateral")), CamaraLateral)
    with pytest.raises(ValueError, match="no es una dirección"):
        crear_camara("stardew", "SE", celda("stardew"))


def test_buffer_de_componente_y_detalles():
    esc = Escena(crear_camara("stardew", "S", celda("stardew")), PAL)
    esc.componente = "cuerpo"
    esc.esfera(v(0, 0, 10), 3, "a")
    esc.componente = "gema"
    esc.detalle(v(3.2, 0, 10), (1, 2, 3))
    img, buf = esc.render(buffers=True)
    nombres = buf["comp_nombres"]
    assert (buf["comp"] == nombres.index("cuerpo")).sum() > 10
    assert (buf["comp"] == nombres.index("gema")).sum() == 1
    assert (1, 2, 3) in buf["colores_detalle"]
    assert buf["solido"].sum() == (buf["mat"] >= 0).sum()


def test_render_sin_buffers_devuelve_imagen():
    esc = Escena(crear_camara("stardew", "S", celda("stardew")), PAL)
    esc.esfera(v(0, 0, 10), 3, "a")
    assert esc.render().size == (16, 32)


def test_conservar_recorta_la_primitiva():
    completa = Escena(crear_camara("volumen", "S", celda("volumen")), PAL)
    completa.esfera(v(0, 0, 20), 8, "a")
    media = Escena(crear_camara("volumen", "S", celda("volumen")), PAL)
    media.esfera(v(0, 0, 20), 8, "a", conservar=lambda d: d[..., 2] > 0)
    assert 0 < opacos(media.render()) < opacos(completa.render())


def test_faldon_recorte():
    todo = lambda d: np.ones(d.shape[:-1], bool)
    a = Escena(crear_camara("volumen", "S", celda("volumen")), PAL)
    a.faldon(v(0, 0, 20), v(0, 0, 6), 5, 7, "a", conservar=todo)
    b = Escena(crear_camara("volumen", "S", celda("volumen")), PAL)
    b.faldon(v(0, 0, 20), v(0, 0, 6), 5, 7, "a", conservar=todo, recorte=lambda d, t: t < .5)
    assert 0 < opacos(b.render()) < opacos(a.render())


def test_escena_vacia():
    img, buf = Escena(crear_camara("stardew", "S", celda("stardew")), PAL).render(buffers=True)
    assert opacos(img) == 0 and not buf["solido"].any()
