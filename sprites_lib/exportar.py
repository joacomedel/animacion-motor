"""Exportación genérica de animaciones (sirve para cualquier motor).

Por animación genera:
  <nombre>.png            tira horizontal de cuadros, fondo transparente
  <nombre>.json           metadatos: tamaño de celda, pivote (pies), fps y rect de cada cuadro
                          (estructura tipo Aseprite/TexturePacker "frames" + "meta")
  <nombre>.gif            vista previa ampliada
  <nombre>_revision.png   todos los cuadros ampliados en grilla, para revisar
Para varias direcciones, `exportar_direcciones` arma una hoja con una fila por dirección.
"""
import json
import os

from PIL import Image

FONDO = (28, 26, 40)


def _gif(frames, ruta, fps, zoom, fondo=FONDO):
    cw, ch = frames[0].size
    out = []
    for f in frames:
        g = Image.new("RGB", (cw, ch), fondo)
        g.paste(f, (0, 0), f)
        out.append(g.resize((cw * zoom, ch * zoom), Image.NEAREST))
    out[0].save(ruta, save_all=True, append_images=out[1:], loop=0, duration=int(1000 / fps), disposal=1)


def revision(frames, ruta, zoom=5, columnas=5):
    cw, ch = frames[0].size
    filas = (len(frames) + columnas - 1) // columnas
    hoja = Image.new("RGB", (cw * zoom * min(columnas, len(frames)), ch * zoom * filas), FONDO)
    for i, f in enumerate(frames):
        big = f.resize((cw * zoom, ch * zoom), Image.NEAREST)
        hoja.paste(big, ((i % columnas) * cw * zoom, (i // columnas) * ch * zoom), big)
    hoja.save(ruta)
    return ruta


def exportar(frames, nombre, carpeta, fps=12, pivote=None, zoom=4, extra=None):
    os.makedirs(carpeta, exist_ok=True)
    cw, ch = frames[0].size
    tira = Image.new("RGBA", (cw * len(frames), ch), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        tira.paste(f, (i * cw, 0))
    base = os.path.join(carpeta, nombre)
    tira.save(base + ".png")
    meta = {
        "frames": [{"filename": f"{nombre}_{i}", "frame": {"x": i * cw, "y": 0, "w": cw, "h": ch},
                    "duration": int(1000 / fps)} for i in range(len(frames))],
        "meta": {"image": nombre + ".png", "size": {"w": cw * len(frames), "h": ch},
                 "cell": {"w": cw, "h": ch}, "fps": fps, "loop": True,
                 "pivot": {"x": pivote[0], "y": pivote[1]} if pivote else None, **(extra or {})},
    }
    with open(base + ".json", "w") as fh:
        json.dump(meta, fh, indent=1)
    _gif(frames, base + ".gif", fps, zoom)
    revision(frames, base + "_revision.png")
    return base


def exportar_direcciones(por_dir, nombre, carpeta, fps=12, pivote=None, zoom=3):
    """por_dir: {"SE": [frames], "E": [...], ...} → hoja con una fila por dirección + JSON + GIF por dirección."""
    os.makedirs(carpeta, exist_ok=True)
    dirs = list(por_dir)
    cw, ch = por_dir[dirs[0]][0].size
    n = max(len(f) for f in por_dir.values())
    hoja = Image.new("RGBA", (cw * n, ch * len(dirs)), (0, 0, 0, 0))
    frames_meta, anims = [], {}
    for r, dname in enumerate(dirs):
        anims[dname] = []
        for i, f in enumerate(por_dir[dname]):
            hoja.paste(f, (i * cw, r * ch))
            key = f"{nombre}_{dname}_{i}"
            frames_meta.append({"filename": key, "frame": {"x": i * cw, "y": r * ch, "w": cw, "h": ch},
                                "duration": int(1000 / fps)})
            anims[dname].append(key)
        _gif(por_dir[dname], os.path.join(carpeta, f"{nombre}_{dname}.gif"), fps, zoom)
    base = os.path.join(carpeta, nombre)
    hoja.save(base + ".png")
    with open(base + ".json", "w") as fh:
        json.dump({"frames": frames_meta,
                   "meta": {"image": nombre + ".png", "size": {"w": cw * n, "h": ch * len(dirs)},
                            "cell": {"w": cw, "h": ch}, "fps": fps, "loop": True,
                            "pivot": {"x": pivote[0], "y": pivote[1]} if pivote else None,
                            "animations": anims}}, fh, indent=1)
    # vista general: todas las direcciones en un GIF
    todos = []
    for i in range(n):
        g = Image.new("RGBA", (cw * len(dirs), ch), (0, 0, 0, 0))
        for r, dname in enumerate(dirs):
            fr = por_dir[dname][i % len(por_dir[dname])]
            g.paste(fr, (r * cw, 0))
        todos.append(g)
    _gif(todos, base + "_todas.gif", fps, zoom)
    return base
