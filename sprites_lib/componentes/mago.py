"""Componentes del mago: rastas, vincha, pulsera, tatuajes rúnicos, túnica abierta y botas.
Lecciones aplicadas: las rastas nacen FUERA del volumen de la cabeza (si no, quedan tapadas) y tienen
1 cuadro de retraso; la túnica va abierta adelante (se ven las piernas) y con pliegues (detalle dibujado);
las mangas separan brazo y torso."""
import numpy as np

from ..cuerpo import lado_de, masc
from ..render3d import v
from . import Componente, entrar, registrar


@registrar
class Rastas(Componente):
    tipo = "rastas"
    anclas_validas = ("cabeza",)
    material_defecto = "pelo"
    params_defecto = {"cantidad": 6, "largo": "hombros", "cuentas": None}
    params_material = ("cuentas",)

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        A, p, s = ctx.anat, spec["parametros"], ctx.escala()
        rf, rl, rz = A.cabeza
        hc = ctx.a["cabeza"]
        n = max(2, int(p["cantidad"]))
        pasos = {"corto": 2, "hombros": 4, "cintura": 6}[p["largo"]]
        bob, prev = ctx.ps["bob"], ctx.ps["bob_prev"]
        for i in range(n):
            ang = np.pi * (.5 + i / (n - 1))              # de un costado a otro pasando por la nuca
            pts = [hc + v(np.cos(ang) * rf * .95, np.sin(ang) * rl * .93, rz * .15)]   # asoman del volumen de la cabeza sin salirse de la celda
            for j in range(1, pasos + 1):
                sw = np.sin(j * .9 - ctx.ps["fase"] * 2 * np.pi + i) * .35 * s
                pts.append(pts[-1] + v(-.2 * s + sw * .6, np.sin(ang) * .03 * s, -1.55 * s - (prev - bob) * .2 * s))
            mat = spec["material"] if i % 2 else f'{spec["material"]}_b'
            for q0, q1 in zip(pts, pts[1:]):
                esc.capsula(q0, q1, .85 * s, mat)
            if p["cuentas"] and i in (0, n - 1):
                esc.detalle(pts[-1] + ctx.cam_local * .9 * s + v(0, 0, -.6 * s), ctx.paleta[p["cuentas"]][1])


@registrar
class Vincha(Componente):
    tipo = "vincha"
    anclas_validas = ("frente",)
    material_defecto = "oro"
    params_defecto = {"gema": None}
    params_material = ("gema",)

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        A, hc = ctx.anat, ctx.a["cabeza"]
        banda = lambda d: np.abs(d[..., 2] - .47) < .08
        radios = tuple(r * 1.05 for r in A.cabeza)
        if ctx.est["proporciones"]["forma_cabeza"] == "caja":
            esc.caja(hc, radios, spec["material"], n=3.2, conservar=banda)
        else:
            esc.elipsoide(hc, radios, spec["material"], conservar=banda)
        g = spec["parametros"]["gema"]
        if g:
            fr = ctx.a["frente"]
            esc.detalle(fr + (fr - hc) * .08 + v(0, 0, A.cabeza[2] * .1), ctx.paleta[g][1])


@registrar
class Pulsera(Componente):
    tipo = "pulsera"
    anclas_validas = ("muneca_derecha", "muneca_izquierda")
    material_defecto = "oro"
    params_defecto = {"grosor": 1.0}

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"])
        a, A, s = ctx.a, ctx.anat, ctx.escala()
        eje = a[f"mano_{lado}"] - a[f"codo_{masc(lado)}"]
        u = eje / (np.linalg.norm(eje) + 1e-9)
        m = a[spec["ancla"]]
        largo = max(.12 * np.linalg.norm(eje), 1.0 * s)                 # nunca menos de ~1 px de ancho
        entrar(esc, ctx, spec)
        esc.capsula(m - u * largo / 2, m + u * largo / 2, A.r_antebrazo + .35 * s * spec["parametros"]["grosor"],
                    spec["material"], tapas=False)


@registrar
class TatuajeRunas(Componente):
    tipo = "tatuaje_runas"
    anclas_validas = ("brazo_derecho", "brazo_izquierdo")
    material_defecto = "runa"
    params_defecto = {"puntos_por_segmento": 1}

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s_ = masc(lado)
        A, a = ctx.anat, ctx.a
        col = ctx.paleta[spec["material"]][1]
        n = max(1, int(spec["parametros"]["puntos_por_segmento"]))
        segs = [(a[f"hombro_{s_}"], a[f"codo_{s_}"], A.r_brazo)]
        if not ctx.ausente(f"antebrazo_{s_}"):
            segs.append((a[f"codo_{s_}"], a[f"muneca_{lado}"], A.r_antebrazo))
        entrar(esc, ctx, spec)
        for q0, q1, r in segs:
            for k in (np.linspace(.3, .8, n) if n > 1 else [.5]):
                esc.detalle(q0 + (q1 - q0) * k + ctx.cam_local * r, col)


@registrar
class TunicaAbierta(Componente):
    tipo = "tunica_abierta"
    anclas_validas = ("torso",)
    material_defecto = "tunica"
    params_defecto = {"interior": None, "ribete": None, "faldon": "hasta_rodilla", "mangas": True}
    params_material = ("interior", "ribete")

    def dibujar(self, esc, ctx, spec):
        A, a, m, p, s = ctx.anat, ctx.a, spec["material"], spec["parametros"], ctx.escala()

        def mat_torso(d):
            adel, lat = d[..., 0], np.abs(d[..., 1])
            out = np.full(d.shape[:-1], m, dtype=object)
            if p["interior"]:
                out[(adel > .2) & (lat < .38)] = p["interior"]
            if p["ribete"]:
                out[(adel > .2) & (lat >= .38) & (lat < .5)] = p["ribete"]
            return out

        entrar(esc, ctx, spec, 0)
        esc.elipsoide(a["torso"], tuple(r * 1.08 for r in A.pecho), mat_torso)
        esc.elipsoide(a["cintura"] + v(0, 0, -A.pelvis[2] * .8), tuple(r * 1.08 for r in A.pelvis), m)
        sube = a["cintura"][2] - (A.pelvis_u + A.pelvis[2] * .8)
        lag = np.sin(2 * np.pi * (ctx.ps["fase"] - .1) * 2)
        hasta = {"hasta_rodilla": A.cadera_u * .45, "medio_muslo": A.cadera_u * .7, "tobillo": A.cadera_u * .12}[p["faldon"]]
        pliegue = lambda d, t: np.where((np.floor(np.arctan2(d[..., 1], d[..., 0]) * 5 / np.pi) % 2) == 0,
                                        m, f"{m}_b").astype(object)
        esc.faldon(a["cintura"], v(-A.H * .05 - .6 * lag * s, 0, hasta + sube), A.pelvis[1] * 1.0,
                   A.pelvis[1] * 1.3, pliegue)
        if p["mangas"]:
            for k, s_ in enumerate(("derecho", "izquierdo")):
                entrar(esc, ctx, spec, 1 + k)                    # la manga separa brazo y torso
                hom, codo = a[f"hombro_{s_}"], a[f"codo_{s_}"]
                esc.capsula(hom, hom + (codo - hom) * .6, A.r_brazo + .25 * s, m)


@registrar
class Botas(Componente):
    tipo = "botas"
    anclas_validas = ("pie_derecho", "pie_izquierdo")
    material_defecto = "bota"
    params_defecto = {"suela": None}
    params_material = ("suela",)

    def dibujar(self, esc, ctx, spec):
        s_ = masc(lado_de(spec["ancla"]))
        A, a, s = ctx.anat, ctx.a, ctx.escala()
        tob, pie = a[f"tobillo_{s_}"], a[f"pie_{s_}"]
        entrar(esc, ctx, spec)
        esc.capsula(tob, pie, A.r_pie * 1.12, spec["material"])
        esc.capsula(tob, tob + v(0, 0, A.canilla * .35), A.r_canilla * 1.15, spec["material"], tapas=False)
        if spec["parametros"]["suela"]:
            col = ctx.paleta[spec["parametros"]["suela"]][1]
            for k in np.linspace(0, 1, 4):
                esc.detalle(tob + (pie - tob) * k + v(0, 0, -A.r_pie * 1.12 + .25 * s) + ctx.cam_local * .6 * s, col)
