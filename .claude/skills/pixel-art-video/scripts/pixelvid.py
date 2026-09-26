"""
pixelvid — a tiny engine for making pixel-art videos in code.

Stack: Python 3 + Pillow + numpy (+ imageio-ffmpeg for MP4, scipy optional).
Idea:  every frame is a pure function of time -> draw at low resolution
       (e.g. 320x180) with a fixed palette -> upscale by an integer factor with
       nearest-neighbour -> encode to MP4 with a synthesized chiptune soundtrack.

Quick start
-----------
    import sys; sys.path.insert(0, r"<skill>/scripts")
    from pixelvid import *

    mv = Movie(320, 180, fps=24, scale=4, pal="pico8")

    @mv.scene(4.0, fade_in=0.5)
    def intro(c, x):                      # c: Canvas, x: Ctx (x.t, x.p, x.dur, x.T, x.f)
        c.vgradient(0, 120, ["darkblue", "darkpurple", "red"])
        c.circ(160, 110, 18, "orange"); c.glow(160, 110, 40, "yellow", 0.3)
        c.text("HELLO", 160, 20, "white", align="center", scale=2, shadow="black")

    song = Song(bpm=100)
    song.track("C4 - E4 - G4 - E4 -", wave="square", duty=0.25, vol=0.2)
    mv.stills([0.5, 2, 3.5], "preview.png")       # look at it before rendering
    mv.render("out.mp4", audio=song)

Colors anywhere accept: palette index (int), palette name ("red"),
"#rrggbb", or an (r, g, b) tuple.
"""
from __future__ import annotations

import math
import os
import random
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw

try:
    from scipy.signal import lfilter as _lfilter
except Exception:  # scipy is optional
    _lfilter = None

# ============================================================================
# Palettes
# ============================================================================


class Palette(list):
    """A list of RGB tuples that can also be indexed by name."""

    def __init__(self, colors, names=None):
        super().__init__(tuple(c) for c in colors)
        self.names = {n: i for i, n in enumerate(names or [])}

    def __getitem__(self, k):
        if isinstance(k, str):
            if k not in self.names:
                raise KeyError(f"colour {k!r} not in palette; available: {', '.join(self.names)}")
            return list.__getitem__(self, self.names[k])
        return list.__getitem__(self, k)

    def index_of(self, k):
        return self.names[k] if isinstance(k, str) else int(k)

    def array(self):
        return np.array(list(self), dtype=np.int32)


def hexpal(s, names=None):
    cols = [tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for h in s.split()]
    return Palette(cols, names)


PALETTES = {
    # 16 colours, the most famous fantasy-console palette
    "pico8": hexpal(
        "000000 1d2b53 7e2553 008751 ab5236 5f574f c2c3c7 fff1e8 "
        "ff004d ffa300 ffec27 00e436 29adff 83769c ff77a8 ffccaa",
        ["black", "darkblue", "darkpurple", "darkgreen", "brown", "darkgray",
         "lightgray", "white", "red", "orange", "yellow", "green", "blue",
         "indigo", "pink", "peach"]),
    # 16 colours, soft and modern (GrafxKid)
    "sweetie16": hexpal(
        "1a1c2c 5d275d b13e53 ef7d57 ffcd75 a7f070 38b764 257179 "
        "29366f 3b5dc9 41a6f6 73eff7 f4f4f4 94b0c2 566c86 333c57",
        ["black", "purple", "red", "orange", "yellow", "lime", "green",
         "teal", "navy", "blue", "sky", "cyan", "white", "silver", "slate",
         "darkslate"]),
    # 32 colours, rich general-purpose palette (ENDESGA)
    "endesga32": hexpal(
        "be4a2f d77643 ead4aa e4a672 b86f50 733e39 3e2731 a22633 "
        "e43b44 f77622 feae34 fee761 63c74d 3e8948 265c42 193c3e "
        "124e89 0099db 2ce8f5 ffffff c0cbdc 8b9bb4 5a6988 3a4466 "
        "262b44 181425 ff0044 68386c b55088 f6757a e8b796 c28569",
        ["rust", "clay", "sand", "tan", "wood", "brown", "darkbrown", "wine",
         "red", "orange", "gold", "yellow", "green", "forest", "pine",
         "deepteal", "navy", "blue", "cyan", "white", "silver", "gray",
         "slate", "darkslate", "night", "black", "crimson", "plum", "magenta",
         "salmon", "skin", "skinshade"]),
    # 8 colours, warm sunset/dusk moods
    "slso8": hexpal("0d2b45 203c56 544e68 8d697a d08159 ffaa5e ffd4a3 ffecd6",
                    ["ink", "night", "dusk", "mauve", "copper", "amber",
                     "peach", "cream"]),
    # 8 colours, melancholic night
    "nyx8": hexpal("08141e 0f2a3f 20394f 4e495f 816271 997577 c3a38a f6d6bd",
                   ["ink", "deep", "navy", "slate", "mauve", "rose", "sand",
                    "cream"]),
    # 4 colours, original Game Boy
    "gameboy": hexpal("0f380f 306230 8bac0f 9bbc0f",
                      ["darkest", "dark", "light", "lightest"]),
}


_CURRENT = {"pal": PALETTES["pico8"]}


def use_palette(pal):
    """Set the default palette for sprites/helpers (Movie() does this for you)."""
    _CURRENT["pal"] = PALETTES[pal] if isinstance(pal, str) else pal
    return _CURRENT["pal"]


def current_palette():
    return _CURRENT["pal"]


# ============================================================================
# Maths / timing helpers (everything is a function of time)
# ============================================================================

def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def lerp(a, b, t):
    return a + (b - a) * t


def seg(t, a, b):
    """Progress 0..1 of t inside the time window [a, b] (clamped)."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def ease_in(t):
    return t * t


def ease_out(t):
    return 1 - (1 - t) * (1 - t)


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def ease_back(t):  # small overshoot, nice for pop-ins
    c = 1.70158
    t -= 1
    return 1 + t * t * ((c + 1) * t + c)


def bounce(t):
    if t < 1 / 2.75:
        return 7.5625 * t * t
    if t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + .75
    if t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + .9375
    t -= 2.625 / 2.75
    return 7.5625 * t * t + .984375


def keys(t, frames, ease=ease_in_out):
    """Keyframe interpolation. frames = [(time, value), ...] sorted by time.
    Values may be numbers or tuples of numbers."""
    if t <= frames[0][0]:
        return frames[0][1]
    for (t0, v0), (t1, v1) in zip(frames, frames[1:]):
        if t <= t1:
            k = ease(seg(t, t0, t1))
            if isinstance(v0, (tuple, list)):
                return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
            return lerp(v0, v1, k)
    return frames[-1][1]


def stepped(t, fps=12):
    """Quantize time -> choppy 'on twos' retro motion."""
    return math.floor(t * fps) / fps


def pingpong(t, period=1.0):
    p = (t / period) % 2
    return p if p < 1 else 2 - p


def ramp(colors, k):
    """Pick a colour from a list by progress k in 0..1 (stepped palette fades)."""
    return colors[min(len(colors) - 1, max(0, int(k * len(colors))))]


def hrand(*k):
    """Deterministic pseudo-random in [0,1) from any ints/floats."""
    h = hash(tuple(int(v * 1000) if isinstance(v, float) else v for v in k))
    h = (h ^ 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    h = (h ^ (h >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
    h = (h ^ (h >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 31
    return (h & 0xFFFFFF) / float(0x1000000)


def anim_frame(frames, t, fps=8, loop=True):
    """Pick the sprite frame for time t from a list of frames."""
    i = int(t * fps)
    return frames[i % len(frames)] if loop else frames[min(i, len(frames) - 1)]


_BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6],
                     [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) + .5) / 16


def bayer(w, h):
    return np.tile(_BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]


def periodic_noise(n, seed=0, octaves=4, base=2, rough=0.5):
    """1D noise of length n that tiles seamlessly (sum of sines). Returns 0..1."""
    rng = np.random.default_rng(seed)
    x = np.arange(n) / n * 2 * np.pi
    y = np.zeros(n)
    amp = 1.0
    for o in range(octaves):
        k = base * (2 ** o)
        y += amp * np.sin(k * x + rng.uniform(0, 2 * np.pi))
        y += amp * .5 * np.sin((k + 1) * x + rng.uniform(0, 2 * np.pi))
        amp *= rough
    y -= y.min()
    return y / (y.max() or 1)


# ============================================================================
# Pixel font (5x7, uppercase Latin + Cyrillic + digits + punctuation)
# ============================================================================

_G = {
    "A": ".###./#...#/#...#/#####/#...#/#...#/#...#",
    "B": "####./#...#/#...#/####./#...#/#...#/####.",
    "C": ".###./#...#/#..../#..../#..../#...#/.###.",
    "D": "####./#...#/#...#/#...#/#...#/#...#/####.",
    "E": "#####/#..../#..../####./#..../#..../#####",
    "F": "#####/#..../#..../####./#..../#..../#....",
    "G": ".###./#...#/#..../#.###/#...#/#...#/.####",
    "H": "#...#/#...#/#...#/#####/#...#/#...#/#...#",
    "I": "###/.#./.#./.#./.#./.#./###",
    "J": "..###/...#./...#./...#./#..#./#..#./.##..",
    "K": "#...#/#..#./#.#../##.../#.#../#..#./#...#",
    "L": "#..../#..../#..../#..../#..../#..../#####",
    "M": "#...#/##.##/#.#.#/#.#.#/#...#/#...#/#...#",
    "N": "#...#/#...#/##..#/#.#.#/#..##/#...#/#...#",
    "O": ".###./#...#/#...#/#...#/#...#/#...#/.###.",
    "P": "####./#...#/#...#/####./#..../#..../#....",
    "Q": ".###./#...#/#...#/#...#/#.#.#/#..#./.##.#",
    "R": "####./#...#/#...#/####./#.#../#..#./#...#",
    "S": ".####/#..../#..../.###./....#/....#/####.",
    "T": "#####/..#../..#../..#../..#../..#../..#..",
    "U": "#...#/#...#/#...#/#...#/#...#/#...#/.###.",
    "V": "#...#/#...#/#...#/#...#/#...#/.#.#./..#..",
    "W": "#...#/#...#/#...#/#.#.#/#.#.#/#.#.#/.#.#.",
    "X": "#...#/#...#/.#.#./..#../.#.#./#...#/#...#",
    "Y": "#...#/#...#/.#.#./..#../..#../..#../..#..",
    "Z": "#####/....#/...#./..#../.#.../#..../#####",
    "0": ".###./#...#/#..##/#.#.#/##..#/#...#/.###.",
    "1": ".#./##./.#./.#./.#./.#./###",
    "2": ".###./#...#/....#/...#./..#../.#.../#####",
    "3": "#####/...#./..#../...#./....#/#...#/.###.",
    "4": "...#./..##./.#.#./#..#./#####/...#./...#.",
    "5": "#####/#..../####./....#/....#/#...#/.###.",
    "6": "..##./.#.../#..../####./#...#/#...#/.###.",
    "7": "#####/....#/...#./..#../.#.../.#.../.#...",
    "8": ".###./#...#/#...#/.###./#...#/#...#/.###.",
    "9": ".###./#...#/#...#/.####/....#/...#./.##..",
    # Cyrillic (letters identical to Latin are aliased below)
    "Б": "#####/#..../#..../####./#...#/#...#/####.",
    "Г": "#####/#..../#..../#..../#..../#..../#....",
    "Д": "..##./.#.#./.#.#./.#.#./.#.#./#####/#...#",
    "Ж": "#.#.#/#.#.#/.###./..#../.###./#.#.#/#.#.#",
    "З": ".###./#...#/....#/..##./....#/#...#/.###.",
    "И": "#...#/#...#/#..##/#.#.#/##..#/#...#/#...#",
    "Й": ".#.#./..#../#...#/#..##/#.#.#/##..#/#...#",
    "Л": "..###/.#..#/.#..#/.#..#/.#..#/.#..#/#...#",
    "П": "#####/#...#/#...#/#...#/#...#/#...#/#...#",
    "У": "#...#/#...#/#...#/.####/....#/#...#/.###.",
    "Ф": "..#../.###./#.#.#/#.#.#/#.#.#/.###./..#..",
    "Ц": "#..#./#..#./#..#./#..#./#..#./#####/....#",
    "Ч": "#...#/#...#/#...#/.####/....#/....#/....#",
    "Ш": "#.#.#/#.#.#/#.#.#/#.#.#/#.#.#/#.#.#/#####",
    "Щ": "#.#.#./#.#.#./#.#.#./#.#.#./#.#.#./######/.....#",
    "Ъ": "##.../.#.../.#.../.###./.#..#/.#..#/.###.",
    "Ы": "#...#/#...#/#...#/###.#/#.#.#/#.#.#/###.#",
    "Ь": "#..../#..../#..../####./#...#/#...#/####.",
    "Э": ".###./#...#/....#/..###/....#/#...#/.###.",
    "Ю": "#..#./#.#.#/#.#.#/###.#/#.#.#/#.#.#/#..#.",
    "Я": ".####/#...#/#...#/.####/..#.#/.#..#/#...#",
    "Ё": ".#.#./#####/#..../####./#..../#..../#####",
    # punctuation
    " ": ".../.../.../.../.../.../...",
    ".": "././././././#",
    ",": "../../../../../.#/#.",
    "!": "#/#/#/#/#/./#",
    "?": ".###./#...#/....#/...#./..#../...../..#..",
    ":": "./#/././#/./.",
    ";": "../.#/../../.#/#./..",
    "-": ".../.../.../###/.../.../...",
    "+": "...../..#../..#../#####/..#../..#../.....",
    "=": "...../...../#####/...../#####/...../.....",
    "'": "#/#/././././.",
    '"': "#.#/#.#/.../.../.../.../...",
    "(": ".#/#./#./#./#./#./.#",
    ")": "#./.#/.#/.#/.#/.#/#.",
    "/": "....#/...#./...#./..#../.#.../.#.../#....",
    "*": "...../#.#.#/.###./#####/.###./#.#.#/.....",
    "%": "##..#/##..#/...#./..#../.#.../#..##/#..##",
    "#": ".#.#./#####/.#.#./.#.#./.#.#./#####/.#.#.",
    "<": "...#/..#./.#../#.../.#../..#./...#",
    ">": "#.../.#../..#./...#/..#./.#../#...",
    "_": "...../...../...../...../...../...../#####",
    "&": ".##../#..#./.##../.#.../#.#.#/#..#./.##.#",
}
for _lat, _cyr in zip("ABEKMHOPCTX", "АВЕКМНОРСТХ"):
    _G[_cyr] = _G[_lat]
_ALIAS = {"«": '"', "»": '"', "—": "-", "–": "-", "…": "...", "№": "N"}
_FONT = {k: [r for r in v.split("/")] for k, v in _G.items()}
FONT_H = 7


def _norm_text(s):
    out = []
    for ch in s.upper():
        ch = _ALIAS.get(ch, ch)
        out.append(ch)
    return "".join(out)


def text_width(s, scale=1, spacing=1):
    s = _norm_text(s)
    lines = s.split("\n")
    best = 0
    for ln in lines:
        w = 0
        for ch in ln:
            g = _FONT.get(ch, _FONT["?"])
            w += (len(g[0]) + spacing) * scale
        best = max(best, w - spacing * scale if ln else 0)
    return best


def wrap_text(s, max_w, scale=1):
    """Greedy word wrap to a pixel width; returns string with newlines."""
    lines, cur = [], ""
    for word in s.split():
        cand = (cur + " " + word).strip()
        if text_width(cand, scale) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def typewriter(s, t, cps=20):
    """Substring shown at time t when typing cps characters per second."""
    return s[:max(0, int(t * cps))]


# ============================================================================
# Sprites
# ============================================================================

_B32 = "0123456789abcdefghijklmnopqrstuv"


class Sprite:
    """RGBA image with binary alpha. Build from ASCII art with from_ascii()."""

    def __init__(self, img: Image.Image):
        self.img = img.convert("RGBA")

    @property
    def w(self):
        return self.img.width

    @property
    def h(self):
        return self.img.height

    @staticmethod
    def from_ascii(art, legend=None, pal=None):
        """ASCII art -> Sprite. '.' and ' ' are transparent.
        legend maps chars -> colours. Without a legend, chars 0-9a-v are
        palette indices (base 32). Rows may be a list or a newline string."""
        pal = pal or current_palette()
        rows = art if isinstance(art, (list, tuple)) else [
            r for r in art.strip("\n").split("\n")]
        rows = [r.rstrip() for r in rows]
        # strip common indentation
        ind = min((len(r) - len(r.lstrip()) for r in rows if r.strip()), default=0)
        rows = [r[ind:] for r in rows]
        w = max(len(r) for r in rows)
        h = len(rows)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        px = img.load()
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch in ". ":
                    continue
                if legend and ch in legend:
                    c = resolve_color(legend[ch], pal)
                else:
                    c = pal[_B32.index(ch.lower()) % len(pal)]
                px[x, y] = (*c, 255)
        return Sprite(img)

    def flipped(self):
        return Sprite(self.img.transpose(Image.FLIP_LEFT_RIGHT))

    def vflipped(self):
        return Sprite(self.img.transpose(Image.FLIP_TOP_BOTTOM))

    def scaled(self, k: int):
        return Sprite(self.img.resize((self.w * k, self.h * k), Image.NEAREST))

    def squashed(self, k):
        """Squash (k>0: wider+shorter) or stretch (k<0: taller+thinner). Keep |k|<=0.3.
        Draw with blit_center so the feet stay on the ground."""
        w = max(1, int(round(self.w * (1 + k))))
        h = max(1, int(round(self.h * (1 - k))))
        return Sprite(self.img.resize((w, h), Image.NEAREST))

    def recolored(self, mapping, pal=None):
        """mapping: {old_color: new_color} (any colour spec)."""
        pal = pal or current_palette()
        a = np.array(self.img)
        out = a.copy()
        for old, new in mapping.items():
            o = resolve_color(old, pal)
            n = resolve_color(new, pal)
            m = (a[..., 0] == o[0]) & (a[..., 1] == o[1]) & (a[..., 2] == o[2]) & (a[..., 3] > 0)
            out[m, :3] = n
        return Sprite(Image.fromarray(out, "RGBA"))

    def silhouette(self, col, pal=None):
        a = np.array(self.img)
        a[a[..., 3] > 0, :3] = resolve_color(col, pal or current_palette())
        return Sprite(Image.fromarray(a, "RGBA"))

    def outlined(self, col, pal=None, diagonal=False):
        """Add a 1px outline (sprite grows by 2px each dimension)."""
        a = np.array(self.img)
        alpha = a[..., 3] > 0
        H, W = alpha.shape
        big = np.zeros((H + 2, W + 2), bool)
        big[1:-1, 1:-1] = alpha
        grown = big.copy()
        shifts = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        if diagonal:
            shifts += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dy, dx in shifts:
            grown |= np.roll(np.roll(big, dy, 0), dx, 1)
        out = np.zeros((H + 2, W + 2, 4), np.uint8)
        out[grown & ~big, :3] = resolve_color(col, pal or current_palette())
        out[grown & ~big, 3] = 255
        out[1:-1, 1:-1][alpha] = a[alpha]
        return Sprite(Image.fromarray(out, "RGBA"))


# Generic colour names usable with ANY palette: if the palette has no colour of
# that name, the nearest palette colour to this reference RGB is used.
_CANON = {
    "black": (0, 0, 0), "white": (255, 245, 235), "gray": (128, 128, 128),
    "grey": (128, 128, 128), "darkgray": (90, 85, 80), "lightgray": (194, 195, 199),
    "silver": (192, 203, 220), "red": (230, 30, 60), "darkred": (120, 20, 40),
    "orange": (250, 150, 30), "yellow": (255, 230, 50), "gold": (250, 180, 50),
    "green": (40, 200, 60), "darkgreen": (0, 120, 70), "lime": (160, 240, 100),
    "blue": (40, 140, 240), "darkblue": (30, 40, 85), "navy": (20, 40, 110),
    "sky": (100, 180, 250), "cyan": (60, 230, 245), "teal": (30, 110, 120),
    "purple": (110, 40, 120), "darkpurple": (120, 40, 80), "indigo": (130, 118, 156),
    "pink": (255, 120, 170), "magenta": (190, 60, 150), "brown": (150, 80, 50),
    "darkbrown": (70, 40, 40), "peach": (255, 205, 170), "skin": (235, 180, 150),
    "sand": (230, 210, 170), "cream": (250, 235, 215),
}


def resolve_color(c, pal):
    if isinstance(c, (tuple, list, np.ndarray)) and len(c) >= 3:
        return tuple(int(v) for v in c[:3])
    if isinstance(c, str):
        if c.startswith("#"):
            return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
        if c in getattr(pal, "names", {}) or c not in _CANON:
            return pal[c]
        ref = np.array(_CANON[c])
        arr = np.array(list(pal))
        return tuple(int(v) for v in arr[((arr - ref) ** 2).sum(1).argmin()])
    return pal[int(c) % len(pal)]


# --- ready-made humanoid with walk cycle ------------------------------------

_HUMAN_TOP = [
    "...hhhh..",
    "..hhhhhh.",
    "..hhhsss.",
    "..hhsses.",
    "...hssss.",
    "....ss...",
    "...cccc..",
    "..cccccc.",
    "..cdcccc.",
    "..cdcccc.",
    "..scccc..",
]
_HUMAN_LEGS = {
    "idle": ["...pppp..", "...p..p..", "...p..p..", "...bb.bb."],
    "w0": ["...pppp..", "..pp..pp.", "..p....p.", ".bb....bb"],
    "w1": ["...pppp..", "....pp...", "....pq...", "....bbb.."],
    "w2": ["...pppp..", "..qq..pp.", "..q....p.", ".bb....bb"],
    "w3": ["...pppp..", "....qp...", "....qp...", "....bbb.."],
}


def humanoid(hair="brown", skin="peach", eye="black", coat="blue",
             coat_shade="darkblue", pants="darkgray", pants_back="black",
             boots="black", outline="black", pal=None, hood=False):
    """Small side-view character (11x17 with outline), facing right.
    Returns dict: idle (2 frames: open/blink), walk (4 frames), and
    'hand' = (x, y) hand anchor relative to sprite top-left.
    Use .flipped() on frames for facing left."""
    pal = pal or current_palette()
    lg = {"h": hair, "s": skin, "e": eye, "c": coat, "d": coat_shade,
          "p": pants, "q": pants_back, "b": boots}
    top = list(_HUMAN_TOP)
    if hood:
        top[0], top[1], top[2] = "...cccc..", "..cccccc.", "..ccssss."
        top[3], top[4] = "..ccsses.", "...cssss."
    blink = [r.replace("e", "s") for r in top]

    def mk(t, legs):
        return Sprite.from_ascii(t + _HUMAN_LEGS[legs], lg, pal).outlined(outline, pal)
    return {
        "idle": [mk(top, "idle")] * 5 + [mk(blink, "idle")],
        "walk": [mk(top, k) for k in ("w0", "w1", "w2", "w3")],
        "hand": (3, 11),
    }


# ============================================================================
# Canvas
# ============================================================================


class Canvas:
    """Low-res drawing surface. All coordinates are integers in canvas pixels."""

    def __init__(self, w, h, pal):
        self.w, self.h = w, h
        self.pal = pal
        self.img = Image.new("RGB", (w, h), resolve_color("black", pal))
        self.d = ImageDraw.Draw(self.img)
        self._bayer = bayer(w, h)
        yy, xx = np.mgrid[0:h, 0:w]
        self._xx, self._yy = xx.astype(np.float32), yy.astype(np.float32)

    # --- colour / array plumbing -------------------------------------------
    def col(self, c):
        return resolve_color(c, self.pal)

    def arr(self):
        return np.array(self.img)

    def put(self, a):
        self.img.paste(Image.fromarray(a.astype(np.uint8), "RGB"))

    # --- primitives ---------------------------------------------------------
    def clear(self, c="black"):
        self.d.rectangle([0, 0, self.w, self.h], fill=self.col(c))

    def px(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img.putpixel((x, y), self.col(c))

    def rect(self, x, y, w, h, c, fill=True):
        x, y, w, h = (int(round(v)) for v in (x, y, w, h))
        if w <= 0 or h <= 0:
            return
        box = [x, y, x + w - 1, y + h - 1]
        if fill:
            self.d.rectangle(box, fill=self.col(c))
        else:
            self.d.rectangle(box, outline=self.col(c))

    def line(self, x0, y0, x1, y1, c, width=1):
        self.d.line([(int(round(x0)), int(round(y0))),
                     (int(round(x1)), int(round(y1)))], fill=self.col(c), width=width)

    def circ(self, cx, cy, r, c, fill=True):
        cx, cy, r = int(round(cx)), int(round(cy)), int(round(r))
        if r <= 0:
            self.px(cx, cy, c)
            return
        box = [cx - r, cy - r, cx + r, cy + r]
        if fill:
            self.d.ellipse(box, fill=self.col(c))
        else:
            self.d.ellipse(box, outline=self.col(c))

    def ellipse(self, cx, cy, rx, ry, c, fill=True):
        box = [int(round(cx - rx)), int(round(cy - ry)),
               int(round(cx + rx)), int(round(cy + ry))]
        if fill:
            self.d.ellipse(box, fill=self.col(c))
        else:
            self.d.ellipse(box, outline=self.col(c))

    def poly(self, pts, c, fill=True):
        pts = [(int(round(x)), int(round(y))) for x, y in pts]
        if fill:
            self.d.polygon(pts, fill=self.col(c))
        else:
            self.d.polygon(pts, outline=self.col(c))

    def blit(self, spr: Sprite, x, y, flip=False):
        s = spr.flipped() if flip else spr
        self.img.paste(s.img, (int(round(x)), int(round(y))), s.img)

    def blit_center(self, spr: Sprite, cx, bottom, flip=False):
        """Place sprite by its bottom-centre (feet) point."""
        self.blit(spr, int(round(cx - spr.w / 2)), int(round(bottom - spr.h)), flip)

    # --- text ---------------------------------------------------------------
    def text(self, s, x, y, c, align="left", scale=1, shadow=None,
             outline=None, spacing=1, line_gap=3):
        s = _norm_text(s)
        lines = s.split("\n")
        for li, ln in enumerate(lines):
            w = text_width(ln, scale, spacing)
            cx = x - (w // 2 if align == "center" else w if align == "right" else 0)
            cy = y + li * (FONT_H + line_gap) * scale
            if outline is not None:
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                    self._text_line(ln, cx + dx, cy + dy, outline, scale, spacing)
            if shadow is not None:
                self._text_line(ln, cx + scale, cy + scale, shadow, scale, spacing)
            self._text_line(ln, cx, cy, c, scale, spacing)

    def _text_line(self, s, x, y, c, scale, spacing):
        col = self.col(c)
        x, y = int(round(x)), int(round(y))
        for ch in s:
            g = _FONT.get(ch, _FONT["?"])
            for gy, row in enumerate(g):
                for gx, bit in enumerate(row):
                    if bit == "#":
                        self.d.rectangle([x + gx * scale, y + gy * scale,
                                          x + gx * scale + scale - 1,
                                          y + gy * scale + scale - 1], fill=col)
            x += (len(g[0]) + spacing) * scale

    # --- masks & dithering ----------------------------------------------------
    def mask_poly(self, pts):
        m = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(m).polygon([(int(round(a)), int(round(b))) for a, b in pts], fill=255)
        return np.array(m) > 0

    def mask_circle(self, cx, cy, r):
        return (self._xx - cx) ** 2 + (self._yy - cy) ** 2 <= r * r

    def mask_rect(self, x, y, w, h):
        return (self._xx >= x) & (self._xx < x + w) & (self._yy >= y) & (self._yy < y + h)

    def dither_fill(self, mask, c, level):
        """Fill mask with colour c at 'opacity' level 0..1 via ordered dither.
        level may be a scalar or an HxW array."""
        a = self.arr()
        m = mask & (self._bayer < level)
        a[m] = self.col(c)
        self.put(a)

    def dither_rect(self, x, y, w, h, c, level):
        self.dither_fill(self.mask_rect(x, y, w, h), c, level)

    def vgradient(self, y0, y1, colors, dither=True, x0=0, x1=None):
        """Vertical band gradient through a list of colours, dithered between."""
        x1 = self.w if x1 is None else x1
        y0, y1 = int(y0), int(y1)
        n = len(colors) - 1
        a = self.arr()
        cols = [self.col(c) for c in colors]
        for y in range(max(0, y0), min(self.h, y1)):
            f = (y - y0) / max(1, (y1 - y0 - 1)) * n
            i = min(int(f), n - 1) if n > 0 else 0
            fr = f - i
            if n == 0:
                a[y, x0:x1] = cols[0]
                continue
            if dither:
                row = self._bayer[y, x0:x1] < fr
                a[y, x0:x1][~row] = cols[i]
                a[y, x0:x1][row] = cols[i + 1]
            else:
                a[y, x0:x1] = cols[i + (1 if fr > .5 else 0)]
        self.put(a)

    def glow(self, cx, cy, r, c, strength=0.5, core=0.0):
        """Radial dithered halo (lamps, sun, magic). core = fully solid radius share."""
        d = np.sqrt((self._xx - cx) ** 2 + (self._yy - cy) ** 2) / max(r, 1)
        lvl = np.clip((1 - d) / max(1e-6, 1 - core), 0, 1) * strength
        self.dither_fill(d < 1, c, lvl)

    def fade(self, level, c="black"):
        """Dithered fade to colour: level 0 = none, 1 = fully covered."""
        if level <= 0:
            return
        a = self.arr()
        a[self._bayer < level] = self.col(c)
        self.put(a)

    def iris(self, cx, cy, r, c="black"):
        """Everything outside a circle becomes colour c (iris in/out)."""
        a = self.arr()
        a[~self.mask_circle(cx, cy, r)] = self.col(c)
        self.put(a)

    def quantize(self, pal=None):
        """Snap every pixel to nearest palette colour (palette discipline)."""
        p = (pal or self.pal).array()
        a = self.arr().astype(np.int32)
        flat = a.reshape(-1, 3)
        d = ((flat[:, None, :] - p[None, :, :]) ** 2).sum(-1)
        self.put(p[d.argmin(1)].reshape(a.shape))

    def _darker_map(self, a, factor, tint):
        p = self.pal.array()
        tgt = np.clip(a.astype(np.float32) * factor + np.array(tint, np.float32), 0, 255)
        flat = tgt.reshape(-1, 3)
        d = ((flat[:, None, :] - p[None, :, :]) ** 2).sum(-1)
        return p[d.argmin(1)].reshape(a.shape)

    def night(self, amount=0.8, lights=(), factor=0.45, tint=(0, 0, 18)):
        """Darken the scene toward darker palette colours with dither.
        lights: [(x, y, radius), ...] areas that stay lit (soft dithered edge)."""
        a = self.arr()
        dark = self._darker_map(a, factor, tint)
        lvl = np.full((self.h, self.w), float(amount), np.float32)
        for (lx, ly, lr) in lights:
            d = np.sqrt((self._xx - lx) ** 2 + (self._yy - ly) ** 2) / max(lr, 1)
            lvl = np.minimum(lvl, np.clip(d, 0, 1) * amount)
        m = self._bayer < lvl
        a[m] = dark[m]
        self.put(a)

    def tint_area(self, mask, factor=0.6, tint=(0, 0, 0), level=1.0):
        """Shadow/light an area by remapping to palette colours (factor<1 darker)."""
        a = self.arr()
        alt = self._darker_map(a, factor, tint)
        m = mask & (self._bayer < level)
        a[m] = alt[m]
        self.put(a)

    def shift(self, dx, dy, fill="black"):
        """Screen shake / whole-canvas offset."""
        dx, dy = int(round(dx)), int(round(dy))
        if not dx and not dy:
            return
        a = self.arr()
        out = np.empty_like(a)
        out[:] = self.col(fill)
        H, W = a.shape[:2]
        xs, xd = (0, dx) if dx >= 0 else (-dx, 0)
        ys, yd = (0, dy) if dy >= 0 else (-dy, 0)
        w, h = W - abs(dx), H - abs(dy)
        if w > 0 and h > 0:
            out[yd:yd + h, xd:xd + w] = a[ys:ys + h, xs:xs + w]
        self.put(out)

    def reflect(self, y_line, t, amp=1, speed=4.0, factor=0.6, tint=(0, 0, 20), level=0.7):
        """Mirror everything above y_line into the area below it with ripples."""
        a = self.arr()
        H = self.h
        y_line = int(y_line)
        src = a.copy()
        for y in range(y_line, H):
            sy = 2 * y_line - y - 1
            if sy < 0:
                break
            off = int(round(amp * math.sin(y * 0.9 + t * speed) * (1 + (y - y_line) * 0.05)))
            a[y] = np.roll(src[sy], off, axis=0)
        self.put(a)
        m = self._yy >= y_line
        self.tint_area(m, factor, tint, level)


# ============================================================================
# Procedural scenery & particles (all deterministic in t -> loop-safe)
# ============================================================================

def stars(c: Canvas, t, n=60, seed=1, cols=("white", "lightgray"), y_max=None, twinkle=0.15):
    rng = random.Random(seed)
    y_max = c.h if y_max is None else y_max
    for i in range(n):
        x, y = rng.randrange(c.w), rng.randrange(int(y_max))
        col = cols[i % len(cols)]
        if hrand(seed, i, int(t * 3 + i)) < twinkle:
            continue
        c.px(x, y, col)
        if i % 17 == 0 and hrand(seed, i, int(t * 2)) > .5:  # occasional cross sparkle
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.px(x + dx, y + dy, cols[-1])


def mountains(c: Canvas, base_y, height, col, seed=0, scroll=0.0, period=None,
              rough=0.5, octaves=4, rim=None):
    """Silhouette ridge. scroll = camera_x * parallax_factor. Tiles seamlessly."""
    period = period or c.w * 2
    h = periodic_noise(period, seed, octaves=octaves, rough=rough)
    xs = (np.arange(c.w) + int(round(scroll))) % period
    tops = np.round(base_y - height * h[xs]).astype(int)
    mask = c._yy >= tops[None, :]
    a = c.arr()
    a[mask] = c.col(col)
    if rim is not None:
        for x in range(c.w):
            if 0 <= tops[x] < c.h:
                a[tops[x], x] = c.col(rim)
    c.put(a)
    return tops


def hills(c: Canvas, base_y, height, col, seed=0, scroll=0.0, rim=None):
    return mountains(c, base_y, height, col, seed, scroll, octaves=2, rough=0.35, rim=rim)


def city(c: Canvas, base_y, col, win_col=None, seed=0, scroll=0.0, t=0.0,
         min_h=15, max_h=60, lit=0.25, period=None):
    """Skyline silhouette with flickering windows. Tiles with period."""
    period = period or c.w * 2
    rng = random.Random(seed)
    blds, x = [], 0
    while x < period:
        w = rng.randint(10, 24)
        blds.append((x, min(w, period - x), rng.randint(min_h, max_h), rng.random()))
        x += w + rng.randint(0, 3)
    off = int(round(scroll)) % period
    for rep in (0, period):
        for bi, (bx, bw, bh, r) in enumerate(blds):
            X = bx - off + rep
            if X > c.w or X + bw < 0:
                continue
            c.rect(X, base_y - bh, bw, bh + c.h, col)
            if r > .7:  # antenna
                c.line(X + bw // 2, base_y - bh - 5, X + bw // 2, base_y - bh, col)
            if win_col is None:
                continue
            for wy in range(base_y - bh + 3, base_y - 2, 4):
                for wx in range(X + 2, X + bw - 2, 3):
                    k = hrand(seed, bi, wx - X, wy, int(t / 3 + r * 7))
                    if k < lit:
                        c.px(wx, wy, win_col)


def clouds(c: Canvas, t, col, shade=None, n=5, seed=3, y0=10, y1=60, speed=4.0,
           size=(10, 26), highlight=None):
    """Drifting pixel clouds: puffy top, flat bottom, shaded underside."""
    rng = random.Random(seed)
    span = c.w + 100
    for i in range(n):
        bx, by = rng.uniform(0, span), rng.uniform(y0, y1)
        sz = rng.uniform(*size)
        sp = speed * rng.uniform(0.6, 1.4)
        x = (bx + t * sp) % span - 50
        k = rng.randint(3, 5)
        m = np.zeros((c.h, c.w), bool)
        for j in range(k):
            px_ = x - sz + (2 * sz) * (j + .5) / k + rng.uniform(-2, 2)
            r = sz * rng.uniform(.35, .6) * (1.15 - abs(j - (k - 1) / 2) / k)
            m |= c.mask_circle(px_, by - r * .45, r)
        bottom = int(round(by))
        m &= c._yy <= bottom
        a = c.arr()
        a[m] = c.col(col)
        if shade is not None:  # underside band
            band = m & (c._yy > bottom - max(2, sz * .18))
            a[band] = c.col(shade)
        if highlight is not None:  # lit top rim
            up = m & ~np.roll(m, 1, axis=0)
            a[up] = c.col(highlight)
        c.put(a)


def sea(c: Canvas, y0, t, col, light=None, highlight=None, seed=5, n=40):
    """Flat sea below y0 with drifting, flickering wave dashes."""
    c.rect(0, y0, c.w, c.h - y0, col)
    rng = random.Random(seed)
    for i in range(n):
        y = y0 + 2 + int((rng.random() ** 1.6) * (c.h - y0 - 3))
        depth = (y - y0) / max(1, c.h - y0)
        L = 2 + int(depth * 6)
        x = (rng.uniform(0, c.w) + t * rng.uniform(-3, 3) * (1 + depth)) % (c.w + 10) - 5
        phase = hrand(seed, i, int(t * 2 + i * .37))
        if phase < 0.6:
            c.line(x, y, x + L, y, light if light is not None else col)
        elif highlight is not None and phase > .93:
            c.line(x + 1, y, x + L - 1, y, highlight)


def rain(c: Canvas, t, col, n=120, seed=7, speed=220.0, slant=0.25, length=5, splash=None, ground=None):
    rng = random.Random(seed)
    H = c.h + length
    for i in range(n):
        x0, y0 = rng.uniform(0, c.w), rng.uniform(0, H)
        sp = speed * rng.uniform(0.8, 1.2)
        y = (y0 + sp * t) % H
        x = (x0 + slant * sp * t) % (c.w + 20) - 10
        c.line(x, y, x - slant * length, y - length, col)
        if splash is not None and ground is not None and abs(y - ground) < 3:
            c.px(x - 1, ground - 1, splash)
            c.px(x + 1, ground - 1, splash)


def snow(c: Canvas, t, cols=("white",), n=90, seed=9, speed=18.0, drift=6.0):
    rng = random.Random(seed)
    for i in range(n):
        x0, y0 = rng.uniform(0, c.w), rng.uniform(0, c.h)
        sp = speed * rng.uniform(.5, 1.5)
        ph = rng.uniform(0, 6.28)
        y = (y0 + sp * t) % c.h
        x = (x0 + drift * t + 3 * math.sin(t * 1.3 + ph)) % c.w
        c.px(x, y, cols[i % len(cols)])
        if i % 9 == 0:
            c.px(x + 1, y, cols[i % len(cols)])


def fireflies(c: Canvas, t, col, glow_col=None, n=14, seed=11, box=None):
    x0, y0, bw, bh = box or (0, 0, c.w, c.h)
    rng = random.Random(seed)
    for i in range(n):
        ax, ay = rng.uniform(0, bw), rng.uniform(0, bh)
        f1, f2, ph = rng.uniform(.2, .5), rng.uniform(.2, .6), rng.uniform(0, 6.28)
        x = x0 + (ax + 12 * math.sin(t * f1 + ph) + 5 * math.sin(t * f2 * 2.3)) % bw
        y = y0 + (ay + 8 * math.cos(t * f2 + ph)) % bh
        on = (math.sin(t * 2 + ph * 3) + 1) / 2
        if on > .3:
            if glow_col is not None and on > .7:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    c.px(x + dx, y + dy, glow_col)
            c.px(x, y, col)


def fire(c: Canvas, x, y, t, w=8, h=14, n=40, seed=13,
         cols=("white", "yellow", "orange", "red", "darkgray")):
    """Campfire/torch flame; (x, y) = base centre."""
    rng = random.Random(seed)
    for i in range(n):
        ph, sp = rng.random(), rng.uniform(1.2, 2.2)
        age = (t * sp + ph) % 1.0
        wob = math.sin(t * 9 + i) * 1.2
        px = x + (rng.random() - .5) * w * (1 - age) + wob * age
        py = y - age * h * rng.uniform(.6, 1.0)
        k = min(len(cols) - 1, int(age * len(cols)))
        c.px(px, py, cols[k])
        if age < .35:
            c.px(px, py + 1, cols[k])


def embers(c: Canvas, t, cols=("yellow", "orange"), n=25, seed=17, box=None, rise=15.0):
    x0, y0, bw, bh = box or (0, 0, c.w, c.h)
    rng = random.Random(seed)
    for i in range(n):
        ax, ay, sp = rng.uniform(0, bw), rng.uniform(0, bh), rng.uniform(.5, 1.5)
        y = y0 + (ay - rise * sp * t) % bh
        x = x0 + (ax + 4 * math.sin(t * 2 + i)) % bw
        if hrand(i, int(t * 6)) > .2:
            c.px(x, y, cols[i % len(cols)])


def lightning(c: Canvas, x, y0, y1, col="white", seed=0, glow_col=None):
    rng = random.Random(seed)
    px_, py_ = x, y0
    while py_ < y1:
        nx, ny = px_ + rng.randint(-6, 6), py_ + rng.randint(5, 12)
        c.line(px_, py_, nx, ny, col)
        if rng.random() < .25:
            c.line(nx, ny, nx + rng.randint(-10, 10), ny + rng.randint(4, 10), glow_col or col)
        px_, py_ = nx, ny


def moon(c: Canvas, x, y, r, col, dark_col=None, phase=0.0, halo=None):
    if halo is not None:
        c.glow(x, y, r * 3, halo, 0.35)
    c.circ(x, y, r, col)
    if dark_col is not None and phase:
        c.circ(x + phase * r, y - r * .2, r, dark_col)


def tree(c: Canvas, x, base_y, h, trunk, leaves, shade=None, kind="pine", t=0.0):
    """Simple tree; kind 'pine' or 'round'. Slight wind sway via t."""
    sway = int(round(math.sin(t * 1.5 + x) * .6))
    c.rect(x - 1, base_y - h // 3, 2, h // 3, trunk)
    if kind == "pine":
        for i in range(4):
            ww = (4 - i) * h // 9 + 2
            yy = base_y - h // 3 - i * h // 6
            c.poly([(x - ww + sway, yy), (x + ww + sway, yy), (x + sway, yy - h // 3)], leaves)
            if shade is not None:
                c.poly([(x + sway, yy), (x + ww + sway, yy), (x + sway, yy - h // 3)], shade)
    else:
        r = h // 3
        c.circ(x + sway, base_y - h + r, r, leaves)
        c.circ(x - r // 2 + sway, base_y - h + r + 3, r - 2, leaves)
        if shade is not None:
            c.circ(x + r // 2 + sway, base_y - h + r + 3, r - 2, shade)


def dialog_box(c: Canvas, text, t=None, cps=25, x=8, y=None, w=None, h=None,
               bg="black", border="white", fg="white", name=None, name_col="yellow"):
    """Classic RPG textbox; typewriter if t is given."""
    w = w or c.w - 16
    body = wrap_text(text, w - 10)
    nlines = body.count("\n") + 1 + (1 if name else 0)
    h = h or nlines * 10 + 8
    y = c.h - h - 6 if y is None else y
    c.rect(x, y, w, h, bg)
    c.rect(x, y, w, h, border, fill=False)
    c.rect(x + 1, y + 1, w - 2, h - 2, bg)
    ty = y + 5
    if name:
        c.text(name, x + 5, ty, name_col)
        ty += 10
    shown = typewriter(body, t, cps) if t is not None else body
    c.text(shown, x + 5, ty, fg)
    if t is not None and len(shown) >= len(body) and int(t * 3) % 2:
        c.poly([(x + w - 9, y + h - 6), (x + w - 5, y + h - 6), (x + w - 7, y + h - 4)], fg)


# ============================================================================
# Movie (timeline of scenes -> frames -> MP4/GIF)
# ============================================================================


class Ctx:
    """Scene context: t (sec in scene), dur, p (0..1), T (global sec), f (frame in scene)."""

    def __init__(self, t, dur, T, f, fps, name):
        self.t, self.dur, self.T, self.f, self.fps, self.name = t, dur, T, f, fps, name
        self.p = clamp(t / dur) if dur else 1.0

    def seg(self, a, b):
        return seg(self.t, a, b)


class Movie:
    def __init__(self, w=320, h=180, fps=24, scale=4, pal="pico8", strict_palette=False):
        self.w, self.h, self.fps, self.scale = w, h, fps, scale
        self.pal = use_palette(pal)
        self.scenes = []          # (name, start, dur, fn, fade_in, fade_out, fade_col)
        self.overlays = []        # fn(c, T)
        self.post = []            # fn(rgb_array_upscaled, T) -> array
        self.strict_palette = strict_palette

    # --- building the timeline --------------------------------------------------
    @property
    def duration(self):
        return sum(s[2] for s in self.scenes)

    def scene(self, dur, name=None, fade_in=0.0, fade_out=0.0, fade_col="black"):
        def deco(fn):
            self.add(fn, dur, name or fn.__name__, fade_in, fade_out, fade_col)
            return fn
        return deco

    def add(self, fn, dur, name=None, fade_in=0.0, fade_out=0.0, fade_col="black"):
        self.scenes.append((name or getattr(fn, "__name__", "scene"),
                            self.duration, dur, fn, fade_in, fade_out, fade_col))

    def scene_start(self, name):
        for s in self.scenes:
            if s[0] == name:
                return s[1]
        raise KeyError(name)

    def overlay(self, fn):
        self.overlays.append(fn)
        return fn

    def subtitle(self, text, start, end, col="white", bg="black", typing=True, cps=24, y=None):
        def ov(c, T):
            if start <= T < end:
                s = wrap_text(text, c.w - 24)
                shown = typewriter(s, T - start, cps) if typing else s
                lines = s.count("\n") + 1
                yy = y if y is not None else c.h - 12 - lines * 10
                c.text(shown, c.w // 2 - text_width(s) // 2, yy, col, outline=bg)
        self.overlays.append(ov)

    def letterbox(self, bar=14, col="black", start=0, end=None):
        def ov(c, T):
            if T >= start and (end is None or T < end):
                c.rect(0, 0, c.w, bar, col)
                c.rect(0, c.h - bar, c.w, bar, col)
        self.overlays.append(ov)

    def scanlines(self, strength=0.18):
        """CRT-ish look applied at output resolution."""
        def pp(a, T):
            a = a.astype(np.float32)
            a[self.scale - 1::self.scale] *= (1 - strength)
            return a.clip(0, 255).astype(np.uint8)
        self.post.append(pp)

    # --- rendering ----------------------------------------------------------------
    def frame_at(self, T):
        c = Canvas(self.w, self.h, self.pal)
        for (name, st, dur, fn, fi, fo, fc) in self.scenes:
            if st <= T < st + dur or (T >= st + dur and (name, st) == self.scenes[-1][:2]):
                t = min(T - st, dur - 1e-6)
                x = Ctx(t, dur, T, int(round(t * self.fps)), self.fps, name)
                fn(c, x)
                if fi and t < fi:
                    c.fade(1 - t / fi, fc)
                if fo and t > dur - fo:
                    c.fade((t - (dur - fo)) / fo, fc)
                break
        for ov in self.overlays:
            ov(c, T)
        if self.strict_palette:
            c.quantize()
        return c

    def _upscaled(self, c, T, scale=None):
        s = scale or self.scale
        a = c.arr()
        a = a.repeat(s, 0).repeat(s, 1)
        for pp in self.post:
            a = pp(a, T)
        return np.ascontiguousarray(a)

    def still(self, T, path, scale=None):
        Image.fromarray(self._upscaled(self.frame_at(T), T, scale)).save(path)
        return path

    def stills(self, times, path, cols=3, scale=2):
        """Contact sheet of frames at given times (for reviewing before render)."""
        times = list(times)
        tiles = []
        for T in times:
            c = self.frame_at(T)
            im = Image.fromarray(c.arr().repeat(scale, 0).repeat(scale, 1))
            lab = Canvas(im.width, 11, self.pal)
            lab.clear((24, 24, 24))
            lab.text(f"{T:.2f}S", 3, 2, (230, 230, 230))
            tile = Image.new("RGB", (im.width, im.height + 11))
            tile.paste(lab.img, (0, 0))
            tile.paste(im, (0, 11))
            tiles.append(tile)
        rows = math.ceil(len(tiles) / cols)
        tw, th = tiles[0].size
        sheet = Image.new("RGB", (cols * tw + (cols + 1) * 4, rows * th + (rows + 1) * 4), (40, 40, 40))
        for i, tl in enumerate(tiles):
            sheet.paste(tl, (4 + (i % cols) * (tw + 4), 4 + (i // cols) * (th + 4)))
        sheet.save(path)
        return path

    def render(self, path, audio=None, crf=16, start=0.0, end=None, verbose=True):
        """Render to .mp4 (H.264 + AAC) or .gif. audio: Song or path to .wav."""
        end = self.duration if end is None else end
        n = int(round((end - start) * self.fps))
        if path.lower().endswith(".gif"):
            return self._render_gif(path, start, n)
        import imageio_ffmpeg
        W, H = self.w * self.scale, self.h * self.scale
        wav = None
        if audio is not None:
            if isinstance(audio, str):
                wav = audio
            else:
                wav = os.path.join(tempfile.gettempdir(), f"pixelvid_{os.getpid()}.wav")
                audio.save_wav(wav, end - start, offset=start)
        gen = imageio_ffmpeg.write_frames(
            path, (W, H), fps=self.fps, codec="libx264", pix_fmt_in="rgb24",
            pix_fmt_out="yuv420p", quality=None, macro_block_size=1,
            output_params=["-crf", str(crf), "-preset", "medium", "-tune", "animation",
                           "-movflags", "+faststart"] + (["-shortest"] if wav else []),
            audio_path=wav, audio_codec="aac" if wav else None,
            ffmpeg_log_level="error")
        gen.send(None)
        for i in range(n):
            T = start + i / self.fps
            gen.send(self._upscaled(self.frame_at(T), T).tobytes())
            if verbose and i % (self.fps * 5) == 0:
                print(f"  frame {i}/{n}", flush=True)
        gen.close()
        if verbose:
            print(f"saved {path}  ({n} frames, {n / self.fps:.1f}s, {W}x{H})")
        return path

    def _render_gif(self, path, start, n, scale=None, fps=None):
        fps = fps or min(self.fps, 25)
        s = scale or max(1, self.scale // 2)
        frames = []
        for i in range(int(n * fps / self.fps)):
            T = start + i / fps
            frames.append(Image.fromarray(self._upscaled(self.frame_at(T), T, s)))
        frames[0].save(path, save_all=True, append_images=frames[1:], loop=0,
                       duration=int(1000 / fps), disposal=1)
        print(f"saved {path}")
        return path


# ============================================================================
# Chiptune synthesizer
# ============================================================================

SR = 44100
_NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_freq(tok):
    """'A4' -> 440.0, 'C#5', 'Eb3'."""
    name = tok[0].upper()
    i = 1
    semi = _NOTE[name]
    while i < len(tok) and tok[i] in "#b":
        semi += 1 if tok[i] == "#" else -1
        i += 1
    octave = int(tok[i:])
    midi = 12 * (octave + 1) + semi
    return 440.0 * 2 ** ((midi - 69) / 12)


def _osc(wave_, freq, n, duty=0.5, phase0=0.0):
    t = np.arange(n) / SR
    if np.isscalar(freq):
        ph = phase0 + freq * t
    else:
        ph = phase0 + np.cumsum(freq) / SR
    ph = ph % 1.0
    if wave_ == "square":
        return np.where(ph < duty, 1.0, -1.0)
    if wave_ == "triangle":
        x = 2 * np.abs(2 * ph - 1) - 1
        return np.round(x * 7.5) / 7.5          # 4-bit NES-style steps
    if wave_ == "saw":
        return 2 * ph - 1
    if wave_ == "sine":
        return np.sin(2 * np.pi * ph)
    if wave_ == "noise":
        return np.random.default_rng(int(np.sum(freq) if not np.isscalar(freq) else freq)).uniform(-1, 1, n)
    raise ValueError(wave_)


def _env(n, a=0.005, d=0.08, s=0.6, r=0.05):
    e = np.full(n, s, np.float32)
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n)
    e[:na] = np.linspace(0, 1, na, endpoint=False) if na else e[:na]
    nd2 = min(nd, max(0, n - na))
    if nd2:
        e[na:na + nd2] = np.linspace(1, s, nd2)
    nr = min(nr, n)
    if nr:
        e[n - nr:] *= np.linspace(1, 0, nr)
    return e


def lowpass(x, cutoff=3000.0):
    a = 1 - math.exp(-2 * math.pi * cutoff / SR)
    if _lfilter is not None:
        return _lfilter([a], [1, a - 1], x)
    k = max(1, int(SR / cutoff / 2))
    return np.convolve(x, np.ones(k) / k, mode="same")


def highpass(x, cutoff=200.0):
    return x - lowpass(x, cutoff)


class Song:
    """Step-sequenced chiptune.

    Pattern syntax (one token per step; a step = 1/steps_per_beat of a beat):
        C4  E#4  Bb3     play note
        -                hold previous note one more step
        .                rest
        C4+E4+G4         arpeggio chord (fast cycling, classic chip sound)
        |                bar separator (ignored)
    Drum tokens: k kick, s snare, h hat, o open hat, . rest
    """

    def __init__(self, bpm=110, steps_per_beat=4):
        self.bpm, self.spb = bpm, steps_per_beat
        self.step = 60.0 / bpm / steps_per_beat
        self.tracks, self.events, self.amb = [], [], []

    def track(self, pattern, wave="square", vol=0.2, duty=0.5, octave=0,
              adsr=(0.005, 0.08, 0.6, 0.04), vibrato=0.0, start=0.0, end=None,
              loop=True, cutoff=None):
        toks = [t for t in pattern.split() if t != "|"]
        self.tracks.append(dict(kind="tone", toks=toks, wave=wave, vol=vol, duty=duty,
                                octave=octave, adsr=adsr, vib=vibrato, start=start,
                                end=end, loop=loop, cutoff=cutoff))
        return self

    def drums(self, pattern, vol=0.3, start=0.0, end=None, loop=True):
        toks = [t for t in pattern.split() if t != "|"]
        self.tracks.append(dict(kind="drum", toks=toks, vol=vol, start=start, end=end, loop=loop))
        return self

    def sfx(self, kind, at, vol=0.4, **kw):
        self.events.append((kind, at, vol, kw))
        return self

    def ambience(self, kind, vol=0.1, start=0.0, end=None, fade=1.0):
        """kind: 'rain', 'wind', 'sea', 'hum', 'crowd'."""
        self.amb.append((kind, vol, start, end, fade))
        return self

    @property
    def pattern_seconds(self):
        return max((len(tr["toks"]) for tr in self.tracks), default=0) * self.step

    # --- synthesis ----------------------------------------------------------------
    def _tone_track(self, tr, total):
        out = np.zeros(total)
        toks = tr["toks"]
        if not toks:
            return out
        st = int(tr["start"] * SR)
        en = int((tr["end"] if tr["end"] is not None else total / SR) * SR)
        step_n = self.step * SR
        # expand into (token, start_step, length_steps)
        notes = []
        i = 0
        while i < len(toks):
            tk = toks[i]
            if tk in ".-":
                i += 1
                continue
            L = 1
            while i + L < len(toks) and toks[i + L] == "-":
                L += 1
            notes.append((tk, i, L))
            i += L
        plen = len(toks)
        rep = 0
        while True:
            base = st + int(rep * plen * step_n)
            if base >= en:
                break
            for tk, s0, L in notes:
                a = base + int(s0 * step_n)
                n = int(L * step_n)
                if a >= en:
                    break
                n = min(n, en - a, total - a)
                if n <= 0:
                    continue
                parts = tk.split("+")
                fr = [note_freq(p) * 2 ** tr["octave"] for p in parts]
                if len(fr) == 1:
                    f = np.full(n, fr[0])
                else:  # arpeggio at ~50 Hz switch rate
                    idx = (np.arange(n) // int(SR / 50)) % len(fr)
                    f = np.array(fr)[idx]
                if tr["vib"]:
                    tt = np.arange(n) / SR
                    f = f * (1 + tr["vib"] * np.sin(2 * np.pi * 5.5 * tt) * np.clip(tt / .25, 0, 1))
                sig = _osc(tr["wave"], f, n, tr["duty"])
                sig *= _env(n, *tr["adsr"])
                out[a:a + n] += sig * tr["vol"]
            if not tr["loop"]:
                break
            rep += 1
        if tr["cutoff"]:
            out = lowpass(out, tr["cutoff"])
        return out

    def _drum_hit(self, kind):
        rng = np.random.default_rng(hash(kind) & 0xffff)
        if kind == "k":
            n = int(.16 * SR)
            t = np.arange(n) / SR
            f = 45 + 110 * np.exp(-t * 35)
            return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18)
        if kind == "s":
            n = int(.14 * SR)
            t = np.arange(n) / SR
            return (highpass(rng.uniform(-1, 1, n), 900) * .9 +
                    np.sin(2 * np.pi * 190 * t) * .4) * np.exp(-t * 28)
        if kind in "ho":
            n = int((.05 if kind == "h" else .22) * SR)
            t = np.arange(n) / SR
            return highpass(rng.uniform(-1, 1, n), 6000) * np.exp(-t * (70 if kind == "h" else 14)) * .6
        return np.zeros(1)

    def _drum_track(self, tr, total):
        out = np.zeros(total)
        st = int(tr["start"] * SR)
        en = int((tr["end"] if tr["end"] is not None else total / SR) * SR)
        step_n = self.step * SR
        hits = {k: self._drum_hit(k) for k in "ksho"}
        rep = 0
        plen = len(tr["toks"])
        while True:
            base = st + int(rep * plen * step_n)
            if base >= en:
                break
            for i, tk in enumerate(tr["toks"]):
                a = base + int(i * step_n)
                if a >= en:
                    break
                for ch in tk:
                    if ch in hits:
                        h = hits[ch]
                        m = min(len(h), total - a)
                        out[a:a + m] += h[:m] * tr["vol"]
            if not tr["loop"]:
                break
            rep += 1
        return out

    @staticmethod
    def sfx_wave(kind, **kw):
        rng = np.random.default_rng(7)

        def tone(f0, f1, dur, wave_="square", duty=.5, decay=8.0):
            n = int(dur * SR)
            t = np.arange(n) / SR
            f = f0 * (f1 / f0) ** (t / dur)
            return _osc(wave_, f, n, duty) * np.exp(-t * decay)
        if kind == "blip":
            return tone(880, 880, .07, decay=20)
        if kind == "select":
            return np.concatenate([tone(660, 660, .05, decay=5), tone(990, 990, .08, decay=20)])
        if kind == "jump":
            return tone(260, 720, .18, duty=.25, decay=6)
        if kind == "coin":
            return np.concatenate([tone(988, 988, .06, decay=2), tone(1319, 1319, .3, decay=9)])
        if kind == "powerup":
            parts = [tone(f, f * 1.02, .06, duty=.25, decay=3) for f in
                     (262, 330, 392, 523, 659, 784, 1047)]
            return np.concatenate(parts)
        if kind == "hit":
            n = int(.15 * SR)
            t = np.arange(n) / SR
            return rng.uniform(-1, 1, n) * np.exp(-t * 25) * .8 + tone(180, 60, .15, decay=15)[:n] * .6
        if kind == "step":
            n = int(.04 * SR)
            return lowpass(rng.uniform(-1, 1, n), 1500) * np.exp(-np.arange(n) / SR * 90) * 1.5
        if kind == "explosion":
            n = int(1.2 * SR)
            t = np.arange(n) / SR
            return lowpass(rng.uniform(-1, 1, n), 900) * np.exp(-t * 3.5) * 2.2
        if kind == "thunder":
            n = int(3.0 * SR)
            t = np.arange(n) / SR
            x = lowpass(lowpass(rng.uniform(-1, 1, n), 300), 200) * 6
            crack = highpass(rng.uniform(-1, 1, n), 1500) * np.exp(-t * 12) * .5
            return (x * (np.exp(-t * 1.2)) * (0.6 + 0.4 * np.sin(t * 9) ** 2) + crack)
        if kind == "whoosh":
            n = int(.5 * SR)
            t = np.arange(n) / SR
            env = np.sin(np.pi * t / .5) ** 2
            return highpass(lowpass(rng.uniform(-1, 1, n), 2500), 400) * env * 1.4
        if kind == "laser":
            return tone(1400, 200, .25, duty=.5, decay=6)
        if kind == "hurt":
            return tone(400, 120, .25, duty=.25, decay=5)
        if kind == "door":
            return tone(90, 70, .35, wave_="triangle", decay=6) + np.concatenate(
                [lowpass(rng.uniform(-1, 1, int(.05 * SR)), 2000), np.zeros(int(.3 * SR))])[:int(.35 * SR)] * .4
        if kind == "chime":
            parts = [tone(f, f, .5, wave_="triangle", decay=4) for f in (1047, 1319, 1568)]
            n = int(.9 * SR)
            out = np.zeros(n)
            for i, p in enumerate(parts):
                a = int(i * .12 * SR)
                out[a:a + len(p)] += p[:n - a]
            return out
        if kind == "heartbeat":
            b = tone(70, 50, .12, wave_="sine", decay=18)
            out = np.zeros(int(.6 * SR))
            out[:len(b)] += b
            out[int(.2 * SR):int(.2 * SR) + len(b)] += b * .7
            return out * 2
        raise ValueError(f"unknown sfx {kind}")

    def _ambience(self, kind, total):
        rng = np.random.default_rng(99)
        n = total
        t = np.arange(n) / SR
        white = rng.uniform(-1, 1, n)
        if kind == "rain":
            return highpass(lowpass(white, 5000), 800) * (0.8 + 0.2 * np.sin(t * .7))
        if kind == "wind":
            return lowpass(white, 500) * 3 * (0.5 + 0.5 * np.sin(t * .4) * np.sin(t * .23 + 1)) ** 2
        if kind == "sea":
            return lowpass(white, 700) * 2.5 * (0.35 + 0.65 * (0.5 + 0.5 * np.sin(t * 2 * np.pi / 6)) ** 3)
        if kind == "hum":
            return (np.sin(2 * np.pi * 60 * t) * .5 + np.sin(2 * np.pi * 120 * t) * .2) * .6
        if kind == "crowd":
            return lowpass(highpass(white, 300), 1500) * 1.5 * (0.7 + 0.3 * np.sin(t * 1.3))
        raise ValueError(kind)

    def render(self, duration, offset=0.0, master=0.9, fade_out=1.5):
        total = int((duration + offset) * SR)
        mix = np.zeros(total)
        for tr in self.tracks:
            mix += self._tone_track(tr, total) if tr["kind"] == "tone" else self._drum_track(tr, total)
        for kind, at, vol, kw in self.events:
            w = self.sfx_wave(kind, **kw) * vol
            a = int(at * SR)
            if 0 <= a < total:
                m = min(len(w), total - a)
                mix[a:a + m] += w[:m]
        for kind, vol, st, en, fd in self.amb:
            a = self._ambience(kind, total) * vol
            env = np.ones(total)
            t = np.arange(total) / SR
            en = en if en is not None else duration + offset + 10
            env *= np.clip((t - st) / max(fd, 1e-3), 0, 1) * np.clip((en - t) / max(fd, 1e-3), 0, 1)
            mix += a * env
        mix = mix[int(offset * SR):]
        mix = np.tanh(mix * 1.1)                      # gentle soft-clip glue
        peak = np.abs(mix).max() or 1
        mix = mix / peak * master
        nf = int(fade_out * SR)
        if nf and nf < len(mix):
            mix[-nf:] *= np.linspace(1, 0, nf)
        return mix

    def save_wav(self, path, duration, offset=0.0):
        mix = self.render(duration, offset)
        data = (mix * 32767).astype(np.int16)
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(data.tobytes())
        return path


# ============================================================================
# CLI helper for film scripts
# ============================================================================

def main(mv: Movie, audio=None, out_dir=None, name=None):
    """Standard CLI for a film script:
        python film.py preview [out_dir]        -> contact sheet, 12 evenly spaced frames
        python film.py stills 1.5,7,12 [out_dir] -> contact sheet at chosen seconds
        python film.py render [out_dir]         -> MP4 with audio
        python film.py gif [out_dir]            -> animated GIF (half scale)
        python film.py wav [out_dir]            -> soundtrack only
    audio may be a Song or a zero-arg function returning one."""
    import sys
    args = sys.argv[1:]
    mode = args[0] if args else "preview"
    name = name or os.path.splitext(os.path.basename(sys.argv[0]))[0]
    times = None
    if mode == "stills":
        times = [float(v) for v in args[1].split(",")]
        args = args[1:]
    out_dir = args[1] if len(args) > 1 else (out_dir or os.getcwd())
    os.makedirs(out_dir, exist_ok=True)
    if callable(audio) and not isinstance(audio, Song):
        audio = audio()
    if mode in ("preview", "stills"):
        if times is None:
            n = 12
            times = [round((i + .5) * mv.duration / n, 2) for i in range(n)]
        path = mv.stills(times, os.path.join(out_dir, f"{name}_{mode}.png"))
        print(f"saved {path}  (scenes: " + ", ".join(
            f"{s[0]}@{s[1]:.1f}s" for s in mv.scenes) + f"; total {mv.duration:.1f}s)")
    elif mode == "render":
        mv.render(os.path.join(out_dir, f"{name}.mp4"), audio=audio)
    elif mode == "gif":
        mv.render(os.path.join(out_dir, f"{name}.gif"))
    elif mode == "wav":
        audio.save_wav(os.path.join(out_dir, f"{name}.wav"), mv.duration)
        print("saved wav")
    else:
        raise SystemExit(f"unknown mode {mode}")


__all__ = [n for n in dir() if not n.startswith("_")] + ["_B32"]
