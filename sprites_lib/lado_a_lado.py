"""Comparación visual ampliada: cuadros de referencia y propios intercalados, para revisarlos con Read.

Uso:
  .venv/bin/python -m sprites_lib.lado_a_lado <salida.png> <ref.png>:<x>,<y>,<w>,<h> <mio.png>:<x>,<y>,<w>,<h> [...]
    Cada argumento es imagen:recorte. Se dibujan en orden, ampliados ×14 (o --zoom N), sobre un fondo medio
    (ni blanco ni negro, para ver bien los contornos).
Ejemplo (frente, perfil y espalda de Abigail vs el mago):
  .venv/bin/python -m sprites_lib.lado_a_lado /tmp/cmp.png \
     referencias/stardew/abigail.png:0,0,16,32   salida/mago_stardew/caminar/caminar.png:0,0,16,32 \
     referencias/stardew/abigail.png:16,32,16,32 salida/mago_stardew/caminar/caminar.png:16,32,16,32
"""
import sys

from PIL import Image


def lado_a_lado(salida, items, zoom=14):
    frs = []
    for it in items:
        ruta, rect = it.rsplit(":", 1)
        x, y, w, h = (int(v) for v in rect.split(","))
        frs.append(Image.open(ruta).convert("RGBA").crop((x, y, x + w, y + h)))
    H = max(f.height for f in frs) * zoom
    W = sum(f.width * zoom + 20 for f in frs)
    o = Image.new("RGB", (W, H), (60, 58, 80))
    x = 0
    for f in frs:
        b = f.resize((f.width * zoom, f.height * zoom), Image.NEAREST)
        o.paste(b, (x, H - b.height), b)
        x += b.width + 20
    o.save(salida)
    return salida


if __name__ == "__main__":
    a = sys.argv[1:]
    z = 14
    if "--zoom" in a:
        i = a.index("--zoom"); z = int(a[i + 1]); a = a[:i] + a[i + 2:]
    if len(a) < 2:
        print(__doc__); sys.exit(0)
    print(lado_a_lado(a[0], a[1:], z))
