"""Motor visual 3D→2D en tiempo real.

Recibe estado de un servidor (o modo demo) y renderiza un personaje
en 8 direcciones con estilo pixel art (stardew8).

Arquitectura desacoplada:
    - Lógica (servidor): física, colisiones, input → manda estado
    - Visual (motor): recibe estado → renderiza 3D → imagen 2D
"""
