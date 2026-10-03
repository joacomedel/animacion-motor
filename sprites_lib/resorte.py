"""Movimiento secundario: resorte determinista y blending de animaciones.

El resorte es un sistema de segundo orden (posición + velocidad) que converge
al objetivo sin oscilar infinitamente. Es DETERMINISTA: mismo estado inicial y
mismos parámetros → mismo resultado.

El blending interpola colores RGB sin introducir valores fuera de rango.

Flag de activación: `mov_secundario` en Contexto (default False).
Con el flag apagado, el render es idéntico al comportamiento actual.
"""

import numpy as np


class Resorte:
    """Resorte de segundo orden determinista.

    Parámetros:
        amortiguacion: 0-1, más alto = converge más lento (menos overshoot)
        frecuencia: velocidad de oscilación (rad/s aprox)
    """

    def __init__(self, amortiguacion=0.3, frecuencia=0.5):
        self.amortiguacion = np.clip(amortiguacion, 0.0, 1.0)
        self.frecuencia = max(frecuencia, 0.01)
        self.valor = 0.0
        self.velocidad = 0.0

    def paso(self, objetivo):
        """Avanza un paso del resorte hacia el objetivo."""
        fuerza = (objetivo - self.valor) * self.frecuencia
        self.velocidad = (self.velocidad + fuerza) * (1.0 - self.amortiguacion)
        self.valor = self.valor + self.velocidad
        return self.valor

    def reset(self):
        """Reinicia el estado del resorte."""
        self.valor = 0.0
        self.velocidad = 0.0


def blending(color_a, color_b, t):
    """Interpola linealmente entre dos colores RGB.

    Args:
        color_a: tuple/list de 3 componentes (0-255)
        color_b: tuple/list de 3 componentes (0-255)
        t: factor de interpolación (0-1), 0 = color_a, 1 = color_b

    Returns:
        tuple de 3 componentes (0-255)
    """
    t = np.clip(t, 0.0, 1.0)
    a = np.array(color_a, dtype=float)
    b = np.array(color_b, dtype=float)
    resultado = a + (b - a) * t
    return tuple(int(round(c)) for c in resultado)


def params_estilo(estilo):
    """Parámetros de resorte por estilo.

    Retorna dict con 'amortiguacion' y 'frecuencia' para el estilo dado.
    """
    # Parámetros por estilo: stardew es más "snappy", volumen más suave
    params = {
        "stardew": {"amortiguacion": 0.35, "frecuencia": 0.6},
        "stardew8": {"amortiguacion": 0.35, "frecuencia": 0.6},
        "volumen": {"amortiguacion": 0.25, "frecuencia": 0.4},
        "lateral": {"amortiguacion": 0.3, "frecuencia": 0.5},
    }
    return params.get(estilo, {"amortiguacion": 0.3, "frecuencia": 0.5})
