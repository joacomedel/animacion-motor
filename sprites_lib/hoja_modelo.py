"""Hoja de modelo: todas las direcciones alineadas por pose, con líneas guía (coronilla, ojos, hombros, cintura,
suelo), muestras de paleta, componentes con su porqué y el resultado de los tests. Es lo que el usuario aprueba."""
import textwrap

from PIL import Image, ImageDraw, ImageFont

from .estilos import ESTILOS
from .paleta import paleta_estilo

ZOOM = {"stardew": 8, "lateral": 6, "volumen": 4}
FONDO = (60, 58, 80)
COLORES_GUIA = {"coronilla": (255, 120, 120), "ojos": (120, 220, 255), "hombros": (255, 220, 90),
                "cintura": (160, 255, 140), "suelo": (200, 200, 200)}


FUENTES = ("/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
           "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
           "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf")


def _fuente(tam=11):
    """Una TrueType con tildes y ñ si hay alguna instalada; si no, la de Pillow (sin tildes)."""
    for ruta in FUENTES:
        try:
            return ImageFont.truetype(ruta, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def _texto(d, xy, txt, col=(230, 230, 240), ancho=58, font=None):
    x, y = xy
    for linea in textwrap.wrap(str(txt), ancho) or [""]:
        d.text((x, y), linea, fill=col, font=font)
        y += 14
    return y


def hoja(ficha, estilo, todo, resultados, ruta):
    est = ESTILOS[estilo]
    dirs = est["direcciones"]
    Z = ZOOM.get(estilo, 5)
    poses = [p for p in ("neutra", "quieto") if (p, dirs[0]) in todo]
    cw, ch = todo[(poses[0], dirs[0])][0].img.size
    colw, filah, panel = cw * Z + 16, ch * Z + 34, 440
    W = colw * len(dirs) + panel
    lineas = 14 + 2 * len(ficha["componentes"]) + 2 * len(ficha["paleta"]) + len(resultados) + len(ficha["identidad"]["concepto"]) // 55
    H = max(filah * len(poses) + 20, 40 + 15 * lineas)          # que entre todo el panel de texto
    im = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(im)
    font = _fuente()
    for r, pose in enumerate(poses):
        y0 = 22 + r * filah
        d.text((6, y0 - 18), f"pose: {pose}", fill=(255, 220, 90), font=font)
        c = todo[(pose, dirs[0])][0]
        guias = {"coronilla": c.anclas_px["coronilla"][1],
                 "ojos": (c.anclas_px["ojo_derecho"][1] + c.anclas_px["ojo_izquierdo"][1]) / 2,
                 "hombros": c.anclas_px["hombro_derecho"][1], "cintura": c.anclas_px["cintura"][1],
                 "suelo": c.anclas_px["suelo"][1]}
        for nombre, gy in guias.items():
            yy = y0 + int(gy * Z)
            d.line([(0, yy), (colw * len(dirs), yy)], fill=COLORES_GUIA[nombre], width=1)
            d.text((colw * len(dirs) - 64, yy - 12), nombre, fill=COLORES_GUIA[nombre], font=font)
        for i, mira in enumerate(dirs):
            fr = todo[(pose, mira)][0].img.resize((cw * Z, ch * Z), Image.NEAREST)
            im.paste(fr, (i * colw + 8, y0), fr)
            d.text((i * colw + 8, y0 + ch * Z + 2), mira, fill=(230, 230, 240), font=font)
    x = colw * len(dirs) + 14
    idt = ficha["identidad"]
    y = _texto(d, (x, 10), f"{idt['nombre']} — estilo {estilo}", (255, 220, 90), font=font)
    y = _texto(d, (x, y + 4), f"Silueta clave: {idt['silueta_clave']}", font=font)
    y = _texto(d, (x, y + 4), idt["concepto"], (200, 200, 215), font=font)
    y = _texto(d, (x, y + 8), "Paleta", (255, 220, 90), font=font)
    for nombre, tonos in paleta_estilo(ficha["paleta"], est).items():
        if nombre.endswith("_b") or nombre not in ficha["paleta"]:
            continue
        for k, t in enumerate(tonos):
            d.rectangle([x + k * 14, y, x + k * 14 + 12, y + 12], fill=t)
        y = _texto(d, (x + 48, y), f"{nombre}: {ficha['paleta'][nombre].get('por_que', '')}", ancho=52, font=font)
    y = _texto(d, (x, y + 8), "Componentes", (255, 220, 90), font=font)
    for comp in ficha["componentes"]:
        y = _texto(d, (x, y), f"- {comp['tipo']}: {comp.get('por_que', '')}", ancho=62, font=font)
    y = _texto(d, (x, y + 8), "Tests", (255, 220, 90), font=font)
    for r in resultados:
        estado = "omitido" if r.omitido else ("OK" if r.ok else "FALLA")
        col = (170, 170, 180) if r.omitido else ((140, 240, 140) if r.ok else (255, 120, 120))
        y = _texto(d, (x, y), f"[{estado}] {r.regla}", col, font=font)
    im.save(ruta)
    return ruta
