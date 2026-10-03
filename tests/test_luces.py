"""Tests para el modelo de luces key/fill/rim + AO de contacto (task-021)."""

import numpy as np

from sprites_lib.render3d import CamaraCenital, Escena

PAL = {"piel": ((100, 60, 60), (200, 150, 130), (240, 200, 180))}

LUCES = dict(
    activas=True,
    fill=dict(dir=(0.5, -0.3, 0.4), color=(180, 160, 200), intensidad=0.35),
    rim=dict(dir=(0.3, -0.6, 0.5), color=(255, 250, 230), intensidad=0.5),
    ao_contacto=dict(activo=True, factor=0.6),
)


def _escena():
    cam = CamaraCenital(mira="S", cw=16, ch=32, gx=8, gy=29)
    esc = Escena(cam, PAL)
    esc.esfera((0, 0, 10), 5, "piel")
    return esc


def test_luces_apagadas_png_igual():
    esc = _escena()
    im1 = esc.render(estilo={"sombreado": "luz"})
    im2 = esc.render(estilo={"sombreado": "luz", "luces": dict(activas=False)})
    assert np.array_equal(np.array(im1), np.array(im2))


def test_luces_activas_cambia_sombreado():
    esc = _escena()
    im1 = esc.render(estilo={"sombreado": "luz"})
    im2 = esc.render(estilo={"sombreado": "luz", "luces": LUCES})
    assert not np.array_equal(np.array(im1), np.array(im2))


def test_rim_aumenta_tono_luz():
    esc = _escena()
    im1 = esc.render(estilo={"sombreado": "luz"})
    im2 = esc.render(estilo={"sombreado": "luz", "luces": LUCES})
    a1, a2 = np.array(im1), np.array(im2)
    luz = (240, 200, 180)
    n1 = ((a1[..., :3] == luz).all(-1) & (a1[..., 3] == 255)).sum()
    n2 = ((a2[..., :3] == luz).all(-1) & (a2[..., 3] == 255)).sum()
    assert n2 > n1


def test_ao_oscurece_contacto():
    cam = CamaraCenital(mira="S", cw=16, ch=32, gx=8, gy=29)
    esc = Escena(cam, PAL)
    esc.pieza = 0
    esc.esfera((-2, 0, 10), 3, "piel")
    esc.pieza = 1
    esc.esfera((2, 0, 10), 3, "piel")
    im1 = esc.render(
        estilo={
            "sombreado": "luz",
            "luces": dict(activas=True, ao_contacto=dict(activo=False)),
        }
    )
    im2 = esc.render(
        estilo={
            "sombreado": "luz",
            "luces": dict(activas=True, ao_contacto=dict(activo=True, factor=0.6)),
        }
    )
    assert not np.array_equal(np.array(im1), np.array(im2))
