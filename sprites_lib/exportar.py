"""Exportación genérica de animaciones (sirve para cualquier motor).

Por animación genera:
  <nombre>.png            tira horizontal de cuadros, fondo transparente
  <nombre>.json           metadatos: tamaño de celda, pivote (pies), fps y rect de cada cuadro
                          (estructura tipo Aseprite/TexturePacker "frames" + "meta")
  <nombre>.gif            vista previa ampliada
  <nombre>_revision.png   todos los cuadros ampliados en grilla, para revisar
Para varias direcciones, `exportar_direcciones` arma una hoja con una fila por dirección.
"""
import colorsys
import json
import os

import numpy as np
from PIL import Image

FONDO = (28, 26, 40)


def _color_mat(i):
    """Color determinista por id de material (para el material map)."""
    r, g, b = colorsys.hsv_to_rgb((i * 0.61803398875) % 1.0, 0.65, 0.95)
    return (int(r * 255), int(g * 255), int(b * 255))


def _mapa_normal(buf):
    """RGBA: normal en RGB ([-1,1] -> [0,255]), alpha 0 donde no hay superficie."""
    ch, cw = buf['solido'].shape
    out = np.zeros((ch, cw, 4), np.uint8)
    out[..., :3] = buf['normal']
    out[..., 3] = np.where(buf['solido'], 255, 0)
    return Image.fromarray(out, 'RGBA')


def _mapa_material(buf):
    """RGBA: color por id de material, alpha 0 donde no hay superficie."""
    ch, cw = buf['solido'].shape
    rgb = np.zeros((ch, cw, 3), np.uint8)
    for i in range(len(buf['mat_nombres'])):
        rgb[buf['mat'] == i] = _color_mat(i)
    out = np.zeros((ch, cw, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(buf['solido'], 255, 0)
    return Image.fromarray(out, 'RGBA')


def _tira(mapas):
    """Apila una lista de imágenes en una tira horizontal RGBA."""
    cw, ch = mapas[0].size
    tira = Image.new('RGBA', (cw * len(mapas), ch), (0, 0, 0, 0))
    for i, m in enumerate(mapas):
        tira.paste(m, (i * cw, 0))
    return tira


def _meta_mapas(nombre, sufijo=''):
    """Campos extra del JSON para referenciar los mapas de superficie."""
    return {'normal_map': f'{nombre}{sufijo}_normal.png',
            'material_map': f'{nombre}{sufijo}_material.png'}


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


def exportar(frames, nombre, carpeta, fps=12, pivote=None, zoom=4, extra=None, loop=True, buffers=None):
    """buffers: lista (uno por frame) de dicts con normal/mat/solido/mat_nombres (de Escena.render).
    Si se proporcionan, genera <nombre>_normal.png y <nombre>_material.png alineados con el sprite."""
    os.makedirs(carpeta, exist_ok=True)
    cw, ch = frames[0].size
    tira = Image.new("RGBA", (cw * len(frames), ch), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        tira.paste(f, (i * cw, 0))
    base = os.path.join(carpeta, nombre)
    tira.save(base + ".png")
    meta_extra = dict(extra or {})
    if buffers:
        _tira([_mapa_normal(b) for b in buffers]).save(base + "_normal.png")
        _tira([_mapa_material(b) for b in buffers]).save(base + "_material.png")
        meta_extra.update(_meta_mapas(nombre))
        meta_extra['materiales'] = {str(i): nm for i, nm in enumerate(buffers[0]['mat_nombres'])}
    meta = {
        "frames": [{"filename": f"{nombre}_{i}", "frame": {"x": i * cw, "y": 0, "w": cw, "h": ch},
                    "duration": int(1000 / fps)} for i in range(len(frames))],
        "meta": {"image": nombre + ".png", "size": {"w": cw * len(frames), "h": ch},
                 "cell": {"w": cw, "h": ch}, "fps": fps, "loop": loop,
                 "pivot": {"x": pivote[0], "y": pivote[1]} if pivote else None, **meta_extra},
    }
    with open(base + ".json", "w") as fh:
        json.dump(meta, fh, indent=1)
    _gif(frames, base + ".gif", fps, zoom)
    revision(frames, base + "_revision.png")
    return base


def exportar_direcciones(por_dir, nombre, carpeta, fps=12, pivote=None, zoom=3, loop=True, extra=None, cuadros=False,
                         buffers=None):
    """por_dir: {"SE": [frames], "E": [...], ...} → hoja con una fila por dirección + JSON + GIF por dirección.
    buffers: {"SE": [buf, ...], ...} (uno por frame y dirección) → genera <nombre>_<dir>_normal.png y
    <nombre>_<dir>_material.png por dirección."""
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
            if cuadros:
                os.makedirs(os.path.join(carpeta, "cuadros"), exist_ok=True)
                f.save(os.path.join(carpeta, "cuadros", key + ".png"))
        _gif(por_dir[dname], os.path.join(carpeta, f"{nombre}_{dname}.gif"), fps, zoom)
    base = os.path.join(carpeta, nombre)
    hoja.save(base + ".png")
    meta_extra = dict(extra or {})
    if buffers:
        normales, materiales = {}, {}
        for dname in dirs:
            bufs = buffers[dname]
            _tira([_mapa_normal(b) for b in bufs]).save(os.path.join(carpeta, f"{nombre}_{dname}_normal.png"))
            _tira([_mapa_material(b) for b in bufs]).save(os.path.join(carpeta, f"{nombre}_{dname}_material.png"))
            normales[dname] = f"{nombre}_{dname}_normal.png"
            materiales[dname] = f"{nombre}_{dname}_material.png"
        meta_extra['normal_map'] = normales
        meta_extra['material_map'] = materiales
        meta_extra['materiales'] = {str(i): nm for i, nm in enumerate(buffers[dirs[0]][0]['mat_nombres'])}
    with open(base + ".json", "w") as fh:
        json.dump({"frames": frames_meta,
                   "meta": {"image": nombre + ".png", "size": {"w": cw * n, "h": ch * len(dirs)},
                            "cell": {"w": cw, "h": ch}, "fps": fps, "loop": loop,
                            "pivot": {"x": pivote[0], "y": pivote[1]} if pivote else None,
                            "animations": anims, **meta_extra}}, fh, indent=1)
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
