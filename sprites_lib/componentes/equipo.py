"""Equipamiento: guante, sombrero y armadura.

Cada pieza se ancla a un ancla que ya mueven los ciclos (mano, coronilla, torso), así que sigue
la animación sin tocar el motor: blandir una espada con guante es reusar `golpear`. El dibujo es
primitivas simples con el material de la ficha (que puede venir de una skin de ítem).
"""

from ..cuerpo import lado_de
from ..render3d import v
from . import Componente, entrar, registrar


@registrar
class Guante(Componente):
    tipo = "guante"
    anclas_validas = ("mano_derecha", "mano_izquierda")
    material_defecto = "cuero"
    params_defecto = {}

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        A, a, m, s = ctx.anat, ctx.a, spec["material"], ctx.escala()
        lado = lado_de(spec["ancla"])
        mano = a[f"mano_{lado}"]
        r = A.r_mano * 1.3
        esc.caja(mano + v(0, 0, -0.15 * s), (r, r, r * 1.25), m, n=2.0)


@registrar
class Sombrero(Componente):
    tipo = "sombrero"
    anclas_validas = ("coronilla",)
    material_defecto = "cuero"
    params_defecto = {"alto": 1.0}

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        A, a, m = ctx.anat, ctx.a, spec["material"]
        rf, _rl, rz = A.cabeza
        copa = a["coronilla"]
        alto = float(spec["parametros"]["alto"])
        # ala: caja ancha y plana sobre la coronilla (no tapa la cara)
        esc.caja(copa + v(0, 0, -rz * 0.05), (rf * 1.6, rf * 1.6, rz * 0.16), m, n=2.0)
        # copa: más angosta y baja (no se corta contra el borde de la celda)
        esc.caja(
            copa + v(0, 0, rz * 0.28 * alto),
            (rf * 0.9, rf * 0.9, rz * 0.34 * alto),
            m,
            n=2.0,
        )


@registrar
class Armadura(Componente):
    tipo = "armadura"
    anclas_validas = ("torso",)
    material_defecto = "metal"
    params_defecto = {}

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        A, a, m = ctx.anat, ctx.a, spec["material"]
        pecho, pelvis = A.pecho, A.pelvis
        centro = (a["torso"] + a["cintura"]) * 0.5
        alto = (pecho[2] + pelvis[2]) * 0.55
        # ajustada al pecho (no más ancha): así no tapa las manos en vista cenital
        esc.caja(
            centro + v(0, 0, 0.1),
            (pecho[0] * 1.0, pecho[1] * 1.0, alto),
            m,
            n=2.0,
        )
