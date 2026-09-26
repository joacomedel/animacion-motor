"""Mago corriendo en isométrico hacia la derecha-abajo (sudeste), 10 cuadros.

Reutiliza la mecánica del ciclo lateral (mago_correr.py, medida sobre Mega Man X) y la lleva a 3D:
  f = adelante (dirección de avance), l = lateral (+ = izquierda del personaje, lejos de cámara),
  u = arriba.  Proyección isométrica 2:1:  x = f*FX + l*LX ;  y = f*FY - l*LY - u
Referencias de vista 3/4: Final Fantasy Tactics (Ramza) e Isometric Hero (C. Bellanger, CC-BY 3.0).
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw

from mago_correr import BOB, C, FOOT_A, FOOT_ANG, N, THIGH, SHIN, UPPER, FORE, hand_path, ik, outline

AQUI = os.path.dirname(os.path.abspath(__file__))
CW, CH = 48, 48
GX, GY = 22, 42                 # punto del piso bajo la cadera en la celda
FX, FY = .78, .39               # eje "adelante" (sudeste) en pantalla, relación 2:1 y acortado
LX, LY = .85, .42               # eje lateral (noreste) en pantalla


def side_to_3d(pt, l):
    """Coordenadas del rig lateral (x, y con piso y=34) → (f, l, u)."""
    return (pt[0] - 18, l, 34 - pt[1])


def proj(f, l, u):
    return (GX + f * FX + l * LX, GY + f * FY - l * LY - u)


def S(pt, l):
    return proj(*side_to_3d(pt, l))


def layer():
    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def R(p):
    return (int(round(p[0])), int(round(p[1])))


def seg(d, a, b, col, w):
    d.line([R(a), R(b)], fill=col, width=w)
    for q in (a, b):
        x, y = R(q)
        r = w // 2
        d.ellipse([x - r, y - r, x + r - (1 - w % 2), y + r - (1 - w % 2)], fill=col)


def dots(d, a, b, col, step=2, off=0):
    n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
    for i in range(off, n, step):
        t = i / n
        d.point(R((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)), fill=col)


# ---------------------------------------------------------------- partes
def draw_leg(hip_s, foot_s, ang, l, far):
    im, d = layer()
    knee_s = ik(hip_s, foot_s, THIGH, SHIN, +1)
    hip, knee, foot = S(hip_s, l), S(knee_s, l), S(foot_s, l)
    pants = C["robe_d"] if far else C["robe_l"]
    seg(d, hip, knee, pants, 4)
    seg(d, knee, foot, pants, 3)
    # bota orientada al sudeste: la punta va en diagonal abajo-derecha
    r = math.radians(ang)
    pts = [(-2, -2), (-2, 1), (4, 1), (4, -1), (1, -2)]
    boot = []
    for x, y in pts:
        sx, sy = x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)
        boot.append(S((foot_s[0] + sx, foot_s[1] + sy), l))
    d.polygon([R(q) for q in boot], fill=C["boot"])
    d.line([R(boot[1]), R(boot[2])], fill=C["rune_d"] if far else C["rune"])
    d.point(R(knee), fill=C["gold"])
    return outline(im)


def draw_arm(sh_s, hand_s, l, far):
    im, d = layer()
    el_s = ik(sh_s, hand_s, UPPER, FORE, -1)
    sh, el, hand = S(sh_s, l), S(el_s, l), S(hand_s, l)
    skin = C["skin_d"] if far else C["skin_l"]
    rune = C["rune_d"] if far else C["rune"]
    seg(d, sh, el, skin, 3)
    seg(d, el, hand, skin, 3)
    dots(d, sh, el, rune, off=1)
    dots(d, el, hand, rune)
    d.point(R((el[0] + (hand[0] - el[0]) * .7, el[1] + (hand[1] - el[1]) * .7)), fill=C["gold"])
    x, y = R(hand)
    d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=skin)
    if not far:
        d.point((x + 1, y - 1), fill=C["hair"])
    x, y = R(sh)
    d.rectangle([x - 2, y - 1, x + 1, y + 1], fill=C["robe_d"] if far else C["gold"])
    d.point((x, y), fill=rune)
    return outline(im)


def draw_body(p, bob):
    im, d = layer()
    lag = math.sin(2 * math.pi * (p - 1) / 5)
    hip_y, neck_y = 21 + bob, 14 + bob
    sh_n, sh_f = S((20, neck_y + 1), -4), S((20, neck_y + 1), 4)
    hp_n, hp_f = S((18, hip_y), -3), S((18, hip_y), 3)
    d.polygon([R(sh_f), R(sh_n), R(hp_n), R(hp_f)], fill=C["robe"])
    # faldón: cae desde la cadera y flamea hacia atrás (noroeste) con retraso
    hem_n = S((17 - 2 * lag, hip_y + 5 + lag), -3)
    hem_f = S((15 - 2 * lag, hip_y + 4 + lag), 3)
    back = S((12 - 3 * lag, hip_y + 2), 0)
    d.polygon([R(hp_f), R(hp_n), R(hem_n), R(back), R(hem_f)], fill=C["robe_d"])
    # frente iluminado (cara que mira a cámara) y detalles
    d.line([R(sh_n), R(hp_n)], fill=C["robe_l"])
    d.line([R(hp_f), R(hp_n)], fill=C["gold"])
    mid = ((hp_f[0] + hp_n[0]) / 2, (hp_f[1] + hp_n[1]) / 2)
    d.point(R(mid), fill=C["rune"])
    cx, cy = R(S((20, neck_y + 3), -1))
    for q in ((0, 0), (1, 0), (1, 1), (1, 2), (0, 2), (2, 2)):
        d.point((cx + q[0], cy + q[1]), fill=C["rune"])
    return outline(im)


# cabeza en 3/4 mirando al sudeste: cara abajo-derecha, pelo arriba-izquierda, dos ojos visibles
HEAD = [
    "..hghhghh....",
    ".hghhghhgh...",
    "hghhghhghhh..",
    "hgdbbbbbbrbb.",
    "ghdssssssssss",
    "hgdsseksseks.",
    "hgdssssssssss",
    ".gddssssrssss",
    ".hddsssssss..",
    "..gddsssdds..",
    "...gddsss....",
    "....ddd......",
]
HEAD_LEG = {"g": "hair_d", "h": "hair", "s": "skin", "d": "skin_d", "b": "gold", "r": "rune", "e": "eye", "k": "out"}


def draw_head(p, bob):
    im, d = layer()
    hx, hy = R(S((20, 3 + bob + 11), 0))
    hx, hy = hx - 6, hy - 11                         # esquina sup. izq. del bloque de 13x12
    prev = BOB[(p - 1) % N]
    for i in range(4):                                # rastas hacia atrás (noroeste) y cayendo
        x0, y0 = hx + 1, hy + 2 + i * 2.2
        pts = []
        for k in range(8):
            wave = math.sin(k * .8 - p * 2 * math.pi / 5 + i) * 1.1
            pts.append((x0 - k * .95, y0 + k * .3 + wave * k / 7 + (prev - bob) * k / 8))
        for a, b in zip(pts, pts[1:]):
            seg(d, a, b, C["hair_d"] if i % 2 else C["hair"], 2)
        d.point(R(pts[-1]), fill=C["rune"] if i % 2 == 0 else C["gold"])
    for y, row in enumerate(HEAD):
        for x, ch in enumerate(row):
            if ch != ".":
                d.point((hx + x, hy + y), fill=C[HEAD_LEG[ch]])
    return outline(im)


def shadow():
    im, d = layer()
    a = np.zeros((CH, CW), bool)
    yy, xx = np.mgrid[0:CH, 0:CW]
    a = ((xx - GX - 1) / 9.0) ** 2 + ((yy - GY - 1) / 4.0) ** 2 <= 1
    checker = (xx + yy) % 2 == 0
    arr = np.zeros((CH, CW, 4), np.uint8)
    arr[a & checker] = (10, 8, 18, 200)
    return Image.fromarray(arr, "RGBA")


def frame(p):
    bob = BOB[p]
    hip = (18, 21 + bob)
    fa, fb = FOOT_A[p], FOOT_A[(p + 5) % N]
    ha, hb = hand_path(p), hand_path(p + 5)
    ha, hb = (ha[0], ha[1] + bob), (hb[0], hb[1] + bob)
    sh = (20, 16 + bob)
    # en isométrico cada pierna conserva su lado (profundidad): A = derecha, cerca de cámara
    leg_near = draw_leg(hip, fa, FOOT_ANG[p], -3, False)
    leg_far = draw_leg(hip, fb, FOOT_ANG[(p + 5) % N], 3, True)
    arm_near = draw_arm(sh, hb, -5, False)      # brazo derecho, opuesto a la pierna derecha
    arm_far = draw_arm(sh, ha, 5, True)
    out = shadow()
    for lay in (arm_far, leg_far, draw_body(p, bob), leg_near, draw_head(p, bob), arm_near):
        out.alpha_composite(lay)
    return out


def iso_floor(w, h, off):
    """Piso de baldosas isométricas 32x16 desplazado 'off' px en la diagonal sudeste."""
    im = Image.new("RGB", (w, h), (28, 26, 40))
    d = ImageDraw.Draw(im)
    ox, oy = -off * 2 % 32, -off % 16
    for j in range(-2, h // 8 + 3):
        for i in range(-2, w // 32 + 3):
            cx = i * 32 + (j % 2) * 16 + ox
            cy = j * 8 + oy
            col = (44, 40, 64) if (i + j) % 2 else (38, 34, 56)
            d.polygon([(cx, cy - 8), (cx + 16, cy), (cx, cy + 8), (cx - 16, cy)], fill=col, outline=(56, 52, 80))
    return im


if __name__ == "__main__":
    frames = [frame(p) for p in range(N)]
    tira = Image.new("RGBA", (CW * N, CH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        tira.paste(f, (i * CW, 0))
    tira.save(os.path.join(AQUI, "mago_iso_correr.png"))
    # GIF en el lugar
    Z = 4
    gif = []
    for f in frames:
        g = Image.new("RGB", (CW, CH), (28, 26, 40))
        g.paste(f, (0, 0), f)
        gif.append(g.resize((CW * Z, CH * Z), Image.NEAREST))
    gif[0].save(os.path.join(AQUI, "mago_iso_correr.gif"), save_all=True, append_images=gif[1:],
                loop=0, duration=int(1000 / 12), disposal=1)
    # GIF avanzando sobre un piso isométrico (cámara fija, el piso se desplaza)
    W, H = 160, 100
    gif2 = []
    for loop in range(3):
        for i, f in enumerate(frames):
            t = loop * N + i
            bg = iso_floor(W, H, t * 1.6)
            bg.paste(f, (W // 2 - GX, H // 2 - GY + 20), f)
            gif2.append(bg.resize((W * 3, H * 3), Image.NEAREST))
    gif2[0].save(os.path.join(AQUI, "mago_iso_escena.gif"), save_all=True, append_images=gif2[1:],
                 loop=0, duration=int(1000 / 12), disposal=1)
    # hoja de revisión ampliada
    sheet = Image.new("RGB", (CW * 5 * 5, CH * 2 * 5), (28, 26, 40))
    for i, f in enumerate(frames):
        sheet.paste(f.resize((CW * 5, CH * 5), Image.NEAREST), ((i % 5) * CW * 5, (i // 5) * CH * 5),
                    f.resize((CW * 5, CH * 5), Image.NEAREST))
    sheet.save(os.path.join(AQUI, "mago_iso_revision.png"))
    print("ok")
