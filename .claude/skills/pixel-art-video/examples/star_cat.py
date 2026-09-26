"""
ЗВЕЗДА — Бездомный кот находит на крыше упавшую звезду, но она гаснет
без неба; кот подбрасывает её обратно — и небо отвечает ему звездопадом.

Format: 23 s, 16:9, sweetie16, cozy lofi 80 bpm (Cmaj7-Am7-Dm7-G7).
Key image: the cat tossing the star back up into the sky.
Colour arc: cold night -> warm star-glow -> dimming -> cold sky full of light.

Beats:
  1 roof     5s  night roof, cat alone, title                          (hook)
  2 fall     4s  a star falls and lands next to the cat; cat jumps     (inciting)
  3 warm     5s  cat snuggles by the star; it slowly dims; a gap in sky (turn)
  4 toss     4s  cat crouches, jumps, the star flies home              (climax)
  5 shower   5s  the star rejoins the sky; a meteor shower; THE END    (payoff)
Run:  python film.py preview|stills 1,5,9|render|gif|wav [out_dir]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from pixelvid import *  # noqa

mv = Movie(320, 180, fps=24, scale=4, pal="sweetie16")
W, H = mv.w, mv.h
ROOF = 140
HOME = (70, 26)          # the star's place in the sky

CAT_LG = {"k": "black", "g": "slate", "l": "silver", "y": "yellow", "p": "red"}
CAT = Sprite.from_ascii("""
.k.......k.
kgk.....kgk
kggkkkkkggk
kgggggggggk
kggyggggygk
kggggpggggk
.kgggggggk.
..kgggggk..
.kgggggggk.
kggglllgggk
kggglllgggk
kgggggggggk
.kkkkkkkkk.
""", CAT_LG).scaled(3)   # hero must read clearly: ~33x39 px
CAT_BLINK = CAT.recolored({"yellow": "slate"})

STAR = Sprite.from_ascii("""
...y...
...y...
yyyyyyy
.yywyy.
..yyy..
.yy.yy.
.y...y.
""", {"y": "yellow", "w": "white"})


def roof(c, t):
    c.vgradient(0, ROOF, ["black", "navy", "navy", "purple"])
    stars(c, t, n=70, seed=2, cols=("white", "silver", "sky"), y_max=ROOF - 40)
    # layers get darker toward the viewer: far city -> near city -> our roof
    city(c, ROOF - 8, "darkslate", "orange", seed=5, t=t, min_h=20, max_h=55, lit=.2)
    city(c, ROOF + 4, "black", "yellow", seed=8, t=t, min_h=6, max_h=22, lit=.12, scroll=60)
    # foreground roof: ledge with lit rim, brick chimney, TV antenna
    c.rect(0, ROOF, W, H - ROOF, "black")
    c.rect(0, ROOF, W, 2, "slate"); c.rect(0, ROOF + 2, W, 1, "darkslate")
    c.rect(250, ROOF - 26, 14, 26, "darkslate"); c.rect(248, ROOF - 29, 18, 4, "slate")
    for by in range(ROOF - 22, ROOF, 6):
        c.line(251, by, 262, by, "black")
    c.line(40, ROOF, 40, ROOF - 34, "slate"); c.line(33, ROOF - 30, 47, ROOF - 30, "slate")
    c.line(35, ROOF - 24, 45, ROOF - 24, "slate")
    for i in range(3):  # chimney smoke puffs drifting up
        age = (t * .35 + i / 3) % 1
        c.dither_fill(c.mask_circle(257 + age * 10, ROOF - 32 - age * 30, 2 + age * 4), "slate", .5 * (1 - age))


def draw_cat(c, x, t, dy=0, squash=0.0, tail=True):
    spr = CAT_BLINK if (t % 3.7) < .12 else CAT
    if squash:
        spr = spr.squashed(squash)
    if tail:  # secondary motion: tail sways, lags behind the body
        sw = math.sin(t * 2.2) * 3
        u = CAT.w / 22  # tail geometry scales with the sprite
        pts = [(x + 10 * u, ROOF - 6 * u + dy), (x + 16 * u, ROOF - 10 * u + dy),
               (x + 18 * u + sw, ROOF - 18 * u + dy), (x + 16 * u + sw * 1.4, ROOF - 24 * u + dy)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            c.line(x0, y0, x1, y1, "black", width=int(4 * u) + 1)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            c.line(x0, y0, x1, y1, "slate", width=int(2 * u))
    c.blit_center(spr, x, ROOF + dy)


def draw_star(c, x, y, col_k=1.0, glow=.45, r=18):
    col = ramp(["slate", "orange", "yellow"], col_k)
    spr = STAR.recolored({"yellow": col, "white": "white" if col_k > .6 else col})
    c.glow(x, y, r, col, glow * col_k)
    c.blit(spr, x - 3, y - 3)


@mv.scene(5.0, fade_in=1.0)
def roof_alone(c, x):
    t = x.t
    roof(c, t)
    draw_cat(c, 145, t)
    k = seg(t, 1.0, 2.2)
    if 0 < k and t < 4.3:
        out = seg(t, 3.6, 4.3)
        col = ramp(["navy", "blue", "sky", "white"], k * (1 - out))
        c.text("ЗВЕЗДА", W // 2, 44, col, align="center", scale=3, shadow="black")


@mv.scene(4.0)
def fall(c, x):
    t = x.t
    roof(c, t + 5)
    land = (215, ROOF - 4)
    k = ease_in(seg(t, .4, 1.6))
    if t < 1.6:  # streak across the sky with a dithered trail
        sx, sy = lerp(HOME[0], land[0], k), lerp(HOME[1], land[1], k)
        for i in range(1, 14):
            kk = max(0, k - i * .012)
            c.dither_fill(c.mask_circle(lerp(HOME[0], land[0], kk), lerp(HOME[1], land[1], kk), 2),
                          "yellow", .8 - i * .05)
        if t > .4:
            draw_star(c, sx, sy)
    else:  # landed: small bounce
        b = 1 - bounce(seg(t, 1.6, 2.4))
        draw_star(c, land[0], land[1] - b * 10, r=26)
    # cat startles: anticipation squash -> jump back -> land
    j = seg(t, 1.65, 2.3)
    dy = -math.sin(j * math.pi) * 14 if 0 < j < 1 else 0
    sq = .2 if 1.55 < t < 1.7 else (-.15 if 0 < j < .5 else (.15 if .9 < j < 1.0 else 0))
    draw_cat(c, 145 - j * 14, t, dy=dy, squash=sq)
    if 1.6 <= t < 1.75:
        c.fade(.5, "white")
    c.shift(round(math.sin(t * 70) * 2) if 1.6 <= t < 1.9 else 0, 0)


@mv.scene(5.0)
def warm(c, x):
    t = x.t
    roof(c, t + 9)
    sx, sy = 215, ROOF - 4
    dim = seg(t, 2.2, 4.6)
    # cat hops closer twice, then sits by the star
    hop1, hop2 = seg(t, .3, .7), seg(t, .9, 1.3)
    cx = 131 + ease_in_out(hop1) * 24 + ease_in_out(hop2) * 22
    dy = -math.sin(hop1 * math.pi) * 6 - math.sin(hop2 * math.pi) * 6
    draw_cat(c, cx, t, dy=dy)
    draw_star(c, sx, sy, col_k=1 - dim * .75, r=24)
    # the empty place in the sky blinks, calling it home
    if dim > .2 and int(t * 3) % 2:
        c.dither_fill(c.mask_circle(*HOME, 4), "sky", .5)
    c.night(.15 + dim * .35, lights=[(sx, sy, 110 - dim * 50)])


@mv.scene(4.0)
def toss(c, x):
    t = x.t
    roof(c, t + 14)
    cx = 177
    # anticipation crouch, launch stretch, fall, landing squash
    crouch = seg(t, .2, .8)
    j = seg(t, .8, 1.5)
    dy = -math.sin(j * math.pi) * 24 if 0 < j < 1 else 0
    if t < .8:
        sq = .25 * ease_out(crouch)
    elif j < .5:
        sq = -.2
    elif j < 1:
        sq = 0
    else:
        sq = .2 * (1 - seg(t, 1.5, 1.8))
    draw_cat(c, cx, t, dy=dy, squash=sq)
    # the star rides the jump, then flies home, brightening
    fk = ease_in_out(seg(t, 1.15, 3.2))
    if t < 1.15:
        sx, sy = lerp(215, cx, seg(t, .8, 1.15)), ROOF - 4 + dy - (40 if t > .8 else 0) * seg(t, .8, 1.15)
        ck = .45
    else:
        sx = lerp(cx, HOME[0], fk)
        sy = lerp(ROOF - 44, HOME[1], fk) - math.sin(fk * math.pi) * 30
        ck = lerp(.45, 1.0, fk)
    draw_star(c, sx, sy, col_k=ck, r=18)
    c.night(.5 * (1 - fk), lights=[(sx, sy, 80)])


@mv.scene(5.0, fade_out=2.0)
def shower(c, x):
    t = x.t
    roof(c, t + 18)
    pulse = 1 - seg(t, 0, .8)
    c.glow(*HOME, 12 + pulse * 30, "white", .3 + pulse * .4)
    c.blit(STAR, HOME[0] - 3, HOME[1] - 3)
    for i in range(10):  # meteor shower answers
        st = .6 + i * .35
        k = seg(t, st, st + .6)
        if 0 < k < 1:
            x0, y0 = 120 + hrand(i, 1) * 200, 5 + hrand(i, 2) * 40
            hx, hy = x0 - k * 70, y0 + k * 35
            c.line(hx, hy, hx + 10, hy - 5, "sky")
            c.px(hx, hy, "white")
    draw_cat(c, 177, t)
    if t > 2.6:
        c.text("КОНЕЦ", W // 2, 70, ramp(["navy", "sky", "white"], seg(t, 2.6, 3.2)),
               align="center", scale=2, shadow="black")


def soundtrack():
    s = Song(bpm=80)
    s.track("E5 - - - G5 - - - B5 - - - A5 - G5 - | E5 - - - C5 - - - E5 - - - D5 - C5 - "
            "| D5 - - - F5 - - - A5 - - - G5 - F5 - | D5 - - - B4 - - - G4 - - - . . . .",
            wave="square", duty=.125, vol=.11, vibrato=.005, adsr=(.01, .15, .45, .12), start=1.0)
    s.track("C4+E4+G4+B4 - - - - - - - - - - - - - - - | A3+C4+E4+G4 - - - - - - - - - - - - - - - "
            "| D4+F4+A4+C5 - - - - - - - - - - - - - - - | G3+B3+D4+F4 - - - - - - - - - - - - - - -",
            wave="square", duty=.5, vol=.045, cutoff=2200, adsr=(.02, .3, .6, .2))
    s.track("C3 - - - - - - - C3 - - - G2 - - - | A2 - - - - - - - A2 - - - E2 - - - "
            "| D3 - - - - - - - D3 - - - A2 - - - | G2 - - - - - - - G2 - - - D3 - - -",
            wave="triangle", vol=.28)
    s.drums("h . . . h . . . h . . . h . h .", vol=.08, start=5.0)
    s.ambience("wind", vol=.05)
    s.ambience("crowd", vol=.02)       # distant city murmur
    f = mv.scene_start("fall")
    s.sfx("whoosh", at=f + .5, vol=.35)
    s.sfx("hit", at=f + 1.6, vol=.3)
    s.sfx("chime", at=f + 1.62, vol=.35)
    s.sfx("jump", at=f + 1.65, vol=.2)
    w = mv.scene_start("warm")
    s.sfx("step", at=w + .3, vol=.2); s.sfx("step", at=w + .9, vol=.2)
    s.sfx("heartbeat", at=w + 3.0, vol=.35); s.sfx("heartbeat", at=w + 3.9, vol=.3)
    tt = mv.scene_start("toss")
    s.sfx("jump", at=tt + .8, vol=.3)
    s.sfx("powerup", at=tt + 1.2, vol=.28)
    sh = mv.scene_start("shower")
    s.sfx("chime", at=sh, vol=.4)
    for i in range(0, 10, 3):
        s.sfx("blip", at=sh + .6 + i * .35, vol=.08)
    return s


if __name__ == "__main__":
    main(mv, audio=soundtrack)
