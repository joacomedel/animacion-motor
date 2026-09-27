"""Biblioteca de componentes: cada pieza de un personaje (cabeza, brazo robótico, pulsera...) sabe dibujarse
en su ancla con primitivas del motor 3D. Las lecciones de CRITERIOS_ANIMACION.md viven acá, en el código:
así se aplican siempre, sin depender de que alguien se acuerde."""
from dataclasses import dataclass, field

import numpy as np

REGISTRO = {}


class Componente:
    tipo = ""
    anclas_validas = ()             # vacío = cualquiera del vocabulario
    estilos = ("stardew", "volumen", "lateral")
    params_defecto = {}
    params_material = ()            # parámetros cuyo valor tiene que ser un material de la paleta (o None)
    material_defecto = None         # material si la ficha no indica uno

    def dibujar(self, esc, ctx, spec):
        raise NotImplementedError


def registrar(cls):
    if not cls.tipo:
        raise ValueError(f"{cls.__name__}: falta 'tipo'")
    if cls.tipo in REGISTRO:
        raise ValueError(f"componente duplicado: {cls.tipo}")
    REGISTRO[cls.tipo] = cls()
    return cls


@dataclass
class Contexto:
    anat: object
    a: dict
    ps: dict
    estilo: str
    est: dict
    cam_local: np.ndarray
    paleta: dict
    mira: str
    ausentes: frozenset = field(default_factory=frozenset)
    pieza_base: int = 0
    cuadro: int = 0

    def ausente(self, nombre):
        return nombre in self.ausentes

    def escala(self):
        """1.0 en un adulto stardew: para dimensionar detalles de forma consistente entre estilos."""
        return self.anat.H / 28.0


def entrar(esc, ctx, spec, k=0):
    """Marca lo que se dibuje a continuación como parte de este componente y de su pieza k."""
    esc.componente = spec["id"]
    esc.pieza = ctx.pieza_base + k


def perpendicular(eje):
    """Un vector unitario perpendicular a eje (si el eje es vertical, usa el lateral)."""
    p = np.cross(eje, [0, 0, 1.0])
    if np.linalg.norm(p) < 1e-3:
        p = np.array([0.0, 1.0, 0.0])
    return p / np.linalg.norm(p)


from . import humano, mago, robot, ropa  # noqa: E402,F401  (registra todos los componentes)
