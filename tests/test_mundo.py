"""Tests del mundo 2D y la cámara."""

from motor.mundo import Mundo, MURO, PISO, ARBOL
from motor.camara import Camara


def test_mundo_dimensiones():
    m = Mundo(ancho=40, alto=25, tile=16)
    assert m.ancho_px == 40 * 16
    assert m.alto_px == 25 * 16


def test_mundo_borde_es_muro():
    m = Mundo(ancho=20, alto=10, tile=16)
    for x in range(20):
        assert m.tile_en(x, 0) == MURO
        assert m.tile_en(x, 9) == MURO
    for y in range(10):
        assert m.tile_en(0, y) == MURO
        assert m.tile_en(19, y) == MURO


def test_mundo_fuera_es_muro():
    m = Mundo(ancho=10, alto=10, tile=16)
    assert m.tile_en(-1, 5) == MURO
    assert m.tile_en(5, 99) == MURO


def test_mundo_interior_es_piso_o_feature():
    m = Mundo(ancho=30, alto=20, tile=16)
    # el centro no es muro (el borde sí)
    assert m.tile_en(15, 10) in (PISO, 2)


def test_mundo_superficie_cacheada():
    m = Mundo(ancho=10, alto=10, tile=16)
    assert m.superficie() is m.superficie()


def test_camara_centra_al_personaje():
    m = Mundo(ancho=80, alto=50, tile=16)  # 1280x800
    c = Camara(800, 600, m)
    x, y = c.seguir(640, 400)  # centro del mundo
    assert (x, y) == (640 - 400, 400 - 300)


def test_camara_clampa_en_bordes():
    m = Mundo(ancho=80, alto=50, tile=16)
    c = Camara(800, 600, m)
    # esquina superior izquierda
    assert c.seguir(0, 0) == (0, 0)
    # esquina inferior derecha
    assert c.seguir(m.ancho_px, m.alto_px) == (m.ancho_px - 800, m.alto_px - 600)


# --- Tests de colisión (task-027) ---


def test_colision_muro_bloquea():
    m = Mundo(ancho=20, alto=10, tile=16)
    m.mapa[5][5] = MURO
    # el centro del muro bloquea
    assert m.colisiona(5 * 16 + 8, 5 * 16 + 8, radio=4)
    # un punto lejos del muro no bloquea
    assert not m.colisiona(5 * 16 + 8, 5 * 16 + 8 + 20, radio=4)


def test_colision_borde_sigue_bloqueando():
    m = Mundo(ancho=20, alto=10, tile=16)
    # el borde del mapa es muro
    assert m.colisiona(0, 5 * 16 + 8, radio=4)
    assert m.colisiona(19 * 16 + 8, 5 * 16 + 8, radio=4)
    assert m.colisiona(5 * 16 + 8, 0, radio=4)
    assert m.colisiona(5 * 16 + 8, 9 * 16 + 8, radio=4)


def test_colision_arbol_no_bloquea():
    m = Mundo(ancho=20, alto=10, tile=16)
    m.mapa[5][5] = ARBOL
    # ARBOL no bloquea el paso
    assert not m.colisiona(5 * 16 + 8, 5 * 16 + 8, radio=4)


def test_colision_radio_chico_no_es_celda_entera():
    m = Mundo(ancho=20, alto=10, tile=16)
    m.mapa[5][5] = MURO
    # a 1 tile de distancia del muro no hay colisión (radio chico)
    assert not m.colisiona(5 * 16 + 8, 7 * 16 + 8, radio=4)
    # a 2px del borde del muro sí hay colisión
    assert m.colisiona(5 * 16 + 8, 5 * 16 + 8 + 6, radio=4)


# --- Offset de cámara entero (fix del crash de render con estado interpolado) ---


def test_camara_devuelve_enteros_con_entrada_float():
    m = Mundo(ancho=80, alto=50, tile=16)  # 1280x800
    c = Camara(800, 600, m)
    x, y = c.seguir(640.5, 400.7)  # estado interpolado: floats
    assert isinstance(x, int) and isinstance(y, int)
    assert (x, y) == c.seguir(640, 400)
    # el uso real aguas abajo: arboles_visibles con el offset no debe romper
    m.arboles_visibles(x, y, 800, 600)
