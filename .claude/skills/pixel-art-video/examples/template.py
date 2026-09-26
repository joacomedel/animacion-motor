"""
<НАЗВАНИЕ> — <логлайн в одно предложение>.

Beats:
  1 <scene>  <dur>s  <what happens>
  ...
Run:  python film.py preview|stills 1,5,9|render|gif|wav [out_dir]
"""
import math
import os
import sys

# path to the skill's engine: env var PIXELVID_DIR, else the default Claude Code skills folder
sys.path.insert(0, os.environ.get("PIXELVID_DIR")
                or os.path.expanduser("~/.claude/skills/pixel-art-video/scripts"))
from pixelvid import *  # noqa

mv = Movie(320, 180, fps=24, scale=4, pal="pico8")   # vertical: Movie(180, 320, scale=6)
W, H = mv.w, mv.h

HERO = humanoid(coat="red", coat_shade="darkpurple")


@mv.scene(5.0, fade_in=0.8)
def opening(c, x):
    t = x.t
    c.vgradient(0, 120, ["darkblue", "darkpurple", "pink"])
    stars(c, t, n=40, y_max=70)
    mountains(c, 125, 40, "darkpurple", seed=1, scroll=t * 3)
    hills(c, 140, 15, "darkblue", seed=2, scroll=t * 8)
    c.rect(0, 140, W, H - 140, "black")
    c.blit_center(anim_frame(HERO["walk"], t, 8), 160, 141)
    k = seg(t, 1.0, 2.0)
    if k:
        c.text("TITLE", W // 2, 40, ramp(["darkpurple", "pink", "white"], k),
               align="center", scale=2, shadow="black")


@mv.scene(5.0, fade_out=1.5)
def ending(c, x):
    t = x.t
    c.clear("black")
    c.text("КОНЕЦ", W // 2, H // 2 - 7, "white", align="center", scale=2)


def soundtrack():
    s = Song(bpm=90)
    s.track("A4 - C5 - E5 - C5 - | G4 - B4 - D5 - B4 -", wave="square", duty=.25, vol=.14)
    s.track("A2 - - - - - - - | G2 - - - - - - -", wave="triangle", vol=.3)
    s.ambience("wind", vol=.08)
    return s


if __name__ == "__main__":
    main(mv, audio=soundtrack)
