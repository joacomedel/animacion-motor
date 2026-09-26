"""Mago isométrico con volumen real: muñeco 3D de primitivas "fotografiado" en isométrico.

Técnica tipo Diablo II / sprites pre-renderizados, pero a resolución de pixel art:
  1. anatomía = esferas, cápsulas, elipsoides y un faldón cónico (medidas en píxeles de mundo);
  2. cada primitiva se muestrea en puntos de superficie con su normal;
  3. proyección isométrica 2:1 + z-buffer por píxel;
  4. luz desde arriba-izquierda-frente → 3 tonos por material; contorno exterior e interior por salto de profundidad;
  5. detalles de 1 px (ojos, runas, suelas, gemas) se pintan encima solo si son visibles.
La mecánica del correr (trayectorias, rebote, tiempos) es la medida sobre Mega Man X (mago_correr.py).
Ejes de mundo: f = adelante (sudeste), l = izquierda del personaje (noreste, lejos de cámara), u = arriba.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw

from mago_correr import BOB, FOOT_A, FOOT_ANG, N, hand_path, ik
from mago_iso import iso_floor

AQUI = os.path.dirname(os.path.abspath(__file__))
CW, CH = 56, 60
GX, GY = 26, 52                       # pantalla del punto (f=0, l=0, u=0)
SC, UZ = .78, .92                     # escala del piso y de la altura

# ---------------------------------------------------------------- anatomía (plantilla)
A = dict(
    head_r=5.6,  head_u=31.5,          # cabeza grande: ~2.9 cabezas de alto (estilo FFT/chibi)
    neck_u=25.5,
    chest=(3.4, 4.6, 4.4), chest_u=21.5,   # radios (adelante, lateral, alto)
    pelvis=(2.8, 3.8, 2.4), pelvis_u=15.5,
    hip_l=2.3, hip_u=15.0,
    thigh=7.3, shin=7.3, foot=3.6,
    sh_l=5.4, sh_u=24.5, upper=5.4, fore=5.2,
    r_thigh=2.1, r_shin=1.7, r_upper=1.5, r_fore=1.35, r_hand=1.95, r_foot=1.7,
)

PAL = {  # material: (oscuro, base, luz)
    "skin":  ((84, 48, 30), (128, 76, 46), (170, 110, 68)),
    "hair":  ((140, 148, 170), (210, 214, 224), (250, 250, 248)),
    "robe":  ((32, 16, 56), (64, 33, 102), (100, 60, 148)),
    "pants": ((36, 32, 56), (62, 56, 92), (94, 86, 130)),
    "hand":  ((110, 64, 38), (156, 96, 58), (196, 134, 86)),
    "gold":  ((140, 100, 36), (214, 170, 66), (250, 226, 130)),
    "boot":  ((20, 18, 30), (40, 38, 56), (64, 62, 86)),
}
MATS = list(PAL)
OUT = (16, 10, 24)
RUNE, RUNE_D, WHITE = (110, 248, 236), (44, 150, 150), (250, 250, 250)

_L = np.array([.40, -.45, .80]); LIGHT = _L / np.linalg.norm(_L)
CAM = np.array([1.0, -1.0, SC / UZ * 1.0]); CAM = CAM / np.linalg.norm(CAM)


def project(p):
    f, l, u = p[..., 0], p[..., 1], p[..., 2]
    x = GX + SC * (f + l)
    y = GY + SC * .5 * (f - l) - UZ * u
    d = p @ CAM
    return x, y, d


# ---------------------------------------------------------------- muestreo de primitivas
class Scene:
    def __init__(self):
        self.P, self.Nn, self.M, self.K = [], [], [], []
        self.part = 0                     # id de la pieza del cuerpo que se está agregando

    def add(self, pts, nrm, mat):
        self.P.append(pts.reshape(-1, 3)); self.Nn.append(nrm.reshape(-1, 3))
        m = np.full(len(self.P[-1]), MATS.index(mat)) if isinstance(mat, str) else mat.reshape(-1)
        self.M.append(m)
        self.K.append(np.full(len(self.P[-1]), self.part))

    def sphere(self, c, r, mat):
        n = max(8, int(2 * math.pi * r / .3))
        th, ph = np.meshgrid(np.linspace(0, math.pi, n // 2 + 1), np.linspace(0, 2 * math.pi, n, endpoint=False))
        d = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], -1)
        self.add(np.asarray(c) + r * d, d, mat if isinstance(mat, str) else mat(d))

    def ellipsoid(self, c, rad, mat):
        rad = np.asarray(rad)
        n = max(10, int(2 * math.pi * rad.max() / .3))
        th, ph = np.meshgrid(np.linspace(0, math.pi, n // 2 + 1), np.linspace(0, 2 * math.pi, n, endpoint=False))
        d = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], -1)
        nrm = d / rad; nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        self.add(np.asarray(c) + d * rad, nrm, mat if isinstance(mat, str) else mat(d))

    def capsule(self, a, b, r, mat, cap=True):
        a, b = np.asarray(a, float), np.asarray(b, float)
        ax = b - a; L = np.linalg.norm(ax) + 1e-9; ax /= L
        e1 = np.cross(ax, [0, 0, 1.0])
        if np.linalg.norm(e1) < 1e-3:
            e1 = np.cross(ax, [1.0, 0, 0])
        e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1)
        t, ang = np.meshgrid(np.linspace(0, L, int(L / .3) + 2), np.linspace(0, 2 * math.pi, max(8, int(2 * math.pi * r / .3)), endpoint=False))
        d = np.cos(ang)[..., None] * e1 + np.sin(ang)[..., None] * e2
        self.add(a + t[..., None] * ax + r * d, d, mat)
        if cap:
            self.sphere(a, r, mat); self.sphere(b, r, mat)

    def coat_tail(self, top, bot, r1, r2, mat, keep):
        """Faldón: tronco de cono desde la cintura; keep(d) decide qué ángulos existen (abierto adelante)."""
        top, bot = np.asarray(top, float), np.asarray(bot, float)
        t, ang = np.meshgrid(np.linspace(0, 1, 26), np.linspace(0, 2 * math.pi, 64, endpoint=False))
        d = np.stack([np.cos(ang), np.sin(ang), np.zeros_like(ang)], -1)
        c = top + t[..., None] * (bot - top)
        r = (r1 + (r2 - r1) * t)[..., None]
        pts, m = c + r * d, keep(d)
        nrm = d + np.array([0, 0, .35]); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        self.add(pts[m], nrm[m], mat)

    # -------------------------------------------------------------- render
    def render(self, details=()):
        P = np.concatenate(self.P); Nn = np.concatenate(self.Nn); M = np.concatenate(self.M); K = np.concatenate(self.K)
        x, y, d = project(P)
        xi, yi = np.round(x).astype(int), np.round(y).astype(int)
        ok = (xi >= 0) & (xi < CW) & (yi >= 0) & (yi < CH)
        xi, yi, d, Nn, M, K = xi[ok], yi[ok], d[ok], Nn[ok], M[ok], K[ok]
        order = np.argsort(d)                       # los más cercanos a cámara quedan al final y ganan
        xi, yi, d, Nn, M, K = xi[order], yi[order], d[order], Nn[order], M[order], K[order]
        depth = np.full((CH, CW), -1e9); mat = np.full((CH, CW), -1); lam = np.zeros((CH, CW))
        part = np.full((CH, CW), -1)
        depth[yi, xi] = d; mat[yi, xi] = M; part[yi, xi] = K; lam[yi, xi] = np.clip(Nn @ LIGHT, 0, 1)
        img = np.zeros((CH, CW, 4), np.uint8)
        for k, name in enumerate(MATS):
            for lvl, (lo, hi) in enumerate(((-1, .28), (.28, .66), (.66, 2))):
                sel = (mat == k) & (lam > lo) & (lam <= hi)
                img[sel] = (*PAL[name][lvl], 255)
        solid = mat >= 0
        # contorno interior: el píxel que queda detrás de un salto de profundidad grande
        inner = np.zeros_like(solid)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nd = np.roll(np.roll(depth, dy, 0), dx, 1)
            npart = np.roll(np.roll(part, dy, 0), dx, 1)
            inner |= solid & (nd - depth > 3.2)
            # contorno entre piezas distintas: se oscurece la que queda detrás (como en X)
            inner |= solid & (npart >= 0) & (npart != part) & (nd - depth > .8)
        img[inner] = (*OUT, 255)
        # detalles de 1 px visibles
        for p, col in details:
            px, py, pd = project(np.asarray(p, float))
            ix, iy = int(round(px)), int(round(py))
            if 0 <= ix < CW and 0 <= iy < CH and solid[iy, ix] and pd >= depth[iy, ix] - 1.3:
                img[iy, ix] = (*col, 255)
        # contorno exterior
        grow = solid.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            grow |= np.roll(np.roll(solid, dy, 0), dx, 1)
        img[grow & ~solid] = (*OUT, 255)
        return Image.fromarray(img, "RGBA")


# ---------------------------------------------------------------- personaje
def v(f, l, u):
    return np.array([f, l, u], float)


def head_mat(d):
    """Materiales sobre la esfera de la cabeza (d = dirección desde el centro)."""
    fwd, up = d[..., 0], d[..., 2]
    m = np.full(d.shape[:-1], MATS.index("hair"))
    face = (fwd > -.2) & (up < .40)
    m[face] = MATS.index("skin")
    band = (up > .40) & (up < .54)
    m[band] = MATS.index("gold")
    return m


def torso_mat(d):
    m = np.full(d.shape[:-1], MATS.index("robe"))
    m[(d[..., 2] < -.72)] = MATS.index("gold")        # cinturón
    return m


def sagittal_ik(a, b, l1, l2, bend):
    """IK en el plano (f, u) usando la función 2D del rig lateral (y hacia abajo)."""
    k = ik((a[0], -a[2]), (b[0], -b[2]), l1, l2, bend)
    return v(k[0], a[1], -k[1])


def build(p, pose=None):
    s = Scene(); det = []
    bob = BOB[p] if pose is None else 0
    lift = -bob * .9                                    # en el rig lateral y crece hacia abajo
    hip_c = v(0, 0, A["hip_u"] + lift)
    # --- piernas (A = derecha, cerca de cámara: l < 0)
    for side, foot_side, ang in ((-1, FOOT_A[p], FOOT_ANG[p]), (1, FOOT_A[(p + 5) % N], FOOT_ANG[(p + 5) % N])):
        if pose == "stand":
            foot_side, ang = (18 + side * .5, 32.5), 0
        hip = hip_c + v(0, side * A["hip_l"], 0)
        s.part = 10 + side                                               # pierna D / I
        ankle = v(foot_side[0] - 18, side * A["hip_l"], (34 - foot_side[1]) * .95)
        knee = sagittal_ik(hip, ankle, A["thigh"], A["shin"], +1)
        s.capsule(hip, knee, A["r_thigh"], "pants")
        s.capsule(knee, ankle, A["r_shin"], "pants")
        r = math.radians(ang)
        toe = ankle + v(A["foot"] * math.cos(r), 0, -A["foot"] * math.sin(r))
        s.sphere(knee + v(.9, 0, 0), 1.2, "gold")                        # rodillera
        s.part = 20 + side                                               # bota D / I
        s.capsule(ankle, toe, A["r_foot"], "boot")
        for k in np.linspace(0, 1, 5):                                   # suela luminosa
            q = ankle + (toe - ankle) * k + v(0, 0, -A["r_foot"] + .2)
            det.append((q + v(0, -.8, 0), RUNE))
    # --- torso, pelvis y faldón
    s.part = 1                                                           # torso
    chest_c = v(-.3, 0, A["chest_u"] + lift)
    s.ellipsoid(chest_c, A["chest"], torso_mat)
    s.ellipsoid(v(0, 0, A["pelvis_u"] + lift), A["pelvis"], "robe")
    lag = math.sin(2 * math.pi * (p - 1) / 5) if pose is None else 0
    s.coat_tail(v(-.4, 0, 16.5 + lift), v(-2.6 - 1.2 * lag, 0, 8.5 + lift + .6 * lag), 3.9, 5.4, "robe",
                keep=lambda d: d[..., 0] < .35)                          # abierto adelante: se ven las piernas
    s.capsule(v(-.3, 0, A["neck_u"] - 1.5 + lift), v(0, 0, A["neck_u"] + 1 + lift), 1.6, "skin", cap=False)
    # circuito rúnico en el pecho (lado que mira a cámara)
    for q in ((3.2, -1.2, 22.5), (3.3, -.4, 22.5), (3.3, .4, 22.5), (3.2, -.4, 21.5), (3.1, -.4, 20.5), (3.1, .8, 20.5)):
        det.append((v(q[0], q[1], q[2] + lift), RUNE))
    det.append((v(2.6, -.6, 13.9 + lift + 2.2), RUNE))                  # gema del cinturón
    # --- brazos: derecho (cerca, l<0) opuesto a la pierna derecha
    for side, hp in ((-1, hand_path(p + 5)), (1, hand_path(p))):
        if pose == "stand":
            hp = (19.5, 26.5)
        sh = v(-.3, side * A["sh_l"], A["sh_u"] + lift)
        # puños un poco más abajo y separados del cuerpo: si suben a la cara, en iso la tapan
        hand = sh + v(hp[0] - 20, side * .9, 16 - hp[1] - 2.5)
        el = sagittal_ik(sh, hand, A["upper"], A["fore"], -1)
        s.part = 30 + side                                               # brazo D / I
        s.capsule(sh, el, A["r_upper"], "skin")
        s.capsule(el, hand, A["r_fore"], "skin")
        s.sphere(sh + v(0, side * .4, .8), 1.5, "gold")                 # hombrera
        wrist = el + (hand - el) * .80
        s.capsule(wrist - (hand - el) * .10, wrist + (hand - el) * .10, A["r_fore"] + .3, "gold", cap=False)  # brazalete
        s.part = 40 + side                                               # mano D / I: pieza propia → contorno propio
        s.sphere(hand + (hand - el) * .06, A["r_hand"], "hand")
        det.append((hand + CAM * A["r_hand"] + v(0, 0, .5), PAL["hand"][2]))    # brillo en los nudillos
        if side < 0:
            det.append((hand + CAM * A["r_hand"] + v(0, 0, -.6), RUNE))        # anillo rúnico en la mano cercana
        det.append((sh + v(0, side * .4, 2.3), RUNE))
        # runas tatuadas: puntos sobre la cara del brazo que mira a cámara
        for a_, b_, r_ in ((sh, el, A["r_upper"]), (el, wrist, A["r_fore"])):
            for k in np.linspace(.2, .9, 3):
                q = a_ + (b_ - a_) * k + CAM * r_
                det.append((q, RUNE if side < 0 else RUNE_D))
    # --- cabeza en 3/4 mirando al sudeste
    s.part = 2
    hc = v(.2, 0, A["head_u"] + lift)
    s.sphere(hc, A["head_r"], head_mat)
    s.sphere(hc + v(A["head_r"] - .6, 0, -1.6), 1.3, "skin")            # nariz / volumen de la cara
    for side in (-1, 1):                                                 # dos ojos visibles (vista 3/4)
        e = hc + v(A["head_r"] * .82, side * 2.0, -.6)
        det.append((e, WHITE)); det.append((e + v(.4, .5, 0), OUT))
    det.append((hc + v(A["head_r"] * .85, 1.0, A["head_r"] * .42), RUNE))  # gema de la vincha
    det.append((hc + v(A["head_r"] * .75, -2.6, -2.2), RUNE))            # runa en la mejilla
    # rastas: cadenas de cápsulas que salen de la nuca hacia atrás y caen, con 1 cuadro de retraso
    prev = BOB[(p - 1) % N] if pose is None else 0
    s.part = 3                                                           # rastas
    for i, (dl, du) in enumerate(((-2.8, 2.5), (-1.0, 3.2), (1.0, 3.0), (2.8, 2.2), (0, .6), (-2.2, -.6), (2.2, -.8))):
        pts = [hc + v(-A["head_r"] * .7, dl, du)]
        for k in range(1, 6):
            sway = math.sin(k * .9 - p * 2 * math.pi / 5 + i) * .8 if pose is None else 0
            pts.append(pts[-1] + v(-1.6, dl * .12 + sway * .5, -1.05 - (prev - bob) * .25 + sway * .3))
        for a_, b_ in zip(pts, pts[1:]):
            s.capsule(a_, b_, 1.05, "hair")
        det.append((pts[-1] + CAM * 1.0, RUNE if i % 2 == 0 else PAL["gold"][2]))
    return s, det


def frame(p, pose=None):
    s, det = build(p, pose)
    fig = s.render(det)
    out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    # sombra 2:1 bajo la cadera con dithering
    yy, xx = np.mgrid[0:CH, 0:CW]
    sh = (((xx - GX) / 10.0) ** 2 + ((yy - GY) / 4.6) ** 2 <= 1) & ((xx + yy) % 2 == 0)
    arr = np.zeros((CH, CW, 4), np.uint8); arr[sh] = (10, 8, 18, 210)
    out.alpha_composite(Image.fromarray(arr, "RGBA"))
    out.alpha_composite(fig)
    return out


def plantilla():
    """Plantilla de anatomía: pose neutra ampliada con articulaciones y medidas."""
    Z = 8
    base = frame(0, pose="stand").resize((CW * Z, CH * Z), Image.NEAREST)
    im = Image.new("RGB", (CW * Z + 330, CH * Z), (24, 22, 34))
    im.paste(base, (0, 0), base)
    d = ImageDraw.Draw(im)
    joints = {
        "cabeza": v(.2, 0, A["head_u"]), "cuello": v(0, 0, A["neck_u"]),
        "hombro D": v(-.3, -A["sh_l"], A["sh_u"]), "hombro I": v(-.3, A["sh_l"], A["sh_u"]),
        "cadera D": v(0, -A["hip_l"], A["hip_u"]), "cadera I": v(0, A["hip_l"], A["hip_u"]),
        "tobillo D": v(.5, -A["hip_l"], 1.5), "tobillo I": v(.5, A["hip_l"], 1.5),
    }
    for name, p in joints.items():
        x, y, _ = project(p)
        X, Y = x * Z, y * Z
        d.ellipse([X - 5, Y - 5, X + 5, Y + 5], outline=(255, 90, 90), width=2)
        d.text((X + 8, Y - 6), name, fill=(255, 200, 200))
    # rombos del piso: eje adelante (sudeste) y lateral (noreste)
    o = project(v(0, 0, 0)); fx = project(v(8, 0, 0)); lx = project(v(0, 8, 0))
    d.line([(o[0] * Z, o[1] * Z), (fx[0] * Z, fx[1] * Z)], fill=(90, 220, 255), width=2)
    d.text((fx[0] * Z + 4, fx[1] * Z), "adelante (SE)", fill=(90, 220, 255))
    d.line([(o[0] * Z, o[1] * Z), (lx[0] * Z, lx[1] * Z)], fill=(255, 220, 90), width=2)
    d.text((lx[0] * Z + 4, lx[1] * Z - 12), "izquierda (NE)", fill=(255, 220, 90))
    tx = CW * Z + 16
    H = A["head_u"] + A["head_r"]
    lines = [
        "PLANTILLA - MAGO ISOMETRICO",
        "",
        f"alto total: {H:.0f} px de mundo",
        f"cabeza: diametro {2*A['head_r']:.1f} -> {H/(2*A['head_r']):.1f} cabezas",
        f"hombros: ancho {2*A['sh_l']:.1f}  caderas: {2*A['hip_l']:.1f}",
        f"muslo {A['thigh']} = canilla {A['shin']}",
        f"brazo {A['upper']} ~ antebrazo {A['fore']}",
        f"cadera a {A['hip_u']} px del piso (~45%)",
        "",
        "proyeccion 2:1:",
        "  x = 0.78 (f + l)",
        "  y = 0.39 (f - l) - 0.92 u",
        "luz: arriba-izq-frente",
        "3 tonos por material",
        "contorno exterior + interior",
        "  (salto de profundidad)",
        "",
        "D = lado derecho, cerca de camara",
        "I = lado izquierdo, lejos",
    ]
    for i, t in enumerate(lines):
        d.text((tx, 20 + i * 18), t, fill=(230, 230, 240) if i else (255, 220, 90))
    im.save(os.path.join(AQUI, "plantilla_anatomia.png"))


if __name__ == "__main__":
    plantilla()
    frames = [frame(p) for p in range(N)]
    tira = Image.new("RGBA", (CW * N, CH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        tira.paste(f, (i * CW, 0))
    tira.save(os.path.join(AQUI, "mago_iso3d_correr.png"))
    Z = 4
    gif = []
    for f in frames:
        g = Image.new("RGB", (CW, CH), (28, 26, 40)); g.paste(f, (0, 0), f)
        gif.append(g.resize((CW * Z, CH * Z), Image.NEAREST))
    gif[0].save(os.path.join(AQUI, "mago_iso3d_correr.gif"), save_all=True, append_images=gif[1:],
                loop=0, duration=int(1000 / 12), disposal=1)
    W, H = 170, 110
    gif2 = []
    for loop in range(3):
        for i, f in enumerate(frames):
            bg = iso_floor(W, H, (loop * N + i) * 1.6)
            bg.paste(f, (W // 2 - GX, H // 2 - GY + 26), f)
            gif2.append(bg.resize((W * 3, H * 3), Image.NEAREST))
    gif2[0].save(os.path.join(AQUI, "mago_iso3d_escena.gif"), save_all=True, append_images=gif2[1:],
                 loop=0, duration=int(1000 / 12), disposal=1)
    sheet = Image.new("RGB", (CW * 5 * 5, CH * 2 * 5), (28, 26, 40))
    for i, f in enumerate(frames):
        big = f.resize((CW * 5, CH * 5), Image.NEAREST)
        sheet.paste(big, ((i % 5) * CW * 5, (i // 5) * CH * 5), big)
    sheet.save(os.path.join(AQUI, "mago_iso3d_revision.png"))
    print("ok")
