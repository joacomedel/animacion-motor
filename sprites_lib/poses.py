"""Poses clave como datos (mismo formato que los ciclos: rig lateral, piso y=34, cadera x=18).
Fase 1: 'neutra' (pose A de construcción) y 'quieto' (respiración). Las animaciones de la fase 2 serán
secuencias de poses clave aprobadas."""

from .ciclos import (
    AGACHAR,
    BLANDIR,
    CAMINAR_LPC,
    COMBO,
    DESENVAINAR,
    GOLPEAR,
    QUIETO,
    SALTAR,
)
from .ciclos import pose as _pose

NEUTRA = dict(
    nombre="neutra",
    n=1,
    fps=1,
    desfase=0,
    loop=True,
    fuente="pose A de construcción: brazos separados, piernas juntas",
    bob=[0],
    pie=[(18, 32.5)],
    pie_ang=[0],
    mano=dict(cx=20, ax=0, y0=27.5, ay=0),
    lag_faldon=1,
    abrir_brazos=1.4,  # 2.2 se sale de una celda de 16 px
)
POSES = {
    "neutra": NEUTRA,
    "quieto": QUIETO,
    "caminar_lpc": CAMINAR_LPC,
    "saltar": SALTAR,
    "agachar": AGACHAR,
    "golpear": GOLPEAR,
    "blandir": BLANDIR,
    "combo": COMBO,
    "desenvainar": DESENVAINAR,
}


def cuadros(nombre):
    if nombre not in POSES:
        raise KeyError(f"pose desconocida {nombre!r}; disponibles: {', '.join(POSES)}")
    c = POSES[nombre]
    out = []
    for p in range(c["n"]):
        ps = _pose(c, p)
        ps["abrir_brazos"] = c.get("abrir_brazos", 0.6)
        ps["cuadro"] = p
        out.append(ps)
    return out


def fps(nombre):
    return POSES[nombre]["fps"]


def loop(nombre):
    """Si la animación se repite (caminar, quieto) o se juega una sola vez (saltar). Depende de la animación,
    no del estilo ni del personaje: default True si el ciclo no lo dice."""
    return POSES[nombre].get("loop", True)


def offset_y(nombre):
    """Cuánto tiene que levantar el motor el sprite por cuadro (px de juego, negativo = arriba) o None si el
    ciclo no se traslada del piso (el sprite ya incluye todo el movimiento vertical, como caminar)."""
    return POSES[nombre].get("offset_y")


def ancho(nombre, estilo):
    """Ancho de celda propio de la animación en ese estilo (px) o None si usa el del estilo. Cada animación ocupa lo
    que necesita: caminar entra en poco, golpear (brazo extendido) necesita más. Se mide con muneco.ancho_necesario."""
    return POSES[nombre].get("ancho", {}).get(estilo)
