"""
МАЯК — reference short film for the pixel-art-video skill (~26 s, 16:9).

Logline: A storm kills the lighthouse lamp while a small boat is heading for
the rocks; the old keeper climbs up with a hand lantern and relights it.

Beats (hook -> setup -> turn -> climax -> payoff):
  1 night_sea   6s  storm, beam sweeping, tiny boat light on horizon  (hook/setup)
  2 blackout    5s  lightning, lamp dies, boat drifts toward rocks     (turn)
  3 keeper      6s  keeper walks through rain with a lantern           (response)
  4 relight     4s  lantern raised, lamp bursts back on                (climax)
  5 dawn        6s  calm sunrise, the boat passes safely; THE END      (payoff)

Run:  python lighthouse.py preview|stills 1,5,9|render|gif|wav [out_dir]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from pixelvid import *  # noqa

mv = Movie(320, 180, fps=24, scale=4, pal="pico8")
W, H = mv.w, mv.h
HORIZON = 118

LIGHTHOUSE = Sprite.from_ascii("""
....000....
...08880...
..0999990..
..0a9a9a0..
..0999990..
.000000000.
...07770...
...08880...
...07770...
...07770...
..0888880..
..0777770..
..0777770..
..0888880..
..0777770..
..0777770..
.078888870.
.077777770.
.077700770.
.077700770.
00000000000
""", {"0": "black", "8": "red", "9": "yellow", "a": "orange", "7": "white"})
LIGHTHOUSE = LIGHTHOUSE.scaled(2)  # hero prop: make it big enough to read
LAMP_OFF = LIGHTHOUSE.recolored({"yellow": "darkgray", "orange": "darkblue"})
LX, LY = 266, HORIZON - 9 - LIGHTHOUSE.h   # lighthouse top-left
LAMP = (LX + 11, LY + 6)                     # lamp centre

BOAT = Sprite.from_ascii("""
....7.....
....77....
....777...
....7777..
....7.....
444444444.
.4444444..
""", {"7": "white", "4": "brown"}).scaled(2)

keeper = humanoid(hair="lightgray", skin="peach", coat="darkgreen",
                  coat_shade="black", pants="darkgray", boots="brown", hood=False)
KWALK = [f.scaled(2) for f in keeper["walk"]]
KIDLE = keeper["idle"][0].scaled(2)


def draw_lantern(c, x, y, lit=True):
    c.px(x, y - 1, "darkgray")
    c.rect(x - 1, y, 3, 3, "orange" if lit else "darkgray")
    c.px(x, y + 1, "yellow" if lit else "black")


def cliff(c, x0):
    c.poly([(x0, HORIZON + 30), (x0 + 30, HORIZON - 8), (W + 5, HORIZON - 12),
            (W + 5, H), (x0 - 10, H)], "black")
    c.poly([(x0 + 30, HORIZON - 8), (W + 5, HORIZON - 12), (W + 5, HORIZON - 9),
            (x0 + 28, HORIZON - 5)], "darkgray")


def rocks(c, y, t):
    for i, (rx, rw, rh) in enumerate(((40, 16, 7), (60, 9, 5), (92, 12, 6))):
        c.poly([(rx - rw // 2, y), (rx - 2, y - rh), (rx + 3, y - rh + 1), (rx + rw // 2, y)], "black")
        c.line(rx - 2, y - rh, rx + 3, y - rh + 1, "darkgray")
        if int(t * 3 + i) % 2:  # foam
            c.line(rx - rw // 2 - 2, y, rx + rw // 2 + 2, y, "lightgray")


def beam(c, t, lx, ly, strength=0.35):
    ang = math.pi + math.sin(t * 0.9) * 0.45 - 0.05  # sweeps low over the sea
    L, spread = 260, 0.09
    p1 = (lx + math.cos(ang - spread) * L, ly + math.sin(ang - spread) * L * .25)
    p2 = (lx + math.cos(ang + spread) * L, ly + math.sin(ang + spread) * L * .25)
    c.dither_fill(c.mask_poly([(lx, ly), p1, p2]), "yellow", strength)


def storm_sky(c, t, lit=0.0):
    c.vgradient(0, HORIZON, ["black", "darkblue", "darkblue", "indigo"])
    clouds(c, t, "darkblue", shade="black", highlight="indigo", n=6, seed=4, y0=18, y1=50, speed=10, size=(18, 34))
    if lit:
        c.fade(lit * .6, "lightgray")


# ---------------------------------------------------------------- scenes
@mv.scene(6.0, fade_in=1.0)
def night_sea(c, x):
    t = x.t
    storm_sky(c, t)
    sea(c, HORIZON, t, "darkblue", light="indigo", highlight="lightgray", n=60)
    beam(c, t, *LAMP)
    cliff(c, 230)
    c.blit(LIGHTHOUSE, LX, LY)
    c.glow(*LAMP, 22, "yellow", .5)
    bx = 20 + t * 2
    by = HORIZON - 1 + round(math.sin(t * 2))
    c.px(bx, by, "yellow"); c.px(bx, by - 1, "orange")
    rain(c, t, "indigo", n=110, slant=.35)
    k = seg(t, 1.2, 2.4)  # title fades in by stepping through a palette ramp
    if k > 0 and t < 5.2:
        col = ramp(["darkblue", "indigo", "lightgray", "white"], k)
        c.text("МАЯК", 110, 60, col, align="center", scale=3, shadow="black")


@mv.scene(5.0)
def blackout(c, x):
    t = x.t
    flash = 1.0 - seg(t, 1.0, 1.35) if t >= 1.0 else 0.0
    storm_sky(c, t + 6, lit=flash)
    if 1.0 <= t < 1.25:
        lightning(c, 150, 0, HORIZON - 5, "white", seed=3, glow_col="lightgray")
    sea(c, HORIZON, t + 6, "darkblue", light="indigo", highlight="lightgray", n=60)
    on = t < 1.1 or (1.4 < t < 1.55) or (1.8 < t < 1.9)  # dies with a flicker
    if on:
        beam(c, t + 6, *LAMP)
    cliff(c, 230)
    c.blit(LIGHTHOUSE if on else LAMP_OFF, LX, LY)
    if on:
        c.glow(*LAMP, 22, "yellow", .5)
    rocks(c, HORIZON + 24, t)
    bx = keys(t, [(0, 32), (5, 70)], ease=lambda k: k)
    by = HORIZON + 8 + keys(t, [(0, 0), (5, 8)]) + round(math.sin(t * 2.5))
    c.blit(BOAT, bx, by - BOAT.h)
    c.px(bx + 9, by - 10, "yellow")
    rain(c, t + 6, "indigo", n=130, slant=.4)
    if not on:
        c.night(.55, lights=[(bx + 9, by - 10, 14)])
    c.shift(round(math.sin(t * 60) * 2) if 1.0 <= t < 1.4 else 0, 0)


@mv.scene(6.0, fade_in=0.4)
def keeper_walk(c, x):
    t = x.t
    c.vgradient(0, 110, ["black", "darkblue"])
    clouds(c, t, "darkblue", shade="black", highlight="indigo", n=5, seed=9, y0=12, y1=40, speed=12, size=(18, 34))
    # tower base on the right, door
    c.rect(250, 30, 50, 120, "lightgray")
    for yy in range(40, 150, 22):
        c.rect(250, yy, 50, 10, "red")
    c.rect(265, 118, 16, 30, "brown")
    c.px(278, 133, "yellow")
    # ground: grassy cliff path
    hills(c, 150, 8, "darkgreen", seed=2, scroll=0, rim="green")
    c.rect(0, 150, W, 30, "black")
    tree(c, 40, 150, 34, "brown", "darkgreen", shade="black", t=t)
    tree(c, 70, 152, 26, "brown", "darkgreen", shade="black", t=t)
    # the keeper walks from the left toward the tower door
    kx = keys(t, [(0, 10), (5.2, 262)], ease=lambda k: k)
    walking = t < 5.2
    fr = anim_frame(KWALK, t, fps=8) if walking else KIDLE
    c.blit_center(fr, kx, 151)
    hx, hy = keeper["hand"]
    lx, ly = kx - fr.w / 2 + hx * 2 + 1, 151 - fr.h + hy * 2 + 2
    c.rect(lx, ly - 2, 1, 2, "darkgray")          # lantern handle + body
    c.rect(lx - 2, ly, 5, 5, "orange"); c.rect(lx - 1, ly + 1, 3, 3, "yellow")
    rain(c, t, "indigo", n=120, slant=.3, splash="lightgray", ground=150)
    c.night(.65, lights=[(lx, ly + 2, 50)])
    c.glow(lx, ly + 2, 16, "orange", .3)


@mv.scene(4.0)
def relight(c, x):
    t = x.t
    c.clear("black")
    # lamp room interior close-up
    c.rect(0, 120, W, 60, "darkgray")
    for gx in range(0, W, 40):
        c.rect(gx, 0, 3, 120, "black")
    lampx, lampy = 205, 70
    lit = t > 2.0
    k = seg(t, 2.0, 2.6)
    c.circ(lampx, lampy, 22, "yellow" if lit else "darkgray")
    c.circ(lampx, lampy, 14, "white" if lit else "lightgray")
    c.rect(lampx - 26, lampy + 22, 52, 8, "brown")
    # keeper raises lantern (idle sprite scaled x3 for close-up)
    big = keeper["idle"][0].scaled(3)
    kx, ky = 90, 170
    c.blit_center(big, kx, ky)
    raise_k = ease_out(seg(t, 0.3, 1.6))
    sx, sy = kx + 2, ky - big.h + 26                 # shoulder
    lx, ly = lerp(sx + 10, sx + 20, raise_k), lerp(sy + 16, sy - 24, raise_k)  # arm ~22px
    c.line(sx, sy, lx, ly + 5, "black", width=6)     # arm outline
    c.line(sx, sy, lx, ly + 5, "darkgreen", width=4)
    c.rect(lx - 4, ly - 4, 9, 9, "orange"); c.rect(lx - 2, ly - 2, 5, 5, "yellow")
    if not lit:
        c.night(.8, lights=[(lx, ly, 45)])
        c.glow(lx, ly, 20, "orange", .35)
    else:
        c.glow(lampx, lampy, 30 + 130 * k, "yellow", .75 * (1.2 - k))
        c.glow(lampx, lampy, 40, "white", .5)
        c.fade(max(0, 1 - (t - 2.0) * 3), "white")


@mv.scene(6.0, fade_in=0.6, fade_out=1.8)
def dawn(c, x):
    t = x.t
    c.vgradient(0, HORIZON, ["darkpurple", "red", "orange", "peach"])
    sun_y = HORIZON + 6 - t * 2.5
    c.glow(160, sun_y, 50, "yellow", .45)
    c.circ(160, sun_y, 14, "yellow")
    clouds(c, t, "pink", shade="darkpurple", highlight="peach", n=4, seed=21, y0=25, y1=60, speed=3, size=(14, 28))
    c.rect(0, HORIZON, W, H - HORIZON, "darkblue")
    c.reflect(HORIZON, t, amp=1, factor=.55, tint=(0, 0, 30), level=.85)
    for i in range(30):  # sun glitter
        gy = HORIZON + 3 + i * 2
        if gy >= H:
            break
        if hrand(i, int(t * 4)) > .4:
            gx = 160 + (hrand(i, 5) - .5) * (10 + i * 2)
            c.line(gx - 2, gy, gx + 2, gy, "yellow")
    cliff(c, 230)
    c.blit(LIGHTHOUSE, LX, LY)
    c.glow(*LAMP, 14, "yellow", .4)
    bx = keys(t, [(0, 50), (6, 170)], ease=lambda k: k)
    c.blit(BOAT, bx, HORIZON + 5 - BOAT.h + round(math.sin(t * 2)))
    for i in range(3):  # gulls
        gx = (50 + i * 30 + t * 12) % W
        gy = 30 + i * 7 + math.sin(t * 2 + i) * 2
        wing = int(t * 6 + i) % 2
        c.px(gx, gy, "black")
        c.px(gx - 1, gy - wing, "black"); c.px(gx + 1, gy - wing, "black")
        c.px(gx - 2, gy - 1 + wing, "black"); c.px(gx + 2, gy - 1 + wing, "black")
    if t > 2.5:
        c.text("КОНЕЦ", W // 2, 150, "white", align="center", scale=2, shadow="darkpurple")


# ---------------------------------------------------------------- sound
def soundtrack():
    s = Song(bpm=84)
    # minor, melancholic lead (A minor -> F -> C -> G), 2 bars per chord
    s.track("A4 - - - C5 - B4 - A4 - - - E4 - - - | F4 - - - A4 - G4 - F4 - - - C4 - - - "
            "| C5 - - - E5 - D5 - C5 - - - G4 - - - | G4 - - - B4 - A4 - G4 - - - - - - -",
            wave="square", duty=.25, vol=.14, vibrato=.006, adsr=(.01, .2, .5, .15))
    s.track("A2 - - - A2 - - - A2 - - - A2 - - - | F2 - - - F2 - - - F2 - - - F2 - - - "
            "| C3 - - - C3 - - - C3 - - - C3 - - - | G2 - - - G2 - - - G2 - - - G2 - - -",
            wave="triangle", vol=.3)
    s.track("A3+C4+E4 - . . A3+C4+E4 - . . | F3+A3+C4 - . . F3+A3+C4 - . . "
            "| C4+E4+G4 - . . C4+E4+G4 - . . | G3+B3+D4 - . . G3+B3+D4 - . .",
            wave="square", duty=.5, vol=.05, cutoff=2500)
    s.ambience("rain", vol=.12, start=0, end=21.5, fade=1.5)
    s.ambience("sea", vol=.15)
    tb = mv.scene_start("blackout")
    s.sfx("thunder", at=tb + 1.0, vol=.7)
    tk = mv.scene_start("keeper_walk")
    for i in range(10):
        s.sfx("step", at=tk + i * 0.5, vol=.25)
    s.sfx("door", at=tk + 5.3, vol=.3)
    tr = mv.scene_start("relight")
    s.sfx("powerup", at=tr + 2.0, vol=.35)
    s.sfx("chime", at=mv.scene_start("dawn") + 2.5, vol=.3)
    return s


if __name__ == "__main__":
    main(mv, audio=soundtrack)
