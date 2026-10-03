"""Escala del juego: el mismo personaje mide lo mismo en todos los estilos de su clase, y todas las
celdas de un estilo tienen el pivote (los pies) en el mismo lugar."""

CLASES = {"nino": 0.75, "adulto": 1.0, "grande": 1.25, "gigante": 1.6}

TAMANOS = {
    # adulto_px: alto en pantalla de un adulto (pies → coronilla, sin pelo parado)
    # pie_desde_abajo: filas de aire DEBAJO de la línea de piso. En 3/4 el pie más cercano cae 2-5 px más abajo que
    # el pivote (profundidad + suela + contorno): con menos, la planta del pie se recorta contra el borde de la celda
    # (medido: stardew8 necesita 5, lateral 3; el aire es celda - pie_desde_abajo, y ch = gy viejo + pie_desde_abajo)
    "stardew": dict(
        adulto_px=26,
        pie_desde_abajo=6,
        celdas={
            "nino": (16, 36),
            "adulto": (16, 36),
            "grande": (32, 52),
            "gigante": (32, 68),
        },
    ),
    "stardew8": dict(
        adulto_px=26,
        pie_desde_abajo=6,
        celdas={
            "nino": (16, 36),
            "adulto": (16, 36),
            "grande": (32, 52),
            "gigante": (32, 68),
        },
    ),
    "fry8": dict(
        adulto_px=54,
        pie_desde_abajo=4,
        celdas={
            "nino": (40, 48),
            "adulto": (48, 64),
            "grande": (56, 76),
            "gigante": (72, 96),
        },
    ),
    "volumen": dict(
        adulto_px=36,
        pie_desde_abajo=8,
        celdas={
            "nino": (56, 60),
            "adulto": (56, 60),
            "grande": (72, 76),
            "gigante": (88, 96),
        },
    ),
    "lateral": dict(
        adulto_px=33,
        pie_desde_abajo=4,
        celdas={
            "nino": (40, 42),
            "adulto": (40, 42),
            "grande": (48, 56),
            "gigante": (64, 68),
        },
    ),
    # solo para verificar plantillas de movimiento contra LPC (celda y alto de la referencia)
    "lpc": dict(
        adulto_px=43,
        pie_desde_abajo=5,  # contorno + pie redondo suman 3 px: queda de 46 como LPC
        celdas={
            "nino": (64, 64),
            "adulto": (64, 64),
            "grande": (64, 64),
            "gigante": (64, 64),
        },
    ),
}


class EscalaError(ValueError):
    pass


def _t(estilo):
    if estilo not in TAMANOS:
        raise EscalaError(
            f"estilo sin escala: {estilo!r}; disponibles: {', '.join(TAMANOS)}"
        )
    return TAMANOS[estilo]


def alto_objetivo_px(estilo, clase="adulto"):
    t = _t(estilo)
    if clase not in CLASES:
        raise EscalaError(
            f"clase de altura desconocida: {clase!r}; disponibles: {', '.join(CLASES)}"
        )
    return round(t["adulto_px"] * CLASES[clase])


def celda(estilo, clase="adulto", ancho=None):
    """ancho: ancho propio de una animación (ver poses.ancho); el alto y los pies no cambian."""
    t = _t(estilo)
    alto_objetivo_px(estilo, clase)  # valida la clase
    cw, ch = t["celdas"][clase]
    if ancho:
        cw = ancho
    return dict(cw=cw, ch=ch, gx=cw // 2, gy=ch - t["pie_desde_abajo"])
