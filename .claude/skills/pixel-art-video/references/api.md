# pixelvid — шпаргалка по API

```python
import os, sys
sys.path.insert(0, os.path.expanduser("~/.claude/skills/pixel-art-video/scripts"))  # или путь к scripts/ этого скилла
from pixelvid import *
```
Цвет везде: индекс палитры (`8`), имя (`"red"`), `"#ff8800"`, или `(r, g, b)`.
Всё рисование — чистая функция времени (кадр можно отрендерить в любом порядке).

## Movie — таймлайн
```python
mv = Movie(w=320, h=180, fps=24, scale=4, pal="pico8", strict_palette=False)  # также ставит палитру по умолчанию для спрайтов

@mv.scene(dur, name=None, fade_in=0, fade_out=0, fade_col="black")
def scene(c, x): ...        # c: Canvas; x.t сек в сцене, x.p 0..1, x.dur, x.T глобальное, x.f кадр
mv.add(fn, dur, ...)          # то же без декоратора (удобно для цикла сцен)
mv.scene_start("name")        # секунда начала сцены (для синхронизации звука)
mv.duration
mv.overlay(fn)                # fn(c, T) поверх всех сцен
mv.subtitle(text, start, end, col="white", bg="black", typing=True, cps=24, y=None)
mv.letterbox(bar=14, col="black", start=0, end=None)
mv.scanlines(0.18)            # CRT-строки на выходном разрешении
mv.stills([t1, t2, ...], "sheet.png", cols=3)   # contact sheet для ревью
mv.still(T, "frame.png")
mv.render("out.mp4", audio=song, crf=16)        # .gif тоже можно
main(mv, audio=song_or_fn)    # CLI: preview | stills 1,5,9 | render | gif | wav [out_dir]
```

## Canvas — рисование (холст низкого разрешения)
```python
c.clear(col); c.px(x, y, col)
c.rect(x, y, w, h, col, fill=True); c.line(x0, y0, x1, y1, col, width=1)
c.circ(cx, cy, r, col, fill=True); c.ellipse(cx, cy, rx, ry, col); c.poly(pts, col)
c.blit(sprite, x, y, flip=False); c.blit_center(sprite, cx, bottom_y, flip=False)
c.text(s, x, y, col, align="left|center|right", scale=1, shadow=None, outline=None)
# маски и дизеринг
m = c.mask_poly(pts) | c.mask_circle(cx, cy, r) | c.mask_rect(x, y, w, h)
c.dither_fill(mask, col, level)          # «полупрозрачность» 0..1 (или массив HxW)
c.dither_rect(x, y, w, h, col, level)
c.vgradient(y0, y1, [cols...])           # небо, дизер между полосами
c.glow(cx, cy, r, col, strength=.5)      # ореол
c.night(amount=.8, lights=[(x, y, r)])   # ночь + зоны света
c.tint_area(mask, factor=.6, tint=(0,0,0), level=1)   # тень/подсветка области
c.reflect(y_line, t, amp=1)              # отражение в воде (вызывать после всего верхнего)
c.fade(level, col)                       # дизер-затемнение (переходы, вспышки)
c.iris(cx, cy, r, col)                   # диафрагма
c.shift(dx, dy)                          # тряска камеры
c.quantize()                             # привести к палитре
```

## Спрайты
```python
S = Sprite.from_ascii("""
..00..
.0880.
""", legend={"0": "black", "8": "red"})   # без legend: символы 0-9a-v = индексы палитры; '.' прозрачно
S.flipped(); S.vflipped(); S.scaled(2); S.outlined("black"); S.silhouette("black")
S.recolored({"red": "blue"}); S.squashed(.2)  # сжатие(+)/растяжение(-); S.w; S.h
hero = humanoid(hair=, skin=, eye=, coat=, coat_shade=, pants=, pants_back=, boots=, outline=, hood=False)
hero["walk"] (4 кадра), hero["idle"] (моргание), hero["hand"] = (x, y) точка руки
anim_frame(frames, t, fps=8, loop=True)
```
Свои спрайты рисуй ASCII-сеткой: 8–16 px для предметов, 12–24 px для персонажей,
2–4 кадра на анимацию. Всегда проверяй их на contact sheet.

## Процедурные декорации и частицы
```python
stars(c, t, n=60, seed=1, cols=("white","lightgray"), y_max=None)
mountains(c, base_y, height, col, seed=0, scroll=0, rim=None)   # бесшовные, для параллакса
hills(c, base_y, height, col, seed=0, scroll=0, rim=None)
city(c, base_y, col, win_col=None, seed=0, scroll=0, t=0, min_h=15, max_h=60, lit=.25)
clouds(c, t, col, shade=None, highlight=None, n=5, seed=3, y0=10, y1=60, speed=4, size=(10, 26))
sea(c, y0, t, col, light=None, highlight=None, n=40)
tree(c, x, base_y, h, trunk, leaves, shade=None, kind="pine|round", t=0)
moon(c, x, y, r, col, dark_col=None, phase=0, halo=None)
rain(c, t, col, n=120, speed=220, slant=.25, length=5, splash=None, ground=None)
snow(c, t, cols=("white",), n=90, speed=18, drift=6)
fireflies(c, t, col, glow_col=None, n=14, box=(x, y, w, h))
fire(c, x, y, t, w=8, h=14, cols=(...))     # костёр/факел
embers(c, t, cols, n=25, box=None)
lightning(c, x, y0, y1, col="white", seed=0)
dialog_box(c, text, t=None, cps=25, name=None)   # RPG-окно с печатью текста
```

## Время и анимация
```python
seg(t, a, b)          # прогресс 0..1 внутри окна [a, b]
keys(t, [(0, 10), (2, 80), (3, 80)], ease=ease_in_out)   # ключевые кадры (числа/кортежи)
lerp, clamp, ease_in, ease_out, ease_in_out, ease_back, bounce, pingpong(t, period)
stepped(t, 12)        # «рывками», как на двойках
ramp([cols], k)       # цвет по прогрессу (палитровое проявление)
hrand(*keys)          # детерминированный random 0..1 (для мерцаний)
typewriter(s, t, cps), wrap_text(s, max_w), text_width(s, scale)
```

## Звук: Song (чиптюн-синтезатор)
```python
s = Song(bpm=100, steps_per_beat=4)          # шаг = 1/16 ноты; такт = 16 шагов = 240/bpm сек
s.track("C4 - E4 - G4 - . . | A4+C5+E5 - - -", wave="square", duty=.25, vol=.15,
        octave=0, adsr=(a, d, s, r), vibrato=.006, start=0, end=None, loop=True, cutoff=None)
#   нота | "-" держать | "." пауза | "C4+E4+G4" арпеджио-аккорд | "|" разделитель такта
#   wave: square (duty .125/.25/.5), triangle (бас), saw, sine, noise
s.drums("k . h . s . h . k k h . s . h o", vol=.3)      # k бочка, s снейр, h хэт, o открытый
s.sfx(kind, at=сек, vol=.4)   # blip select jump coin powerup hit hurt step explosion thunder
                              # whoosh laser door chime heartbeat
s.ambience(kind, vol=.1, start=0, end=None, fade=1)    # rain wind sea hum crowd
s.save_wav(path, duration)    # обычно не нужно: mv.render(audio=s) делает сам
```
Роли: мелодия — square .25/.125 vol .12–.18; бас — triangle vol .25–.35;
гармония — арпеджио-аккорды square vol .04–.07 с `cutoff=2500`; барабаны .2–.35.
Паттерны зацикливаются до конца фильма; последние 1.5 с музыка затухает.
Синхронизация: `s.sfx("thunder", at=mv.scene_start("storm") + 1.0)`.

Прогрессии: грусть Am–F–C–G; героика C–G–Am–F (130–150 bpm); тайна Dm–Bb–Gm–A;
уют Cmaj7–Am7–Dm7–G7 (70–85 bpm, арпеджио); тревога — одна низкая нота + heartbeat.

## Имена цветов в разных палитрах
Каждая палитра имеет свои имена (`PALETTES["endesga32"].names`). Общие имена
(`black white gray darkgray lightgray red orange yellow gold green darkgreen blue
darkblue navy sky cyan purple pink magenta brown peach skin sand cream ...`)
работают с ЛЮБОЙ палитрой: если такого имени нет, берётся ближайший цвет палитры.
Поэтому встроенные эффекты работают в любой палитре, но для точного контроля
передавай имена/индексы именно своей палитры.
