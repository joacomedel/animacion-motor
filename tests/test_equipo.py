"""Tests del equipamiento: catálogo, composición de ficha y skins de ítems."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

from motor.equipo import ITEMS, Equipo, ficha_con_equipo
from motor.renderer import Renderer
from motor.estado import Estado
from sprites_lib import skins
from sprites_lib.componentes import REGISTRO

SKIN = "skins/caballero_carmesi.png"


def test_catalogo_items_validos():
    for nombre, item in ITEMS.items():
        assert item["tipo"] in REGISTRO, (
            f"{nombre}: tipo {item['tipo']!r} no registrado"
        )
        comp = REGISTRO[item["tipo"]]
        if comp.anclas_validas:
            assert item["ancla"] in comp.anclas_validas, (
                f"{nombre}: ancla {item['ancla']!r} no válida para {item['tipo']}"
            )


def test_ficha_con_equipo_agrega_componentes_en_orden():
    f = ficha_con_equipo(skins.ficha(SKIN), ["armadura_malla", "sombrero"])
    tipos = [c["tipo"] for c in f["componentes"]]
    assert tipos == ["armadura", "sombrero"]


def test_ficha_con_equipo_skin_aporta_materiales():
    f = ficha_con_equipo(skins.ficha(SKIN), ["espada_roja"])
    # el color principal de items/espada_roja.png es (200,30,30) -> sk_c81e1e
    assert "sk_c81e1e" in f["paleta"]
    assert f["componentes"][-1]["material"] == "sk_c81e1e"


def test_ficha_con_equipo_item_desconocido():
    with pytest.raises(KeyError):
        ficha_con_equipo(skins.ficha(SKIN), ["espada_de_lava"])


def test_equipo_alternar():
    eq = Equipo()
    eq.equipar("espada")
    eq.equipar("sombrero")
    assert eq.items == ["espada", "sombrero"]
    eq.alternar("espada")
    assert eq.items == ["sombrero"]
    eq.alternar("espada")
    assert eq.items == ["sombrero", "espada"]


def test_equipo_item_desconocido():
    with pytest.raises(KeyError):
        Equipo(["espada_de_lava"])


def test_renderer_set_equipo_invalida_cache():
    r = Renderer("stardew8", SKIN, zoom=4)
    r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    assert len(r._cache) == 1
    r.set_equipo(["armadura_malla", "sombrero"])
    assert len(r._cache) == 0
    assert r.equipo == ["armadura_malla", "sombrero"]


def test_item_nuevo_sin_tocar_motor(monkeypatch):
    """Regla de escalabilidad: un ítem nuevo es 1 entrada en ITEMS y funciona sin tocar el motor."""
    from motor import equipo as eq

    monkeypatch.setitem(
        eq.ITEMS,
        "espada_roja2",
        {
            "tipo": "objeto",
            "ancla": "mano_derecha",
            "parametros": {"forma": "espada"},
            "skin": "items/espada_roja.png",
        },
    )
    f = eq.ficha_con_equipo(skins.ficha(SKIN), ["espada_roja2"])
    assert f["componentes"][-1]["tipo"] == "objeto"
    assert "sk_c81e1e" in f["paleta"]


def test_renderer_renderiza_personaje_equipado():
    r = Renderer("stardew8", SKIN, zoom=4)
    r.set_equipo(["armadura_malla", "sombrero", "guante_cuero"])
    from motor.estado import Estado

    sup = r.renderizar(Estado(animacion="idle", direccion="S", frame=0))
    assert isinstance(sup, pygame.Surface)
    assert sup.get_width() > 0 and sup.get_height() > 0
