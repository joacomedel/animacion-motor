"""Cuerpo base humano: cabeza, rostro, torso, brazos y piernas. Cada estilo cambia formas; las lecciones
aplicadas: puño como pieza propia y más grande que el antebrazo, cabeza cuadrada en estilos no volumétricos,
cara corrida hacia la cámara (se lee de perfil), ojos de 2 px en Stardew."""
import numpy as np

from ..cuerpo import centro_cara, lado_de, masc
from ..render3d import v
from . import Componente, entrar, registrar

BLANCO = (250, 250, 250)


def _oscuro(c, k):
    return tuple(int(x * k) for x in c)


@registrar
class CabezaHumana(Componente):
    tipo = "cabeza_humana"
    anclas_validas = ("cabeza",)
    params_defecto = {"cabello": "corto"}
    material_defecto = "piel"

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        c = centro_cara(ctx.cam_local, ctx.est["proporciones"].get("cara_hacia_camara", .9))
        corto = spec["parametros"]["cabello"] == "corto"

        def mat(d):
            frente = d[..., 0] * c[0] + d[..., 1] * c[1]
            m = np.full(d.shape[:-1], "piel", dtype=object)
            if not corto:
                # rapado: la zona del pelo corto (arriba y atrás) va en el color de pelo (o un tono de piel más oscuro);
                # si no, la cabeza es un bloque liso de piel
                zona = (d[..., 2] > .35) | ((frente < -.25) & (d[..., 2] > -.35))
                base = "pelo" if "pelo" in ctx.paleta else "piel_b"
                ang = np.arctan2(d[..., 1], -d[..., 0])
                veta = (np.floor(ang * 9 / np.pi) % 3) == 1 if base == "pelo" else np.zeros(d.shape[:-1], bool)
                m[zona] = base
                m[zona & veta] = "pelo_b"                     # textura de pelo corto (detalle dibujado)
            if corto:
                frente = d[..., 0] * c[0] + d[..., 1] * c[1]
                ang = np.arctan2(d[..., 1], -d[..., 0])
                pelo = np.where((np.floor(ang * 9 / np.pi) % 3) == 1, "pelo_b", "pelo")     # mechones: 1 de cada 3
                m = np.where((frente > .62) & (d[..., 2] < .42), "piel", pelo).astype(object)
            return m

        if ctx.est["proporciones"]["forma_cabeza"] == "caja":
            esc.caja(ctx.a["cabeza"], ctx.anat.cabeza, mat, n=3.2)
        else:
            esc.elipsoide(ctx.a["cabeza"], ctx.anat.cabeza, mat)
        # nariz: asoma hacia donde mira; de perfil es lo que dice "para allá va"
        A = ctx.anat
        esc.esfera(ctx.a["cabeza"] + v(A.cabeza[0] * .98, 0, -A.cabeza[2] * .3), .55 * ctx.escala(), "piel")
        # orejas: pieza propia (contorno propio); rompen la silueta cuadrada y agregan detalle dibujado
        entrar(esc, ctx, spec, 1)
        s, rz = ctx.escala(), ctx.anat.cabeza[2]
        for lado in ("derecha", "izquierda"):
            sien = ctx.a[f"sien_{lado}"]
            hacia_centro = (ctx.a["cabeza"] - sien) * np.array([0, .05, 0])        # pegadas a la cabeza, pero asomando
            esc.esfera(sien + hacia_centro + v(0, 0, -rz * .45), .7 * s, "piel")


@registrar
class Ojos(Componente):
    tipo = "ojos"
    anclas_validas = ("cara",)
    params_defecto = {"solo": None, "iris": None}
    params_material = ("iris",)

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        p, pal, s = spec["parametros"], ctx.paleta, ctx.escala()
        oscuro = _oscuro(pal["piel"][0], .45)
        iris = pal[p["iris"]][1] if p["iris"] else (44, 34, 48)
        izq, der = ctx.a["ojo_izquierdo"], ctx.a["ojo_derecho"]
        perp = (izq - der) / (np.linalg.norm(izq - der) + 1e-9)
        for nombre, e, lado in (("ojo_izquierdo", izq, 1), ("ojo_derecho", der, -1)):
            if p["solo"] and nombre != p["solo"]:
                continue
            esc.componente = f'{spec["id"]}#{nombre}'      # cada ojo es una parte: se mide por separado
            if ctx.est["ojos"] == "stardew":
                esc.detalle(e + v(0, 0, 1.0 * s), oscuro)              # pestaña
                esc.detalle(e, BLANCO)
                esc.detalle(e - perp * lado * .9 * s, iris)             # iris hacia el centro de la cara
            else:
                esc.detalle(e, BLANCO)
                esc.detalle(e - perp * lado * .6 * s, oscuro)
        esc.componente = f'rostro@{spec["ancla"]}'     # cejas, nariz y boca aparte: las líneas guía miden los ojos
        esc.detalle(ctx.a["cara"] + v(0, 0, -ctx.anat.cabeza[2] * .55), _oscuro(pal["piel"][0], .8))   # boca
        esc.detalle(ctx.a["cara"] + v(.3 * s, 0, -ctx.anat.cabeza[2] * .3), pal["piel"][0])           # sombra de nariz
        ceja = pal["pelo"][0] if "pelo" in pal else _oscuro(pal["piel"][0], .6)
        for nombre, e, lado in (("ojo_izquierdo", izq, 1), ("ojo_derecho", der, -1)):
            if p["solo"] and nombre != p["solo"]:
                continue
            for k in (0, 1):                                                                       # cejas de 2 px
                esc.detalle(e + v(0, 0, 2.0 * s) - perp * lado * k * .9 * s, ceja)


@registrar
class TorsoHumano(Componente):
    tipo = "torso_humano"
    anclas_validas = ("torso",)
    material_defecto = "piel"

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        A, a, m = ctx.anat, ctx.a, spec["material"]
        esc.elipsoide(a["torso"], A.pecho, m)
        esc.elipsoide(a["cintura"] + v(0, 0, -A.pelvis[2] * .8), A.pelvis, m)
        esc.capsula(a["cuello"] + v(0, 0, -A.H * .05), a["cuello"] + v(0, 0, A.H * .035), A.H * .056, "piel", tapas=False)


@registrar
class BrazoHumano(Componente):
    tipo = "brazo_humano"
    anclas_validas = ("brazo_derecho", "brazo_izquierdo")
    material_defecto = "piel"

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s = masc(lado)
        A, a, m = ctx.anat, ctx.a, spec["material"]
        hom, codo, mano = a[f"hombro_{s}"], a[f"codo_{s}"], a[f"mano_{lado}"]
        entrar(esc, ctx, spec, 0)
        esc.capsula(hom, codo, A.r_brazo, m)
        if ctx.ausente(f"antebrazo_{s}"):
            return
        esc.capsula(codo, mano, A.r_antebrazo, m)
        if not ctx.ausente(f"mano_{lado}"):
            entrar(esc, ctx, spec, 1)                   # el puño es pieza propia: tiene contorno propio
            esc.esfera(mano + (mano - codo) * .06, A.r_mano, "mano")


@registrar
class PiernaHumana(Componente):
    tipo = "pierna_humana"
    anclas_validas = ("pierna_derecha", "pierna_izquierda")
    params_defecto = {"calzado": None}
    params_material = ("calzado",)
    material_defecto = "piel"

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s = masc(lado)
        A, a, m = ctx.anat, ctx.a, spec["material"]
        entrar(esc, ctx, spec, 0)
        esc.capsula(a[f"cadera_{lado}"], a[f"rodilla_{lado}"], A.r_muslo, m)
        esc.capsula(a[f"rodilla_{lado}"], a[f"tobillo_{s}"], A.r_canilla, m)
        entrar(esc, ctx, spec, 1)
        esc.capsula(a[f"tobillo_{s}"], a[f"pie_{s}"], A.r_pie, spec["parametros"]["calzado"] or m)
