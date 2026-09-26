"""Perfiles de estilo: cómo se "ve" un sprite, independiente de qué personaje es y de cómo se mueve.

Cada perfil sale de analizar un juego de referencia (skill `sprite-estilo`) y define:
  vista        'iso' (8 direcciones, Camara) o 'cenital' (4 direcciones, CamaraCenital)
  celda        tamaño de celda y pivote (punto del piso) — define la resolución
  render       parámetros de Escena.render(estilo=...): umbrales de los 3 tonos, contorno, interior
  proporciones guía para la ANATOMIA del personaje (cabeza/alto, piernas/alto)
  paleta       reglas para armar la PALETA
  ciclos       ciclos recomendados
Los números medidos y el razonamiento quedan en CRITERIOS_ANIMACION.md.
"""

ESTILOS = {
    "volumen": dict(
        descripcion="Pre-renderizado tipo Diablo II/Isometric Hero: volumen marcado, contorno negro por pieza.",
        vista="iso", celda=dict(cw=56, ch=60, gx=26, gy=52),
        render=dict(umbrales=(.28, .66), contorno="negro", interior="negro"),
        proporciones=dict(cabezas=3.3, cabeza_frac=.30, piernas_frac=.42),
        paleta="3 tonos por material bien separados; contorno casi negro azulado",
        ciclos=["correr", "quieto"],
    ),
    "stardew": dict(
        descripcion="Stardew Valley: cenital 3/4, chibi, sombreado plano, contorno de color (selout).",
        vista="cenital", celda=dict(cw=16, ch=32, gx=8, gy=30),
        # plano: casi todo en tono base; luz solo arriba-izquierda y sombra solo en lo muy oscuro
        render=dict(umbrales=(.12, .82), contorno="color", interior="color", oscurecer=.45, sombreado="borde"),
        proporciones=dict(cabezas=2.2, cabeza_frac=.44, piernas_frac=.25),
        paleta="saturada y cálida; 3-4 tonos por material con corrimiento de tono (sombras hacia violeta, "
               "luces hacia amarillo); contorno = tono más oscuro del mismo material, nunca negro puro "
               "(salvo materiales negros); 20-30 colores por cuadro",
        ciclos=["caminar", "quieto"],
    ),
}
