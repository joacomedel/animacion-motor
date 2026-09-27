"""Componentes robóticos: prótesis de brazo y pierna, brazo amputado, muñón con cables, visor, placa y cables.
Lección aplicada: detalles chicos (visor, chispa) con tamaño mínimo en px y color emisivo para que se lean a 16 px."""
import numpy as np

from ..cuerpo import lado_de, masc
from ..render3d import v
from . import Componente, entrar, perpendicular, registrar


def _hacia_afuera(p, centro):
    d = p - centro
    return d / (np.linalg.norm(d) + 1e-9)


def _detalles_metal(esc, ctx, p, segmentos, juntas):
    if p.get("rayas"):
        col = ctx.paleta[p["rayas"]][1]
        for q0, q1, r in segmentos:
            esc.detalle(q0 + (q1 - q0) * .5 + ctx.cam_local * r, col)
    if p.get("juntas"):
        col = ctx.paleta[p["juntas"]][1]
        for j, r in juntas:
            esc.detalle(j + ctx.cam_local * r, col)


@registrar
class BrazoRobotico(Componente):
    tipo = "brazo_robotico"
    anclas_validas = ("brazo_derecho", "brazo_izquierdo")
    material_defecto = "metal"
    params_defecto = {"juntas": None, "rayas": None, "mano": "pinza_3_dedos"}
    params_material = ("juntas", "rayas")

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s_ = masc(lado)
        A, a, m, p = ctx.anat, ctx.a, spec["material"], spec["parametros"]
        hom, codo, mano = a[f"hombro_{s_}"], a[f"codo_{s_}"], a[f"mano_{lado}"]
        entrar(esc, ctx, spec, 0)
        esc.esfera(hom, A.r_brazo * 1.3, m)                          # rótula del hombro
        esc.capsula(hom, codo, A.r_brazo * .95, m)
        esc.esfera(codo, A.r_brazo * 1.1, m)
        esc.capsula(codo, mano, A.r_antebrazo * .95, m)
        _detalles_metal(esc, ctx, p, [(hom, codo, A.r_brazo), (codo, mano, A.r_antebrazo)], [(codo, A.r_brazo * 1.1)])
        entrar(esc, ctx, spec, 1)                                    # mano = pieza propia
        eje = (mano - codo) / (np.linalg.norm(mano - codo) + 1e-9)
        if p["mano"] == "pinza_3_dedos":
            lat = perpendicular(eje)
            esc.esfera(mano, A.r_mano * .8, m)
            for off in (-.6, .6):
                esc.capsula(mano, mano + eje * A.r_mano * 1.4 + lat * off * A.r_mano, A.r_mano * .32, m)
            esc.capsula(mano, mano + eje * A.r_mano * 1.1 - np.cross(lat, eje) * A.r_mano * .8, A.r_mano * .32, m)
        else:
            esc.esfera(mano, A.r_mano, m)


@registrar
class BrazoRoboticoAmputado(Componente):
    tipo = "brazo_robotico_amputado"
    anclas_validas = ("brazo_derecho", "brazo_izquierdo")
    material_defecto = "metal"
    params_defecto = {"termina_en": None, "juntas": None}
    params_material = ("juntas",)

    def dibujar(self, esc, ctx, spec):
        s_ = masc(lado_de(spec["ancla"]))
        A, a, m = ctx.anat, ctx.a, spec["material"]
        hom, codo = a[f"hombro_{s_}"], a[f"codo_{s_}"]
        entrar(esc, ctx, spec)
        esc.esfera(hom, A.r_brazo * 1.3, m)
        esc.capsula(hom, codo, A.r_brazo * .95, m)
        esc.esfera(codo, A.r_brazo * 1.05, m)                        # termina en el codo: tapa rota
        _detalles_metal(esc, ctx, spec["parametros"], [], [(hom, A.r_brazo * 1.3)])


@registrar
class MunonCables(Componente):
    tipo = "munon_cables"
    anclas_validas = ("codo_derecho", "codo_izquierdo", "rodilla_derecha", "rodilla_izquierda")
    material_defecto = "cable"
    params_defecto = {"cables": 3, "largo_px": 2, "chispa": None, "chispa_cada_cuadros": 3}
    params_material = ("chispa",)

    def dibujar(self, esc, ctx, spec):
        an = spec["ancla"]; lado = lado_de(an)
        a, e, p = ctx.a, ctx.escala(), spec["parametros"]
        padre = a[f"hombro_{masc(lado)}"] if an.startswith("codo") else a[f"cadera_{lado}"]
        eje = (a[an] - padre) / (np.linalg.norm(a[an] - padre) + 1e-9)
        perp = perpendicular(eje)
        n = max(1, int(p["cables"]))
        entrar(esc, ctx, spec)
        puntas = []
        for i in range(n):
            t = (i - (n - 1) / 2) / max(1, n - 1)
            fin = a[an] + eje * (p["largo_px"] * e + ctx.anat.r_brazo) + perp * t * 1.2 * e + v(0, 0, -.6 * e * abs(t))
            esc.capsula(a[an], fin, .38 * e, spec["material"])
            puntas.append(fin)
        if p["chispa"] and ctx.cuadro % max(1, int(p["chispa_cada_cuadros"])) == 0:
            esc.detalle(puntas[0] + ctx.cam_local * .5 * e, ctx.paleta[p["chispa"]][2])


@registrar
class PiernaRobotica(Componente):
    tipo = "pierna_robotica"
    anclas_validas = ("pierna_derecha", "pierna_izquierda")
    material_defecto = "metal"
    params_defecto = {"juntas": None, "rodilla": "piston", "pie": "bota_metalica"}
    params_material = ("juntas",)

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s_ = masc(lado)
        A, a, m, p, e = ctx.anat, ctx.a, spec["material"], spec["parametros"], ctx.escala()
        cad, rod, tob, pie = a[f"cadera_{lado}"], a[f"rodilla_{lado}"], a[f"tobillo_{s_}"], a[f"pie_{s_}"]
        entrar(esc, ctx, spec, 0)
        esc.esfera(cad, A.r_muslo * 1.1, m)
        esc.capsula(cad, rod, A.r_muslo * .9, m)
        esc.esfera(rod, A.r_muslo * .95, m)
        esc.capsula(rod, tob, A.r_canilla * .95, m)
        if p["rodilla"] == "piston":
            esc.capsula(cad + (rod - cad) * .45 + v(A.r_muslo * .9, 0, 0),
                        rod + (tob - rod) * .45 + v(A.r_canilla * .9, 0, 0), .35 * e, m)
        _detalles_metal(esc, ctx, p, [], [(rod, A.r_muslo * .95)])
        entrar(esc, ctx, spec, 1)
        esc.esfera(tob, A.r_canilla * 1.05, m)
        esc.capsula(tob, pie, A.r_pie * 1.15, m)


@registrar
class Visor(Componente):
    tipo = "visor"
    anclas_validas = ("ojo_derecho", "ojo_izquierdo")
    material_defecto = "metal"
    params_defecto = {"lente": None, "tamano_min_px": 2}
    params_material = ("lente",)

    def dibujar(self, esc, ctx, spec):
        o, hc, e, p = ctx.a[spec["ancla"]], ctx.a["cabeza"], ctx.escala(), spec["parametros"]
        afuera = _hacia_afuera(o, hc)
        entrar(esc, ctx, spec)
        esc.caja(o + afuera * .3 * e, (1.0 * e, 1.2 * e, .9 * e), spec["material"], n=3.0)
        if p["lente"]:
            n = max(1, int(p["tamano_min_px"]))
            for k in range(n):
                esc.detalle(o + afuera * 1.3 * e + v(0, 0, (k - (n - 1) / 2) * e), ctx.paleta[p["lente"]][1])


@registrar
class PlacaSien(Componente):
    tipo = "placa_sien"
    anclas_validas = ("sien_derecha", "sien_izquierda")
    material_defecto = "metal"

    def dibujar(self, esc, ctx, spec):
        o, e = ctx.a[spec["ancla"]], ctx.escala()
        afuera = _hacia_afuera(o, ctx.a["cabeza"])
        entrar(esc, ctx, spec)
        esc.caja(o + afuera * .25 * e, (1.3 * e, .6 * e, 1.4 * e), spec["material"], n=4.0)
        esc.detalle(o + afuera * .9 * e, ctx.paleta[spec["material"]][2])        # remache


@registrar
class CablesNuca(Componente):
    tipo = "cables_nuca"
    anclas_validas = ("nuca",)
    material_defecto = "cable"
    params_defecto = {"cables": 2, "luz_en_punta": None}
    params_material = ("luz_en_punta",)

    def dibujar(self, esc, ctx, spec):
        o, e, p = ctx.a["nuca"], ctx.escala(), spec["parametros"]
        n = max(1, int(p["cables"]))
        entrar(esc, ctx, spec)
        for i in range(n):
            lat = (i - (n - 1) / 2) * 1.4 * e
            fin = o + v(-1.6 * e, lat, -2.2 * e)
            esc.capsula(o + v(-.2 * e, lat, 0), fin, .42 * e, spec["material"])
            if p["luz_en_punta"]:
                esc.detalle(fin + ctx.cam_local * .4 * e, ctx.paleta[p["luz_en_punta"]][1])
