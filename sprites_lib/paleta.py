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


def _lab(c):
    import numpy as np
    v = np.array(c) / 255.
    v = np.where(v > .04045, ((v + .055) / 1.055) ** 2.4, v / 12.92)
    x = np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]]) @ v / np.array([.9505, 1, 1.089])
    f = np.where(x > .008856, np.cbrt(x), 7.787 * x + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def reducir_paleta(por_dir, n):
    """Deja a lo sumo `n` colores en TODAS las direcciones y cuadros a la vez ({dir: [imágenes RGBA]}, in situ).
    Junta de a pares los colores más parecidos (distancia Lab, ponderada por cantidad de píxeles) y conserva
    siempre el más usado del par: nunca inventa un color nuevo. Referencia: Fry (CC0) usa 14 en toda su hoja."""
    import collections
    cnt = collections.Counter(p[:3] for fs in por_dir.values() for im in fs for p in im.getdata() if p[3] > 0)
    if len(cnt) <= n:
        return por_dir
    lab = {k: _lab(k) for k in cnt}
    rep = {k: k for k in cnt}
    while len(cnt) > n:
        ks = list(cnt)
        w, a, b = min((cnt[a] * cnt[b] / (cnt[a] + cnt[b]) * float(((lab[a] - lab[b]) ** 2).sum()), a, b)
                      for i, a in enumerate(ks) for b in ks[i + 1:])
        keep, drop = (a, b) if cnt[a] >= cnt[b] else (b, a)
        cnt[keep] += cnt.pop(drop)
        rep = {k: (keep if v == drop else v) for k, v in rep.items()}
    for fs in por_dir.values():
        for im in fs:
            im.putdata([(*rep[p[:3]], p[3]) if p[3] > 0 else p for p in im.getdata()])
    return por_dir
