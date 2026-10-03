"""Paleta de un personaje por estilo: la ficha da solo el tono base de cada material; el estilo deriva
sombra y luz con su propio corrimiento de tono (p. ej. Stardew: sombras a violeta, luces a amarillo)."""

import re
from functools import lru_cache

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


class Material(tuple):
    """Material con propiedades de render: (sombra, base, luz) + especular, transmision, textura, rugosidad.

    Subclass de tuple para compatibilidad con todo el código existente que espera (sombra, base, luz).
    """

    def __new__(
        cls, tonos, especular=0.0, transmision=0.0, textura=None, rugosidad=0.5
    ):
        obj = super().__new__(cls, tonos)
        obj.especular = especular
        obj.transmision = transmision
        obj.textura = textura
        obj.rugosidad = rugosidad
        return obj


# Materiales estándar de equipamiento: siempre presentes en la paleta.
# Se usan como base para motor/equipo.py y como referencia para materiales con propiedades.
MATERIALES_BASE = {
    "cuero": {
        "base": "#8a5a2b",
        "especular": 0.1,
        "transmision": 0.0,
        "rugosidad": 0.8,
    },
    "metal": {
        "base": "#9aa0a8",
        "especular": 0.9,
        "transmision": 0.0,
        "rugosidad": 0.2,
    },
    "oro": {
        "base": "#e0b34a",
        "especular": 0.95,
        "transmision": 0.0,
        "rugosidad": 0.15,
    },
    "tela": {"base": "#4a6fa5", "especular": 0.0, "transmision": 0.0, "rugosidad": 0.9},
    "madera": {
        "base": "#7a4a22",
        "especular": 0.05,
        "transmision": 0.0,
        "rugosidad": 0.7,
    },
    "fuego": {
        "base": "#ff8c1a",
        "emisivo": True,
        "especular": 0.0,
        "transmision": 0.0,
        "rugosidad": 0.5,
    },
    "agua": {"base": "#4a90d9", "especular": 0.3, "transmision": 0.6, "rugosidad": 0.1},
    "cristal": {
        "base": "#a0d8ef",
        "especular": 0.8,
        "transmision": 0.9,
        "rugosidad": 0.05,
    },
    "piedra": {
        "base": "#808080",
        "especular": 0.0,
        "transmision": 0.0,
        "rugosidad": 0.95,
    },
    "tierra": {
        "base": "#8b6914",
        "especular": 0.0,
        "transmision": 0.0,
        "rugosidad": 0.9,
    },
}


def hex_rgb(h):
    if not isinstance(h, str) or not HEX.match(h):
        raise ValueError(f"color inválido {h!r}: tiene que ser #rrggbb")
    return tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))


def _mezclar(c, hacia, t):
    return tuple(max(0, min(255, round(a + (b - a) * t))) for a, b in zip(c, hacia))


def _mult(c, k):
    return tuple(max(0, min(255, round(v * k))) for v in c)


def tonos(base, regla, emisivo=False):
    """(sombra, base, luz). Los emisivos (runas, visor) no se oscurecen: brillan igual en todos lados."""
    base = tuple(base)
    if emisivo:
        return (base, base, _mezclar(base, (255, 255, 255), 0.35))
    ks, hs, ms = regla["sombra"]
    kl, hl, ml = regla["luz"]
    return (_mezclar(_mult(base, ks), hs, ms), base, _mezclar(_mult(base, kl), hl, ml))


def _props_mat(nombre, ficha_mat):
    """Propiedades de render para un material: busca en MATERIALES_BASE y mezcla con la ficha."""
    base = MATERIALES_BASE.get(nombre, {})
    return {
        "especular": ficha_mat.get("especular", base.get("especular", 0.0)),
        "transmision": ficha_mat.get("transmision", base.get("transmision", 0.0)),
        "textura": ficha_mat.get("textura", base.get("textura")),
        "rugosidad": ficha_mat.get("rugosidad", base.get("rugosidad", 0.5)),
    }


def paleta_estilo(paleta_ficha, estilo):
    """{material: Material}. Agrega '<material>_b' (variante un poco más oscura para texturas:
    mechones, pliegues) y 'mano' (piel un tono más clara) si la ficha no la define."""
    regla = estilo["tonos"]
    out = {}
    for nombre, m in paleta_ficha.items():
        base = hex_rgb(m["base"])
        emi = bool(m.get("emisivo", False))
        props = _props_mat(nombre, m)
        out[nombre] = Material(tonos(base, regla, emi), **props)
        if not nombre.endswith("_b"):
            out.setdefault(
                f"{nombre}_b", Material(tonos(_mult(base, 0.86), regla, emi), **props)
            )
    if "piel" in paleta_ficha and "mano" not in paleta_ficha:
        base = _mezclar(hex_rgb(paleta_ficha["piel"]["base"]), (255, 255, 255), 0.12)
        props = _props_mat("piel", paleta_ficha["piel"])
        out["mano"] = Material(tonos(base, regla), **props)
    return out


def _lab(c):
    import numpy as np

    v = np.array(c) / 255.0
    v = np.where(v > 0.04045, ((v + 0.055) / 1.055) ** 2.4, v / 12.92)
    x = (
        np.array(
            [
                [0.4124, 0.3576, 0.1805],
                [0.2126, 0.7152, 0.0722],
                [0.0193, 0.1192, 0.9505],
            ]
        )
        @ v
        / np.array([0.9505, 1, 1.089])
    )
    f = np.where(x > 0.008856, np.cbrt(x), 7.787 * x + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def _lab_lote(c):
    """Lab (CIE) vectorizado para un lote de colores (N, 3) o (..., 3) en 0..255."""
    import numpy as np

    v = np.asarray(c, float) / 255.0
    v = np.where(v > 0.04045, ((v + 0.055) / 1.055) ** 2.4, v / 12.92)
    M = np.array(
        [
            [0.4124, 0.3576, 0.1805],
            [0.2126, 0.7152, 0.0722],
            [0.0193, 0.1192, 0.9505],
        ]
    )
    x = (v @ M.T) / np.array([0.9505, 1.0, 1.089])
    f = np.where(x > 0.008856, np.cbrt(x), 7.787 * x + 16 / 116)
    return np.stack(
        [116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])],
        axis=-1,
    )


def como_rgb(colores):
    """Normaliza una lista de colores a tuplas (r, g, b): acepta '#rrggbb' o tuplas."""
    return [hex_rgb(c) if isinstance(c, str) else tuple(int(v) for v in c) for c in colores]


@lru_cache(maxsize=64)
def _lab_pal_cache(colores_key):
    """Lab de la paleta memoizado (la paleta es fija; no hay que recalcularlo por frame)."""
    import numpy as np

    return _lab_lote(np.array(colores_key, float))


def snap_rgb(arr, colores):
    """Cada píxel de `arr` (..., 3) al color más cercano de `colores` (hex o tuplas), en Lab.

    A diferencia de `ajustar_paleta` (que trabaja sobre imágenes PIL), sirve para arrays y para
    superficies del motor: mismo snap por píxel, sin inventar color. Devuelve np.uint8 con la forma de `arr`.
    """
    import numpy as np

    arr = np.asarray(arr)
    forma = arr.shape
    plano = arr.reshape(-1, 3)
    pal = np.array(como_rgb(colores), float)
    lab_pal = _lab_pal_cache(tuple(map(tuple, pal.tolist())))
    uniq, inv = np.unique(plano, axis=0, return_inverse=True)
    if uniq.size == 0:
        return arr.astype(np.uint8)
    lab = _lab_lote(uniq.astype(float))
    d = ((lab[:, None, :] - lab_pal[None, :, :]) ** 2).sum(-1)
    cerca = pal[d.argmin(1)].astype(np.uint8)
    return cerca[inv].reshape(forma)


def reducir_paleta(por_dir, n):
    """Deja a lo sumo `n` colores en TODAS las direcciones y cuadros a la vez ({dir: [imágenes RGBA]}, in situ).
    Junta de a pares los colores más parecidos (distancia Lab, ponderada por cantidad de píxeles) y conserva
    siempre el más usado del par: nunca inventa un color nuevo. Referencia: Fry (CC0) usa 14 en toda su hoja."""
    import collections

    cnt = collections.Counter(
        p[:3] for fs in por_dir.values() for im in fs for p in im.getdata() if p[3] > 0
    )
    if len(cnt) <= n:
        return por_dir
    lab = {k: _lab(k) for k in cnt}
    rep = {k: k for k in cnt}
    while len(cnt) > n:
        ks = list(cnt)
        w, a, b = min(
            (
                cnt[a]
                * cnt[b]
                / (cnt[a] + cnt[b])
                * float(((lab[a] - lab[b]) ** 2).sum()),
                a,
                b,
            )
            for i, a in enumerate(ks)
            for b in ks[i + 1 :]
        )
        keep, drop = (a, b) if cnt[a] >= cnt[b] else (b, a)
        cnt[keep] += cnt.pop(drop)
        rep = {k: (keep if v == drop else v) for k, v in rep.items()}
    for fs in por_dir.values():
        for im in fs:
            im.putdata([(*rep[p[:3]], p[3]) if p[3] > 0 else p for p in im.getdata()])
    return por_dir


def ajustar_paleta(por_dir, colores):
    """Mapea cada píxel opaco al color más cercano de `colores` (lista de hex #rrggbb), en TODAS las direcciones
    y cuadros a la vez ({dir: [imágenes RGBA]}, in situ). A diferencia de `reducir_paleta`, el mapeo es por píxel
    contra una lista fija: no inventa un color y el resultado no depende de cómo se agrupen las imágenes, así que
    dos personajes del mismo estilo caen exactamente en la misma paleta."""
    pal = [hex_rgb(c) for c in colores]
    lab = [_lab(c) for c in pal]
    cache = {}
    for fs in por_dir.values():
        for im in fs:
            salida = []
            for p in im.getdata():
                if p[3] == 0:
                    salida.append(p)
                    continue
                k = p[:3]
                cerca = cache.get(k)
                if cerca is None:
                    v = _lab(k)
                    i = min(
                        range(len(pal)), key=lambda j: float(((lab[j] - v) ** 2).sum())
                    )
                    cerca = cache[k] = pal[i]
                salida.append((*cerca, p[3]))
            im.putdata(salida)
    return por_dir
