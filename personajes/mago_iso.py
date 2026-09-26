"""PLANTILLA de personaje isométrico con volumen — el mago de rastas blancas y runas.

Para crear un personaje nuevo: copiar este archivo como personajes/<nombre>_iso.py y cambiar
ANATOMIA (proporciones), PALETA (materiales con 3 tonos) y construir() (qué primitivas lo forman).
La mecánica de movimiento viene de sprites_lib.ciclos (no hace falta tocarla).

Uso (desde la raíz del proyecto):
  .venv/bin/python -m personajes.mago_iso --anim correr --dir SE
  .venv/bin/python -m personajes.mago_iso --anim correr --dir todas      (8 direcciones)
  .venv/bin/python -m personajes.mago_iso --plantilla                    (hoja de anatomía)
Salida: salida/mago_iso/<anim>/...
"""
import argparse
import math
import os

import numpy as np
from PIL import Image, ImageDraw

from sprites_lib.ciclos import CICLOS, pose
from sprites_lib.exportar import exportar, exportar_direcciones
from sprites_lib.render3d import DIRECCIONES, Camara, Escena, ik_sagital, piso_iso, sombra, v

NOMBRE = "mago_iso"
CELDA = dict(cw=56, ch=60, gx=26, gy=52)          # tamaño de celda y punto del piso bajo la cadera (pivote)

# ---------------------------------------------------------------- 1. anatomía (px de mundo)
ANATOMIA = dict(
    cabeza_r=5.6, cabeza_u=31.5,                  # ~3.3 cabezas de alto
    cuello_u=25.5,
    pecho=(3.4, 4.6, 4.4), pecho_u=21.5,          # radios (adelante, lateral, alto)
    pelvis=(2.8, 3.8, 2.4), pelvis_u=15.5,
    cadera_l=2.3, cadera_u=15.0,                  # cadera al ~45% de la altura
    muslo=7.3, canilla=7.3, pie=3.6,              # muslo = canilla
    hombro_l=5.4, hombro_u=24.5, brazo=5.4, antebrazo=5.2,
    r_muslo=2.1, r_canilla=1.7, r_brazo=1.5, r_antebrazo=1.35, r_mano=1.95, r_pie=1.7,
)

# ---------------------------------------------------------------- 2. paleta: material → (sombra, base, luz)
PALETA = {
    "piel":     ((84, 48, 30), (128, 76, 46), (170, 110, 68)),
    "mano":     ((110, 64, 38), (156, 96, 58), (196, 134, 86)),   # un tono más clara: el puño se lee
    "pelo":     ((140, 148, 170), (210, 214, 224), (250, 250, 248)),
    "tunica":   ((32, 16, 56), (64, 33, 102), (100, 60, 148)),
    "pantalon": ((36, 32, 56), (62, 56, 92), (94, 86, 130)),
    "oro":      ((140, 100, 36), (214, 170, 66), (250, 226, 130)),
    "bota":     ((20, 18, 30), (40, 38, 56), (64, 62, 86)),
}
RUNA, RUNA_D, BLANCO, CONTORNO = (110, 248, 236), (44, 150, 150), (250, 250, 250), (16, 10, 24)

# piezas: cada una recibe contorno propio donde toca a otra
PIEZA = dict(torso=1, cabeza=2, pelo=3, pierna=10, bota=20, brazo=30, mano=40)


def mat_cabeza(d):
    """Cara (adelante, abajo), vincha (franja) y pelo (resto) sobre la esfera de la cabeza."""
    adel, arr = d[..., 0], d[..., 2]
    m = np.full(d.shape[:-1], "pelo", dtype=object)
    m[(adel > -.2) & (arr < .40)] = "piel"
    m[(arr > .40) & (arr < .54)] = "oro"
    return m


def mat_torso(d):
    m = np.full(d.shape[:-1], "tunica", dtype=object)
    m[d[..., 2] < -.72] = "oro"                    # cinturón
    return m


# ---------------------------------------------------------------- 3. construcción del cuerpo
def construir(esc, ps):
    A, cam = ANATOMIA, esc.cam.cam_local
    bob, sube = ps["bob"], -ps["bob"] * .9
    cadera = v(0, 0, A["cadera_u"] + sube)
    # piernas: A = derecha (l<0), B = izquierda; cada una conserva su lado (clave en isométrico)
    for lado, pie, ang in ((-1, ps["pie_a"], ps["ang_a"]), (1, ps["pie_b"], ps["ang_b"])):
        h = cadera + v(0, lado * A["cadera_l"], 0)
        tob = v(pie[0] - 18, lado * A["cadera_l"], (34 - pie[1]) * .95)
        rod = ik_sagital(h, tob, A["muslo"], A["canilla"], +1)
        esc.pieza = PIEZA["pierna"] + lado
        esc.capsula(h, rod, A["r_muslo"], "pantalon")
        esc.capsula(rod, tob, A["r_canilla"], "pantalon")
        esc.esfera(rod + v(.9, 0, 0), 1.2, "oro")                       # rodillera
        r = math.radians(ang)
        punta = tob + v(A["pie"] * math.cos(r), 0, -A["pie"] * math.sin(r))
        esc.pieza = PIEZA["bota"] + lado
        esc.capsula(tob, punta, A["r_pie"], "bota")
        for k in np.linspace(0, 1, 5):                                  # suela luminosa
            esc.detalle(tob + (punta - tob) * k + v(0, -.8, -A["r_pie"] + .2), RUNA)
    # torso, pelvis, faldón (movimiento secundario con retraso) y cuello
    esc.pieza = PIEZA["torso"]
    esc.elipsoide(v(-.3, 0, A["pecho_u"] + sube), A["pecho"], mat_torso)
    esc.elipsoide(v(0, 0, A["pelvis_u"] + sube), A["pelvis"], "tunica")
    lag = math.sin(2 * math.pi * (ps["fase"] - .1) * 2)
    esc.faldon(v(-.4, 0, 16.5 + sube), v(-2.6 - 1.2 * lag, 0, 8.5 + sube + .6 * lag), 3.9, 5.4, "tunica")
    esc.capsula(v(-.3, 0, A["cuello_u"] - 1.5 + sube), v(0, 0, A["cuello_u"] + 1 + sube), 1.6, "piel", tapas=False)
    for q in ((3.2, -1.2, 22.5), (3.3, -.4, 22.5), (3.3, .4, 22.5), (3.2, -.4, 21.5), (3.1, -.4, 20.5), (3.1, .8, 20.5)):
        esc.detalle(v(q[0], q[1], q[2] + sube), RUNA)                   # circuito rúnico del pecho
    esc.detalle(v(2.6, -.6, 16.1 + sube), RUNA)                         # gema del cinturón
    # brazos: el derecho (cerca) va opuesto a la pierna derecha
    for lado, mano_p in ((-1, ps["mano_b"]), (1, ps["mano_a"])):
        hom = v(-.3, lado * A["hombro_l"], A["hombro_u"] + sube)
        # puños un poco más abajo y separados: en iso, un puño a la altura de la cara la tapa
        mano = hom + v(mano_p[0] - 20, lado * .9, 16 - mano_p[1] - 2.5)
        codo = ik_sagital(hom, mano, A["brazo"], A["antebrazo"], -1)
        esc.pieza = PIEZA["brazo"] + lado
        esc.capsula(hom, codo, A["r_brazo"], "piel")
        esc.capsula(codo, mano, A["r_antebrazo"], "piel")
        esc.esfera(hom + v(0, lado * .4, .8), 1.5, "oro")               # hombrera
        esc.detalle(hom + v(0, lado * .4, 2.3), RUNA)
        muneca = codo + (mano - codo) * .80
        esc.capsula(muneca - (mano - codo) * .10, muneca + (mano - codo) * .10, A["r_antebrazo"] + .3, "oro", tapas=False)
        for a_, b_, r_ in ((hom, codo, A["r_brazo"]), (codo, muneca, A["r_antebrazo"])):
            for k in np.linspace(.2, .9, 3):                            # runas tatuadas del lado de la cámara
                esc.detalle(a_ + (b_ - a_) * k + cam * r_, RUNA if lado < 0 else RUNA_D)
        esc.pieza = PIEZA["mano"] + lado
        esc.esfera(mano + (mano - codo) * .06, A["r_mano"], "mano")
        esc.detalle(mano + cam * A["r_mano"] + v(0, 0, .5), PALETA["mano"][2])   # brillo en nudillos
        if lado < 0:
            esc.detalle(mano + cam * A["r_mano"] + v(0, 0, -.6), RUNA)           # anillo rúnico
    # cabeza en 3/4 (la cámara la ve de costado-frente según la dirección)
    esc.pieza = PIEZA["cabeza"]
    hc = v(.2, 0, A["cabeza_u"] + sube)
    esc.esfera(hc, A["cabeza_r"], mat_cabeza)
    esc.esfera(hc + v(A["cabeza_r"] - .6, 0, -1.6), 1.3, "piel")        # nariz
    for lado in (-1, 1):
        ojo = hc + v(A["cabeza_r"] * .82, lado * 2.0, -.6)
        esc.detalle(ojo, BLANCO); esc.detalle(ojo + v(.4, .5, 0), CONTORNO)
    esc.detalle(hc + v(A["cabeza_r"] * .85, 1.0, A["cabeza_r"] * .42), RUNA)      # gema de la vincha
    esc.detalle(hc + v(A["cabeza_r"] * .75, -2.6, -2.2), RUNA)                   # runa en la mejilla
    # rastas: cadenas de cápsulas hacia atrás que caen, con retraso respecto del rebote
    esc.pieza = PIEZA["pelo"]
    for i, (dl, du) in enumerate(((-2.8, 2.5), (-1.0, 3.2), (1.0, 3.0), (2.8, 2.2), (0, .6), (-2.2, -.6), (2.2, -.8))):
        pts = [hc + v(-A["cabeza_r"] * .7, dl, du)]
        for k in range(1, 6):
            sw = math.sin(k * .9 - ps["fase"] * 4 * math.pi + i) * .8
            pts.append(pts[-1] + v(-1.6, dl * .12 + sw * .5, -1.05 - (ps["bob_prev"] - bob) * .25 + sw * .3))
        for a_, b_ in zip(pts, pts[1:]):
            esc.capsula(a_, b_, 1.05, "pelo")
        esc.detalle(pts[-1] + cam, RUNA if i % 2 == 0 else PALETA["oro"][2])


# ---------------------------------------------------------------- render
def cuadro(ciclo, p, mira="SE"):
    cam = Camara(mira, **CELDA)
    esc = Escena(cam, PALETA)
    construir(esc, pose(ciclo, p))
    out = sombra(cam)
    out.alpha_composite(esc.render(contorno=CONTORNO))
    return out


def animacion(nombre_ciclo, mira="SE"):
    c = CICLOS[nombre_ciclo]
    return [cuadro(c, p, mira) for p in range(c["n"])], c["fps"]


def escena_gif(frames, fps, ruta, mira="SE", vel=1.6):
    W, H = 170, 110
    out = []
    for loop in range(3):
        for i, f in enumerate(frames):
            bg = piso_iso(W, H, (loop * len(frames) + i) * vel, mira)
            bg.paste(f, (W // 2 - CELDA["gx"], H // 2 - CELDA["gy"] + 26), f)
            out.append(bg.resize((W * 3, H * 3), Image.NEAREST))
    out[0].save(ruta, save_all=True, append_images=out[1:], loop=0, duration=int(1000 / fps), disposal=1)


def plantilla(ruta):
    Z = 8
    base = cuadro(CICLOS["quieto"], 0).resize((CELDA["cw"] * Z, CELDA["ch"] * Z), Image.NEAREST)
    im = Image.new("RGB", (CELDA["cw"] * Z + 330, CELDA["ch"] * Z), (24, 22, 34))
    im.paste(base, (0, 0), base)
    d = ImageDraw.Draw(im)
    A, cam = ANATOMIA, Camara("SE", **CELDA)
    for nm, p in {"cabeza": v(.2, 0, A["cabeza_u"]), "hombro D": v(-.3, -A["hombro_l"], A["hombro_u"]),
                  "hombro I": v(-.3, A["hombro_l"], A["hombro_u"]), "cadera D": v(0, -A["cadera_l"], A["cadera_u"]),
                  "cadera I": v(0, A["cadera_l"], A["cadera_u"]), "tobillo D": v(.5, -A["cadera_l"], 1.5)}.items():
        x, y, _ = cam.proyectar(p)
        d.ellipse([x * Z - 5, y * Z - 5, x * Z + 5, y * Z + 5], outline=(255, 90, 90), width=2)
        d.text((x * Z + 8, y * Z - 6), nm, fill=(255, 200, 200))
    alto = A["cabeza_u"] + A["cabeza_r"]
    txt = [f"PLANTILLA - {NOMBRE}", "", f"alto: {alto:.0f} px de mundo",
           f"cabezas de alto: {alto / (2 * A['cabeza_r']):.1f}",
           f"hombros {2 * A['hombro_l']:.1f} / caderas {2 * A['cadera_l']:.1f}",
           f"muslo {A['muslo']} canilla {A['canilla']}", f"brazo {A['brazo']} antebrazo {A['antebrazo']}",
           f"cadera a {A['cadera_u'] / alto:.0%} de la altura", "", "D = derecha (cerca de camara)"]
    for i, t in enumerate(txt):
        d.text((CELDA["cw"] * Z + 16, 20 + i * 18), t, fill=(255, 220, 90) if i == 0 else (230, 230, 240))
    im.save(ruta)
    return ruta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--anim", default="correr", choices=list(CICLOS))
    ap.add_argument("--dir", default="SE", help="SE, E, NE, N, NW, W, SW, S o 'todas'")
    ap.add_argument("--plantilla", action="store_true")
    a = ap.parse_args()
    carpeta = os.path.join("salida", NOMBRE)
    os.makedirs(carpeta, exist_ok=True)
    if a.plantilla:
        print(plantilla(os.path.join(carpeta, "plantilla_anatomia.png")))
    else:
        dirs = list(DIRECCIONES) if a.dir == "todas" else a.dir.split(",")
        por_dir = {}
        for dname in dirs:
            frames, fps = animacion(a.anim, dname)
            por_dir[dname] = frames
        sal = os.path.join(carpeta, a.anim)
        pivote = (CELDA["gx"], CELDA["gy"])
        if len(dirs) == 1:
            exportar(por_dir[dirs[0]], f"{a.anim}_{dirs[0]}", sal, fps=fps, pivote=pivote)
        else:
            exportar_direcciones(por_dir, a.anim, sal, fps=fps, pivote=pivote)
        escena_gif(por_dir[dirs[0]], fps, os.path.join(sal, f"escena_{dirs[0]}.gif"), dirs[0])
        print("listo →", sal)
