"""Tests para bloom/halo post-proceso de materiales emisivos."""

import numpy as np
import pytest

from sprites_lib.escala import celda
from sprites_lib.estilos import crear_camara
from sprites_lib.render3d import Escena, v

# Paleta con un material emisivo (runa) y uno no emisivo (piel)
PAL = {
    "piel": ((180, 140, 120), (240, 200, 180), (255, 230, 210)),
    "runa": ((255, 0, 0), (255, 0, 0), (255, 100, 100)),  # emisivo: sombra == base
}


def opacos(img):
    return int((np.array(img)[..., 3] > 0).sum())


def test_bloom_sin_emissivos_no_cambia():
    """Sin materiales emisivos, el bloom no debe cambiar la imagen."""
    esc = Escena(crear_camara("stardew", "S", celda("stardew")), PAL)
    esc.esfera(v(0, 0, 10), 3, "piel")
    img_sin_bloom = esc.render()
    img_con_bloom = esc.render(bloom=True)
    assert np.array_equal(np.array(img_sin_bloom), np.array(img_con_bloom))


def test_bloom_con_emissivos_expande_halo():
    """Con material emisivo, el bloom debe expandir el halo 1-2 px alrededor."""
    esc = Escena(crear_camara("stardew", "S", celda("stardew")), PAL)
    esc.esfera(v(0, 0, 10), 3, "runa")
    img_sin_bloom = esc.render()
    img_con_bloom = esc.render(bloom=True)
    # El bloom debe agregar píxeles de halo (más píxeles opacos)
    assert opacos(img_con_bloom) > opacos(img_sin_bloom)


def test_bloom_no_sangra_contorno_exterior():
    """El bloom no debe crear píxeles fuera del sprite original."""
    esc = Escena(crear_camara("stardew", "S", celda("stardew")), PAL)
    esc.esfera(v(0, 0, 10), 3, "runa")
    img_sin_bloom = esc.render()
    img_con_bloom = esc.render(bloom=True)
    arr_sin = np.array(img_sin_bloom)
    arr_con = np.array(img_con_bloom)
    # Los píxeles opacos del bloom deben estar dentro del bounding box del original
    ys_sin, xs_sin = np.where(arr_sin[..., 3] > 0)
    ys_con, xs_con = np.where(arr_con[..., 3] > 0)
    assert ys_con.min() >= ys_sin.min()
    assert ys_con.max() <= ys_sin.max()
    assert xs_con.min() >= xs_sin.min()
    assert xs_con.max() <= xs_sin.max()


def test_bloom_determinista():
    """El bloom debe ser determinismo: misma entrada, misma salida."""
    esc = Escena(crear_camara("stardew", "S", celda("stardew")), PAL)
    esc.esfera(v(0, 0, 10), 3, "runa")
    img1 = esc.render(bloom=True)
    img2 = esc.render(bloom=True)
    assert np.array_equal(np.array(img1), np.array(img2))
