from sprites_lib import mapa


def test_mapa_esta_al_dia():
    """Si falla: correr `.venv/bin/python -m sprites_lib.mapa` y commitear sprites_lib/MAPA.md."""
    assert open(mapa.RUTA, encoding="utf-8").read() == mapa.generar()
