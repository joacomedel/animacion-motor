"""Escala del juego: el mismo personaje mide lo mismo en todos los estilos de su clase, y todas las
celdas de un estilo tienen el pivote (los pies) en el mismo lugar."""

CLASES = {"nino": .75, "adulto": 1.0, "grande": 1.25, "gigante": 1.6}

TAMANOS = {
    # adulto_px: alto en pantalla de un adulto (pies → coronilla, sin pelo parado)
    "stardew": dict(adulto_px=26, pie_desde_abajo=2,
                    celdas={"nino": (16, 32), "adulto": (16, 32), "grande": (32, 48), "gigante": (32, 64)}),
    "volumen": dict(adulto_px=36, pie_desde_abajo=8,
                    celdas={"nino": (56, 60), "adulto": (56, 60), "grande": (72, 76), "gigante": (88, 96)}),
    "lateral": dict(adulto_px=33, pie_desde_abajo=2,
                    celdas={"nino": (40, 40), "adulto": (40, 40), "grande": (48, 52), "gigante": (64, 64)}),
    # solo para verificar plantillas de movimiento contra LPC (celda y alto de la referencia)
    "lpc": dict(adulto_px=43, pie_desde_abajo=5,     # contorno + pie redondo suman 3 px: queda de 46 como LPC
                celdas={"nino": (64, 64), "adulto": (64, 64), "grande": (64, 64), "gigante": (64, 64)}),
}


class EscalaError(ValueError):
    pass


def _t(estilo):
    if estilo not in TAMANOS:
        raise EscalaError(f"estilo sin escala: {estilo!r}; disponibles: {', '.join(TAMANOS)}")
    return TAMANOS[estilo]


def alto_objetivo_px(estilo, clase="adulto"):
    t = _t(estilo)
    if clase not in CLASES:
        raise EscalaError(f"clase de altura desconocida: {clase!r}; disponibles: {', '.join(CLASES)}")
    return round(t["adulto_px"] * CLASES[clase])


def celda(estilo, clase="adulto"):
    t = _t(estilo)
    alto_objetivo_px(estilo, clase)                 # valida la clase
    cw, ch = t["celdas"][clase]
    return dict(cw=cw, ch=ch, gx=cw // 2, gy=ch - t["pie_desde_abajo"])
