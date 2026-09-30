import numpy as np
import pytest
from sprites_lib.cuerpo import anatomia, posar
from sprites_lib.escala import CLASES
from sprites_lib.estilos import ESTILOS
from sprites_lib.poses import POSES, cuadros

CAM = np.array([0.0, 0.0, 1.0])


@pytest.mark.parametrize("estilo", sorted(ESTILOS))
@pytest.mark.parametrize("clase", sorted(CLASES))
def test_huesos_y_piso(estilo, clase):
    a = anatomia(estilo, clase)
    assert abs(a.muslo - a.canilla) / a.muslo <= .02
    assert a.hombro_u > a.cadera_u
    ratio = (a.muslo + a.canilla) / (a.cadera_u - a.r_pie)
    assert .95 <= ratio <= 1.10


@pytest.mark.parametrize("estilo", ["stardew", "lateral"])
@pytest.mark.parametrize("anim", sorted(POSES))
def test_cadera_sobre_tobillo_en_todas_las_poses(estilo, anim):
    """La cadera va sobre el tobillo cuando el personaje está en el piso. En 'saltar' los cuadros en el aire
    recogen las piernas a propósito (tobillo por encima de la cadera; ver CRITERIOS_ANIMACION.md, plantilla de
    salto): esos cuadros los declara el propio ciclo con `offset_y != 0` y quedan afuera de la aserción."""
    a = anatomia(estilo)
    ofs = POSES[anim].get("offset_y")
    for ps in cuadros(anim):
        if ofs and ofs[ps["cuadro"]] != 0:
            continue
        pos = posar(a, ps, CAM)
        for lado, m in (("derecha", "derecho"), ("izquierda", "izquierdo")):
            assert pos[f"cadera_{lado}"][2] > pos[f"tobillo_{m}"][2]


@pytest.mark.parametrize("estilo", ["stardew", "lateral"])
def test_brazos_no_se_estiran(estilo):
    a = anatomia(estilo)
    for anim in ("caminar_lpc", "golpear"):
        for ps in cuadros(anim):
            pos = posar(a, ps, CAM)
            for m in ("derecho", "izquierdo"):
                largo = np.linalg.norm(pos[f"codo_{m}"] - pos[f"hombro_{m}"])
                assert largo <= a.brazo + .01
