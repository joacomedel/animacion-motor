import numpy as np
import pytest

from sprites_lib import skins
from sprites_lib.armado import render_cuadro
from sprites_lib.paleta import paleta_estilo
from sprites_lib.estilos import ESTILOS

COLORES = {
    "piel": "#8c5638",
    "pelo": "#e2e2f0",
    "remera": "#5c2c96",
    "pantalon": "#42366e",
    "calzado": "#62392a",
    "iris": "#5af0e6",
}


@pytest.fixture(scope="module")
def ruta(tmp_path_factory):
    return skins.desde_colores(
        COLORES, str(tmp_path_factory.mktemp("sk") / "prueba.png")
    )


def test_la_skin_tiene_una_zona_por_parte_sin_solaparse():
    ocupado = np.zeros((skins.LADO, skins.LADO), int)
    for x, y, w, h in skins.ZONAS.values():
        assert x + w <= skins.LADO and y + h <= skins.LADO
        ocupado[y : y + h, x : x + w] += 1
    assert ocupado.max() == 1


def test_frente_y_espalda_de_la_zona():
    d = np.array([[1.0, 0, 0], [-1.0, 0, 0], [0, 1.0, 0]])
    assert np.allclose(
        skins.u_de(d) % 1, [0.5, 0, 0.75]
    )  # frente al centro, espalda en el borde, izquierda a la derecha


def test_los_colores_de_la_skin_llegan_al_sprite(ruta):
    f = skins.ficha(ruta)
    q = render_cuadro(f, "stardew", "caminar_lpc", 0, "S")
    pal = paleta_estilo(f["paleta"], ESTILOS["stardew"])
    usados = {
        tuple(c) for c in np.array(q.img)[..., :3][np.array(q.img)[..., 3] > 0].tolist()
    }
    remera = set(pal[skins.material((0x5C, 0x2C, 0x96))])
    assert usados & remera, "la remera de la skin no aparece en el torso"


def test_la_espalda_cierra_en_las_skins_generadas(ruta):
    assert skins.continuidad(ruta) == []


def test_continuidad_detecta_una_costura_abierta(tmp_path):
    from PIL import Image

    a = np.zeros((skins.LADO, skins.LADO, 4), np.uint8)
    x0, y0, w, h = skins.ZONAS["torso"]
    a[y0 : y0 + h, x0] = (255, 0, 0, 255)  # columna 0 roja
    a[y0 : y0 + h, x0 + w - 1] = (0, 0, 255, 255)  # última azul: la costura no cierra
    p = str(tmp_path / "rota.png")
    Image.fromarray(a, "RGBA").save(p)
    assert skins.continuidad(p) == [("torso", h)]


def test_columnas_por_direccion_ubica_frente_y_espalda():
    cols = skins.columnas_por_direccion("stardew8")
    # torso 16 de ancho: frente (S) al centro, espalda (N) en el borde
    assert cols["S"]["torso"] == 8
    assert cols["N"]["torso"] == 0
    # E al costado izquierdo del mapa, W al derecho
    assert cols["E"]["torso"] < cols["S"]["torso"] < cols["W"]["torso"]
    # las diagonales frontales caen entre el frente y su costado
    assert cols["SE"]["torso"] < cols["S"]["torso"] < cols["SW"]["torso"]
    # los brazos son de 8 de ancho: las 8 direcciones caen en 8 columnas distintas (con 4 se repetían de a pares)
    brazo = {
        cols[d]["brazo_derecho"] for d in ("S", "SE", "E", "NE", "N", "NW", "W", "SW")
    }
    assert len(brazo) == 8


def test_guia_marca_las_direcciones(tmp_path):
    from PIL import Image

    p = str(tmp_path / "guia.png")
    skins.guia(p, zoom=4, estilo="stardew8")
    im = Image.open(p)
    assert im.width == skins.LADO * 4
    assert (
        im.height > skins.LADO * 4
    )  # la franja de leyenda suma alto debajo de las 32 filas


def test_ficha_con_arma_pone_el_arma_en_la_mano(ruta):
    from sprites_lib.tests_personaje import mascara

    f = skins.ficha_con_arma(ruta, "espada")
    assert f["identidad"]["nombre"].endswith("_espada")
    assert any(c["tipo"] == "objeto" for c in f["componentes"])
    c = render_cuadro(f, "stardew", "quieto", 0, "S")
    assert mascara(c, "objeto@mano_derecha").sum() > 0


def test_salida_arma_exporta_la_animacion(ruta, tmp_path):
    import os

    car = skins.salida_arma(
        ruta, "espada", anim="golpear", estilo="stardew", raiz=str(tmp_path)
    )
    assert car.endswith(os.path.join("_espada", "stardew", "golpear"))
    assert os.path.exists(os.path.join(car, "golpear.png"))
    assert os.path.exists(os.path.join(car, "golpear.json"))
