"""Objetos sostenidos: la espada, el hacha, la antorcha, el escudo y el bastón se enganchan a una mano y se
orientan con el antebrazo (eje codo→mano). Como la mano es un ancla que ya mueven todos los ciclos, un objeto
"sigue" la animación sin tocar el motor: blandir es reusar `golpear` sobre el brazo que lo sostiene.

Materiales planos de la paleta (la skin del objeto vendrá después: ver docs/OBJETOS.md). Cada forma dibuja en
coordenadas del ancla `mano_*` y usa `ctx.escala()` para medir en px de forma consistente entre estilos.
"""

import math

import numpy as np

from ..cuerpo import lado_de, masc
from . import Componente, entrar, registrar


def _eje(mano, codo):
    """Dirección unitaria del antebrazo (codo→mano): hacia dónde apunta lo que se sostiene."""
    d = np.asarray(mano, float) - np.asarray(codo, float)
    n = np.linalg.norm(d)
    return d / n if n > 1e-9 else np.array([1.0, 0.0, 0.0])


def _girar(d, grados):
    """Gira la dirección en el plano (adelante, arriba) del personaje alrededor de su eje lateral."""
    if not grados:
        return d
    a = math.radians(float(grados))
    c, s = math.cos(a), math.sin(a)
    R = np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])
    return R @ np.asarray(d, float)


def _lateral_a(d, cam_local):
    """Vector unitario perpendicular a `d` y a la cámara: sirve para cruzar la guarda o el filo en pantalla."""
    lat = np.cross(d, cam_local)
    if np.linalg.norm(lat) < 1e-6:
        lat = np.array([0.0, 1.0, 0.0])
    return lat / np.linalg.norm(lat)


def _espada(esc, ctx, mano, d, e, m, p):
    mango, pomo, guarda = p["mango"] or m, p["pomo"] or m, p["guarda"] or m
    fin = mano - d * 0.9 * e
    esc.capsula(fin, mano, 0.42 * e, mango)
    esc.esfera(fin - d * 0.25 * e, 0.62 * e, pomo)
    g = mano + d * 0.35 * e
    lat = _lateral_a(d, ctx.cam_local) * 1.2 * e
    esc.capsula(g - lat, g + lat, 0.3 * e, guarda)  # guarda
    base = mano + d * 0.5 * e
    punta = base + d * (float(p["largo"]) * e)
    esc.capsula(base, punta, 0.4 * e, m)  # hoja
    esc.esfera(punta, 0.4 * e, m)
    if p["detalle"]:
        esc.detalle(punta + ctx.cam_local * 0.4 * e, ctx.paleta[p["detalle"]][1])


def _hacha(esc, ctx, mano, d, e, m, p):
    mango = p["mango"] or m
    largo = float(p["largo"]) * e
    esc.capsula(mano - d * 1.1 * e, mano, 0.38 * e, mango)  # empuñadura
    fin = mano + d * largo
    esc.capsula(mano, fin, 0.32 * e, mango)  # asta
    cabeza = fin + d * 0.2 * e
    lat = _lateral_a(d, ctx.cam_local)
    esc.caja(cabeza, (1.4 * e, 0.5 * e, 1.5 * e), m, n=3.0)  # cabeza
    esc.capsula(cabeza, cabeza + lat * 1.3 * e, 0.4 * e, m)  # filo hacia un lado
    if p["detalle"]:
        esc.detalle(
            cabeza + lat * 1.3 * e + ctx.cam_local * 0.4 * e,
            ctx.paleta[p["detalle"]][1],
        )


def _antorcha(esc, ctx, mano, d, e, m, p):
    largo = float(p["largo"]) * e
    mango = p["mango"] or m
    esc.capsula(mano - d * 0.7 * e, mano + d * largo, 0.3 * e, mango)
    llama = mano + d * (largo + 0.3 * e)
    esc.esfera(llama, 0.95 * e, m)  # llama (material emisivo)
    esc.esfera(llama + d * 0.7 * e, 0.55 * e, m)
    if p["detalle"]:
        esc.detalle(llama + ctx.cam_local * 0.5 * e, ctx.paleta[p["detalle"]][2])


def _escudo(esc, ctx, mano, d, e, m, p):
    centro = mano + d * 0.35 * e
    esc.caja(centro, (0.55 * e, 2.0 * e, 2.6 * e), m, n=3.2, giro=0.0)  # tabla
    esc.caja(
        centro + ctx.cam_local * 0.35 * e,
        (0.5 * e, 1.6 * e, 2.1 * e),
        p["guarda"] or m,
        n=3.2,
    )
    if p["detalle"]:
        esc.esfera(centro + ctx.cam_local * 0.7 * e, 0.7 * e, p["detalle"])  # umbo


def _baston(esc, ctx, mano, d, e, m, p):
    largo = float(p["largo"]) * e
    mango = p["mango"] or m
    esc.capsula(mano - d * 1.2 * e, mano + d * largo, 0.28 * e, mango)
    gema = mano + d * largo + d * 0.6 * e
    esc.esfera(gema, 0.85 * e, m)
    if p["detalle"]:
        esc.detalle(gema + ctx.cam_local * 0.5 * e, ctx.paleta[p["detalle"]][2])


FORMAS = {
    "espada": _espada,
    "hacha": _hacha,
    "antorcha": _antorcha,
    "escudo": _escudo,
    "baston": _baston,
}


@registrar
class Objeto(Componente):
    tipo = "objeto"
    anclas_validas = ("mano_derecha", "mano_izquierda")
    material_defecto = "metal"
    params_defecto = {
        "forma": "espada",
        "largo": 8.0,
        "angulo": 0.0,
        "agarre": "antebrazo",  # 'antebrazo': alineado con el brazo · 'vertical': apunta hacia arriba
        "mango": None,
        "pomo": None,
        "guarda": None,
        "detalle": None,
    }
    params_material = ("mango", "pomo", "guarda", "detalle")
    params_opciones = {"forma": tuple(FORMAS), "agarre": ("antebrazo", "vertical")}

    def dibujar(self, esc, ctx, spec):
        if not ctx.ps.get("objeto_visible", True):
            return  # cuadro en que el objeto todavía no está (desenvainar: aparece de golpe)
        ancla = spec["ancla"]
        lado = lado_de(ancla)
        a, p = ctx.a, spec["parametros"]
        mano = a[ancla]
        codo = a[f"codo_{masc(lado)}"]
        d = np.array([0.0, 0.0, 1.0]) if p["agarre"] == "vertical" else _eje(mano, codo)
        d = _girar(d, p["angulo"])
        entrar(esc, ctx, spec)
        FORMAS[p["forma"]](esc, ctx, mano, d, ctx.escala(), spec["material"], p)
