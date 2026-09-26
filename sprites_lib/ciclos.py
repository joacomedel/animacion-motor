"""Ciclos de movimiento reutilizables, en coordenadas del "rig lateral".

Rig lateral: x crece hacia adelante, y hacia abajo, piso en y=34, cadera en x=18.
Cada ciclo define por cuadro: rebote de la cabeza, tobillo de la pierna A, ángulo del pie
y la trayectoria de la mano del brazo A. La pierna/brazo B es la misma curva desfasada.
Para agregar un ciclo nuevo: medirlo con `python -m sprites_lib.analizar` sobre una referencia,
cargar acá los números y anotar el origen en CRITERIOS_ANIMACION.md.
"""
import math

CORRER = dict(
    nombre="correr", n=10, fps=12, desfase=5,
    fuente="Mega Man X (SNES) 04_correr — ver CRITERIOS_ANIMACION.md",
    bob=[1, 0, 1, 2, 2, 1, 0, 1, 2, 2],
    pie=[(17, 32), (13, 32), (6, 32), (4, 22), (5, 25), (11, 28), (18, 27), (24, 26), (26, 31), (22, 32)],
    pie_ang=[0, 0, 25, 70, 55, 35, 20, 10, 0, 0],
    mano=dict(cx=20, ax=7, y0=21, ay=7),          # adelante/atrás ±7 px, sube 7 px en los extremos
    lag_faldon=1,                                  # cuadros de retraso del movimiento secundario
)

QUIETO = dict(
    nombre="quieto", n=4, fps=4, desfase=0,
    fuente="respiración genérica: 1 px de rebote cada 2 cuadros",
    bob=[0, 0, 1, 1],
    pie=[(17.5, 32.5)] * 4,
    pie_ang=[0] * 4,
    mano=dict(cx=19.5, ax=0, y0=26.5, ay=0),
    lag_faldon=1,
)

CAMINAR = dict(
    nombre="caminar", n=4, fps=7, desfase=2,
    fuente="Stardew Valley (Abigail/Wizard, 16x32): 4 cuadros, pasos en 1 y 3, rebote de 1 px en los pasos",
    bob=[0, 1, 0, 1],
    pie=[(18, 32.5), (24, 32.5), (18, 32.5), (12, 31.5)],   # neutro, pierna A adelante, neutro, A atrás
    pie_ang=[0, 0, 0, 20],
    mano=dict(cx=19.5, ax=-3, y0=26.5, ay=0, fase=0),       # balanceo chico, opuesto a la pierna
    lag_faldon=1,
)

CICLOS = {c["nombre"]: c for c in (CORRER, QUIETO, CAMINAR)}


def mano(ciclo, p):
    """Posición de la mano del brazo A en el cuadro p (coordenadas del rig lateral)."""
    m = ciclo["mano"]
    s = math.sin(2 * math.pi * (p - m.get("fase", .5)) / ciclo["n"]) if m["ax"] or m["ay"] else 0.0
    return m["cx"] + m["ax"] * s, m["y0"] - m["ay"] * abs(s)


def pose(ciclo, p):
    """Todo lo que cambia por cuadro, para las extremidades A (cercana) y B (lejana)."""
    n, k = ciclo["n"], ciclo["desfase"]
    return dict(
        bob=ciclo["bob"][p % n],
        bob_prev=ciclo["bob"][(p - ciclo["lag_faldon"]) % n],
        pie_a=ciclo["pie"][p % n], ang_a=ciclo["pie_ang"][p % n],
        pie_b=ciclo["pie"][(p + k) % n], ang_b=ciclo["pie_ang"][(p + k) % n],
        mano_a=mano(ciclo, p), mano_b=mano(ciclo, p + k),
        fase=p / n,
    )
