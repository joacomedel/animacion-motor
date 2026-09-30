"""Paleta de un personaje por estilo: la ficha da solo el tono base de cada material; el estilo deriva
sombra y luz con su propio corrimiento de tono (p. ej. Stardew: sombras a violeta, luces a amarillo)."""
import re

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def hex_rgb(h):
    if not isinstance(h, str) or not HEX.match(h):
        raise ValueError(f"color inválido {h!r}: tiene que ser #rrggbb")
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _mezclar(c, hacia, t):
    return tuple(max(0, min(255, round(a + (b - a) * t))) for a, b in zip(c, hacia))


def _mult(c, k):
    return tuple(max(0, min(255, round(v * k))) for v in c)


def tonos(base, regla, emisivo=False):
    """(sombra, base, luz). Los emisivos (runas, visor) no se oscurecen: brillan igual en todos lados."""
    base = tuple(base)
    if emisivo:
        return (base, base, _mezclar(base, (255, 255, 255), .35))
    ks, hs, ms = regla["sombra"]
    kl, hl, ml = regla["luz"]
    return (_mezclar(_mult(base, ks), hs, ms), base, _mezclar(_mult(base, kl), hl, ml))


def paleta_estilo(paleta_ficha, estilo):
    """{material: (sombra, base, luz)}. Agrega '<material>_b' (variante un poco más oscura para texturas:
    mechones, pliegues) y 'mano' (piel un tono más clara) si la ficha no la define."""
    regla = estilo["tonos"]
    out = {}
    for nombre, m in paleta_ficha.items():
        base = hex_rgb(m["base"])
        emi = bool(m.get("emisivo", False))
        out[nombre] = tonos(base, regla, emi)
        if not nombre.endswith("_b"):
            out.setdefault(f"{nombre}_b", tonos(_mult(base, .86), regla, emi))
    if "piel" in paleta_ficha and "mano" not in paleta_ficha:
        out["mano"] = tonos(_mezclar(hex_rgb(paleta_ficha["piel"]["base"]), (255, 255, 255), .12), regla)
    return out
