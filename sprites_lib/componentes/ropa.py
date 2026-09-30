"""Ropa genérica: remera larga rota y cinturón. La prenda grande con jirones se lee mejor a baja resolución
que varias prendas chicas; las costuras son detalle dibujado (evita el look liso de render)."""
import numpy as np

from ..render3d import v
from . import Componente, entrar, registrar


@registrar
class RemeraLargaRota(Componente):
    tipo = "remera_larga_rota"
    anclas_validas = ("torso",)
    material_defecto = "ropa"
    params_defecto = {"largo": "medio_muslo", "jirones": 3, "sin_mangas": True}

    def dibujar(self, esc, ctx, spec):
        A, a, m, p, s = ctx.anat, ctx.a, spec["material"], spec["parametros"], ctx.escala()
        costuras = lambda d: np.where((np.floor((d[..., 2] + 1) * 6) % 3) == 1, f"{m}_b", m).astype(object)
        entrar(esc, ctx, spec, 0)
        esc.elipsoide(a["torso"], tuple(r * 1.1 for r in A.pecho), costuras)
        esc.elipsoide(a["cintura"] + v(0, 0, -A.pelvis[2] * .8), tuple(r * 1.1 for r in A.pelvis), m)
        sube = a["cintura"][2] - (A.pelvis_u + A.pelvis[2] * .8)
        hasta = {"cadera": A.cadera_u * .9, "medio_muslo": A.cadera_u * .62, "rodilla": A.cadera_u * .45}[p["largo"]]
        j = max(1, int(p["jirones"]))
        jirones = lambda d, t: ~((t > .72) & ((np.floor(np.arctan2(d[..., 1], d[..., 0]) * j / np.pi) % 2) == 0))
        esc.faldon(a["cintura"], v(-.3 * s, 0, hasta + sube), A.pelvis[1] * 1.08, A.pelvis[1] * 1.3, m,
                   conservar=lambda d: np.ones(d.shape[:-1], bool), recorte=jirones)
        # desgaste: agujeros y manchas en posiciones fijas (deterministas: no titilan entre cuadros)
        oscuro = ctx.paleta[m][0]
        rng = np.random.default_rng(7)
        for _ in range(int(p["jirones"]) * 6):
            ang, alto = rng.uniform(-1.2, 1.2), rng.uniform(-.6, .9)
            q = a["torso"] + v(np.cos(ang) * A.pecho[0] * 1.1, np.sin(ang) * A.pecho[1] * 1.1, alto * A.pecho[2])
            esc.detalle(q, oscuro)
        if not p["sin_mangas"]:
            for k, s_ in enumerate(("derecho", "izquierdo")):
                entrar(esc, ctx, spec, 1 + k)
                hom, codo = a[f"hombro_{s_}"], a[f"codo_{s_}"]
                esc.capsula(hom, hom + (codo - hom) * .5, A.r_brazo + .25 * s, m)


@registrar
class Cinturon(Componente):
    tipo = "cinturon"
    anclas_validas = ("cintura",)
    material_defecto = "cuero"
    params_defecto = {"hebilla": None}
    params_material = ("hebilla",)

    def dibujar(self, esc, ctx, spec):
        A, a = ctx.anat, ctx.a
        entrar(esc, ctx, spec)
        esc.elipsoide(a["cintura"], (A.pelvis[0] * 1.22, A.pelvis[1] * 1.22, A.pelvis[2] * 1.2), spec["material"],
                      conservar=lambda d: np.abs(d[..., 2]) < .3)
        if spec["parametros"]["hebilla"]:
            esc.detalle(a["cintura"] + v(A.pelvis[0] * 1.25, 0, 0), ctx.paleta[spec["parametros"]["hebilla"]][2])
