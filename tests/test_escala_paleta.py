import pytest

from sprites_lib.escala import EscalaError, alto_objetivo_px, celda
from sprites_lib.estilos import ESTILOS, uz
from sprites_lib.paleta import hex_rgb, paleta_estilo, tonos


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def test_alto_por_clase():
    assert alto_objetivo_px("stardew") == 26
    assert alto_objetivo_px("stardew", "grande") == 32
    assert alto_objetivo_px("lateral") == 33
    assert alto_objetivo_px("volumen") == 36


def test_celda_pivote_en_los_pies():
    # el pivote (gy) no se mueve al agregar aire abajo: cambia cuántas filas hay bajo la línea de piso, para que la
    # suela del pie y su contorno no se recorten (en 3/4 el pie más cercano cae hasta 5 px debajo del pivote)
    assert celda("stardew") == dict(cw=16, ch=36, gx=8, gy=30)
    assert celda("volumen") == dict(cw=56, ch=60, gx=28, gy=52)
    assert celda("lateral") == dict(cw=40, ch=42, gx=20, gy=38)


def test_todas_las_clases_entran_en_su_celda():
    for est in ("stardew", "volumen", "lateral"):
        for clase in ("nino", "adulto", "grande", "gigante"):
            c = celda(est, clase)
            assert c["gy"] - alto_objetivo_px(est, clase) >= 3, (
                est,
                clase,
            )  # aire arriba para pelo/sombrero


def test_errores_claros():
    with pytest.raises(EscalaError, match="clase de altura desconocida"):
        alto_objetivo_px("stardew", "enano")
    with pytest.raises(EscalaError, match="estilo sin escala"):
        celda("pixar")


def test_estilos_tienen_lo_necesario():
    for nombre, e in ESTILOS.items():
        for k in (
            "vista",
            "direcciones",
            "render",
            "proporciones",
            "tonos",
            "ojos",
            "referencia",
        ):
            assert k in e, (nombre, k)
        for k in (
            "cabeza_frac",
            "piernas_frac",
            "hombros_frac",
            "brazos_frac",
            "forma_cabeza",
            "bajar_punos",
            "luz",
        ):
            assert k in e["proporciones"], (nombre, k)
    assert ESTILOS["lateral"]["direcciones"] == ["E", "W"]
    assert ESTILOS["stardew"]["celda"] == dict(
        cw=16, ch=32, gx=8, gy=30
    )  # compatibilidad con los generadores por ficha


def test_uz_por_vista():
    assert uz("lateral") == 1.0 and uz("stardew") == 0.92 and uz("volumen") == 0.92


def test_tonos_ordenados_por_luz():
    s, b, l = tonos((140, 86, 56), ESTILOS["stardew"]["tonos"])
    assert lum(s) < lum(b) < lum(l)


def test_sombra_stardew_corre_a_violeta():
    s, b, _ = tonos((140, 86, 56), ESTILOS["stardew"]["tonos"])
    assert s[2] - s[0] > b[2] * 0.66 - b[0] * 0.66  # más azul que un oscurecido simple


def test_emisivo_no_se_oscurece():
    s, b, l = tonos((90, 240, 230), ESTILOS["stardew"]["tonos"], emisivo=True)
    assert s == b and lum(l) >= lum(b)


def test_paleta_estilo_agrega_variantes():
    p = paleta_estilo(
        {"piel": {"base": "#8c5638"}, "pelo": {"base": "#e2e2f0"}}, ESTILOS["stardew"]
    )
    assert {"piel", "pelo", "piel_b", "pelo_b", "mano"} <= set(p)
    assert lum(p["mano"][1]) > lum(
        p["piel"][1]
    )  # la mano es un tono más clara: el puño se lee


def test_hex_invalido():
    with pytest.raises(ValueError, match="#rrggbb"):
        hex_rgb("rojo")
