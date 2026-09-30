"""Muñeco base: sin skin ni ficha de personaje, solo para ver y probar un ciclo/pose antes de aplicarlo a alguien
(el mismo pipeline de render que las skins y los personajes, con una ficha mínima fija). Genérico por animación:
no hay nada de "caminar" fijo acá, `demo(anim=...)` sirve para cualquier ciclo/pose registrado en `sprites_lib.poses`.

Uso:  .venv/bin/python -m sprites_lib.muneco demo --anim saltar [--estilo stardew]   → salida/muneco/<anim>/
"""
import os
import sys

FICHA = {
    "identidad": {"nombre": "muñeco base"},
    "cuerpo": {"base": "humano", "clase_altura": "adulto", "complexion": "normal", "cabello": "calvo"},
    "paleta": {"piel": {"base": "#f9d5ba"}},
    "componentes": [],
}


def demo(anim="caminar_lpc", estilo="stardew"):
    from .armado import render_cuadro, pivote
    from .estilos import ESTILOS
    from .exportar import exportar_direcciones
    from .poses import POSES, fps, loop, offset_y
    n = POSES[anim]["n"]
    por_dir = {m: [render_cuadro(FICHA, estilo, anim, p, m).img for p in range(n)] for m in ESTILOS[estilo]["direcciones"]}
    carpeta = os.path.join("salida", "muneco", anim)
    oy = offset_y(anim)
    exportar_direcciones(por_dir, anim, carpeta, fps=fps(anim), zoom=6, pivote=pivote(estilo, pose=anim), loop=loop(anim),
                         extra={"offset_y": oy} if oy else None)
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
    im = Image.new("RGB", (M + len(ps) * cw * zoom, M + len(dirs) * ch * zoom), (28, 26, 40))
    dr = ImageDraw.Draw(im)
    for j, p in enumerate(ps):
        dr.text((M + j * cw * zoom + 2, 4), f"c{p}", fill=(255, 255, 255))
    for i, d in enumerate(dirs):
        dr.text((2, M + i * ch * zoom + 4), d, fill=(255, 255, 255))
        for j, p in enumerate(ps):
            g = fr[(d, p)].resize((cw * zoom, ch * zoom), Image.NEAREST)
            im.paste(g, (M + j * cw * zoom, M + i * ch * zoom), g)
    ruta = ruta or os.path.join("salida", "muneco", f"{anim}_{estilo}_zonas.png")
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
    else:
        print(__doc__)
