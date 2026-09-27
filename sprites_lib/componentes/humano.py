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
        c = centro_cara(ctx.cam_local)
        corto = spec["parametros"]["cabello"] == "corto"

        def mat(d):
            m = np.full(d.shape[:-1], "piel", dtype=object)
            if corto:
                frente = d[..., 0] * c[0] + d[..., 1] * c[1]
                ang = np.arctan2(d[..., 1], -d[..., 0])
                pelo = np.where((np.floor(ang * 7 / np.pi) % 2) == 0, "pelo", "pelo_b")     # mechones
                m = np.where((frente > .62) & (d[..., 2] < .42), "piel", pelo).astype(object)
            return m

        if ctx.est["proporciones"]["forma_cabeza"] == "caja":
            esc.caja(ctx.a["cabeza"], ctx.anat.cabeza, mat, n=3.2)
        else:
            esc.elipsoide(ctx.a["cabeza"], ctx.anat.cabeza, mat)


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
            if ctx.est["ojos"] == "stardew":
                esc.detalle(e + v(0, 0, 1.0 * s), oscuro)              # pestaña
                esc.detalle(e, BLANCO)
                esc.detalle(e - perp * lado * .9 * s, iris)             # iris hacia el centro de la cara
            else:
                esc.detalle(e, BLANCO)
                esc.detalle(e - perp * lado * .6 * s, oscuro)
        esc.detalle(ctx.a["cara"] + v(0, 0, -ctx.anat.cabeza[2] * .55), _oscuro(pal["piel"][0], .8))   # boca


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
