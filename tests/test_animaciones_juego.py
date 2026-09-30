"""Requisitos para que una animación sirva como sprite de juego (motor externo, sin margen fijo de antemano):
- ningún cuadro exportado toca el borde superior de la celda (si lo toca, un motor sin ese margen corta cabeza/pelo).
- el pivote (punto de los pies) existe para los estilos activos."""
import numpy as np
import pytest

from sprites_lib.armado import FICHA_MINIMA, pivote, render_cuadro
from sprites_lib.estilos import ACTIVOS, ESTILOS
from sprites_lib.poses import POSES


@pytest.mark.parametrize("estilo", ACTIVOS)
def test_ningun_cuadro_toca_el_borde_superior(estilo):
    for anim in POSES:
        n = POSES[anim]["n"]
        for mira in ESTILOS[estilo]["direcciones"]:
            for p in range(n):
                c = render_cuadro(FICHA_MINIMA, estilo, anim, p, mira)
                fila0 = np.array(c.img.convert("RGBA"))[0, :, 3]
                assert not fila0.any(), f"{estilo}/{anim}/{mira} cuadro {p} toca el borde superior de la celda"


@pytest.mark.parametrize("estilo", ACTIVOS)
def test_pivote_no_es_null(estilo):
    x, y = pivote(estilo)
    assert x is not None and y is not None
