"""Poses clave como datos (mismo formato que los ciclos: rig lateral, piso y=34, cadera x=18).
Fase 1: 'neutra' (pose A de construcción) y 'quieto' (respiración). Las animaciones de la fase 2 serán
secuencias de poses clave aprobadas."""
from .ciclos import QUIETO
from .ciclos import pose as _pose

NEUTRA = dict(
    nombre="neutra", n=1, fps=1, desfase=0, fuente="pose A de construcción: brazos separados, piernas juntas",
    bob=[0], pie=[(18, 32.5)], pie_ang=[0], mano=dict(cx=20, ax=0, y0=27.5, ay=0), lag_faldon=1,
    abrir_brazos=1.4,                         # 2.2 se sale de una celda de 16 px
)
POSES = {"neutra": NEUTRA, "quieto": QUIETO}


def cuadros(nombre):
    if nombre not in POSES:
        raise KeyError(f"pose desconocida {nombre!r}; disponibles: {', '.join(POSES)}")
    c = POSES[nombre]
    out = []
    for p in range(c["n"]):
        ps = _pose(c, p)
        ps["abrir_brazos"] = c.get("abrir_brazos", .6)
        ps["cuadro"] = p
        out.append(ps)
    return out


def fps(nombre):
    return POSES[nombre]["fps"]
