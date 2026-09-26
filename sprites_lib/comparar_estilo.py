"""Comparar el estilo de un sprite propio contra una referencia con métricas objetivas.

Sirve para detectar solo, sin que el usuario lo tenga que decir, cosas como "se ve muy 3D", "tiene ruido",
"tiene demasiados tonos" o "el contorno no es igual".

Uso:
  .venv/bin/python -m sprites_lib.comparar_estilo <ref.png> <celda_w>x<celda_h> <mio.png> <celda_w>x<celda_h>
     [--ref-recorte x0,y0,x1,y1] [--mio-recorte x0,y0,x1,y1]

Métricas (promedio por cuadro; los grupos de material se estiman por tono/saturación del color):
  colores       colores distintos por cuadro
  borde_negro   % del contorno exterior casi negro (<30 de luminancia)
  planitud      qué fracción de cada material está en su tono dominante (alto = plano, dibujado a mano)
  tonos_mat     tonos por material con >=4% de sus píxeles
  degrade_R2    qué tan bien se explica la luminancia de cada material con un degradé lineal x,y
                (alto = sombreado de render 3D que sigue la curvatura)
  huerfanos     % de píxeles cuyo color no comparte con ningún vecino (ruido)
  cluster       tamaño medio de los grupos de píxeles del mismo color (bajo = fragmentado)
  bandas        transiciones de tono dentro de un mismo material por cada 100 px (alto = bandas de degradé)
"""
import colorsys
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

VEC4 = ((0, 1), (0, -1), (1, 0), (-1, 0))


def _lum(c):
    return .3 * c[..., 0] + .59 * c[..., 1] + .11 * c[..., 2]


def _grupo(rgb):
    """Grupo de material aproximado: grises por un lado, colores por franjas de tono de 30°."""
    r, g, b = [x / 255 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if v < .12:
        return "oscuro"
    if s < .2:
        return "gris"
    return f"h{int(h * 12) % 12}"


def metricas_cuadro(a):
    op = a[..., 3] > 0
    if op.sum() < 20:
        return None
    rgb = a[..., :3].astype(int)
    tr = ~op
    borde = np.zeros_like(op)
    for dy, dx in VEC4:
        borde |= op & np.roll(np.roll(tr, dy, 0), dx, 1)
    lum = _lum(rgb.astype(float))
    m = {}
    m["borde_negro"] = float((lum[borde] < 30).mean())
    interior = op & ~borde                       # el contorno no cuenta para el sombreado
    cols = [tuple(c) for c in rgb[op]]
    m["colores"] = len(set(cols))
    # código de color por píxel
    codigo = np.full(op.shape, -1)
    tabla = {}
    for (y, x) in zip(*np.where(op)):
        codigo[y, x] = tabla.setdefault(tuple(rgb[y, x]), len(tabla))
    gid = {c: _grupo(c) for c in tabla}
    grupo = np.full(op.shape, "", dtype=object)
    for c, k in tabla.items():
        grupo[codigo == k] = gid[c]
    # huérfanos y clusters
    igual = np.zeros_like(op)
    for dy, dx in VEC4:
        igual |= op & (np.roll(np.roll(codigo, dy, 0), dx, 1) == codigo)
    m["huerfanos"] = float((interior & ~igual).sum() / max(1, interior.sum()))
    tam = []
    for k in tabla.values():
        lab, n = ndimage.label(codigo == k)
        if n:
            tam += list(np.bincount(lab.ravel())[1:])
    m["cluster"] = float(np.mean(tam))
    # por material: planitud, tonos, degradé, bandas
    plan, tonos, r2s, pesos, trans = [], [], [], [], 0
    for gname in set(gid.values()):
        if gname == "oscuro":
            continue
        sel = interior & (grupo == gname)
        n = sel.sum()
        if n < 12:
            continue
        cs, cnt = np.unique(codigo[sel], return_counts=True)
        plan.append(cnt.max() / n)
        tonos.append(int((cnt / n >= .04).sum()))
        pesos.append(n)
        ys, xs = np.where(sel)
        L = lum[sel]
        if L.std() > 1e-6 and n >= 20:
            X = np.stack([xs, ys, np.ones_like(xs)], 1).astype(float)
            coef, *_ = np.linalg.lstsq(X, L, rcond=None)
            pred = X @ coef
            r2s.append(1 - ((L - pred) ** 2).sum() / ((L - L.mean()) ** 2).sum())
        else:
            r2s.append(0.0)
        # transiciones horizontales dentro del material
        g2 = sel & np.roll(sel, 1, 1)
        trans += int((g2 & (codigo != np.roll(codigo, 1, 1))).sum())
    w = np.array(pesos, float)
    m["planitud"] = float(np.average(plan, weights=w)) if plan else 0
    m["tonos_mat"] = float(np.average(tonos, weights=w)) if tonos else 0
    m["degrade_R2"] = float(np.average(r2s, weights=w)) if r2s else 0
    m["bandas"] = 100 * trans / max(1, interior.sum())
    # silueta: recorte, rectitud (lados rectos = dibujado; escalonado continuo = esfera) y proporción de cabeza
    H, W = op.shape
    m["recorte"] = float(op[0].any())            # solo arriba: en muchos estilos los pies tocan el borde inferior
    filas = [y for y in range(H) if op[y].any()]
    izq = np.array([np.argmax(op[y]) for y in filas]); der = np.array([W - 1 - np.argmax(op[y][::-1]) for y in filas])
    rect = [(np.diff(e) == 0).mean() for e in (izq, der)]
    m["rectitud"] = float(np.mean(rect))
    alto = len(filas); corte = int(alto * .45)
    anch = der - izq + 1
    m["cabeza_ancho"] = float(anch[:corte].max() / max(1, anch[corte:].max()))
    return m


def metricas(ruta, celda, recorte=None):
    im = Image.open(ruta).convert("RGBA")
    if recorte:
        im = im.crop(recorte)
    a = np.array(im)
    cw, ch = celda
    res = []
    for y in range(0, a.shape[0] - ch + 1, ch):
        for x in range(0, a.shape[1] - cw + 1, cw):
            m = metricas_cuadro(a[y:y + ch, x:x + cw])
            if m:
                res.append(m)
    return {k: float(np.mean([r[k] for r in res])) for k in res[0]}, len(res)


# qué significa alejarse en cada métrica y cómo corregirlo en el generador
CONSEJOS = {
    "degrade_R2":  ("sombreado de render (degradé que sigue la curvatura) → se ve 3D",
                    "usar sombreado por bordes (sombreado='borde'): tono base plano, luz en el borde superior-izquierdo "
                    "y sombra en el inferior-derecho de cada pieza"),
    "planitud":    ("cada material reparte sus píxeles en varios tonos → poco plano",
                    "subir la dominancia del tono base (umbrales más extremos o sombreado='borde')"),
    "tonos_mat":   ("cantidad de tonos por material distinta a la referencia",
                    "ajustar los tonos de la paleta o los umbrales"),
    # (mensaje si el mío tiene MÁS, mensaje si tiene MENOS)
    "huerfanos":   (("píxeles sueltos de más → ruido de render", "limpiar huérfanos"),
                    ("casi sin píxeles de detalle → superficie lisa de render, se ve 3D",
                     "agregar detalle dibujado: mechones, pliegues, costuras, textura (texturas en los materiales)")),
    "cluster":     (("manchas de color grandes y lisas → se ve render/3D",
                      "partir las superficies con detalle: capas de ropa, mechones, brillos puntuales"),
                    ("demasiado fragmentado", "simplificar detalles o agrandar piezas")),
    "bandas":      (("demasiadas transiciones → ruido", "menos tonos o limpiar"),
                    ("pocas transiciones dentro de los materiales → liso, falta detalle dibujado",
                     "texturas de detalle (mechones en el pelo, pliegues y bordes en la ropa)")),
    "borde_negro": ("contorno distinto al de la referencia",
                    "contorno='color' (selout) si la referencia tiene poco negro; 'negro' si tiene mucho"),
    "colores":     ("cantidad de colores distinta",
                    "ajustar paleta (materiales y tonos)"),
    "recorte":     ("el sprite toca el borde de la celda → está cortado",
                    "bajar el personaje (gy), achicar la cabeza o agrandar la celda"),
    "rectitud":    ("silueta escalonada y curva (esferas) → se ve 3D",
                    "usar formas cuadradas (caja/superelipsoide) para cabeza, torso y pelo"),
    "cabeza_ancho": ("proporción de ancho cabeza/cuerpo distinta",
                     "ajustar el radio lateral de la cabeza o del pelo"),
}
TOL = {"degrade_R2": .15, "planitud": .12, "tonos_mat": .8, "huerfanos": .16, "cluster": .5,
       "bandas": 12, "borde_negro": .5, "colores": .35, "recorte": 0, "rectitud": .1, "cabeza_ancho": .15}
# dependen del personaje (ropa negra, pelo largo...) más que del estilo: se informan pero no bloquean
INFORMATIVAS = {"borde_negro", "tonos_mat", "colores"}
RELATIVA = {"cluster", "colores"}


def comparar(ref, mio):
    print(f"{'métrica':12s} {'referencia':>11s} {'mío':>8s}   estado")
    fallas = []
    for k in ref:
        r, v = ref[k], mio[k]
        lim = TOL[k] * (r if k in RELATIVA else 1)
        ok = abs(v - r) <= lim
        estado = "OK" if ok else ("difiere (informativa)" if k in INFORMATIVAS else "DIFIERE")
        print(f"{k:12s} {r:11.2f} {v:8.2f}   {estado}")
        if not ok and k not in INFORMATIVAS:
            fallas.append((k, r, v))
    if fallas:
        print("\nDiagnóstico y cómo corregirlo:")
        for k, r, v in fallas:
            c = CONSEJOS[k]
            que, como = (c[0] if v > r else c[1]) if isinstance(c[0], tuple) else c
            print(f"- {k} ({'más' if v > r else 'menos'} que la referencia): {que}\n    → {como}")
    else:
        print("\nEl estilo coincide con la referencia en todas las métricas.")
    return fallas


def _celda(s):
    w, h = s.lower().split("x")
    return int(w), int(h)


def _rect(s):
    return tuple(int(v) for v in s.split(","))


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 4:
        print(__doc__); sys.exit(0)
    opts = {a[i]: a[i + 1] for i in range(len(a) - 1) if a[i].startswith("--")}
    ref, n1 = metricas(a[0], _celda(a[1]), _rect(opts["--ref-recorte"]) if "--ref-recorte" in opts else None)
    mio, n2 = metricas(a[2], _celda(a[3]), _rect(opts["--mio-recorte"]) if "--mio-recorte" in opts else None)
    print(f"referencia: {n1} cuadros | mío: {n2} cuadros\n")
    comparar(ref, mio)
