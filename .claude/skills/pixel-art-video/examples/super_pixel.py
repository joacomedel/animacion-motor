"""
СУПЕР ПИКСЕЛЬ — original platformer-style short (NES-era look, not a copy of any game).

Logline: A tiny runner speeds through World 1-1, misjudges a pit and loses a
life — then on the second try grabs a star, becomes unstoppable and reaches the flag.

Format: 36 s, 16:9, pico8, original chiptune at 150 bpm (C major), NES-like HUD.
Key image: the rainbow-flashing hero sailing over the pit on the second try.
Structure: title -> world card -> attempt 1 (fail) -> world card -> attempt 2 (win) -> clear.

Beats:
  1 title   4s  logo, "press start", hero idle, beetle patrol      (hook)
  2 card1   2s  WORLD 1-1, lives x3                               (setup)
  3 run1   10s  coin block, pipe, stomp, short hop -> falls in pit (failure)
  4 card2   2s  WORLD 1-1, lives x2                               (stakes)
  5 run2   12s  star block -> invincible, kick beetle, big jump, flagpole (climax)
  6 clear   6s  fireworks, time bonus counts into score           (payoff)
Run:  python film.py preview|stills 1,5,9|render|gif|wav [out_dir]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from pixelvid import *  # noqa

mv = Movie(320, 180, fps=24, scale=4, pal="pico8")
W, H = mv.w, mv.h
G = 148                     # ground line (feet y)
BLOCK_Y = 84                # top of the floating block row
PIT = (600, 660)
PIPE = (360, 32, 36)        # x, w, h
POLE_X = 880
TOWER_X = 930
CAM_MAX = 1040 - W

# ------------------------------------------------------------------ sprites
HERO_LG = {"w": "white", "r": "red", "h": "brown", "s": "peach", "e": "black",
           "j": "darkpurple", "p": "darkblue", "b": "brown"}
TOP = ["...wwww...", "..wwwwww..", "..rrrrrrrr", "..hhssess.", "..hsssss..",
       "...ssss...", "..jjjjjj..", ".jjjjjjjj.", ".sjjjjjjs."]
TOP_JUMP = ["...wwww..s", "..wwwwww.s", "..rrrrrrrr", "..hhssessj", "..hsssssj.",
            "...ssssj..", "..jjjjjj..", ".jjjjjjjj.", "sjjjjjjj.."]
LEGS = {
    "stand": ["..pppppp..", "..pppppp..", "..pp..pp..", "..pp..pp..", ".bbb..bbb."],
    "a": ["..pppppp..", ".pppppppp.", ".pp....pp.", "pp......pp", "bb......bb"],
    "c": ["..pppppp..", "..ppppppp.", "..pp...pp.", ".pp....pp.", ".bb....bb."],
    "b": ["..pppppp..", "...ppppp..", "....pp....", "....pp....", "....bbb..."],
    "jump": ["..pppppp..", ".ppppppp..", ".pp...pp..", "bb.....pp.", ".......bb."],
}


def hero_sprite(top, legs):
    return Sprite.from_ascii(top + LEGS[legs], HERO_LG).outlined("black")


STAND = hero_sprite(TOP, "stand")
RUN = [hero_sprite(TOP, k) for k in ("a", "c", "b", "c")]
JUMP = hero_sprite(TOP_JUMP, "jump")
FLASH = [{"darkpurple": "red", "darkblue": "orange"},        # star-power colour cycle
         {"darkpurple": "white", "darkblue": "pink"},
         {"darkpurple": "yellow", "darkblue": "green"}, {}]

BEETLE_LG = {"k": "black", "b": "brown", "w": "white"}
BEETLE_TOP = ["....kkkk....", "..kkbbbbkk..", ".kbbbbbbbbk.", "kbbwkbbwkbbk",
              "kbbwkbbwkbbk", "kbbbbbbbbbbk", ".kbbbbbbbbk.", "..kkkkkkkk.."]
BEETLE = [Sprite.from_ascii(BEETLE_TOP + [".kk......kk."], BEETLE_LG),
          Sprite.from_ascii(BEETLE_TOP + ["..kk....kk.."], BEETLE_LG)]
BEETLE_FLAT = Sprite.from_ascii(["..kkkkkkkk..", ".kbbwkkwbbk.", "kkkkkkkkkkkk"], BEETLE_LG)

STAR = Sprite.from_ascii(["....y....", "...yyy...", "yyyyyyyyy", ".yykykyy.", "..yyyyy..",
                          "..yyyyy..", ".yyy.yyy.", ".yy...yy."], {"y": "yellow", "k": "black"})


def star_sprite(t):
    return STAR.recolored({"yellow": ramp(["yellow", "white", "orange"], (t * 8) % 1)})


# ------------------------------------------------------------------ world drawing
def ground_tile(c, x, y):
    c.rect(x, y, 16, 16, "brown")
    c.rect(x, y, 16, 1, "peach"); c.rect(x, y, 1, 16, "orange")
    c.rect(x, y + 15, 16, 1, "darkpurple"); c.rect(x + 15, y, 1, 16, "darkpurple")
    c.line(x + 3, y + 5, x + 7, y + 5, "darkpurple"); c.line(x + 9, y + 10, x + 12, y + 10, "darkpurple")


def brick(c, x, y):
    c.rect(x, y, 16, 16, "brown")
    c.rect(x, y, 16, 1, "orange")
    for yy in (0, 8):
        c.line(x, y + yy + 7, x + 15, y + yy + 7, "black")
    for xx in (0, 8):
        c.line(x + xx + 7, y, x + xx + 7, y + 6, "black")
        c.line(x + ((xx + 4) % 16) + 3, y + 8, x + ((xx + 4) % 16) + 3, y + 14, "black")


def star_block(c, x, y, t, used):
    c.rect(x, y, 16, 16, "black")
    if used:
        c.rect(x + 1, y + 1, 14, 14, "brown")
        for px_, py_ in ((3, 3), (12, 3), (3, 12), (12, 12)):
            c.px(x + px_, y + py_, "black")
        return
    col = ramp(["orange", "yellow", "orange", "brown"], (t * 1.2) % 1)  # shimmer
    c.rect(x + 1, y + 1, 14, 14, col)
    c.rect(x + 1, y + 1, 14, 1, "peach")
    c.blit(STAR.recolored({"yellow": "white" if col != "yellow" else "orange"}), x + 4, y + 4)
    for px_, py_ in ((2, 2), (13, 2), (2, 13), (13, 13)):
        c.px(x + px_, y + py_, "brown")


def pipe(c, sx, w, h):
    top = G - h
    c.rect(sx + 2, top + 10, w - 4, h - 10, "black")
    c.rect(sx + 3, top + 10, w - 6, h - 10, "green")
    c.rect(sx + 6, top + 10, 3, h - 10, "white"); c.rect(sx + w - 9, top + 10, 5, h - 10, "darkgreen")
    c.rect(sx, top, w, 11, "black")
    c.rect(sx + 1, top + 1, w - 2, 9, "green")
    c.rect(sx + 4, top + 1, 3, 9, "white"); c.rect(sx + w - 8, top + 1, 6, 9, "darkgreen")


def hill(c, x, r, col="green", edge="darkgreen"):
    c.ellipse(x, G, r + 1, r * .7 + 1, edge)
    c.ellipse(x, G, r, r * .7, col)
    for i, (dx, dy) in enumerate(((-r * .3, -r * .35), (r * .15, -r * .45), (r * .35, -r * .2))):
        c.rect(x + dx, G + dy, 2, 3, edge)


def bush(c, x):
    for dx, r in ((-10, 7), (0, 10), (10, 7)):
        c.circ(x + dx, G - 3, r + 1, "darkgreen")
    for dx, r in ((-10, 7), (0, 10), (10, 7)):
        c.circ(x + dx, G - 3, r, "green")
    c.px(x - 3, G - 9, "white"); c.px(x + 7, G - 6, "white")


BLOCKS = [(200, "star"), (216, "brick"), (232, "star"), (248, "brick")]


def draw_world(c, cam, t, hits=None, flag_y=52, tower_flag=0.0):
    """hits: {block_x: local time it was bumped}."""
    hits = hits or {}
    c.clear("blue")
    clouds(c, (t - cam * .3) / 4, "white", shade="lightgray", n=5, seed=12, y0=30, y1=62,
           speed=4, size=(14, 24))
    for hx, r in ((80, 60), (330, 36), (520, 64), (820, 40), (1050, 58)):
        hill(c, hx - cam * .5, r)
    for bx in (150, 470, 760, 1010):
        bush(c, bx - cam)
    # ground (with the pit)
    for tx in range(int(cam // 16) * 16, int(cam) + W + 16, 16):
        if PIT[0] <= tx < PIT[1]:
            continue
        ground_tile(c, tx - cam, G); ground_tile(c, tx - cam, G + 16)
    # floating blocks
    for bx, kind in BLOCKS:
        th = hits.get(bx)
        bump = -round(5 * math.sin(math.pi * seg(t, th, th + .2))) if th is not None else 0
        if kind == "brick":
            brick(c, bx - cam, BLOCK_Y + bump)
        else:
            star_block(c, bx - cam, BLOCK_Y + bump, t, used=th is not None and t >= th)
    pipe(c, PIPE[0] - cam, PIPE[1], PIPE[2])
    # flagpole on its base block
    px_ = POLE_X - cam
    star_block(c, px_ - 8, G - 16, t, used=True)
    c.rect(px_ - 1, 48, 2, G - 16 - 48, "lightgray"); c.px(px_, 48, "white")
    c.circ(px_, 46, 3, "black"); c.circ(px_, 46, 2, "green")
    c.poly([(px_ - 1, flag_y), (px_ - 17, flag_y + 7), (px_ - 1, flag_y + 14)], "white")
    c.circ(px_ - 6, flag_y + 7, 2, "green")
    # tower
    tx = TOWER_X - cam
    for yy in range(G - 56, G, 16):
        for xx in range(0, 80, 16):
            brick(c, tx + xx, yy)
    for xx in range(0, 80, 32):  # battlements
        brick(c, tx + xx, G - 72)
    c.rect(tx + 32, G - 26, 16, 26, "black"); c.circ(tx + 39, G - 26, 8, "black")
    c.rect(tx + 12, G - 46, 6, 10, "black"); c.rect(tx + 62, G - 46, 6, 10, "black")
    if tower_flag:
        fy = G - 72 - tower_flag * 22
        c.rect(tx + 39, fy, 1, G - 72 - fy, "lightgray")
        c.poly([(tx + 40, fy), (tx + 52, fy + 4), (tx + 40, fy + 8)], "red")


def draw_hero(c, x, y, frame, flash_t=None, flip=False):
    spr = frame
    if flash_t is not None:
        spr = frame.recolored(FLASH[int(flash_t / .07) % len(FLASH)])
    c.blit_center(spr, x, y, flip=flip)


def coin(c, x, y, t):
    w = (3, 2, 1, 2)[int(t * 12) % 4]
    c.ellipse(x, y, w, 5, "black")
    c.ellipse(x, y, max(0, w - 1), 4, "yellow")
    if w > 1:
        c.line(x, y - 2, x, y + 2, "orange")


# ------------------------------------------------------------------ HUD / score
EVENTS = []   # (global T, score, coins) filled in after scenes are placed


def score_at(T):
    return sum(e[1] for e in EVENTS if e[0] <= T), sum(e[2] for e in EVENTS if e[0] <= T)


def hud(c, T, timer):
    s, k = score_at(T)
    cols = [(14, "ПИКСЕЛЬ", f"{s:06d}"), (110, "МОНЕТЫ", f"X{k:02d}"),
            (190, "МИР", "1-1"), (260, "ВРЕМЯ", f"{int(timer):03d}" if timer is not None else "")]
    for x, lab, val in cols:
        c.text(lab, x, 6, "white", shadow="black")
        c.text(val, x, 16, "white", shadow="black")
    if int(T * 3) % 3:  # blinking coin icon
        coin(c, 104, 19, T)


def jump_y(t, jumps, base=G):
    """jumps: [(t0, dur, height, y_from, y_to)] -> feet y (and whether airborne)."""
    for t0, dur, h, y0, y1 in jumps:
        if t0 <= t < t0 + dur:
            k = (t - t0) / dur
            return lerp(y0, y1, k) - 4 * h * k * (1 - k), True
    last = None
    for j in jumps:
        if t >= j[0] + j[1]:
            last = j[4]
    return (last if last is not None else base), False


# ------------------------------------------------------------------ scenes
@mv.scene(4.0, fade_out=.4)
def title(c, x):
    t = x.t
    draw_world(c, 0, t)
    hud(c, x.T, None)
    c.rect(58, 32, 204, 68, "black")
    c.rect(60, 34, 200, 64, "orange")
    c.rect(60, 34, 200, 2, "peach"); c.rect(60, 96, 200, 2, "brown")
    for px_, py_ in ((63, 37), (255, 37), (63, 93), (255, 93)):
        c.rect(px_, py_, 2, 2, "brown")
    c.text("СУПЕР", W // 2, 40, "white", align="center", scale=2, shadow="brown")
    c.text("ПИКСЕЛЬ", W // 2, 62, "yellow", align="center", scale=3, outline="black")
    pressed = t > 2.8
    if (int(t * 2.5) % 2 == 0 and not pressed) or (pressed and int(t * 12) % 2 == 0):
        c.text("НАЖМИ СТАРТ", W // 2, 112, "white", align="center", shadow="black")
    draw_hero(c, 60, G, STAND)
    bx = 250 + pingpong(t, 3.0) * 40
    c.blit_center(anim_frame(BEETLE, t, 6), bx, G)


def world_card(lives):
    def card(c, x):
        c.clear("black")
        c.text("МИР 1-1", W // 2, 70, "white", align="center", scale=2)
        c.blit_center(STAND, 140, 118)
        c.text(f"X  {lives}", 156, 104, "white", scale=2)
    return card


mv.add(world_card(3), 2.0, "card1")

# attempt 1 -------------------------------------------------------
J1 = [(2.24, .6, 32, G, G), (4.3, .8, 52, G, G), (5.3, .5, 30, G, G - 9),
      (5.8, .4, 18, G - 9, G), (7.6, .45, 18, G, G)]
DEATH1 = 8.05


def hx1(t):
    return 40 if t < .3 else 40 + 75 * (min(t, 8.3) - .3)


def beetle_x(t):
    return 520 - 14 * t


@mv.scene(10.0, name="run1")
def run1(c, x):
    t = x.t
    hx = hx1(t)
    cam = clamp(hx - 130, 0, CAM_MAX)
    draw_world(c, cam, t, hits={200: 2.54})
    # coin popping out of the block
    k = seg(t, 2.54, 3.1)
    if 0 < k < 1:
        coin(c, 208 - cam, BLOCK_Y - 6 - math.sin(k * math.pi) * 30, t)
    # beetle: walks, then flattened by the stomp
    if t < 5.8:
        c.blit_center(anim_frame(BEETLE, t, 6), beetle_x(t) + 6 - cam, G)
    elif t < 6.4:
        c.blit_center(BEETLE_FLAT, beetle_x(5.8) + 6 - cam, G)
        c.text("100", beetle_x(5.8) - cam, G - 30 - (t - 5.8) * 20, "white", shadow="black")
    # hero
    if t < DEATH1:
        y, air = jump_y(t, J1)
    else:
        y, air = G + 400 * (t - DEATH1) ** 2, True
    frame = JUMP if air else (anim_frame(RUN, t, 12) if t >= .3 else STAND)
    if y < H + 30:
        draw_hero(c, hx - cam, y, frame)
    hud(c, x.T, 400 - t * 2.5)


mv.add(world_card(2), 2.0, "card2")

# attempt 2 -------------------------------------------------------
STAR_T = 3.6
J2 = [(2.67, .6, 32, G, G), (3.92, .75, 52, G, G), (6.145, 1.0, 50, G, G)]


def hx2(t):
    if t < .2:
        return 40
    if t < STAR_T:
        return 40 + 75 * (t - .2)
    if t < 8.9:
        return 295 + 110 * (t - STAR_T)
    if t < 10.0:
        return POLE_X - 6
    if t < 10.35:
        return lerp(POLE_X - 6, 900, seg(t, 10.0, 10.35))
    return min(968, 900 + 72 * (t - 10.35))


def hy2(t):
    if t < 8.45:
        return jump_y(t, J2)
    if t < 8.9:
        return G - 80 * ease_out(seg(t, 8.45, 8.9)), True
    if t < 10.0:
        return lerp(G - 80, G - 16, seg(t, 8.9, 9.9)), True
    if t < 10.35:
        k = seg(t, 10.0, 10.35)
        return lerp(G - 16, G, k) - 40 * k * (1 - k), True
    return G, False


KICK_T = 5.056


@mv.scene(12.0, name="run2")
def run2(c, x):
    t = x.t
    hx = hx2(t)
    cam = clamp(hx - 130, 0, CAM_MAX)
    flag_y = lerp(52, 118, seg(t, 8.9, 9.9))
    draw_world(c, cam, t, hits={232: 2.97}, flag_y=flag_y)
    # star power-up: rises from the block, then hops into the hero's hands
    if 2.97 <= t < STAR_T:
        if t < 3.3:
            sx, sy = 240, BLOCK_Y - 5 - 16 * seg(t, 2.97, 3.3)
        else:
            k = seg(t, 3.3, STAR_T)
            sx = lerp(240, hx2(STAR_T), k)
            sy = lerp(BLOCK_Y - 21, G - 10, k) - 24 * math.sin(k * math.pi)
        c.blit(star_sprite(t), sx - 4 - cam, sy - 4)
    # beetle: walks, then gets knocked flying by the invincible hero
    if t < KICK_T:
        c.blit_center(anim_frame(BEETLE, t, 6), beetle_x(t) + 6 - cam, G)
    elif t < KICK_T + 1.2:
        k = t - KICK_T
        bx = beetle_x(KICK_T) + 6 + 60 * k
        by = G - 40 * k + 200 * k * k
        c.blit_center(BEETLE[0].vflipped(), bx - cam, by)
        c.text("200", beetle_x(KICK_T) - cam, G - 34 - k * 20, "white", shadow="black")
    if 8.9 <= t < 10.5:
        c.text("5000", POLE_X + 6 - cam, G - 80 - (t - 8.9) * 10, "white", shadow="black")
    # hero (disappears into the tower door)
    if t < 11.3:
        y, air = hy2(t)
        frame = JUMP if air else (anim_frame(RUN, t, 14 if t > STAR_T else 12) if t >= .2 else STAND)
        inv = t - STAR_T if STAR_T <= t < STAR_T + 6.0 else None
        draw_hero(c, hx - cam, y, frame, flash_t=inv)
        if inv is not None and int(t * 10) % 2:  # sparkle trail
            c.px(hx - cam - 8, y - 6 - (int(t * 20) % 8), "white")
            c.px(hx - cam - 12, y - 12 + (int(t * 16) % 6), "yellow")
    hud(c, x.T, 400 - t * 2.5)


# clear -----------------------------------------------------------
TIME_LEFT = int(400 - 12.0 * 2.5)


def firework(c, x, y, k, col):
    """Chunky burst readable on a bright sky: rising shell, then 2px sparks with dark rims."""
    if k <= 0 or k >= 1:
        return
    if k < .25:  # shell rising
        kk = k / .25
        c.rect(x, y + 60 * (1 - kk), 2, 3, "white")
        return
    k = (k - .25) / .75
    r = 5 + ease_out(k) * 30
    cc = ramp(["white", "yellow", col, col, "darkpurple"], k)
    for i in range(20):
        a = i / 20 * 2 * math.pi
        px_, py_ = x + math.cos(a) * r, y + math.sin(a) * r + k * k * 12
        c.rect(px_ - 1, py_ - 1, 3, 3, "darkpurple")
        c.rect(px_, py_, 2, 2, cc)
        if k < .5:
            c.px(x + math.cos(a) * r * .55, y + math.sin(a) * r * .55, "white")


@mv.scene(6.0, name="clear", fade_out=1.5)
def clear_(c, x):
    t = x.t
    draw_world(c, CAM_MAX, t + 12, flag_y=118, tower_flag=ease_out(seg(t, .3, 1.3)))
    for i, (fx, fy, col) in enumerate(((240, 45, "red"), (290, 60, "yellow"), (262, 38, "green"),
                                        (215, 62, "pink"))):
        firework(c, fx, fy, seg(t, 1.0 + i * .55, 1.9 + i * .55), col)
    if t > .5:
        c.text("УРОВЕНЬ ПРОЙДЕН!", 110, 70, "white", align="center", outline="black", scale=1)
    if t > 3.4:
        c.text("СПАСИБО ЗА ИГРУ!", 110, 86, ramp(["blue", "white"], seg(t, 3.4, 3.8)),
               align="center", outline="black")
    timer = TIME_LEFT * (1 - seg(t, .8, 2.8))
    hud(c, x.T, timer)


# score events (global times) -----------------------------------
def _events():
    r1, r2, cl = mv.scene_start("run1"), mv.scene_start("run2"), mv.scene_start("clear")
    ev = [(r1 + 2.54, 200, 1), (r1 + 5.8, 100, 0), (r2 + STAR_T, 1000, 0),
          (r2 + KICK_T, 200, 0), (r2 + 8.9, 5000, 0)]
    for i in range(TIME_LEFT):  # time bonus: 50 points per remaining second
        ev.append((cl + .8 + 2.0 * (i + 1) / TIME_LEFT, 50, 0))
    return ev


EVENTS.extend(_events())


# ------------------------------------------------------------------ sound
LEAD = ("C5 . E5 G5 . C6 . G5 E5 . G5 . A5 - G5 . | F5 . A5 . C6 . A5 . G5 - E5 . D5 - . . "
        "| C5 . E5 G5 . C6 . E6 D6 . C6 . A5 - G5 . | F5 . E5 . D5 . G4 . C5 - - - . . . .")
BASS = ("C3 . G3 . C3 . G3 . C3 . G3 . C3 . G3 . | F2 . C3 . F2 . C3 . G2 . D3 . G2 . D3 . "
        "| C3 . G3 . C3 . G3 . A2 . E3 . A2 . E3 . | F2 . C3 . G2 . D3 . C3 . G2 . C3 . . .")
DRUM = "k . h . s . h . k . h k s . h ."
STARPOWER = "C5+E5+G5 - C5+E5+G5 . D5+F5+A5 - D5+F5+A5 . E5+G5+B5 - E5+G5+B5 . D5+F5+A5 - . ."


def soundtrack():
    s = Song(bpm=150)

    def theme(a, b, vol=1.0):
        s.track(LEAD, wave="square", duty=.5, vol=.12 * vol, start=a, end=b, adsr=(.003, .05, .5, .03))
        s.track(BASS, wave="triangle", vol=.3 * vol, start=a, end=b)
        s.drums(DRUM, vol=.18 * vol, start=a, end=b)

    ti, r1, r2, cl = 0.0, mv.scene_start("run1"), mv.scene_start("run2"), mv.scene_start("clear")
    theme(ti + .2, ti + 3.9, .8)
    s.sfx("select", at=2.8, vol=.4)
    # attempt 1
    theme(r1 + .3, r1 + DEATH1)
    for j in J1:
        s.sfx("jump", at=r1 + j[0], vol=.25)
    s.sfx("blip", at=r1 + 2.54, vol=.3); s.sfx("coin", at=r1 + 2.56, vol=.35)
    s.sfx("hit", at=r1 + 5.8, vol=.4)
    s.sfx("hurt", at=r1 + DEATH1 + .1, vol=.4)
    s.track("G4 - - F#4 - - F4 - - E4 - - - - - - . . C4 - - - - - - -", wave="square", duty=.25,
            vol=.14, start=r1 + DEATH1 + .45, loop=False, vibrato=.01)
    s.track("C3 - - B2 - - A#2 - - A2 - - - - - - . . C2 - - - - - - -", wave="triangle",
            vol=.3, start=r1 + DEATH1 + .45, loop=False)
    # attempt 2
    theme(r2 + .2, r2 + STAR_T)
    for j in J2:
        s.sfx("jump", at=r2 + j[0], vol=.25)
    s.sfx("blip", at=r2 + 2.97, vol=.3)
    s.sfx("powerup", at=r2 + STAR_T, vol=.35)
    s.track(STARPOWER, wave="square", duty=.25, vol=.1, start=r2 + STAR_T + .5, end=r2 + 8.9)
    s.track("C3 C4 C3 C4 D3 D4 D3 D4 E3 E4 E3 E4 D3 D4 D3 D4", wave="triangle", vol=.28,
            start=r2 + STAR_T + .5, end=r2 + 8.9)
    s.drums("k h s h k h s h k h s h k k s s", vol=.2, start=r2 + STAR_T + .5, end=r2 + 8.9)
    s.sfx("hit", at=r2 + KICK_T, vol=.4)
    s.sfx("jump", at=r2 + 8.45, vol=.25)
    s.sfx("whoosh", at=r2 + 8.95, vol=.35)
    # victory fanfare as the flag comes down
    s.track("G4 C5 E5 G5 C6 E6 G6 - - - E6 - - - . . A4 C5 F5 A5 C6 F6 A6 - - - F6 - - - . . "
            "B4 D5 G5 B5 D6 G6 B6 - - - B6 B6 B6 C7 - - - - - - - -",
            wave="square", duty=.5, vol=.13, start=r2 + 9.0, loop=False)
    s.track("C3 - - - - - - - - - - - - - - - F2 - - - - - - - - - - - - - - - "
            "G2 - - - - - - - - - G2 G2 G2 C3 - - - - - - - -",
            wave="triangle", vol=.3, start=r2 + 9.0, loop=False)
    s.sfx("door", at=r2 + 11.3, vol=.3)
    # clear: fireworks + score tally
    for i in range(4):
        s.sfx("explosion", at=cl + 1.0 + i * .55, vol=.25)
    for i in range(20):
        s.sfx("blip", at=cl + .8 + i * .1, vol=.12)
    s.sfx("chime", at=cl + 3.4, vol=.35)
    return s


if __name__ == "__main__":
    main(mv, audio=soundtrack)
