"""Muñeco base: sin skin ni ficha de personaje, solo para ver y probar un ciclo/pose antes de aplicarlo a alguien
(el mismo pipeline de render que las skins y los personajes, con una ficha mínima fija). Genérico por animación:
no hay nada de "caminar" fijo acá, `demo(anim=...)` sirve para cualquier ciclo/pose registrado en `sprites_lib.poses`.

Uso:  .venv/bin/python -m sprites_lib.muneco demo --anim saltar [--estilo stardew]   → docs/diagnostico/muneco/<anim>/
      .venv/bin/python -m sprites_lib.muneco objetos --anim golpear [--formas espada,hacha]  → docs/diagnostico/objetos/
"""

import os
import sys

FICHA = {
    "identidad": {"nombre": "muñeco base"},
    "cuerpo": {
        "base": "humano",
        "clase_altura": "adulto",
        "complexion": "normal",
        "cabello": "calvo",
    },
    "paleta": {"piel": {"base": "#f9d5ba"}},
    "componentes": [],
}

# Materiales de los objetos del demo (siempre presentes en la paleta del muñeco): cada forma usa los que necesita.
MATERIALES_OBJETO = {
    "metal": {"base": "#c8d2dc"},
    "cuero": {"base": "#7a4a2a"},
    "oro": {"base": "#e2aa34"},
    "fuego": {"base": "#ff9a2e", "emisivo": True},
}


def _ficha_objeto(forma):
    """Muñeco base con un objeto en la mano derecha, para ver cómo se comporta una forma en un ciclo."""
    f = {**FICHA, "paleta": {**FICHA["paleta"], **MATERIALES_OBJETO}}
    f["componentes"] = [
        {
            "tipo": "objeto",
            "ancla": "mano_derecha",
            "material": "metal",
            "parametros": {
                "forma": forma,
                "mango": "cuero",
                "pomo": "oro",
                "detalle": "fuego",
            },
            "por_que": "demo de objetos",
        }
    ]
    return f


def demo(anim="caminar_lpc", estilo="stardew"):
    from .armado import render_cuadro, pivote
    from .estilos import ESTILOS
    from .exportar import exportar_direcciones
    from .poses import POSES, fps, loop, offset_y

    n = POSES[anim]["n"]
    por_dir = {
        m: [render_cuadro(FICHA, estilo, anim, p, m).img for p in range(n)]
        for m in ESTILOS[estilo]["direcciones"]
    }
    carpeta = os.path.join("docs", "diagnostico", "muneco", anim)
    oy = offset_y(anim)
    exportar_direcciones(
        por_dir,
        anim,
        carpeta,
        fps=fps(anim),
        zoom=6,
        pivote=pivote(estilo, pose=anim),
        loop=loop(anim),
        extra={"offset_y": oy} if oy else None,
    )
    return carpeta


def ancho_necesario(anim="caminar_lpc", estilo="stardew8", margen=1):
    """Ancho de celda (par) que necesita la animación: se renderiza en una celda enorme con el muñeco y se mide cuánto
    se aleja del pivote hacia cada lado en todas las direcciones y cuadros (+ margen de píxeles libres a cada lado)."""
    import numpy as np
    from .armado import render_cuadro
    from .estilos import ESTILOS
    from .poses import POSES

    izq = der = 0
    for d in ESTILOS[estilo]["direcciones"]:
        for p in range(POSES[anim]["n"]):
            c = render_cuadro(FICHA, estilo, anim, p, d, ancho=96)
            cols = np.nonzero(np.array(c.img.convert("RGBA"))[..., 3].any(0))[0]
            gx = round(c.anclas_px["suelo"][0])
            izq, der = max(izq, gx - cols.min()), max(der, cols.max() - gx + 1)
    m = max(izq, der) + margen
    return 2 * m + (2 * m) % 2


def objetos(
    anim="golpear",
    estilo="lateral",
    mira=None,
    formas=None,
    ruta=None,
    zoom=6,
):
    """Misma animación, distintas cosas en la mano: una fila por forma, una columna por cuadro. Sirve para
    iterar el objeto sin tocar la animación (y la animación sin tocar el objeto). Devuelve la ruta del PNG."""
    from PIL import Image, ImageDraw

    from .armado import render_cuadro
    from .estilos import ESTILOS
    from .poses import POSES

    formas = list(formas or ("espada", "hacha", "antorcha", "escudo", "baston"))
    if mira is None:
        mira = ESTILOS[estilo]["direcciones"][0]
    n = POSES[anim]["n"]
    fr = {
        (forma, p): render_cuadro(_ficha_objeto(forma), estilo, anim, p, mira).img
        for forma in formas
        for p in range(n)
    }
    cw, ch = fr[(formas[0], 0)].size
    M = 46
    im = Image.new(
        "RGB", (M + n * cw * zoom, M + len(formas) * ch * zoom), (28, 26, 40)
    )
    dr = ImageDraw.Draw(im)
    for j in range(n):
        dr.text((M + j * cw * zoom + 2, 4), f"c{j}", fill=(255, 255, 255))
    for i, forma in enumerate(formas):
        dr.text((2, M + i * ch * zoom + 4), forma, fill=(255, 255, 255))
        for j in range(n):
            g = fr[(forma, j)].resize((cw * zoom, ch * zoom), Image.NEAREST)
            im.paste(g, (M + j * cw * zoom, M + i * ch * zoom), g)
    ruta = ruta or os.path.join(
        "docs", "diagnostico", "objetos", f"{anim}_{estilo}_objetos.png"
    )
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    im.save(ruta)
    return ruta


def grilla(anim="caminar_lpc", estilo="stardew8", ruta=None, zoom=6, cuadros=None):
    """Plantilla de zonas: una fila por dirección, una columna por cuadro (skins/zonas.png), para revisar a ojo."""
    from PIL import Image, ImageDraw
    from . import skins
    from .armado import render_cuadro
    from .estilos import ESTILOS
    from .poses import POSES

    f = skins.ficha(skins.plantilla_zonas())
    dirs, n = ESTILOS[estilo]["direcciones"], POSES[anim]["n"]
    ps = list(range(n)) if cuadros is None else cuadros
    fr = {(d, p): render_cuadro(f, estilo, anim, p, d).img for d in dirs for p in ps}
    cw, ch = fr[(dirs[0], ps[0])].size
    M = 22
    im = Image.new(
        "RGB", (M + len(ps) * cw * zoom, M + len(dirs) * ch * zoom), (28, 26, 40)
    )
    dr = ImageDraw.Draw(im)
    for j, p in enumerate(ps):
        dr.text((M + j * cw * zoom + 2, 4), f"c{p}", fill=(255, 255, 255))
    for i, d in enumerate(dirs):
        dr.text((2, M + i * ch * zoom + 4), d, fill=(255, 255, 255))
        for j, p in enumerate(ps):
            g = fr[(d, p)].resize((cw * zoom, ch * zoom), Image.NEAREST)
            im.paste(g, (M + j * cw * zoom, M + i * ch * zoom), g)
    ruta = ruta or os.path.join(
        "docs", "diagnostico", "muneco", f"{anim}_{estilo}_zonas.png"
    )
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    im.save(ruta)
    return ruta


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["demo"]:
        anim = args[args.index("--anim") + 1] if "--anim" in args else "caminar_lpc"
        estilo = args[args.index("--estilo") + 1] if "--estilo" in args else "stardew"
        print("→", demo(anim, estilo))
    elif args[:1] == ["ancho"]:
        anim = args[args.index("--anim") + 1] if "--anim" in args else "caminar_lpc"
        estilo = args[args.index("--estilo") + 1] if "--estilo" in args else "stardew8"
        print(anim, estilo, "→ ancho", ancho_necesario(anim, estilo))
    elif args[:1] == ["zonas"]:
        anim = args[args.index("--anim") + 1] if "--anim" in args else "caminar_lpc"
        estilo = args[args.index("--estilo") + 1] if "--estilo" in args else "stardew8"
        print("→", grilla(anim, estilo))
    elif args[:1] == ["objetos"]:
        anim = args[args.index("--anim") + 1] if "--anim" in args else "golpear"
        estilo = args[args.index("--estilo") + 1] if "--estilo" in args else "lateral"
        mira = args[args.index("--mira") + 1] if "--mira" in args else None
        formas = (
            args[args.index("--formas") + 1].split(",") if "--formas" in args else None
        )
        print("→", objetos(anim, estilo, mira, formas))
    else:
        print(__doc__)
