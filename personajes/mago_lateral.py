"""PLANTILLA de personaje 2D plano (vista lateral, mira a la derecha) — el mago.

Para crear un personaje nuevo: copiar este archivo como personajes/<nombre>_lateral.py y cambiar
CELDA, COLORES, CABEZA (bloque ASCII) y las funciones pierna/brazo/cuerpo/cabeza.
La mecánica viene de sprites_lib.ciclos. Cada parte se dibuja en su propia capa con contorno
y se apila de atrás hacia adelante: brazo lejano, pierna lejana, cuerpo, pierna cercana, cabeza,
brazo cercano, puño cercano.

Uso (desde la raíz del proyecto):
  .venv/bin/python -m personajes.mago_lateral --anim correr
  .venv/bin/python -m personajes.mago_lateral --anim quieto
Salida: salida/mago_lateral/<anim>/...
"""
import argparse
import math
import os

from sprites_lib.ciclos import CICLOS, pose
from sprites_lib.exportar import exportar
from sprites_lib.pixel2d import Lienzo, apilar, contorno
from sprites_lib.rig import ik

NOMBRE = "mago_lateral"
L = Lienzo(cw=40, ch=37, ox=4)       # el rig lateral usa piso y=34 y cadera x=18; ox corre todo dentro de la celda
MUSLO, CANILLA, BRAZO, ANTEBRAZO = 7.0, 7.0, 5.5, 5.5

COLORES = {
    "contorno": (18, 12, 28),
    "piel": (122, 72, 44), "piel_d": (84, 48, 32), "piel_l": (156, 98, 62), "mano": (178, 118, 76),
    "pelo": (240, 240, 236), "pelo_d": (170, 178, 196),
    "tunica": (70, 36, 110), "tunica_d": (40, 20, 68), "tunica_l": (104, 60, 150),
    "oro": (232, 192, 80), "runa": (110, 248, 236), "runa_d": (40, 150, 150),
    "bota": (44, 40, 60), "ojo": (250, 250, 250),
}
C = COLORES
CABEZA = [
    "...hghhgh...",
    "..hghhghhg..",
    ".ghhghhghhh.",
    ".hgbbbbbbrbb",
    "hgdsssssssss",
    "ghdssssseess",
    "hgdsssssekss",
    ".gddssrsssss",
    ".hddsssssss.",
    "..gddsssdds.",
    "...gddsss...",
    "....ddd.....",
]
LEYENDA = {"g": "pelo_d", "h": "pelo", "s": "piel", "d": "piel_d", "b": "oro", "r": "runa", "e": "ojo", "k": "contorno"}


def pierna(cadera, pie, ang, lejana):
    im, d = L.capa()
    rod = ik(cadera, pie, MUSLO, CANILLA, +1)
    col = C["tunica_d"] if lejana else C["tunica_l"]
    L.seg(d, cadera, rod, col, 4)
    L.seg(d, rod, pie, col, 3)
    r = math.radians(ang)
    pts = [(-2, -2), (-2, 1), (4, 1), (4, -1), (1, -2)]
    rot = [(pie[0] + x * math.cos(r) - y * math.sin(r), pie[1] + x * math.sin(r) + y * math.cos(r)) for x, y in pts]
    d.polygon([L.P(*q) for q in rot], fill=C["bota"])
    d.line([L.P(*rot[1]), L.P(*rot[2])], fill=C["runa_d"] if lejana else C["runa"])   # suela luminosa
    d.point(L.P(*rod), fill=C["oro"])
    return contorno(im, C["contorno"])


def brazo(hombro, mano, lejano):
    """Devuelve (capa del brazo, capa del puño): el puño va en capa propia para que tenga contorno."""
    im, d = L.capa()
    codo = ik(hombro, mano, BRAZO, ANTEBRAZO, -1)
    piel = C["piel_d"] if lejano else C["piel_l"]
    runa = C["runa_d"] if lejano else C["runa"]
    L.seg(d, hombro, codo, piel, 3)
    L.seg(d, codo, mano, piel, 3)
    L.puntos(d, hombro, codo, runa, off=1)
    L.puntos(d, codo, mano, runa)
    mx, my = codo[0] + (mano[0] - codo[0]) * .8, codo[1] + (mano[1] - codo[1]) * .8
    d.point(L.P(mx, my), fill=C["oro"])                                     # brazalete pegado a la mano
    sx, sy = L.P(*hombro)
    d.rectangle([sx - 2, sy - 1, sx + 1, sy + 1], fill=C["tunica_d"] if lejano else C["oro"])
    d.point((sx, sy), fill=runa)
    brazo_capa = contorno(im, C["contorno"])
    im2, d2 = L.capa()
    x, y = L.P(*mano)
    d2.rectangle([x - 1, y - 1, x + 1, y + 1], fill=C["piel_d"] if lejano else C["mano"])
    if not lejano:
        d2.point((x + 1, y - 1), fill=C["pelo"])                            # brillo en los nudillos
    return brazo_capa, contorno(im2, C["contorno"])


def cuerpo(ps):
    im, d = L.capa()
    bob = ps["bob"]
    cad, cue = (18, 21 + bob), (21, 14 + bob)
    lag = math.sin(2 * math.pi * (ps["fase"] - .1) * 2)                     # faldón con retraso
    d.polygon([L.P(*q) for q in ((cue[0] - 4, cue[1]), (cue[0] + 3, cue[1]), (cad[0] + 4, cad[1]), (cad[0] - 4, cad[1]))],
              fill=C["tunica"])
    d.polygon([L.P(*q) for q in ((cad[0] - 4, cad[1] - 1), (cad[0] + 4, cad[1] - 1), (cad[0] + 3, cad[1] + 5),
                                 (cad[0] - 5 - 2 * lag, cad[1] + 4 + lag), (cad[0] - 7 - 2 * lag, cad[1] + 2))],
              fill=C["tunica_d"])
    d.line([L.P(cue[0] + 2, cue[1] + 1), L.P(cad[0] + 3, cad[1] - 1)], fill=C["tunica_l"])
    d.line([L.P(cad[0] - 4, cad[1] - 1), L.P(cad[0] + 4, cad[1] - 1)], fill=C["oro"])
    d.point(L.P(cad[0] + 1, cad[1] - 1), fill=C["runa"])
    for q in ((0, 0), (1, 0), (1, 1), (1, 2), (0, 2), (2, 2)):
        d.point(L.P(cue[0] - 1 + q[0], cue[1] + 3 + q[1]), fill=C["runa"])
    return contorno(im, C["contorno"])


def cabeza(ps):
    im, d = L.capa()
    bob = ps["bob"]
    hx, hy = 15, 3 + bob
    for i in range(4):                                                       # rastas con retraso
        x0, y0 = hx + 1, hy + 2 + i * 2.2
        pts = []
        for k in range(8):
            ola = math.sin(k * .8 - ps["fase"] * 4 * math.pi + i) * 1.1
            pts.append((x0 - k * 1.05, y0 + k * .55 + ola * k / 7 + (ps["bob_prev"] - bob) * k / 8))
        for a, b in zip(pts, pts[1:]):
            L.seg(d, a, b, C["pelo_d"] if i % 2 else C["pelo"], 2)
        d.point(L.P(*pts[-1]), fill=C["runa"] if i % 2 == 0 else C["oro"])
    L.ascii(d, CABEZA, hx, hy, LEYENDA, C)
    return contorno(im, C["contorno"])


def cuadro(ciclo, p):
    ps = pose(ciclo, p)
    bob = ps["bob"]
    cad = (18, 21 + bob)
    ma = (ps["mano_a"][0], ps["mano_a"][1] + bob)
    mb = (ps["mano_b"][0], ps["mano_b"][1] + bob)
    # en perfil se puede reflejar medio ciclo: la pierna A es la cercana en la primera mitad
    a_cerca = p < ciclo["n"] // 2 or ciclo["desfase"] == 0
    pc, pl = (ps["pie_a"], ps["ang_a"]), (ps["pie_b"], ps["ang_b"])
    if not a_cerca:
        pc, pl = pl, pc
    bc, bl = (mb, ma) if a_cerca else (ma, mb)                               # brazo opuesto a la pierna cercana
    brazo_l, puno_l = brazo((18, 15 + bob), bl, True)
    brazo_c, puno_c = brazo((21, 16 + bob), bc, False)
    return apilar(L.cw, L.ch, [brazo_l, puno_l, pierna(cad, *pl, True), cuerpo(ps), pierna(cad, *pc, False),
                               cabeza(ps), brazo_c, puno_c])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--anim", default="correr", choices=list(CICLOS))
    a = ap.parse_args()
    c = CICLOS[a.anim]
    frames = [cuadro(c, p) for p in range(c["n"])]
    sal = os.path.join("salida", NOMBRE, a.anim)
    exportar(frames, a.anim, sal, fps=c["fps"], pivote=(18 + L.ox, 34))
    print("listo →", sal)
