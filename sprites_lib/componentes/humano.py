"""Cuerpo base humano: cabeza, rostro, torso, brazos y piernas. Cada estilo cambia formas; las lecciones
aplicadas: puño como pieza propia y más grande que el antebrazo, cabeza cuadrada en estilos no volumétricos,
cara corrida hacia la cámara (se lee de perfil), ojos de 2 px en Stardew. El pelo rizado suma volumen de
esferas fuera del cráneo, como las rastas: si nacen adentro, quedan tapadas."""

import numpy as np

from ..cuerpo import centro_cara, fuerza_cara, giro_cabeza, radios_cabeza, lado_de, masc
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
        c = centro_cara(
            ctx.cam_local, fuerza_cara(ctx.est["proporciones"], ctx.cam_local)
        )
        cabello = spec["parametros"]["cabello"]
        corto = cabello == "corto"

        def mat(d):
            frente = d[..., 0] * c[0] + d[..., 1] * c[1]
            m = np.full(d.shape[:-1], "piel", dtype=object)
            if cabello not in ("corto", "calvo"):
                # rapado: la zona del pelo corto (arriba y atrás) va en el color de pelo (o un tono de piel más oscuro);
                # si no, la cabeza es un bloque liso de piel
                zona = (d[..., 2] > 0.35) | ((frente < -0.25) & (d[..., 2] > -0.35))
                base = "pelo" if "pelo" in ctx.paleta else "piel_b"
                ang = np.arctan2(d[..., 1], -d[..., 0])
                veta = (
                    (np.floor(ang * 9 / np.pi) % 3) == 1
                    if base == "pelo"
                    else np.zeros(d.shape[:-1], bool)
                )
                m[zona] = base
                m[zona & veta] = "pelo_b"  # textura de pelo corto (detalle dibujado)
            if corto:
                frente = d[..., 0] * c[0] + d[..., 1] * c[1]
                ang = np.arctan2(d[..., 1], -d[..., 0])
                pelo = np.where(
                    (np.floor(ang * 9 / np.pi) % 3) == 1, "pelo_b", "pelo"
                )  # mechones: 1 de cada 3
                m = np.where((frente > 0.62) & (d[..., 2] < 0.42), "piel", pelo).astype(
                    object
                )
            return m

        if ctx.est["proporciones"]["forma_cabeza"] == "caja":
            esc.caja(
                ctx.a["cabeza"],
                radios_cabeza(ctx.est["proporciones"], ctx.mira, ctx.anat.cabeza),
                mat,
                n=3.2,
                giro=giro_cabeza(ctx.est["proporciones"], ctx.mira),
            )
        else:
            esc.elipsoide(ctx.a["cabeza"], ctx.anat.cabeza, mat)
        if cabello == "cresta":
            # cresta: de la nuca a la frente, más alta adelante y terminando en punta hacia donde mira.
            # De perfil la silueta de la cabeza señala la dirección (como las rastas largas señalan la nuca).
            entrar(esc, ctx, spec, 2)
            rf, rl, rz = ctx.anat.cabeza
            hc, s = ctx.a["cabeza"], ctx.escala()
            pts = [
                hc + v(rf * t, 0, rz * (0.95 + 0.12 * (t + 1)))
                for t in (-0.9, -0.45, 0, 0.45, 0.85)
            ]
            pts.append(hc + v(rf * 1.25, 0, rz * 1.0))  # punta hacia adelante
            for i, (q0, q1) in enumerate(zip(pts, pts[1:])):
                esc.capsula(
                    q0, q1, (0.9 + 0.15 * i) * s, "pelo" if i % 2 == 0 else "pelo_b"
                )
            entrar(esc, ctx, spec, 0)
        # nariz: asoma hacia donde mira; de perfil es lo que dice "para allá va"
        A = ctx.anat
        esc.esfera(
            ctx.a["cabeza"] + v(A.cabeza[0] * 0.98, 0, -A.cabeza[2] * 0.3),
            0.55 * ctx.escala(),
            "piel",
        )
        # orejas: pieza propia (contorno propio); rompen la silueta cuadrada y agregan detalle dibujado
        entrar(esc, ctx, spec, 1)
        s, rz = ctx.escala(), ctx.anat.cabeza[2]
        for lado in ("derecha", "izquierda"):
            sien = ctx.a[f"sien_{lado}"]
            hacia_centro = (ctx.a["cabeza"] - sien) * np.array(
                [0, 0.05, 0]
            )  # pegadas a la cabeza, pero asomando
            esc.esfera(sien + hacia_centro + v(0, 0, -rz * 0.45), 0.7 * s, "piel")


@registrar
class Ojos(Componente):
    tipo = "ojos"
    anclas_validas = ("cara",)
    params_defecto = {"solo": None, "iris": None}
    params_material = ("iris",)

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        p, pal, s = spec["parametros"], ctx.paleta, ctx.escala()
        oscuro = _oscuro(pal["piel"][0], 0.45)
        iris = pal[p["iris"]][1] if p["iris"] else (44, 34, 48)
        izq, der = ctx.a["ojo_izquierdo"], ctx.a["ojo_derecho"]
        perp = (izq - der) / (np.linalg.norm(izq - der) + 1e-9)
        cara = {
            n: float((e - ctx.a["cabeza"]) @ ctx.cam_local)
            for n, e in (("ojo_izquierdo", izq), ("ojo_derecho", der))
        }
        lejano = (
            min(cara, key=cara.get) if len(ctx.mira) == 2 else None
        )  # diagonal: el ojo lejano se ve de canto (1 px)
        for nombre, e, lado in (("ojo_izquierdo", izq, 1), ("ojo_derecho", der, -1)):
            if p["solo"] and nombre != p["solo"]:
                continue
            umbral = ctx.est["proporciones"].get("ojos_umbral")
            if (
                umbral is not None
            ):  # ojo que mira de canto (casi de espaldas): no se dibuja, asomaba 1 px en NE/NW
                n = e - ctx.a["cabeza"]
                if float(n @ ctx.cam_local) / (np.linalg.norm(n) + 1e-9) < umbral:
                    continue
            if ctx.mira in (
                "E",
                "W",
            ) and nombre == min(
                cara, key=cara.get
            ):  # perfil: el ojo lejano queda detrás de la cabeza
                continue
            esc.componente = (
                f"{spec['id']}#{nombre}"  # cada ojo es una parte: se mide por separado
            )
            if ctx.est["ojos"] == "stardew":
                esc.detalle(e + v(0, 0, 1.0 * s), oscuro)  # pestaña
                esc.detalle(e, BLANCO)
                esc.detalle(
                    e - perp * lado * 0.9 * s, iris
                )  # iris hacia el centro de la cara
            elif (
                ctx.est["ojos"] == "fry"
            ):  # 2×2 px: pestaña oscura, blanco afuera, iris adentro
                adentro = perp * lado * 1.0 * s
                esc.detalle(e + v(0, 0, 1.0 * s), oscuro)
                esc.detalle(e, BLANCO)
                if nombre != lejano:
                    esc.detalle(e + v(0, 0, 1.0 * s) - adentro, oscuro)
                    esc.detalle(e - adentro, iris)
            else:
                esc.detalle(e, BLANCO)
                esc.detalle(e - perp * lado * 0.6 * s, oscuro)
        # cejas, nariz y boca aparte: las líneas guía miden los ojos. Cada rasgo es una parte con nombre propio
        # ('rostro@cara#boca', ...) solo en el buffer de componentes: la imagen no cambia (lo usa sprites_lib.zonas)
        rostro = f"rostro@{spec['ancla']}"
        if not (
            ctx.est["proporciones"].get("sin_boca_diagonal") and len(ctx.mira) == 2
        ):
            # en las diagonales de 8 direcciones la boca cae sobre el contorno de la cabeza y se confunde con él
            esc.componente = rostro + "#boca"
            esc.detalle(
                ctx.a["boca"], _oscuro(pal["piel"][0], 0.8)
            )  # boca (ancla apoyada en la caja de la cabeza, ver cuerpo.posar)
            esc.componente = rostro + "#nariz"
            esc.detalle(
                ctx.a["cara"] + v(0.3 * s, 0, -ctx.anat.cabeza[2] * 0.3), pal["piel"][0]
            )  # sombra de nariz
        ceja = pal["pelo"][0] if "pelo" in pal else _oscuro(pal["piel"][0], 0.6)
        for nombre, e, lado in (("ojo_izquierdo", izq, 1), ("ojo_derecho", der, -1)):
            if p["solo"] and nombre != p["solo"]:
                continue
            esc.componente = rostro + (
                "#ceja_izquierda" if nombre == "ojo_izquierdo" else "#ceja_derecha"
            )
            for k in (
                (0, 1) if ctx.est["ojos"] != "fry" else (-0.5, 0.5, 1.5)
            ):  # cejas de 2 px (fry: 3 px seguidos)
                esc.detalle(
                    e
                    + v(0, 0, (2.0 if ctx.est["ojos"] != "fry" else 2.6) * s)
                    - perp * lado * k * (0.9 if ctx.est["ojos"] != "fry" else 1.0) * s,
                    ceja,
                )


@registrar
class TorsoHumano(Componente):
    tipo = "torso_humano"
    anclas_validas = ("torso",)
    material_defecto = "piel"

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        A, a, m = ctx.anat, ctx.a, spec["material"]
        esc.elipsoide(a["torso"], A.pecho, m)
        esc.elipsoide(a["cintura"] + v(0, 0, -A.pelvis[2] * 0.8), A.pelvis, m)
        esc.capsula(
            a["cuello"] + v(0, 0, -A.H * 0.05),
            a["cuello"] + v(0, 0, A.H * 0.035),
            A.H * 0.056,
            "piel",
            tapas=False,
        )


@registrar
class BrazoHumano(Componente):
    tipo = "brazo_humano"
    anclas_validas = ("brazo_derecho", "brazo_izquierdo")
    material_defecto = "piel"

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"])
        s = masc(lado)
        A, a, m = ctx.anat, ctx.a, spec["material"]
        hom, codo, mano = a[f"hombro_{s}"], a[f"codo_{s}"], a[f"mano_{lado}"]
        entrar(esc, ctx, spec, 0)
        esc.capsula(hom, codo, A.r_brazo, m)
        if ctx.ausente(f"antebrazo_{s}"):
            return
        esc.capsula(codo, mano, A.r_antebrazo, m)
        if not ctx.ausente(f"mano_{lado}"):
            entrar(esc, ctx, spec, 1)  # el puño es pieza propia: tiene contorno propio
            esc.esfera(mano + (mano - codo) * 0.06, A.r_mano, "mano")


@registrar
class PiernaHumana(Componente):
    tipo = "pierna_humana"
    anclas_validas = ("pierna_derecha", "pierna_izquierda")
    params_defecto = {"calzado": None}
    params_material = ("calzado",)
    material_defecto = "piel"

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"])
        s = masc(lado)
        A, a, m = ctx.anat, ctx.a, spec["material"]
        entrar(esc, ctx, spec, 0)
        esc.capsula(a[f"cadera_{lado}"], a[f"rodilla_{lado}"], A.r_muslo, m)
        esc.capsula(a[f"rodilla_{lado}"], a[f"tobillo_{s}"], A.r_canilla, m)
        entrar(esc, ctx, spec, 1)
        esc.capsula(
            a[f"tobillo_{s}"],
            a[f"pie_{s}"],
            A.r_pie,
            spec["parametros"]["calzado"] or m,
        )


@registrar
class PeloRizado(Componente):
    tipo = "pelo_rizado"
    anclas_validas = ("cabeza",)
    material_defecto = "pelo"
    params_defecto = {"filas": 2, "volumen": 1.0}

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        A, s = ctx.anat, ctx.escala()
        hc, (rf, rl, rz) = ctx.a["cabeza"], A.cabeza
        m, mb = spec["material"], f"{spec['material']}_b"
        filas = max(1, int(spec["parametros"]["filas"]))
        vol = float(spec["parametros"]["volumen"])
        for fila, z in enumerate(np.linspace(0.45, 0.8, filas)):
            n = max(2, 8 - fila)
            for i in range(n):
                ang = np.pi * (
                    0.5 + i / (n - 1)
                )  # costado → nuca → costado (la cara queda libre)
                q = hc + v(np.cos(ang) * rf * 0.82, np.sin(ang) * rl * 0.82, rz * z)
                esc.esfera(
                    q,
                    (0.62 + 0.16 * (i % 2)) * s * vol,
                    mb if (i + fila) % 2 else m,
                )
        entrar(esc, ctx, spec, 1)
        for i, l in enumerate(
            (-0.6, -0.2, 0.2, 0.6)
        ):  # corona: rizos sobre la línea del pelo, sin tapar la cara
            esc.esfera(
                hc + v(rf * 0.6, l * rl * 0.5, rz * 0.68),
                (0.56 + 0.08 * (abs(l) < 0.4)) * s * vol,
                mb if i % 2 else m,
            )
