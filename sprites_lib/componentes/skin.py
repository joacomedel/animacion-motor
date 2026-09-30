"""Muñeco base con skin: mismas formas que el cuerpo humano, pero cada punto toma el color de su lugar en la skin
(ver sprites_lib/skins.py). La cabeza usa como "frente" la dirección de la cara corrida hacia la cámara (trampa de
Stardew), así el pelo pintado enmarca los ojos que dibuja el componente `ojos`."""
import math

import numpy as np

from ..cuerpo import centro_cara, fuerza_cara, giro_cabeza, radios_cabeza, lado_de, masc
from ..render3d import v
from ..skins import cargar, material, u_de, CARA
from . import Componente, entrar, registrar


def _skin(spec):
    return cargar(spec["parametros"]["skin"])


@registrar
class CabezaSkin(Componente):
    tipo = "cabeza_skin"
    anclas_validas = ("cabeza",)
    params_defecto = {"skin": None}

    def dibujar(self, esc, ctx, spec):
        sk, A = _skin(spec), ctx.anat
        c = centro_cara(ctx.cam_local, fuerza_cara(ctx.est["proporciones"], ctx.cam_local))
        ref = math.atan2(c[1], c[0])
        mat = lambda d: sk.zona("cabeza", u_de(d, ref), (1 - d[..., 2]) / 2)
        piel = material(sk.color(*CARA))
        entrar(esc, ctx, spec)
        if ctx.est["proporciones"]["forma_cabeza"] == "caja":
            esc.caja(ctx.a["cabeza"], radios_cabeza(ctx.est["proporciones"], ctx.mira, A.cabeza), mat, n=3.2, giro=giro_cabeza(ctx.est["proporciones"], ctx.mira))
        else:
            esc.elipsoide(ctx.a["cabeza"], A.cabeza, mat)
        esc.esfera(ctx.a["cabeza"] + v(A.cabeza[0] * .98, 0, -A.cabeza[2] * .3), .55 * ctx.escala(), piel)   # nariz
        entrar(esc, ctx, spec, 1)                                               # orejas: pieza propia
        s, rz = ctx.escala(), A.cabeza[2]
        for lado in ("derecha", "izquierda"):
            sien = ctx.a[f"sien_{lado}"]
            esc.esfera(sien + (ctx.a["cabeza"] - sien) * np.array([0, .05, 0]) + v(0, 0, -rz * .45), .7 * s, piel)


@registrar
class TorsoSkin(Componente):
    tipo = "torso_skin"
    anclas_validas = ("torso",)
    params_defecto = {"skin": None}

    def dibujar(self, esc, ctx, spec):
        sk, A, a = _skin(spec), ctx.anat, ctx.a
        entrar(esc, ctx, spec)
        esc.elipsoide(a["torso"], A.pecho, lambda d: sk.zona("torso", u_de(d), (1 - d[..., 2]) / 2 * .7))
        esc.elipsoide(a["cintura"] + v(0, 0, -A.pelvis[2] * .8), A.pelvis,
                      lambda d: sk.zona("torso", u_de(d), .6 + (1 - d[..., 2]) / 2 * .4))
        esc.capsula(a["cuello"] + v(0, 0, -A.H * .05), a["cuello"] + v(0, 0, A.H * .035), A.H * .056,
                    material(sk.color(*CARA)), tapas=False)


@registrar
class BrazoSkin(Componente):
    tipo = "brazo_skin"
    anclas_validas = ("brazo_derecho", "brazo_izquierdo")
    params_defecto = {"skin": None}

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s = masc(lado)
        sk, A, a = _skin(spec), ctx.anat, ctx.a
        hom, codo, mano = a[f"hombro_{s}"], a[f"codo_{s}"], a[f"mano_{lado}"]
        z = f"brazo_{s}"
        entrar(esc, ctx, spec, 0)
        esc.capsula(hom, codo, A.r_brazo, lambda d, t: sk.zona(z, u_de(d), t * .5))
        esc.capsula(codo, mano, A.r_antebrazo, lambda d, t: sk.zona(z, u_de(d), .5 + t * .5))
        entrar(esc, ctx, spec, 1)                                               # el puño es pieza propia
        esc.esfera(mano + (mano - codo) * .06, A.r_mano,
                   lambda d: sk.zona(f"mano_{lado}", u_de(d), (1 - d[..., 2]) / 2))


@registrar
class PiernaSkin(Componente):
    tipo = "pierna_skin"
    anclas_validas = ("pierna_derecha", "pierna_izquierda")
    params_defecto = {"skin": None}

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s = masc(lado)
        sk, A, a = _skin(spec), ctx.anat, ctx.a
        z = f"pierna_{lado}"
        entrar(esc, ctx, spec, 0)
        esc.capsula(a[f"cadera_{lado}"], a[f"rodilla_{lado}"], A.r_muslo, lambda d, t: sk.zona(z, u_de(d), t * .5))
        esc.capsula(a[f"rodilla_{lado}"], a[f"tobillo_{s}"], A.r_canilla, lambda d, t: sk.zona(z, u_de(d), .5 + t * .5))
        entrar(esc, ctx, spec, 1)
        esc.capsula(a[f"tobillo_{s}"], a[f"pie_{s}"], A.r_pie, lambda d, t: sk.zona(f"pie_{s}", u_de(d), t))
