"""Paleta fija compartida por estilo (task-017): con `render.paleta_fija`, todo color opaco que sale del render
pertenece a esa lista, y dos personajes distintos del mismo estilo comparten exactamente la misma paleta."""

import numpy as np
import pytest
from PIL import Image

from sprites_lib import skins
from sprites_lib.estilos import ESTILOS
from sprites_lib.paleta import ajustar_paleta, hex_rgb

FICHA = {
    "identidad": {
        "nombre": "Prueba",
        "concepto": "humano de prueba",
        "silueta_clave": "ninguna",
    },
    "cuerpo": {"base": "humano", "clase_altura": "adulto", "cabello": "corto"},
    "paleta": {"piel": {"base": "#c89070"}, "pelo": {"base": "#302018"}},
    "componentes": [],
}

# otro personaje: mismo estilo, colores base distintos → tiene que caer en la misma lista
FICHA2 = {
    **FICHA,
    "identidad": {
        "nombre": "Prueba 2",
        "concepto": "humano de prueba",
        "silueta_clave": "ninguna",
    },
    "paleta": {"piel": {"base": "#e0b090"}, "pelo": {"base": "#101820"}},
}

ESTILOS_CON_FIJA = ["stardew", "stardew8", "volumen", "fry8"]
TAMANO_ESPERADO = {"stardew": 50, "stardew8": 50, "volumen": 64, "fry8": 14}


def colores(img):
    a = np.array(img)
    return {tuple(int(x) for x in px[:3]) for px in a[a[..., 3] > 0]}


def permitidos(estilo):
    return {hex_rgb(c) for c in ESTILOS[estilo]["render"]["paleta_fija"]}


def test_ajustar_paleta_mapea_cada_pixel_al_mas_cercano():
    fijos = ["#000000", "#ffffff", "#ff0000"]
    im = Image.new("RGBA", (3, 1))
    im.putdata([(20, 20, 20, 255), (250, 5, 5, 255), (0, 0, 0, 0)])
    ajustar_paleta({"S": [im]}, fijos)
    assert colores(im) <= {hex_rgb(c) for c in fijos}
    assert im.getpixel((2, 0))[3] == 0  # el transparente no se toca


@pytest.mark.parametrize("estilo", ESTILOS_CON_FIJA)
def test_cada_estilo_declara_su_paleta_fija_valida(estilo):
    lista = ESTILOS[estilo]["render"]["paleta_fija"]
    assert len(lista) == TAMANO_ESPERADO[estilo]
    for c in lista:
        hex_rgb(c)  # revienta si no es #rrggbb


@pytest.mark.parametrize("estilo", ["stardew", "stardew8"])
def test_pipeline_con_paleta_fija_solo_usa_esa_paleta(estilo):
    ok = permitidos(estilo)
    for f in (FICHA, FICHA2):
        _, por_dir = skins._por_dir_ficha(f, "quieto", estilo)
        usados = set().union(*(colores(im) for imgs in por_dir.values() for im in imgs))
        assert usados <= ok, usados - ok


def test_dos_personajes_comparten_exactamente_la_misma_paleta():
    ok = permitidos("stardew")
    paletas = []
    for f in (FICHA, FICHA2):
        _, por_dir = skins._por_dir_ficha(f, "quieto", "stardew")
        paletas.append(
            set().union(*(colores(im) for imgs in por_dir.values() for im in imgs))
        )
    assert paletas[0] <= ok and paletas[1] <= ok
