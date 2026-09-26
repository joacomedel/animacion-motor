"""El mago en estilo Stardew Valley: cenital 3/4, 4 direcciones, celda 16x32, chibi, sombreado plano
y contorno de color. Mismo motor 3D que mago_iso.py, pero con el perfil de estilo "stardew".

Uso (desde la raíz del proyecto):
  .venv/bin/python -m personajes.mago_stardew --anim caminar
  .venv/bin/python -m personajes.mago_stardew --anim quieto
  .venv/bin/python -m personajes.mago_stardew --anim caminar --comparar   (lado a lado con la referencia)
Salida: salida/mago_stardew/<anim>/...
"""
import argparse
import math
import os

import numpy as np
from PIL import Image

from sprites_lib.ciclos import CICLOS, pose
from sprites_lib.estilos import ESTILOS
from sprites_lib.exportar import exportar_direcciones
from sprites_lib.render3d import DIRECCIONES_CENITAL, CamaraCenital, Escena, ik_sagital, v

NOMBRE = "mago_stardew"
ESTILO = ESTILOS["stardew"]
CELDA = ESTILO["celda"]

# chibi: cabeza ≈ 44% del alto, piernas ≈ 25% (medido en Abigail/Wizard)
ANATOMIA = dict(
    cabeza=(4.9, 5.1, 4.8), cabeza_u=20.8,          # caja redondeada, no esfera (~14 px de ancho con pelo)
    cuello_u=16.4,
    pecho=(2.4, 3.3, 3.0), pecho_u=13.4,
    pelvis=(2.0, 3.0, 1.7), pelvis_u=9.2,
    cadera_l=1.6, cadera_u=8.1,
    muslo=4.2, canilla=4.2, pie=2.2,
    hombro_l=3.5, hombro_u=15.4, brazo=3.4, antebrazo=3.2,
    r_muslo=1.35, r_canilla=1.15, r_brazo=1.0, r_antebrazo=.95, r_mano=1.3, r_pie=1.15,
)
ESCALA = (ANATOMIA["muslo"] + ANATOMIA["canilla"]) / 14.0   # trayectorias del rig lateral → este cuerpo

# paleta saturada y cálida, sombras corridas a violeta y luces a amarillo (como Stardew)
PALETA = {
    "piel":     ((92, 48, 50), (140, 86, 56), (182, 122, 76)),
    "mano":     ((110, 62, 56), (162, 104, 68), (204, 144, 92)),
    "pelo":     ((146, 144, 196), (226, 226, 240), (255, 255, 250)),
    "pelo_m":   ((118, 116, 170), (184, 186, 218), (232, 232, 246)),   # mechón: textura dibujada
    "camisa":   ((30, 26, 60), (54, 46, 98), (82, 72, 138)),
    "tunica_m": ((42, 18, 80), (76, 34, 128), (116, 66, 172)),         # pliegue
    "tunica":   ((52, 24, 96), (92, 44, 150), (138, 82, 196)),
    "pantalon": ((40, 32, 72), (66, 54, 110), (98, 84, 152)),
    "oro":      ((156, 96, 32), (226, 170, 52), (255, 226, 120)),
    "bota":     ((62, 34, 28), (98, 58, 40), (132, 88, 58)),
}
RUNA, OJO, IRIS = (90, 240, 230), (250, 250, 250), (40, 170, 190)
PIEZA = dict(torso=1, cabeza=2, pelo=3, pierna=10, bota=20, brazo=30, mano=40)


def centro_cara(cam_local):
    """Trampa de Stardew: la cara se corre hacia la cámara. De frente queda adelante; de perfil, sobre el costado
    visible (si no, desde el costado solo se ve pelo); de espaldas queda oculta."""
    ch = np.array([cam_local[0], cam_local[1], 0.0]); ch /= np.linalg.norm(ch) + 1e-9
    c = np.array([1.0, 0, 0]) + .9 * ch
    return c / (np.linalg.norm(c) + 1e-9)


def mat_cabeza_para(c):
    return lambda d: mat_cabeza(d, c)


def mat_cabeza(d, c=np.array([1.0, 0, 0])):
    adel, lat, arr = d[..., 0], d[..., 1], d[..., 2]
    frente = d[..., 0] * c[0] + d[..., 1] * c[1]                  # qué tan "de cara" está cada punto
    # pelo con mechones: franjas alternas por ángulo alrededor de la cabeza (detalle dibujado, no degradé)
    ang = np.arctan2(lat, -adel)
    m = np.where((np.floor(ang * 7 / np.pi) % 2) == 0, "pelo", "pelo_m").astype(object)
    # cara chica al frente (Stardew ~6x5 px): el pelo la enmarca por arriba y los costados
    m[(frente > .62) & (arr < .30)] = "piel"
    m[(arr >= .30) & (arr < .42) & (frente > .5)] = "oro"          # vincha
    return m


def mat_torso(d):
    adel, lat, arr = d[..., 0], d[..., 1], d[..., 2]
    m = np.full(d.shape[:-1], "tunica", dtype=object)
    m[(adel > .2) & (np.abs(lat) < .38)] = "camisa"                 # túnica abierta: se ve la camisa
    m[(adel > .2) & (np.abs(lat) >= .38) & (np.abs(lat) < .5)] = "oro"   # ribete de la abertura
    m[arr < -.7] = "oro"                                             # cinturón
    return m


def mat_faldon(d, t):
    ang = np.arctan2(d[..., 1], d[..., 0])
    return np.where((np.floor(ang * 5 / np.pi) % 2) == 0, "tunica", "tunica_m").astype(object)   # pliegues


def construir(esc, ps):
    A, cam, k = ANATOMIA, esc.cam.cam_local, ESCALA
    bob, sube = ps["bob"], -ps["bob"] * .9
    cadera = v(0, 0, A["cadera_u"] + sube)
    for lado, pie, ang in ((-1, ps["pie_a"], ps["ang_a"]), (1, ps["pie_b"], ps["ang_b"])):
        h = cadera + v(0, lado * A["cadera_l"], 0)
        tob = v((pie[0] - 18) * k, lado * A["cadera_l"], (34 - pie[1]) * k + .3)
        rod = ik_sagital(h, tob, A["muslo"], A["canilla"], +1)
        esc.pieza = PIEZA["pierna"] + lado
        esc.capsula(h, rod, A["r_muslo"], "pantalon")
        esc.capsula(rod, tob, A["r_canilla"], "pantalon")
        r = math.radians(ang)
        punta = tob + v(A["pie"] * math.cos(r), 0, -A["pie"] * math.sin(r))
        esc.pieza = PIEZA["bota"] + lado
        esc.capsula(tob, punta, A["r_pie"], "bota")
    esc.pieza = PIEZA["torso"]
    esc.elipsoide(v(-.2, 0, A["pecho_u"] + sube), A["pecho"], mat_torso)
    esc.elipsoide(v(0, 0, A["pelvis_u"] + sube), A["pelvis"], "tunica")
    lag = math.sin(2 * math.pi * (ps["fase"] - .1) * 2)
    esc.faldon(v(-.3, 0, 10.2 + sube), v(-1.4 - .6 * lag, 0, 3.6 + sube + .3 * lag), 2.7, 3.7, mat_faldon)
    esc.detalle(v(A["pecho"][0] + .1, -.4, A["pecho_u"] + .6 + sube), RUNA)      # runa en el pecho
    esc.detalle(v(A["pelvis"][0] + .1, 0, A["pelvis_u"] + 1.2 + sube), RUNA)     # gema del cinturón
    for lado, mano_p in ((-1, ps["mano_b"]), (1, ps["mano_a"])):
        hom = v(-.2, lado * A["hombro_l"], A["hombro_u"] + sube)
        mano = hom + v((mano_p[0] - 20) * k, lado * .6, (16 - mano_p[1]) * k)
        codo = ik_sagital(hom, mano, A["brazo"], A["antebrazo"], -1)
        esc.pieza = PIEZA["brazo"] + lado
        esc.capsula(hom, codo, A["r_brazo"], "tunica")                          # manga: separa brazo y torso
        esc.capsula(codo, mano, A["r_antebrazo"], "piel")
        esc.esfera(hom + v(0, lado * .3, .5), 1.05, "oro")                       # hombrera
        esc.detalle((hom + codo) / 2 + cam * A["r_brazo"], RUNA)                  # runa tatuada
        esc.detalle(codo + (mano - codo) * .45 + cam * A["r_antebrazo"], RUNA)
        esc.pieza = PIEZA["mano"] + lado
        esc.esfera(mano, A["r_mano"], "mano")
    esc.pieza = PIEZA["cabeza"]
    hc = v(.1, 0, A["cabeza_u"] + sube)
    cf, cl, cu = A["cabeza"]
    c = centro_cara(cam)
    esc.caja(hc, A["cabeza"], mat_cabeza_para(c), n=3.2)
    perp = np.array([-c[1], c[0], 0.0])                      # horizontal, perpendicular al centro de la cara
    cara = hc + np.array([c[0] * cf, c[1] * cl, 0]) * 1.02
    for lado in (-1, 1):                                     # ojos Stardew: pestaña oscura arriba, blanco + iris
        e = cara + perp * lado * 1.6 + v(0, 0, -1.2)
        esc.detalle(e + v(0, 0, 1.0), (40, 20, 30))
        esc.detalle(e, OJO); esc.detalle(e - perp * lado * .9, IRIS)
    esc.detalle(cara + v(0, 0, cu * .36), RUNA)                                  # gema de la vincha
    esc.detalle(cara + v(0, 0, -3.0), (110, 60, 50))                             # boca
    # rastas: caen a los costados y atrás de la cabeza hasta los hombros
    esc.pieza = PIEZA["pelo"]
    # arrancan POR FUERA de la esfera de la cabeza (si no, quedan tapadas) y enmarcan la cara
    for i, (df, dl) in enumerate(((-1.9, -5.5), (-3.6, -4.8), (-5.2, -1.8), (-5.2, 1.8), (-3.6, 4.8), (-1.9, 5.5))):
        pts = [hc + v(df, dl, .8)]
        for j in range(1, 5):
            sw = math.sin(j * .9 - ps["fase"] * 2 * math.pi + i) * .35
            pts.append(pts[-1] + v(-.35 + sw, dl * .06, -1.55 - (ps["bob_prev"] - bob) * .2))
        for a_, b_ in zip(pts, pts[1:]):
            esc.capsula(a_, b_, .95, "pelo" if i % 2 else "pelo_m")
        if i in (0, 5):
            esc.detalle(pts[-1] + cam * .9 + v(0, 0, -.6), RUNA)            # cuentas solo en las rastas del frente


def cuadro(ciclo, p, mira):
    cam = CamaraCenital(mira, luz=(-.25, .75, .6), **CELDA)     # luz más frontal = sombreado más plano
    esc = Escena(cam, PALETA)
    construir(esc, pose(ciclo, p))
    return esc.render(estilo=ESTILO["render"])


def comparar(por_dir, ruta):
    """Referencia (Abigail y Wizard) arriba, mago abajo, mismas 4 direcciones, ×6."""
    Z = 6
    ab = Image.open("referencias/stardew/abigail.png").convert("RGBA").crop((0, 0, 64, 128))
    wz = Image.open("referencias/stardew/wizard.png").convert("RGBA").crop((21, 236, 85, 364))
    dirs = ["S", "E", "N", "W"]
    out = Image.new("RGB", (16 * 4 * Z * 3 + 40, 32 * 4 * Z), (40, 38, 56))
    for r, dname in enumerate(dirs):
        for c in range(4):
            for col, src in enumerate((ab, wz, None)):
                if src is not None:
                    fr = src.crop((c * 16, r * 32, c * 16 + 16, r * 32 + 32))
                else:
                    fr = por_dir[dname][c % len(por_dir[dname])]
                big = fr.resize((16 * Z, 32 * Z), Image.NEAREST)
                out.paste(big, (col * (16 * 4 * Z + 20) + c * 16 * Z, r * 32 * Z), big)
    out.save(ruta)
    return ruta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--anim", default="caminar", choices=list(CICLOS))
    ap.add_argument("--comparar", action="store_true")
    a = ap.parse_args()
    c = CICLOS[a.anim]
    por_dir = {d: [cuadro(c, p, d) for p in range(c["n"])] for d in DIRECCIONES_CENITAL}
    sal = os.path.join("salida", NOMBRE, a.anim)
    exportar_direcciones(por_dir, a.anim, sal, fps=c["fps"], pivote=(CELDA["gx"], CELDA["gy"]), zoom=6)
    if a.comparar:
        print(comparar(por_dir, os.path.join(sal, "comparacion_stardew.png")))
    print("listo →", sal)
