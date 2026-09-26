# pixel-art-video — a Claude skill for making pixel-art videos with code

**English** · [Русский](README.ru.md)

This skill teaches Claude to come up with a story and turn it into a finished
pixel-art clip (MP4 or GIF) with 8-bit music and sound effects. Everything is made
with Python code: no image-generation models, no video editor, no pre-made assets.

Ask Claude, for example:
- "make a pixel-art cartoon about a cat on a rooftop"
- "come up with a story and make a 30-second video in the style of old games"
- "a vertical Shorts clip: a robot finds a flower in a junkyard"
- "a lofi loop: a cozy room, rain outside the window"

| Lighthouse (27 s) | Star (23 s) | Super Pixel (36 s) |
|---|---|---|
| ![](previews/lighthouse_preview.png) | ![](previews/star_cat_preview.png) | ![](previews/super_pixel_preview.png) |

## What's inside

```
pixel-art-video/
├── SKILL.md              instructions for Claude: story → code → frame review → video
├── scripts/pixelvid.py   the engine: palettes, pixel font (Latin + Cyrillic),
│                         sprites from ASCII art, a walking character, rain/snow/fire/clouds,
│                         light and night, reflections, transitions, subtitles, scene timeline,
│                         chiptune synth (melody, bass, chords, drums, 15 sound effects)
├── references/
│   ├── story.md          how to invent stories: formats, beats, idea generator
│   ├── craft.md          pixel-art rules for video + review checklist
│   └── api.md            engine cheat sheet and music notation
├── examples/             template.py + three finished films (sources of the clips above)
└── previews/             preview images of the examples
```

The skill's own documentation (`SKILL.md`, `references/`) is written in Russian;
Claude reads it fine and answers in whatever language you write to it.

## Installation

You need Python 3.10+ and a few packages:

```bash
pip install pillow numpy imageio imageio-ffmpeg scipy
```

`imageio-ffmpeg` ships its own ffmpeg, so there's nothing else to install; `scipy` is optional.

- **Claude Code:** unzip so that you get `~/.claude/skills/pixel-art-video/SKILL.md`
  (on Windows: `C:\Users\<name>\.claude\skills\pixel-art-video\SKILL.md`),
  then start a new session.
- **Claude.ai / Claude Desktop:** upload the zip in Settings, under Skills
  (code execution must be enabled).

If the skill lives somewhere other than `~/.claude/skills/`, point the engine path to it
with the environment variable `PIXELVID_DIR=<path>/pixel-art-video/scripts`.
Claude can also fix the path in `film.py` itself.

## Running the examples without Claude

```bash
cd pixel-art-video/examples
python lighthouse.py preview out      # contact sheet of frames for review
python lighthouse.py render out       # 1280×720 MP4 with sound
python super_pixel.py gif out         # GIF
```

Modes: `preview`, `stills 1.5,7,12`, `render`, `gif`, `wav`.

## Credits

Palettes from [Lospec](https://lospec.com/palette-list): PICO-8 (Lexaloffle),
Sweetie 16 (GrafxKid), Endesga 32 (ENDESGA), SLSO8, NYX8, and the classic Game Boy palette.
"Super Pixel" is an original platformer-style clip: its characters, graphics and music
are original and not taken from any existing game.

## License

[MIT](LICENSE): free to use, modify and share, including commercially,
as long as the copyright notice is kept.
