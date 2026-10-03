"""Tests para los buffers de normal y lam (task-019).

Verifica que Escena.render(buffers=True) devuelve:
- normal: RGB (ch, cw, 3) uint8 que codifica la normal en ejes de mundo, [-1,1] -> [0,255]
- lam: (ch, cw) float, termino difuso N·luz (clippeado a [0,1])
Y que el PNG renderizado no cambia.
"""

import numpy as np

from sprites_lib.render3d import Escena, CamaraCenital


def _escena_simple():
    """Escena minima: una esfera con luz direccional (variacion en lam)."""
    cam = CamaraCenital(mira="S", cw=16, ch=32, gx=8, gy=29)
    pal = {"piel": ((100, 60, 60), (200, 150, 130), (240, 200, 180))}
    esc = Escena(cam, pal)
    esc.esfera((0, 0, 10), 5, "piel")
    return esc, cam


def test_buffers_incluye_normal_y_lam():
    esc, cam = _escena_simple()
    im, buf = esc.render(buffers=True)
    assert "normal" in buf, "el dict de buffers no incluye 'normal'"
    assert "lam" in buf, "el dict de buffers no incluye 'lam'"
    assert buf["normal"].shape == (32, 16, 3), f"shape normal: {buf['normal'].shape}"
    assert buf["normal"].dtype == np.uint8, f"dtype normal: {buf['normal'].dtype}"
    assert buf["lam"].shape == (32, 16), f"shape lam: {buf['lam'].shape}"


def test_normal_reconstruye_lam():
    """Donde lam es alto, la normal reconstruida apunta hacia la luz (dot > umbral);
    donde es bajo, apunta al lado opuesto."""
    esc, cam = _escena_simple()
    im, buf = esc.render(buffers=True)
    solido = buf["solido"]
    assert solido.any(), "no hay píxeles sólidos"
    normal_rgb = buf["normal"][solido].astype(float) / 255.0 * 2 - 1
    luz = cam.luz
    lam_reconstruido = normal_rgb @ luz
    lam = buf["lam"][solido]
    # lam es el clip del dot product (con tolerancia por cuantización RGB)
    assert np.allclose(lam, np.clip(lam_reconstruido, 0, 1), atol=0.05), (
        f"lam no coincide con clip(N·luz): max diff {np.abs(lam - np.clip(lam_reconstruido, 0, 1)).max()}"
    )
    # donde lam es alto, el dot debe ser alto
    alto = lam > 0.7
    assert alto.any(), "no hay píxeles con lam > 0.7"
    assert (lam_reconstruido[alto] > 0.5).all(), (
        f"donde lam>0.7, dot min={lam_reconstruido[alto].min():.3f} (debería ser >0.5)"
    )
    # donde lam es bajo, el dot debe ser bajo (puede ser negativo)
    bajo = lam < 0.1
    if bajo.any():
        assert (lam_reconstruido[bajo] < 0.2).all(), (
            f"donde lam<0.1, dot max={lam_reconstruido[bajo].max():.3f} (debería ser <0.2)"
        )


def test_png_no_cambia():
    """El PNG renderizado debe ser idéntico con y sin buffers."""
    esc, cam = _escena_simple()
    im1 = esc.render(buffers=False)
    im2, buf = esc.render(buffers=True)
    a1, a2 = np.array(im1), np.array(im2)
    assert a1.shape == a2.shape, f"shape distinta: {a1.shape} vs {a2.shape}"
    assert np.array_equal(a1, a2), "el PNG cambió al agregar buffers"
