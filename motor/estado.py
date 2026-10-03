"""Estado del personaje que recibe el motor visual.

Este es el contrato entre el servidor de lógica y el motor visual.
El servidor manda un Estado, el motor lo renderiza.
"""

from dataclasses import dataclass


@dataclass
class Estado:
    """Estado del personaje en un momento dado.

    Atributos:
        x: posición X en el mundo (unidades de tiles)
        y: posición Y en el mundo (unidades de tiles)
        z: altura sobre el piso (para salto)
        animacion: nombre de la animación ("idle", "run", "jump", "crouch")
        direccion: dirección del personaje ("S", "SE", "E", "NE", "N", "NW", "W", "SW")
        frame: frame actual de la animación (0-N)
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    animacion: str = "idle"
    direccion: str = "S"
    frame: int = 0

    def lerp(self, otro: "Estado", t: float) -> "Estado":
        """Interpola entre este estado y otro.

        Args:
            otro: estado destino
            t: factor de interpolación (0.0 = este estado, 1.0 = otro)

        Returns:
            Estado interpolado
        """
        return Estado(
            x=self.x + (otro.x - self.x) * t,
            y=self.y + (otro.y - self.y) * t,
            z=self.z + (otro.z - self.z) * t,
            animacion=otro.animacion if t > 0.5 else self.animacion,
            direccion=otro.direccion if t > 0.5 else self.direccion,
            frame=otro.frame if t > 0.5 else self.frame,
        )
