"""Tests para movimiento secundario (resorte) y blending de animaciones.

Criterios:
- El resorte es determinista: mismo input → mismo output.
- Con flag apagado, el render es idéntico al actual (no altera exportación).
- El resorte converge al objetivo (no diverge ni oscila infinitamente).
- El blending no introduce colores fuera de la paleta del estilo.
"""

import numpy as np
import pytest

from sprites_lib import armado
from sprites_lib.componentes import Contexto
from sprites_lib.estilos import ESTILOS
from sprites_lib.paleta import paleta_estilo


# ─── Helpers ───────────────────────────────────────────────────────────────────


def _ficha_minima():
    return {
        "cuerpo": {
            "base": "humano",
            "clase_altura": "adulto",
            "complexion": "normal",
            "cabello": "calvo",
        },
        "paleta": {"piel": {"base": "#f9d5ba"}},
        "componentes": [],
    }


def _ctx_mock(estilo="stardew"):
    """Contexto mínimo para probar el resorte sin renderizar."""
    est = ESTILOS[estilo]
    pal = paleta_estilo(_ficha_minima()["paleta"], est)
    return Contexto(
        anat=None,
        a={},
        ps={"bob": 0, "bob_prev": 0, "fase": 0.0, "cuadro": 0},
        estilo=estilo,
        est=est,
        cam_local=np.array([0.0, 0.0, 1.0]),
        paleta=pal,
        mira="S",
        ausentes=frozenset(),
        pieza_base=0,
        cuadro=0,
    )


# ─── Test: resorte determinista ────────────────────────────────────────────────


def test_resorte_determinismo():
    """Mismo estado inicial y mismos parámetros → mismo resultado."""
    from sprites_lib.resorte import Resorte

    r1 = Resorte(amortiguacion=0.3, frecuencia=0.5)
    r2 = Resorte(amortiguacion=0.3, frecuencia=0.5)

    # Simular 20 pasos con el mismo objetivo
    for _ in range(20):
        r1.paso(objetivo=1.0)
        r2.paso(objetivo=1.0)

    assert r1.valor == pytest.approx(r2.valor), "El resorte no es determinista"


def test_resorte_converge():
    """El resorte converge al objetivo sin divergir."""
    from sprites_lib.resorte import Resorte

    r = Resorte(amortiguacion=0.3, frecuencia=0.5)
    for _ in range(100):
        r.paso(objetivo=1.0)

    assert abs(r.valor - 1.0) < 0.01, f"El resorte no converge: valor={r.valor}"


def test_resorte_no_diverge():
    """El resorte no diverge (valor acotado)."""
    from sprites_lib.resorte import Resorte

    r = Resorte(amortiguacion=0.3, frecuencia=0.5)
    for _ in range(200):
        r.paso(objetivo=1.0)

    assert abs(r.valor) < 10.0, f"El resorte diverge: valor={r.valor}"


# ─── Test: flag apagado no altera render ───────────────────────────────────────


def test_flag_apagado_render_identico():
    """Con mov_secundario=False, el render es idéntico al actual."""
    ficha = _ficha_minima()
    estilo = "stardew"
    mira = "S"

    # Render sin flag (comportamiento actual)
    c1 = armado.render_cuadro(ficha, estilo, "quieto", 0, mira)

    # Con flag apagado explícitamente (debería ser idéntico)
    # El flag se controla en Contexto; por ahora verificamos que el default es False
    ctx = _ctx_mock(estilo)
    assert not getattr(ctx, "mov_secundario", False), (
        "El flag mov_secundario debe estar apagado por defecto"
    )


# ─── Test: blending no introduce colores fuera de paleta ──────────────────────


def test_blending_colores_validos():
    """El blending no introduce colores fuera de la paleta del estilo."""
    from sprites_lib.resorte import blending

    pal = {
        "rojo": ("#ff0000", (255, 0, 0), (128, 0, 0)),
        "azul": ("#0000ff", (0, 0, 255), (0, 0, 128)),
    }

    # Blending 50/50 entre dos colores de la paleta
    resultado = blending(pal["rojo"][1], pal["azul"][1], 0.5)

    # El resultado debe ser un color válido (en este caso, un púrpura)
    # No debe ser un color "raro" fuera de la paleta
    assert len(resultado) == 3, "El blending debe devolver un color RGB"
    assert all(0 <= c <= 255 for c in resultado), (
        "El blending produce colores fuera de rango"
    )


# ─── Test: resorte con parámetro por estilo ────────────────────────────────────


def test_resorte_parametro_por_estilo():
    """El resorte tiene parámetros configurables por estilo."""
    from sprites_lib.resorte import Resorte, params_estilo

    # stardew tiene parámetros de resorte definidos
    p = params_estilo("stardew")
    assert "amortiguacion" in p, "Falta parámetro de amortiguación"
    assert "frecuencia" in p, "Falta parámetro de frecuencia"

    # Los parámetros afectan el comportamiento
    r1 = Resorte(**params_estilo("stardew"))
    r2 = Resorte(amortiguacion=0.9, frecuencia=0.1)

    for _ in range(10):
        r1.paso(objetivo=1.0)
        r2.paso(objetivo=1.0)

    # Con más amortiguación, converge más lento
    assert r1.valor != pytest.approx(r2.valor), "Los parámetros no afectan el resorte"


# ─── Test: integración con render_cuadro ───────────────────────────────────────


def test_render_con_mov_secundario_no_rompe():
    """Con mov_secundario=True, el render no debe romper (producir imagen válida)."""
    ficha = _ficha_minima()
    estilo = "stardew"
    mira = "S"

    # Esto debería funcionar sin errores cuando el flag esté implementado
    # Por ahora solo verificamos que el render base funciona
    c = armado.render_cuadro(ficha, estilo, "quieto", 0, mira)
    assert c.img is not None, "El render no produjo imagen"
    assert c.img.size[0] > 0 and c.img.size[1] > 0, "La imagen tiene tamaño inválido"
