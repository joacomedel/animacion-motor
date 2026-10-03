"""Demo visual de las implementaciones nuevas (tasks 017-024, 027 + luces/bloom/paleta en el motor).

Genera láminas "antes vs después" de cada feature, más una que muestra que TODO lo que dibuja el motor
(sprite, luces, bloom, iluminación dinámica y ambiente) cae dentro de la paleta fija del estilo.

Uso (desde la raíz del repo):
    .venv/bin/python demos/demo_tasks.py [--out docs/diagnostico/demo_tasks]

Requiere el entorno headless (SDL_VIDEODRIVER=dummy) para no abrir ventana.
"""

import argparse
import copy
import os
import sys
from pathlib import Path

# El repo está un nivel arriba: correrlo directo sin depender del cwd.
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import numpy as np  # noqa: E402
import pygame  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from sprites_lib import armado, estilos, skins  # noqa: E402
from sprites_lib.paleta import hex_rgb  # noqa: E402
from motor import equipo as eq  # noqa: E402
from motor.camara import Camara  # noqa: E402
from motor.config import SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from motor.estado import Estado  # noqa: E402
from motor.main import elementos_ordenados  # noqa: E402
from motor.mundo import ARBOL, Mundo  # noqa: E402
from motor.renderer import LUCES_MOTOR, Renderer  # noqa: E402

SKIN = "skins/caballero_carmesi.png"
BG = (18, 18, 24)
CARD = (34, 34, 44)
try:
    FONT = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
except Exception:  # pragma: no cover - depende de las fuentes del sistema
    FONT = ImageFont.load_default()


# ---------------------------------------------------------------- utilidades de composición


def pil_de_sup(s):
    return Image.frombytes("RGBA", s.get_size(), pygame.image.tostring(s, "RGBA"))


def tile(img, caption, zoom=1):
    im = img.convert("RGBA")
    im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
    pad, cap = 8, 28
    c = Image.new("RGBA", (im.width + pad * 2, im.height + cap + pad * 2), CARD)
    c.alpha_composite(im, (pad, pad))
    ImageDraw.Draw(c).text((pad, pad + im.height + 6), caption, fill=(235, 235, 245), font=FONT)
    return c


def hcat(imgs, gap=10):
    h = max(i.height for i in imgs)
    c = Image.new("RGBA", (sum(i.width for i in imgs) + gap * (len(imgs) - 1), h), BG)
    x = 0
    for i in imgs:
        c.alpha_composite(i, (x, 0))
        x += i.width + gap
    return c


def vcat(imgs, gap=10):
    w = max(i.width for i in imgs)
    c = Image.new("RGBA", (w, sum(i.height for i in imgs) + gap * (len(imgs) - 1)), BG)
    y = 0
    for i in imgs:
        c.alpha_composite(i, (0, y))
        y += i.height + gap
    return c


def columna(img_a, cap_a, img_b, cap_b, zoom=1):
    return vcat([tile(img_a, cap_a, zoom), tile(img_b, cap_b, zoom)])


# ---------------------------------------------------------------- features del kit (render directo)


def ficha_equipada():
    f = skins.ficha(SKIN, nombre="demo")
    return eq.ficha_con_equipo(f, ["armadura_malla", "guante_cuero", "sombrero", "antorcha"])


def render(estilo, ficha, pose="quieto", p=0, mira="S", luces=None, bloom=False, mat_flat=False):
    base = estilos.ESTILOS[estilo]["render"]
    orig = base.get("luces")
    if luces is not None:
        base["luces"] = luces
    if mat_flat:
        ficha = copy.deepcopy(ficha)
        for m in ficha["paleta"].values():
            if isinstance(m, dict):
                m["especular"] = 0.0
                m["textura"] = None
    try:
        return armado.render_cuadro(ficha, estilo, pose, p, mira, bloom=bloom)
    finally:
        if orig is None:
            base.pop("luces", None)
        else:
            base["luces"] = orig


def galeria_features(out):
    f = ficha_equipada()
    base = render("stardew", f)
    luces = render("stardew", f, luces=LUCES_MOTOR)
    bloom = render("stardew", f, bloom=True)
    flat = render("stardew", f, mat_flat=True)
    normal = Image.fromarray(base.buf["normal"], "RGB")
    por = {"S": [base.img.convert("RGBA")]}
    skins.ajustar_a_paleta_fija(por, "stardew")
    fija = por["S"][0]
    cols = [
        columna(base.img, "sin luces", luces.img, "+ Luces (task-021)", 9),
        columna(flat.img, "especular 0", base.img, "+ Materiales (task-022)", 9),
        columna(base.img, "sin bloom", bloom.img, "+ Bloom (task-023)", 9),
        columna(base.img, "paleta libre", fija, "paleta fija (task-017)", 9),
        columna(base.img, "color", normal, "normal map (task-019/024)", 9),
    ]
    salida = hcat(cols)
    salida.save(Path(out) / "galeria_features.png")
    return salida.size


# ---------------------------------------------------------------- motor en vivo (luces, sombra, paleta)


def galeria_motor(out):
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    r = Renderer("stardew8", skin=SKIN, zoom=10)
    est = Estado(x=0, y=0, z=0, animacion="idle", direccion="S", frame=0)
    base = r.renderizar(est)
    normal = r.buffer_normal()
    ilu = r.iluminar(base, normal, (base.get_width() - 8, base.get_height() // 3), (255, 180, 80), 160, 1.5)
    sombra = r.sombra()

    def con_sombra(sp):
        c = Image.new("RGBA", (sp.get_width() + 24, sp.get_height() + 24), (0, 0, 0, 0))
        c.alpha_composite(
            pil_de_sup(sombra),
            (12 + (sp.get_width() - sombra.get_width()) // 2, sp.get_height() - sombra.get_height() // 3),
        )
        c.alpha_composite(pil_de_sup(sp), (12, 12))
        return c

    cols = [
        columna(pil_de_sup(base), "sin luz", pil_de_sup(ilu), "+ luz dinamica (task-020)", 1),
        columna(pil_de_sup(base), "sin sombra", con_sombra(base), "+ sombra de contacto", 1),
    ]
    salida = hcat(cols)
    salida.save(Path(out) / "galeria_motor.png")
    pygame.quit()
    return salida.size


def _swatch(estilo, ancho):
    """Franja con todos los colores de la paleta fija del estilo."""
    cols = estilos.ESTILOS[estilo]["render"].get("paleta_fija") or []
    rgb = [hex_rgb(c) for c in cols]
    por_fila = 10
    cw, ch = max(8, ancho // por_fila), 14
    filas = (len(rgb) + por_fila - 1) // por_fila
    img = Image.new("RGBA", (cw * por_fila, ch * filas), BG)
    for i, c in enumerate(rgb):
        x, y = (i % por_fila) * cw, (i // por_fila) * ch
        ImageDraw.Draw(img).rectangle([x, y, x + cw - 1, y + ch - 1], fill=(*c, 255))
    return img


def galeria_paleta(out):
    """El mismo sprite con cada efecto del motor: todos los colores caen en la paleta fija."""
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    r = Renderer("stardew8", skin=SKIN, zoom=8)
    est = Estado(x=0, y=0, z=0, animacion="idle", direccion="S", frame=0)
    base = r.renderizar(est)
    r.set_luces(True)
    luces = r.renderizar(est)
    r.set_luces(False)
    r.set_equipo(["antorcha"])
    r.set_bloom(True)
    bloom = r.renderizar(est)
    normal = r.buffer_normal()
    encendida = r.iluminar(bloom, normal, (bloom.get_width() - 8, bloom.get_height() // 3), (255, 180, 80), 160, 1.5)
    r.set_bloom(False)
    r.set_equipo([])
    r.set_ambiente("noche")
    noche = r.renderizar(est)

    ok = {hex_rgb(c) for c in r.paleta_fija}
    fuera = {}
    for nombre, sup in (("base", base), ("luces", luces), ("bloom", bloom), ("antorcha", encendida), ("noche", noche)):
        a = pygame.surfarray.array3d(sup)
        al = pygame.surfarray.array_alpha(sup)
        fuera[nombre] = len({tuple(int(x) for x in c) for c in a[al > 0]} - ok)

    cols = [
        tile(pil_de_sup(base), "base", 1),
        tile(pil_de_sup(luces), "+ luces (task-021)", 1),
        tile(pil_de_sup(bloom), "+ bloom (task-023)", 1),
        tile(pil_de_sup(encendida), "+ antorcha (task-020)", 1),
        tile(pil_de_sup(noche), "ambiente noche", 1),
    ]
    fila = hcat(cols)
    sw = tile(_swatch("stardew8", fila.width - 16), "paleta fija stardew8 (50 colores) — fuera de paleta: "
                                                    + ", ".join(f"{k}={v}" for k, v in fuera.items()), 1)
    salida = vcat([fila, sw])
    salida.save(Path(out) / "galeria_paleta.png")
    pygame.quit()
    return salida.size


# ---------------------------------------------------------------- mundo (depth-sorting + sombra)


def galeria_mundo(out):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    r = Renderer("stardew8", skin=SKIN, zoom=3)
    m = Mundo(ancho=80, alto=50, tile=16)
    cy, cx = m.alto // 2, m.ancho // 2
    for dy, dx in [(-1, -2), (-1, 2), (2, 0), (1, 3), (0, -3)]:
        m.mapa[cy + dy][cx + dx] = ARBOL
    cam = Camara(SCREEN_WIDTH, SCREEN_HEIGHT, m)
    est = Estado(x=m.ancho_px // 2, y=m.alto_px // 2, z=0, animacion="idle", direccion="S", frame=0)
    personaje = r.renderizar(est)
    px, py = r.pies()
    w, h = personaje.get_size()
    char_px = min(max(est.x, px), m.ancho_px - (w - px))
    char_py = min(max(est.y, py), m.alto_px - (h - py))
    cam_x, cam_y = cam.seguir(char_px, char_py)
    screen.fill((0, 0, 0))
    screen.blit(r.ambientar(m.superficie_piso()), (-cam_x, -cam_y))
    for elem in elementos_ordenados(m, cam_x, cam_y, SCREEN_WIDTH, SCREEN_HEIGHT, char_py):
        if elem[0] == "arbol":
            tx, ty = elem[1], elem[2]
            screen.blit(r.ambientar(m._render_arbol(tx, ty)), (tx * m.tile - cam_x, ty * m.tile - cam_y))
        else:
            s = r.sombra()
            screen.blit(s, (int(char_px - cam_x - s.get_width() // 2),
                            int(char_py - cam_y - s.get_height() // 2 - est.z)))
            screen.blit(personaje, (int(char_px - cam_x - px), int(char_py - cam_y - py - est.z)))
    full = pil_de_sup(screen)
    cx0, cy0 = int(char_px - cam_x), int(char_py - cam_y)
    box = (max(0, cx0 - 170), max(0, cy0 - 210), min(SCREEN_WIDTH, cx0 + 170), min(SCREEN_HEIGHT, cy0 + 80))
    salida = tile(full.crop(box), "Mundo: depth-sorting por Y + sombra   (task-027 + sombra)", 2)
    salida.save(Path(out) / "galeria_mundo.png")
    pygame.quit()
    return salida.size


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="docs/diagnostico/demo_tasks", help="carpeta de salida")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for nombre, fn in (
        ("galeria_features.png", galeria_features),
        ("galeria_motor.png", galeria_motor),
        ("galeria_paleta.png", galeria_paleta),
        ("galeria_mundo.png", galeria_mundo),
    ):
        print(nombre, fn(out))


if __name__ == "__main__":
    main()
