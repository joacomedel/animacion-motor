import numpy as np
import pytest

from sprites_lib import skins
from sprites_lib.armado import render_cuadro
from sprites_lib.paleta import paleta_estilo
from sprites_lib.estilos import ESTILOS

COLORES = {"piel": "#8c5638", "pelo": "#e2e2f0", "remera": "#5c2c96", "pantalon": "#42366e",
           "calzado": "#62392a", "iris": "#5af0e6"}


@pytest.fixture(scope="module")
def ruta(tmp_path_factory):
    return skins.desde_colores(COLORES, str(tmp_path_factory.mktemp("sk") / "prueba.png"))


def test_la_skin_tiene_una_zona_por_parte_sin_solaparse():
    ocupado = np.zeros((skins.LADO, skins.LADO), int)
    for x, y, w, h in skins.ZONAS.values():
        assert x + w <= skins.LADO and y + h <= skins.LADO
        ocupado[y:y + h, x:x + w] += 1
    assert ocupado.max() == 1


def test_frente_y_espalda_de_la_zona():
    d = np.array([[1.0, 0, 0], [-1.0, 0, 0], [0, 1.0, 0]])
    assert np.allclose(skins.u_de(d) % 1, [.5, 0, .75])      # frente al centro, espalda en el borde, izquierda a la derecha


def test_los_colores_de_la_skin_llegan_al_sprite(ruta):
    f = skins.ficha(ruta)
    q = render_cuadro(f, "stardew", "caminar_lpc", 0, "S")
    pal = paleta_estilo(f["paleta"], ESTILOS["stardew"])
    usados = {tuple(c) for c in np.array(q.img)[..., :3][np.array(q.img)[..., 3] > 0].tolist()}
    remera = set(pal[skins.material((0x5c, 0x2c, 0x96))])
    assert usados & remera, "la remera de la skin no aparece en el torso"
