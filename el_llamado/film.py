"""
EL LLAMADO — Un caballero cansado se pone la armadura pieza por pieza y sale a
una batalla que ya empezó sin él.

Beats:
  1 intro     4.0s  sala del castillo de noche, antorcha, título
  2 sacar    10.0s  abre el cofre y deja 4 piezas en la mesa
  3 suspiro   4.5s  primer plano: mira al techo y suspira
  4 vestirse  8.0s  se pone peto, grebas, yelmo y escudo
  5 puerta    8.0s  abre la puerta: caos afuera; sale y la puerta se cierra
  6 final     4.5s  sala vacía, ruido amortiguado, FIN
Run:  .venv/bin/python el_llamado/film.py preview|stills 1,5,9|render|gif [out_dir]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                                ".claude", "skills", "pixel-art-video", "scripts"))
from pixelvid import *  # noqa

mv = Movie(320, 180, fps=24, scale=4, pal="pico8")
W, H = mv.w, mv.h
FLOOR = 150
MAN_X = 108
LIN = lambda k: k  # noqa: E731  linear ease


# ---------------------------------------------------------------- characters
def make_man(stage):
    kw = dict(hair="brown", skin="peach", coat="darkpurple", coat_shade="black",
              pants="brown", pants_back="black", boots="black")
    if stage >= 1:  # peto
        kw.update(coat="lightgray", coat_shade="darkgray")
    if stage >= 2:  # grebas
        kw.update(pants="lightgray", pants_back="darkgray", boots="darkgray")
    if stage >= 3:  # yelmo
        kw.update(hood=True)
    h = humanoid(**kw)
    return {"idle": [f.scaled(3) for f in h["idle"]],
            "walk": [f.scaled(3) for f in h["walk"]]}


MEN = [make_man(s) for s in range(5)]          # stage 4 = 3 + escudo
SIL = [f.silhouette("black") for f in humanoid()["walk"]]  # peleadores lejanos

ARMOR_LEG = {"7": "lightgray", "6": "darkgray", "0": "black", "8": "red", "9": "yellow"}
PIECES = [
    Sprite.from_ascii("""
77...77
7777777
7767677
.77677.
.77777.
..777..
""", ARMOR_LEG),                                   # peto
    Sprite.from_ascii("""
77..77
77..77
67..67
77..77
777.777
""", ARMOR_LEG),                                   # grebas
    Sprite.from_ascii("""
..777..
.77777.
7777777
7700077
7777777
.7...7.
""", ARMOR_LEG),                                   # yelmo
    Sprite.from_ascii("""
8888888
8889888
8999998
8889888
.88988.
..888..
...8...
""", ARMOR_LEG),                                   # escudo
]
PIECES = [p.scaled(2).outlined("black") for p in PIECES]
SHIELD_SMALL = PIECES[3]

CHEST_MOUTH = (58, 130)
SLOTS = [147, 160, 173, 187]
TABLE_Y = 126
# where each piece lands on the man (bottom-centre)
BODY = [(MAN_X, 134), (MAN_X, 148), (MAN_X, 117), (MAN_X + 10, 138)]


def arc(k, a, b, hgt=26):
    k = ease_in_out(clamp(k))
    return lerp(a[0], b[0], k), lerp(a[1], b[1], k) - math.sin(math.pi * k) * hgt


def draw_man(c, stage, x, t, walking=False, flip=False, silhouette=False):
    frames = MEN[min(stage, 3)]
    fr = anim_frame(frames["walk"], t, fps=8) if walking else anim_frame(frames["idle"], t, fps=4)
    if silhouette:
        fr = fr.silhouette("black")
    c.blit_center(fr, x, FLOOR, flip=flip)
    if stage >= 4 and not silhouette:
        c.blit_center(SHIELD_SMALL, x + (-10 if flip else 10), 138)


# ---------------------------------------------------------------- room
DX0, DY0, DW, DH = 262, 88, 32, 62
TORCHES = [(125, 88), (245, 88)]


def chaos(t, w, h):
    s = Canvas(w, h, mv.pal)
    s.vgradient(0, h, ["black", "darkpurple", "red", "orange"])
    for i, fx in enumerate((5, 18, 28)):
        fire(s, fx, h - 16, t + i, w=9, h=18, seed=13 + i)
    s.rect(0, h - 12, w, 12, "black")
    for i in range(4):
        fr = anim_frame(SIL, t + i * .3, fps=10)
        fx = i * 9 + pingpong(t * 1.5 + i * .7, 1) * 10 - 6
        s.blit_center(fr, fx, h - 9, flip=(i % 2 == 1))
        if hrand(i, int(t * 8)) > .72:  # choque de espadas
            s.line(fx + 3, h - 22, fx + 9, h - 29, "white")
    for i in range(3):  # flechas
        ax = (t * 90 + i * 17) % (w + 20) - 10
        s.line(ax, 8 + i * 9, ax + 5, 7 + i * 9, "lightgray")
    embers(s, t, cols=("yellow", "orange"), n=20, box=(0, 0, w, h), rise=25)
    if hrand(7, int(t * 6)) > .85:
        s.fade(.5, "white")
    return s


def door(c, t, o):
    c.rect(DX0 - 4, DY0 - 4, DW + 8, DH + 4, "lightgray")
    c.rect(DX0, DY0, DW, DH, "black")
    ow = int(round(DW * o))
    if ow > 0:
        sub = chaos(t, DW, DH)
        c.img.paste(sub.img.crop((0, 0, ow, DH)), (DX0, DY0))
    lw = DW - ow
    if lw > 0:
        x = DX0 + ow
        c.rect(x, DY0, lw, DH, "brown")
        for px_ in range(x + 5, x + lw - 1, 6):
            c.line(px_, DY0, px_, DY0 + DH - 1, "darkpurple")
        c.rect(x, DY0 + 10, lw, 3, "darkgray")
        c.rect(x, DY0 + DH - 14, lw, 3, "darkgray")
        if lw > 10:
            c.rect(x + 3, DY0 + 33, 2, 3, "yellow")


def chest(c, open_):
    if open_:
        c.rect(40, 110, 36, 16, "brown")          # tapa levantada
        c.rect(40, 110, 36, 2, "yellow")
        c.rect(40, 125, 36, 3, "black")           # boca del cofre
    c.rect(38, 126 if not open_ else 128, 40, 22 if open_ else 24, "brown")
    if not open_:
        c.rect(38, 126, 40, 3, "yellow")
    c.rect(38, 140, 40, 2, "yellow")
    c.rect(55, 131, 6, 5, "yellow")
    c.px(58, 133, "black")


def table(c):
    c.rect(140, TABLE_Y, 56, 4, "brown")
    c.line(140, TABLE_Y + 4, 195, TABLE_Y + 4, "darkpurple")
    c.rect(143, TABLE_Y + 4, 4, FLOOR - TABLE_Y - 4, "brown")
    c.rect(189, TABLE_Y + 4, 4, FLOOR - TABLE_Y - 4, "brown")


def room(c, t, o=0.0, chest_open=True, window_fire=0.3):
    c.rect(0, 0, W, FLOOR, "darkgray")
    for r, y in enumerate(range(0, FLOOR, 10)):
        c.line(0, y, W, y, "darkblue")
        for x in range((r % 2) * 10, W, 20):
            c.line(x, y, x, y + 9, "darkblue")
    c.rect(0, FLOOR, W, H - FLOOR, "black")
    for x in range(0, W, 24):
        c.line(x, FLOOR + 1, x - 12, H, "darkblue")
    c.line(0, FLOOR, W, FLOOR, "darkgray")
    # estandarte
    c.rect(18, 18, 16, 50, "red")
    c.poly([(18, 68), (26, 60), (34, 68)], "darkgray")
    c.rect(24, 30, 4, 16, "yellow"); c.rect(20, 35, 12, 4, "yellow")
    # ventana con resplandor de incendios lejanos
    c.rect(188, 34, 22, 36, "black")
    c.vgradient(36, 68, ["black", "darkblue"], x0=190, x1=208)
    for i in range(5):
        c.px(192 + i * 3, 40 + (i * 7) % 12, "lightgray")
    lvl = window_fire * (0.6 + 0.4 * hrand(3, int(t * 7)))
    c.dither_rect(190, 56, 18, 12, "orange", lvl)
    c.dither_rect(190, 62, 18, 6, "red", lvl)
    c.line(199, 36, 199, 68, "black"); c.line(190, 52, 208, 52, "black")
    # antorchas
    for i, (tx, ty) in enumerate(TORCHES):
        c.rect(tx - 1, ty + 2, 3, 8, "brown")
        fire(c, tx, ty + 2, t + i, w=6, h=12, seed=20 + i)
    chest(c, chest_open)
    table(c)
    door(c, t, o)


def lighting(c, t, o=0.0):
    flick = 4 * math.sin(t * 13) + 3 * math.sin(t * 7.3)
    lights = [(tx, ty, 95 + flick) for tx, ty in TORCHES]
    if o > 0:
        lights.append((DX0 + DW // 2, DY0 + DH // 2, 80 * o))
    c.night(.42, lights=lights)
    for tx, ty in TORCHES:
        c.glow(tx, ty, 16, "orange", .3)
    if o > 0:
        c.glow(DX0 + DW // 2, DY0 + DH // 2, 60, "orange", .3 * o)


# ---------------------------------------------------------------- scenes
@mv.scene(4.0, fade_in=1.0)
def intro(c, x):
    t = x.t
    room(c, t, chest_open=False)
    draw_man(c, 0, MAN_X, t, flip=True)
    lighting(c, t)
    k = seg(t, .8, 1.8)
    if k and t < 3.6:
        c.text("EL LLAMADO", W // 2, 20, ramp(["darkblue", "indigo", "lightgray", "white"], k),
               align="center", scale=2, shadow="black")


def take_times(i):
    s = 1.0 + i * 2.2
    return s, s + .5, s + 1.6


@mv.scene(10.0)
def sacar(c, x):
    t = x.t
    room(c, t, chest_open=t > .4)
    facing_chest = t < 1.0
    for i, p in enumerate(PIECES):
        s0, s1, s2 = take_times(i)
        hand = (MAN_X - 4, 118)
        if t < s0:
            continue
        if t < s1:
            px_, py_ = arc(seg(t, s0, s1), CHEST_MOUTH, hand, hgt=6)
            facing_chest = True
        elif t < s2:
            px_, py_ = arc(seg(t, s1, s2), hand, (SLOTS[i], TABLE_Y))
        else:
            px_, py_ = SLOTS[i], TABLE_Y
        c.blit_center(p, px_, py_)
    draw_man(c, 0, MAN_X, t, flip=facing_chest)
    lighting(c, t)


@mv.scene(4.5)
def suspiro(c, x):
    t = x.t
    # pared en primer plano: ladrillos grandes
    c.rect(0, 0, W, H, "darkgray")
    for r, y in enumerate(range(0, H, 24)):
        c.line(0, y, W, y, "darkblue")
        for xx in range((r % 2) * 24, W, 48):
            c.line(xx, y, xx, y + 23, "darkblue")
    up = 1.0 <= t < 3.2
    tilt = 3 if up else 0
    drop = keys(t, [(1.2, 0), (1.7, -3), (2.4, 4), (4.5, 4)])
    open_ = 1.8 <= t < 3.0
    blink = 0.55 < t < 0.7
    spr = face(up, open_, blink)
    top = 26 + drop * .5 - tilt
    # cuerpo (túnica)
    by = 112 + drop
    c.poly([(90, H), (112, by), (208, by), (230, H)], "darkpurple")
    c.poly([(140, by), (160, by + 14), (180, by)], "black")
    c.blit(spr, 160 - spr.w // 2, top)
    # vapor del suspiro
    for i in range(3):
        k = seg(t, 2.0 + i * .25, 3.3 + i * .25)
        if 0 < k < 1:
            c.dither_fill(c.mask_circle(160 + i * 4, top + 66 - k * 30, 4 + k * 8), "lightgray", .45 * (1 - k))
    if 1.9 < t < 3.6:
        c.text(typewriter("UFFF...", t - 1.9, 10), 214, 52, "white", scale=2, shadow="black")
    c.night(.5, lights=[(160, 70, 120)])
    c.glow(290, 10, 40, "orange", .25)


_FACE = [
    "...hhhhhh...",
    "..hhhhhhhh..",
    ".hhhhhhhhhh.",
    ".hssssssssh.",
    ".sbbssssbbs.",
    ".sWWssssWWs.",
    ".sPPssssPPs.",
    ".sWWssssWWs.",
    ".ssssddssss.",
    ".ssssssssss.",
    ".sssmmmmsss.",
    "..ssssssss..",
    "...ssssss...",
    "....ssss....",
]
_FACE_LEG = {"h": "brown", "s": "peach", "b": "black", "W": "white", "P": "black",
             "d": "orange", "m": "darkpurple"}


def face(up, open_, blink):
    rows = list(_FACE)
    if up:  # pupilas arriba, cejas levantadas
        rows[3], rows[4] = ".hbbssssbbh.", ".ssssssssss."
        rows[5], rows[6] = ".sPPssssPPs.", ".sWWssssWWs."
    if blink:
        rows[5] = rows[6] = rows[7] = ".ssssssssss."
        rows[6] = ".sbbssssbbs."
    if open_:
        rows[10], rows[11] = ".ssssmmssss.", "..sssmmsss.."
    return Sprite.from_ascii(rows, _FACE_LEG).scaled(6)


def dress_times(i):
    s = .6 + i * 1.7
    return s, s + 1.0


@mv.scene(8.0)
def vestirse(c, x):
    t = x.t
    room(c, t)
    stage = 0
    for i, p in enumerate(PIECES):
        s0, s1 = dress_times(i)
        if t < s0:
            c.blit_center(p, SLOTS[i], TABLE_Y)
        elif t < s1:
            px_, py_ = arc(seg(t, s0, s1), (SLOTS[i], TABLE_Y), BODY[i], hgt=22)
            c.blit_center(p, px_, py_)
        else:
            stage = i + 1
    draw_man(c, stage, MAN_X, t)
    lighting(c, t)
    for i in range(4):  # destello al encajar cada pieza
        s1 = dress_times(i)[1]
        if s1 <= t < s1 + .15:
            c.glow(*BODY[i], 12, "white", .6)
    if 7.0 <= t < 7.25:  # brillo final en el yelmo
        c.glow(MAN_X + 3, 106, 8, "white", .8)


@mv.scene(8.0)
def puerta(c, x):
    t = x.t
    o = keys(t, [(0, 0), (2.6, 0), (3.2, .85), (5.6, .85), (6.2, 0)])
    room(c, t, o)
    if t < 2.5:
        draw_man(c, 4, keys(t, [(0, MAN_X), (2.5, 250)], ease=LIN), t, walking=True)
    elif t < 4.4:
        draw_man(c, 4, 250, t)
    elif t < 5.0:
        k = seg(t, 4.4, 5.0)
        draw_man(c, 4, lerp(250, 278, k), t, walking=True, silhouette=k > .6)
    lighting(c, t, o)
    if o > .3 and hrand(int(t * 10)) > .6:
        c.shift(round(math.sin(t * 50)), 0)
    if 6.2 <= t < 6.35:  # portazo
        c.shift(0, 1)


@mv.scene(4.5, fade_out=1.8)
def final(c, x):
    t = x.t
    room(c, t, window_fire=.6)
    lighting(c, t)
    if t > 1.2:
        c.text("FIN", 100, 40, ramp(["darkblue", "indigo", "lightgray", "white"], seg(t, 1.2, 2.0)),
               align="center", scale=3, shadow="black")


# ---------------------------------------------------------------- sound
def soundtrack():
    s = Song(bpm=76)
    s.track("D5 - - - F5 - E5 - D5 - - - A4 - - - | Bb4 - - - D5 - C5 - Bb4 - - - F4 - - - "
            "| G4 - - - Bb4 - A4 - G4 - - - D4 - - - | A4 - - - C#5 - B4 - A4 - - - - - - -",
            wave="square", duty=.125, vol=.12, vibrato=.006, adsr=(.01, .2, .5, .15))
    s.track("D3 - - - D3 - - - D3 - - - D3 - - - | Bb2 - - - Bb2 - - - Bb2 - - - Bb2 - - - "
            "| G2 - - - G2 - - - G2 - - - G2 - - - | A2 - - - A2 - - - A2 - - - A2 - - -",
            wave="triangle", vol=.3)
    s.track("D4+F4+A4 - . . D4+F4+A4 - . . | Bb3+D4+F4 - . . Bb3+D4+F4 - . . "
            "| G3+Bb3+D4 - . . G3+Bb3+D4 - . . | A3+C#4+E4 - . . A3+C#4+E4 - . .",
            wave="square", duty=.5, vol=.045, cutoff=2500)
    s.ambience("crowd", vol=.04)            # batalla lejana, amortiguada
    s.ambience("wind", vol=.05)
    ts = mv.scene_start("sacar")
    s.sfx("door", at=ts + .3, vol=.35)       # tapa del cofre
    for i in range(4):
        s.sfx("hit", at=ts + take_times(i)[2], vol=.2)
    s.sfx("whoosh", at=mv.scene_start("suspiro") + 2.0, vol=.35)
    tv = mv.scene_start("vestirse")
    for i in range(4):
        s.sfx("hit", at=tv + dress_times(i)[1], vol=.3)
        s.sfx("blip", at=tv + dress_times(i)[1] + .05, vol=.12)
    s.sfx("chime", at=tv + 7.0, vol=.2)
    tp = mv.scene_start("puerta")
    for i in range(7):
        s.sfx("step", at=tp + i * .36, vol=.22)
    s.sfx("door", at=tp + 2.6, vol=.4)
    s.drums("k . k s k . k s k k . s k . s s", vol=.35, start=tp + 2.7, end=tp + 6.2)
    s.ambience("crowd", vol=.4, start=tp + 2.7, end=tp + 6.2, fade=.3)
    for dt in (3.0, 3.4, 3.9, 4.3, 4.8, 5.3):
        s.sfx("hit", at=tp + dt, vol=.3)
    s.sfx("explosion", at=tp + 3.6, vol=.4)
    s.sfx("step", at=tp + 4.5, vol=.22); s.sfx("step", at=tp + 4.85, vol=.22)
    s.sfx("door", at=tp + 6.1, vol=.45)
    s.sfx("hit", at=tp + 6.2, vol=.5)       # portazo
    return s


if __name__ == "__main__":
    main(mv, audio=soundtrack)
