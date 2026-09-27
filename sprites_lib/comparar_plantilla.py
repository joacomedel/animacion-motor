"""Comparar una plantilla de movimiento contra la referencia de la que salió: huesos y silueta, cuadro por cuadro.

El muñeco base (pintado con la piel de LPC) se genera en el estilo de verificación 'lpc' (mismo alto y celda que la
referencia) con el ciclo medido, y se mide contra la fila de LPC:
  huesos   distancia en px entre tobillos, manos y cadera del muñeco y los marcados en la referencia
  silueta  superposición (intersección / unión) de lo opaco de cada cuadro
No busca igualdad de píxeles: el dibujo de LPC es a mano y el nuestro sale de volúmenes (y copiarlo no se puede).

Uso:  .venv/bin/python -m sprites_lib.comparar_plantilla      → tabla + salida/plantillas/caminar_lpc/comparacion.png
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw

from .armado import render_cuadro

REF_IMG = "referencias/caminar/lpc_fila_E.png"
REF_HUESOS = "referencias/caminar/lpc_E_huesos.json"
SALIDA = "salida/plantillas/caminar_lpc"
MUNECO = {
    "identidad": {"nombre": "muñeco base"},
    "cuerpo": {"base": "humano", "clase_altura": "adulto", "complexion": "normal", "cabello": "calvo"},
    "paleta": {"piel": {"base": "#f9d5ba"}},
    "componentes": [],
}
# criterio (px a escala LPC): error medio y peor caso. El peor caso admite 4 px porque la plantilla es simétrica y
# LPC no lo es en los cuadros de cruce. La silueta es informativa: las proporciones son nuestras (más finas que LPC),
# solo se exige que no empeore. La mano B no cuenta y la A tolera ~3 px atrás: LPC corre el hombro cercano 4 px
# hacia atrás y el lejano 4 px adelante (trampa de dibujo); nuestros hombros están donde van.
TOL_MEDIO, TOL_PEOR, TOL_SILUETA = 2.0, 4.0, .65
SIN_META = ("mano B",)


def _ref_cuadro(im, c):
    return np.array(im.crop((c * 64, 0, c * 64 + 64, 64)))


def _mascara(a):
    return a[..., 3] > 0


def _mover(m, dx):
    return np.roll(m, dx, axis=1)


def medir(estilo="lpc", pose="caminar_lpc", mira="E"):
    """Por cuadro: silueta (IoU) y error de cada hueso; el muñeco se corre en x una sola vez para toda la tira."""
    ref = Image.open(REF_IMG).convert("RGBA")
    marcas = {f["c"]: f for f in json.load(open(REF_HUESOS))["cuadros"]}
    nuestros = [render_cuadro(MUNECO, estilo, pose, p, mira) for p in range(8)]
    refs = [_ref_cuadro(ref, p + 1) for p in range(8)]                 # cuadro p del ciclo = c(p+1) de LPC
    mr = [_mascara(r) for r in refs]
    mn = [_mascara(np.array(q.img.convert("RGBA"))) for q in nuestros]

    def iou(a, b):
        return (a & b).sum() / max(1, (a | b).sum())
    dx = max(range(-4, 5), key=lambda d: sum(iou(a, _mover(b, d)) for a, b in zip(mr, mn)))
    filas = []
    for p, (q, r) in enumerate(zip(nuestros, refs)):
        m = marcas[p + 1]
        ap = {k: (v[0] + dx, v[1]) for k, v in q.anclas_px.items()}          # (x, y, profundidad)
        cad = ((ap["cadera_derecha"][0] + ap["cadera_izquierda"][0]) / 2, (ap["cadera_derecha"][1] + ap["cadera_izquierda"][1]) / 2)
        pares = {"tobillo A": (ap["tobillo_derecho"], m["tob_A"]), "tobillo B": (ap["tobillo_izquierdo"], m["tob_B"]),
                 "mano A": (ap["mano_derecha"], m["mano_A"]), "mano B": (ap["mano_izquierda"], m["mano_B"]),
                 "cadera": (cad, (30.5, m["top"] + 32))}
        err = {k: float(np.hypot(a[0] - b[0], a[1] - b[1])) for k, (a, b) in pares.items() if b}
        filas.append(dict(cuadro=p, iou=float(iou(mr[p], _mover(mn[p], dx))), err=err, pares=pares))
    return dict(dx=dx, filas=filas, nuestros=nuestros, refs=refs, mr=mr, mn=[_mover(x, dx) for x in mn])


def imagen(res, ruta, zoom=6):
    """Tres filas: LPC, nuestro muñeco y siluetas superpuestas (azul LPC, rojo nuestro, violeta coinciden)
    con los huesos marcados (círculo = referencia, cruz = nuestro)."""
    n, W = len(res["filas"]), 64 * zoom
    out = Image.new("RGB", (n * W, 3 * W), (230, 230, 230))
    dr = ImageDraw.Draw(out)
    for p, f in enumerate(res["filas"]):
        ref = Image.fromarray(res["refs"][p])
        nuestro = Image.fromarray(np.roll(np.array(res["nuestros"][p].img.convert("RGBA")), res["dx"], axis=1))
        for k, im in enumerate((ref, nuestro)):
            fondo = Image.new("RGBA", im.size, (215, 215, 215, 255)); fondo.alpha_composite(im)
            out.paste(fondo.convert("RGB").resize((W, W), Image.NEAREST), (p * W, k * W))
        a, b = res["mr"][p], res["mn"][p]
        sup = np.full((64, 64, 3), 245, np.uint8)
        sup[a & ~b], sup[b & ~a], sup[a & b] = (90, 120, 230), (230, 80, 80), (150, 90, 190)
        out.paste(Image.fromarray(sup).resize((W, W), Image.NEAREST), (p * W, 2 * W))
        for nombre, (nu, rf) in f["pares"].items():
            if not rf:
                continue
            P = lambda q: (p * W + (q[0] + .5) * zoom, 2 * W + (q[1] + .5) * zoom)
            (x0, y0), (x1, y1) = P(rf), P(nu)
            dr.line([(x0, y0), (x1, y1)], fill=(0, 0, 0), width=1)
            dr.ellipse([x0 - 5, y0 - 5, x0 + 5, y0 + 5], outline=(0, 0, 160), width=2)
            dr.line([(x1 - 5, y1 - 5), (x1 + 5, y1 + 5)], fill=(160, 0, 0), width=2)
            dr.line([(x1 - 5, y1 + 5), (x1 + 5, y1 - 5)], fill=(160, 0, 0), width=2)
        dr.text((p * W + 6, 2 * W + 6), f"c{p} IoU {f['iou']:.2f}  peor {max(f['err'].values()):.1f}px", fill=(0, 0, 0))
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    out.save(ruta)


def resumen(res):
    lineas = [f"corrimiento x del muñeco: {res['dx']:+d} px", "cuadro  IoU   " + "  ".join(f"{k:>9}" for k in
              ("tobillo A", "tobillo B", "mano A", "mano B", "cadera"))]
    for f in res["filas"]:
        celdas = [f"{f['err'][k]:9.1f}" if k in f["err"] else "        —" for k in
                  ("tobillo A", "tobillo B", "mano A", "mano B", "cadera")]
        lineas.append(f"  c{f['cuadro']}   {f['iou']:.2f}  " + "  ".join(celdas))
    errs = [e for f in res["filas"] for k, e in f["err"].items() if k not in SIN_META]
    ious = [f["iou"] for f in res["filas"]]
    ok_h, ok_s = np.mean(errs) <= TOL_MEDIO and max(errs) <= TOL_PEOR, min(ious) >= TOL_SILUETA
    lineas.append(f"huesos (sin {', '.join(SIN_META)}): medio {np.mean(errs):.1f} px, peor {max(errs):.1f} px "
                  f"(meta ≤ {TOL_MEDIO} / {TOL_PEOR}) → {'OK' if ok_h else 'FALLA'}")
    lineas.append(f"silueta: media {np.mean(ious):.2f}, peor {min(ious):.2f} (meta ≥ {TOL_SILUETA}) → {'OK' if ok_s else 'FALLA'}")
    res["ok"] = ok_h and ok_s
    return "\n".join(lineas)


if __name__ == "__main__":
    r = medir()
    print(resumen(r))
    ruta = os.path.join(SALIDA, "comparacion.png")
    imagen(r, ruta)
    print(f"→ {ruta}")
