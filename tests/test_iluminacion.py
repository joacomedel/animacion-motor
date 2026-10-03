"""Tests de iluminación dinámica (task-020).

Verifican que `Renderer.iluminar` aplica una luz puntual por píxel
sobre normales cacheadas, sin re-renderizar 3D.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import numpy as np  # noqa: E402
import pygame  # noqa: E402
import pytest  # noqa: E402

from motor.estado import Estado  # noqa: E402
from motor.renderer import Renderer  # noqa: E402

SKIN = "skins/caballero_carmesi.png"


def setup_module(module):
    pygame.init()


def _renderer():
    return Renderer("stardew8", SKIN, zoom=1)


def _surface_gris(ancho=64, alto=64, valor=128):
    """Surface opaca gris del tamaño dado."""
    sup = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    sup.fill((valor, valor, valor, 255))
    return sup


def _normal_constante(ancho, alto, nx, ny, nz):
    """Buffer de normal (h, w, 3) uint8 con normal constante."""
    h, w = alto, ancho
    buf = np.zeros((h, w, 3), dtype=np.uint8)
    buf[:, :, 0] = int((nx * 0.5 + 0.5) * 255)
    buf[:, :, 1] = int((ny * 0.5 + 0.5) * 255)
    buf[:, :, 2] = int((nz * 0.5 + 0.5) * 255)
    return buf


def test_buffer_normal_existe_y_tiene_forma():
    r = _renderer()
    r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    normal = r.buffer_normal()
    assert normal.ndim == 3
    assert normal.shape[2] == 3
    assert normal.dtype == np.uint8
    assert normal.shape[0] > 0 and normal.shape[1] > 0


def test_luz_cerca_ilumina_mas():
    """Un píxel cerca del centro de la luz recibe más brillo que uno lejano."""
    r = _renderer()
    sup = _surface_gris(64, 64, 100)
    normal = _normal_constante(64, 64, 0.0, 0.0, 1.0)  # normal hacia la cámara
    luz_pos = (32, 32)
    luz_color = (255, 200, 100)
    radio = 60
    intensidad = 1.0

    iluminada = r.iluminar(sup, normal, luz_pos, luz_color, radio, intensidad)
    arr = pygame.surfarray.array3d(iluminada)  # (w, h, 3)

    centro = arr[32, 32].astype(float)  # píxel en el centro de la luz
    lejos = arr[32, 52].astype(float)  # píxel a 20px del centro

    assert centro.sum() > lejos.sum()


def test_luz_fuera_del_radio_no_ilumina():
    """Píxeles fuera del radio de la luz quedan sin modificar."""
    r = _renderer()
    sup = _surface_gris(64, 64, 100)
    normal = _normal_constante(64, 64, 0.0, 0.0, 1.0)
    luz_pos = (0, 0)
    luz_color = (255, 200, 100)
    radio = 30
    intensidad = 1.0

    iluminada = r.iluminar(sup, normal, luz_pos, luz_color, radio, intensidad)
    arr_orig = pygame.surfarray.array3d(sup)
    arr_ilu = pygame.surfarray.array3d(iluminada)

    # Píxel en (60, 60) está fuera del radio (dist ~85 > 30)
    assert np.array_equal(arr_orig[60, 60], arr_ilu[60, 60])


def test_normal_hacia_luz_ilumina_mas():
    """Una normal apuntando hacia la luz ilumina más que una en contra."""
    r = _renderer()
    sup = _surface_gris(64, 64, 100)
    luz_pos = (32, 32)
    luz_color = (255, 255, 255)
    radio = 80
    intensidad = 1.0

    # Normal hacia la cámara (0,0,1): N·L > 0
    normal_frente = _normal_constante(64, 64, 0.0, 0.0, 1.0)
    ilu_frente = r.iluminar(sup, normal_frente, luz_pos, luz_color, radio, intensidad)

    # Normal en contra (0,0,-1): N·L < 0 → clip a 0 → no ilumina
    normal_atras = _normal_constante(64, 64, 0.0, 0.0, -1.0)
    ilu_atras = r.iluminar(sup, normal_atras, luz_pos, luz_color, radio, intensidad)

    arr_frente = pygame.surfarray.array3d(ilu_frente)
    arr_atras = pygame.surfarray.array3d(ilu_atras)

    assert arr_frente[32, 32].sum() > arr_atras[32, 32].sum()


def test_pixel_transparente_no_se_modifica():
    """Los píxeles con alpha 0 no son tocados por la iluminación."""
    r = _renderer()
    sup = pygame.Surface((64, 64), pygame.SRCALPHA)
    sup.fill((0, 0, 0, 0))  # todo transparente
    # Solo un píxel opaco en el centro
    sup.set_at((32, 32), (100, 100, 100, 255))

    normal = _normal_constante(64, 64, 0.0, 0.0, 1.0)
    iluminada = r.iluminar(sup, normal, (32, 32), (255, 200, 100), 60, 1.0)

    alpha = pygame.surfarray.array_alpha(iluminada)
    # Los píxeles transparentes siguen con alpha 0
    assert alpha[0, 0] == 0
    assert alpha[63, 63] == 0
    # El píxel opaco fue iluminado (cambió de color)
    arr = pygame.surfarray.array3d(iluminada)
    assert not np.array_equal(arr[32, 32], np.array([100, 100, 100]))


def test_iluminar_devuelve_surface_mismo_tamaño():
    r = _renderer()
    sup = _surface_gris(48, 32, 128)
    normal = _normal_constante(48, 32, 0.0, 0.0, 1.0)
    iluminada = r.iluminar(sup, normal, (16, 16), (255, 255, 255), 40, 1.0)
    assert isinstance(iluminada, pygame.Surface)
    assert iluminada.get_width() == 48
    assert iluminada.get_height() == 32


def test_iluminar_no_modifica_surface_original():
    """La superficie original no debe ser mutada."""
    r = _renderer()
    sup = _surface_gris(64, 64, 100)
    normal = _normal_constante(64, 64, 0.0, 0.0, 1.0)
    antes = pygame.surfarray.array3d(sup).copy()
    r.iluminar(sup, normal, (32, 32), (255, 200, 100), 60, 1.0)
    despues = pygame.surfarray.array3d(sup)
    assert np.array_equal(antes, despues)
