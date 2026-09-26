"""Ciclo de correr de un mago (10 cuadros) con la mecánica medida de 04_correr (Mega Man X).

Cada cuadro se arma con un esqueleto 2D: cadera, rodillas, tobillos, hombros, codos y manos.
Las trayectorias de pies y manos, el rebote y los tiempos salen del análisis (ver
CRITERIOS_ANIMACION.md); rodillas y codos se resuelven con IK de dos huesos.
Cada parte se dibuja en su capa con contorno propio y se apila de atrás hacia adelante.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
CW, CH = 40, 37           # celda un poco más ancha que la de X (34x35) por las rastas
OX, GROUND = 4, 35        # desplazamiento x respecto de la celda de X y línea del piso
N = 10

# ---------------------------------------------------------------- paleta (15 colores, como X)
C = {
    "out":   (18, 12, 28),
    "skin":  (122, 72, 44), "skin_d": (84, 48, 32), "skin_l": (156, 98, 62),
    "hair":  (240, 240, 236), "hair_d": (170, 178, 196),
    "robe":  (70, 36, 110), "robe_d": (40, 20, 68), "robe_l": (104, 60, 150),
    "gold":  (232, 192, 80),
    "rune":  (110, 248, 236), "rune_d": (40, 150, 150),
    "boot":  (44, 40, 60), "eye": (250, 250, 250),
}

# ---------------------------------------------------------------- mecánica medida de X
BOB = [1, 0, 1, 2, 2, 1, 0, 1, 2, 2]              # borde superior de la cabeza por cuadro
# tobillo de la pierna A en cada fase (coordenadas de la celda de X, piso y=34)
FOOT_A = [(17, 32), (13, 32), (6, 32), (4, 22), (5, 25),
          (11, 28), (18, 27), (24, 26), (26, 31), (22, 32)]
FOOT_ANG = [0, 0, 25, 70, 55, 35, 20, 10, 0, 0]  # grados: punta del pie hacia abajo
THIGH, SHIN = 7.0, 7.0
UPPER, FORE = 5.5, 5.5


def hand_path(p):
    """Mano del brazo A: adelante (28,15) en p≈2.5, atrás (8,13) en p≈7.5, al costado en el cruce."""
    s = math.sin(2 * math.pi * (p - .5) / N)
    return 20 + 7 * s, 21 - 7 * abs(s)


def ik(a, b, l1, l2, bend):
    """Articulación intermedia entre a y b; bend=+1 dobla hacia adelante (x+), -1 hacia atrás."""
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    d = max(1e-3, min(math.hypot(dx, dy), l1 + l2 - 1e-3))
    k = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0, l1 * l1 - k * k))
    ux, uy = dx / d, dy / d
    px, py = ax + ux * k, ay + uy * k
    c1 = (px - uy * h, py + ux * h)
    c2 = (px + uy * h, py - ux * h)
    return max(c1, c2, key=lambda c: c[0] * bend)


# ---------------------------------------------------------------- capas
def layer():
    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def P(x, y):
    return (int(round(x + OX)), int(round(y)))


def outline(im):
    a = np.array(im)
    op = a[..., 3] > 0
    grow = op.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        grow |= np.roll(np.roll(op, dy, 0), dx, 1)
    ring = grow & ~op
    a[ring] = (*C["out"], 255)
    return Image.fromarray(a, "RGBA")


def seg(d, a, b, col, w):
    d.line([P(*a), P(*b)], fill=col, width=w)
    for q in (a, b):
        x, y = P(*q)
        r = w // 2
        d.ellipse([x - r, y - r, x + r - (1 - w % 2), y + r - (1 - w % 2)], fill=col)


def dots_along(d, a, b, col, step=2, off=0):
    n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
    for i in range(off, n, step):
        t = i / n
        d.point(P(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), fill=col)


def draw_leg(hip, foot, ang, far):
    im, d = layer()
    knee = ik(hip, foot, THIGH, SHIN, +1)
    pants = C["robe_d"] if far else C["robe_l"]
    seg(d, hip, knee, pants, 4)
    seg(d, knee, foot, pants, 3)
    # bota: talón, punta hacia adelante, rotada por ang
    r = math.radians(ang)
    pts = [(-2, -2), (-2, 1), (4, 1), (4, -1), (1, -2)]
    rot = [(foot[0] + x * math.cos(r) - y * math.sin(r), foot[1] + x * math.sin(r) + y * math.cos(r)) for x, y in pts]
    d.polygon([P(*q) for q in rot], fill=C["boot"])
    sole = rot[1], rot[2]
    d.line([P(*sole[0]), P(*sole[1])], fill=C["rune_d"] if far else C["rune"])  # suela luminosa
    d.point(P(*knee), fill=C["gold"])                                          # rodillera
    return outline(im)


def draw_arm(sh, hand, far):
    im, d = layer()
    elbow = ik(sh, hand, UPPER, FORE, -1)
    skin = C["skin_d"] if far else C["skin_l"]
    rune = C["rune_d"] if far else C["rune"]
    seg(d, sh, elbow, skin, 3)
    seg(d, elbow, hand, skin, 3)
    dots_along(d, sh, elbow, rune, step=2, off=1)          # runas tatuadas
    dots_along(d, elbow, hand, rune, step=2)
    wx, wy = elbow[0] + (hand[0] - elbow[0]) * .7, elbow[1] + (hand[1] - elbow[1]) * .7
    d.point(P(wx, wy), fill=C["gold"])                      # brazalete
    x, y = P(*hand)
    d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=skin)     # puño
    d.point((x + 1, y - 1), fill=C["hair"] if not far else skin)
    # hombrera tecno-mágica
    sx, sy = P(*sh)
    d.rectangle([sx - 2, sy - 1, sx + 1, sy + 1], fill=C["robe_d"] if far else C["gold"])
    d.point((sx, sy), fill=rune)
    return outline(im)


def draw_body(p, bob):
    im, d = layer()
    hip = (18, 21 + bob)
    neck = (21, 14 + bob)
    lag = math.sin(2 * math.pi * (p - 1) / 5)                 # el faldón reacciona 1 cuadro tarde
    # túnica: torso + faldón que flamea hacia atrás
    torso = [(neck[0] - 4, neck[1]), (neck[0] + 3, neck[1]), (hip[0] + 4, hip[1]), (hip[0] - 4, hip[1])]
    d.polygon([P(*q) for q in torso], fill=C["robe"])
    hem = [(hip[0] - 4, hip[1] - 1), (hip[0] + 4, hip[1] - 1), (hip[0] + 3, hip[1] + 5),
           (hip[0] - 5 - 2 * lag, hip[1] + 4 + lag), (hip[0] - 7 - 2 * lag, hip[1] + 2)]
    d.polygon([P(*q) for q in hem], fill=C["robe_d"])
    d.line([P(neck[0] + 2, neck[1] + 1), P(hip[0] + 3, hip[1] - 1)], fill=C["robe_l"])   # luz de frente
    # cinturón dorado con gema y circuito rúnico en el pecho
    d.line([P(hip[0] - 4, hip[1] - 1), P(hip[0] + 4, hip[1] - 1)], fill=C["gold"])
    d.point(P(hip[0] + 1, hip[1] - 1), fill=C["rune"])
    cx, cy = neck[0] - 1, neck[1] + 3
    for q in ((0, 0), (1, 0), (1, 1), (1, 2), (0, 2), (2, 2)):
        d.point(P(cx + q[0], cy + q[1]), fill=C["rune"])
    return outline(im)


HEAD = [
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
HEAD_LEG = {"g": "hair_d", "h": "hair", "s": "skin", "d": "skin_d", "b": "gold", "r": "rune", "e": "eye", "k": "out"}


def draw_head(p, bob):
    im, d = layer()
    hx, hy = 15, 3 + bob                                      # esquina sup. izq. de la cabeza
    # rastas: 5 mechones que cuelgan hacia atrás con retraso respecto del rebote
    prev = BOB[(p - 1) % N]
    for i in range(4):
        x0, y0 = hx + 1, hy + 2 + i * 2.2
        pts = []
        for k in range(8):
            wave = math.sin(k * .8 - p * 2 * math.pi / 5 + i) * 1.1
            pts.append((x0 - k * 1.05, y0 + k * .55 + wave * k / 7 + (prev - bob) * k / 8))
        for a, b in zip(pts, pts[1:]):
            seg(d, a, b, C["hair_d"] if i % 2 else C["hair"], 2)
        d.point(P(*pts[-1]), fill=C["rune"] if i % 2 == 0 else C["gold"])   # cuentas en las puntas
    for y, row in enumerate(HEAD):
        for x, ch in enumerate(row):
            if ch != ".":
                d.point(P(hx + x, hy + y), fill=C[HEAD_LEG[ch]])
    return outline(im)


def frame(p):
    bob = BOB[p]
    hip = (18, 21 + bob)
    fa, fb = FOOT_A[p], FOOT_A[(p + 5) % N]
    ha, hb = hand_path(p), hand_path(p + 5)
    ha, hb = (ha[0], ha[1] + bob), (hb[0], hb[1] + bob)
    sh_near, sh_far = (21, 16 + bob), (18, 15 + bob)
    # qué pierna/brazo queda adelante: la A es la cercana en 0-4, la B en 5-9 (como en X)
    near_leg_a = p < 5
    leg_near = draw_leg(hip, fa if near_leg_a else fb, FOOT_ANG[p if near_leg_a else (p + 5) % N], False)
    leg_far = draw_leg(hip, fb if near_leg_a else fa, FOOT_ANG[(p + 5) % N if near_leg_a else p], True)
    arm_near = draw_arm(sh_near, hb if near_leg_a else ha, False)   # brazo opuesto a la pierna cercana
    arm_far = draw_arm(sh_far, ha if near_leg_a else hb, True)
    out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    for lay in (arm_far, leg_far, draw_body(p, bob), leg_near, draw_head(p, bob), arm_near):
        out.alpha_composite(lay)
    return out


if __name__ == "__main__":
    frames = [frame(p) for p in range(N)]
    tira = Image.new("RGBA", (CW * N, CH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        tira.paste(f, (i * CW, 0))
    tira.save(os.path.join(AQUI, "mago_correr.png"))
    S = 4
    gif = []
    for f in frames:
        g = Image.new("RGB", (CW, CH), (28, 28, 40))
        g.paste(f, (0, 0), f)
        gif.append(g.resize((CW * S, CH * S), Image.NEAREST))
    gif[0].save(os.path.join(AQUI, "mago_correr.gif"), save_all=True, append_images=gif[1:],
                loop=0, duration=int(1000 / 12), disposal=1)
    # comparación: X arriba, mago abajo, mismos cuadros
    x = Image.open(os.path.join(AQUI, "..", "sprites_x", "animaciones", "04_correr.png"))
    comp = Image.new("RGB", (CW * N * S, (CH * 2 + 4) * S), (28, 28, 40))
    for i in range(N):
        xf = x.crop((i * 34, 0, (i + 1) * 34, 35)).resize((34 * S, 35 * S), Image.NEAREST)
        comp.paste(xf, (i * CW * S + OX * S, 2 * S), xf)
        mf = frames[i].resize((CW * S, CH * S), Image.NEAREST)
        comp.paste(mf, (i * CW * S, (CH + 4) * S), mf)
    comp.save(os.path.join(AQUI, "comparacion.png"))
    print("ok")
