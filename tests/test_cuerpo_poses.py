import numpy as np
import pytest

from sprites_lib.cuerpo import (ANCLAS, PADRE, SEGMENTOS, VOCABULARIO, anatomia, anclas_ausentes, centro_cara,
                                lado_de, masc, posar)
from sprites_lib.estilos import uz
from sprites_lib.poses import POSES, cuadros

FRENTE = np.array([1.0, 0, 0])


def test_anatomia_mide_el_alto_de_la_escala():
    for est in ("stardew", "volumen", "lateral"):
        A = anatomia(est)
        assert A.H * uz(est) == pytest.approx(A.alto_px)


def test_clase_grande_mide_mas():
    assert anatomia("stardew", "grande").H > anatomia("stardew").H


def test_complexion_desconocida():
    with pytest.raises(ValueError, match="complexión"):
        anatomia("stardew", complexion="gordito")


def test_posar_da_todas_las_anclas():
    a = posar(anatomia("stardew"), cuadros("quieto")[0], FRENTE)
    assert set(ANCLAS) <= set(a)


def test_coronilla_a_la_altura_del_personaje():
    A = anatomia("lateral")
    a = posar(A, cuadros("neutra")[0], FRENTE)
    assert a["coronilla"][2] == pytest.approx(A.H)


def test_lados():
    a = posar(anatomia("stardew"), cuadros("quieto")[0], FRENTE)
    assert a["hombro_derecho"][1] < 0 < a["hombro_izquierdo"][1]
    assert a["cadera_derecha"][1] < 0 < a["cadera_izquierda"][1]


def test_huesos_miden_lo_que_dice_la_anatomia():
    A = anatomia("volumen")
    a = posar(A, cuadros("quieto")[0], FRENTE)
    assert np.linalg.norm(a["rodilla_derecha"] - a["cadera_derecha"]) == pytest.approx(A.muslo, abs=.01)
    assert np.linalg.norm(a["codo_izquierdo"] - a["hombro_izquierdo"]) == pytest.approx(A.brazo, abs=.01)


def test_neutra_abre_los_brazos():
    A = anatomia("stardew")
    neutra = posar(A, cuadros("neutra")[0], FRENTE)["mano_izquierda"][1]
    quieto = posar(A, cuadros("quieto")[0], FRENTE)["mano_izquierda"][1]
    assert neutra > quieto


def test_la_cara_sigue_a_la_camara():
    A = anatomia("stardew")
    de_frente = posar(A, cuadros("quieto")[0], FRENTE)
    camara_a_la_derecha = posar(A, cuadros("quieto")[0], np.array([0.0, -1.0, .3]))
    assert camara_a_la_derecha["cara"][1] < de_frente["cara"][1]
    assert np.linalg.norm(centro_cara(FRENTE) - FRENTE) < 1e-9


def test_anclas_ausentes_conserva_la_raiz():
    aus = anclas_ausentes(["antebrazo_derecho"])
    assert {"antebrazo_derecho", "muneca_derecha", "mano_derecha"} <= aus
    assert "codo_derecho" not in aus


def test_vocabulario_y_padres():
    assert "brazo_derecho" in VOCABULARIO and "muneca_derecha" in VOCABULARIO
    assert PADRE["codo_derecho"] == "hombro_derecho" and PADRE["muneca_derecha"] == "codo_derecho"
    assert SEGMENTOS["pierna_izquierda"][0] == "cadera_izquierda"
    assert lado_de("codo_derecho") == "derecha" and masc("izquierda") == "izquierdo"


def test_poses():
    assert set(POSES) == {"neutra", "quieto"}
    assert [ps["bob"] for ps in cuadros("quieto")] == [0, 0, 1, 1]
    assert [ps["cuadro"] for ps in cuadros("quieto")] == [0, 1, 2, 3]
    with pytest.raises(KeyError, match="pose desconocida"):
        cuadros("bailar")


def test_el_antebrazo_nunca_se_estira():
    for est in ("stardew", "volumen", "lateral"):
        A = anatomia(est)
        for pose in ("neutra", "quieto"):
            for ps in cuadros(pose):
                a = posar(A, ps, FRENTE)
                for s, lado in (("derecho", "derecha"), ("izquierdo", "izquierda")):
                    largo = np.linalg.norm(a[f"mano_{lado}"] - a[f"codo_{s}"])
                    assert largo <= A.antebrazo + .01, (est, pose, s, largo, A.antebrazo)


def test_de_perfil_la_cara_mira_hacia_adelante_en_lateral():
    """La trampa de Stardew (cara hacia la cámara) no aplica en plataformas: de perfil, la cara mira hacia donde va."""
    A = anatomia("lateral")
    a = posar(A, cuadros("quieto")[0], np.array([0.0, -1.0, 0.0]))     # cámara del lado derecho
    assert abs(a["cara"][1] - a["cabeza"][1]) < A.cabeza[1] * .35
