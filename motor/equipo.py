"""Catálogo de equipamiento y composición de la ficha con lo equipado.

Regla de escalabilidad: agregar un ítem = una entrada en `ITEMS` (y, solo si necesita un dibujo
nuevo, un componente en `sprites_lib/componentes/equipo.py`). El motor no cambia: renderiza
la ficha resultante.
"""

from sprites_lib import skins_item

# materiales estándar de equipamiento: siempre presentes en la paleta, así un ítem con
# material "metal" o "cuero" funciona aunque la skin del personaje no los tenga.
MATERIALES = {
    "cuero": {"base": "#8a5a2b"},
    "metal": {"base": "#9aa0a8"},
    "oro": {"base": "#e0b34a"},
    "tela": {"base": "#4a6fa5"},
    "madera": {"base": "#7a4a22"},
}

# nombre -> spec de componente. "skin" (opcional) aporta materiales a la paleta y define el
# material principal del componente (el color más usado del PNG).
ITEMS = {
    "guante_cuero": {"tipo": "guante", "ancla": "mano_derecha", "material": "cuero"},
    "espada": {
        "tipo": "objeto",
        "ancla": "mano_derecha",
        "parametros": {"forma": "espada"},
    },
    "antorcha": {
        "tipo": "objeto",
        "ancla": "mano_derecha",
        "parametros": {"forma": "antorcha"},
    },
    "espada_roja": {
        "tipo": "objeto",
        "ancla": "mano_derecha",
        "parametros": {"forma": "espada"},
        "skin": "items/espada_roja.png",
    },
    "sombrero": {"tipo": "sombrero", "ancla": "coronilla", "material": "cuero"},
    "armadura_malla": {"tipo": "armadura", "ancla": "torso", "material": "metal"},
}


def ficha_con_equipo(ficha_base, items):
    """Devuelve la ficha base con los componentes de `items` agregados (en orden = capas).

    Args:
        ficha_base: ficha de personaje (p. ej. de `skins.ficha`)
        items: nombres de ítem de `ITEMS`, en el orden en que se pintan

    Returns:
        ficha nueva, lista para `armado.render_cuadro`
    """
    ficha = {
        **ficha_base,
        "paleta": {**MATERIALES, **ficha_base["paleta"]},
        "componentes": list(ficha_base.get("componentes") or []),
    }
    for nombre in items:
        if nombre not in ITEMS:
            raise KeyError(
                f"ítem desconocido {nombre!r}; disponibles: {', '.join(ITEMS)}"
            )
        item = ITEMS[nombre]
        spec = {"tipo": item["tipo"], "ancla": item["ancla"]}
        if "material" in item:
            spec["material"] = item["material"]
        if "parametros" in item:
            spec["parametros"] = dict(item["parametros"])
        if "skin" in item:
            paleta, principal = skins_item.paleta_y_material(item["skin"])
            ficha["paleta"].update(paleta)
            spec["material"] = principal
        ficha["componentes"].append(spec)
    return ficha


class Equipo:
    """Lista ordenada de ítems equipados (el orden = capas de pintado)."""

    def __init__(self, items=()):
        self.items = []
        for nombre in items:
            self.equipar(nombre)

    def equipar(self, nombre):
        if nombre not in ITEMS:
            raise KeyError(
                f"ítem desconocido {nombre!r}; disponibles: {', '.join(ITEMS)}"
            )
        if nombre not in self.items:
            self.items.append(nombre)

    def desequipar(self, nombre):
        if nombre in self.items:
            self.items.remove(nombre)

    def alternar(self, nombre):
        if nombre in self.items:
            self.desequipar(nombre)
        else:
            self.equipar(nombre)

    def ficha(self, ficha_base):
        return ficha_con_equipo(ficha_base, self.items)
