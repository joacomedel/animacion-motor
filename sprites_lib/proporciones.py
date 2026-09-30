"""Contrato numérico del muñeco por estilo: mide el render real y lo compara con el perfil.

`medir` renderiza la ficha mínima en pose neutra en cada dirección del estilo y mide sobre los píxeles del
cuerpo (`buf["solido"]`: el muñeco dibujado; el contorno exterior de 1 px no cuenta) el alto total desde el
pivote (ancla `suelo`), la cabeza, las dos piernas juntas y los anchos. `comparar` contrasta el resumen de la
primera dirección con lo que promete el perfil (`estilos.ESTILOS[estilo]["proporciones"]` + `escala`) y devuelve
un `tests_personaje.Resultado` con cada desvío.

Tolerancias calibradas el 2026-09-29 sobre los 6 estilos existentes (medidas en CRITERIOS_ANIMACION.md): las
vistas 3/4 (cenital e iso) proyectan la profundidad sobre la pantalla, así que la silueta de cabeza y piernas
mide más que su tamaño vertical; por eso `TOL_REL` es más ancho que el .10 inicial del boceto.
"""
import numpy as np

from . import armado, tests_personaje
from .cuerpo import anatomia
from .escala import alto_objetivo_px
from .estilos import ESTILOS, uz

TOL_PX = 2           # px: alto, ancho de cabeza y variación de alto entre direcciones
TOL_REL = .35        # desvío relativo: cabezas y fracción de piernas contra el perfil


def _bbox(mascara):
    ys, xs = np.nonzero(mascara)
    if not len(ys):
        return None
    return int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max())


def _mascara_piernas(cuadro):
    return (tests_personaje.mascara(cuadro, "pierna_humana@pierna_derecha")
            | tests_personaje.mascara(cuadro, "pierna_humana@pierna_izquierda"))


def _medir_direccion(ficha, estilo, mira):
    c = armado.render_cuadro(ficha, estilo, "neutra", 0, mira)
    cuerpo = _bbox(c.buf["solido"])
    cabeza = _bbox(tests_personaje.mascara(c, "cabeza_humana@cabeza"))
    piernas = _bbox(_mascara_piernas(c))
    if cuerpo is None or cabeza is None or piernas is None:
        raise ValueError(f"el render de {estilo}/{mira} no tiene cuerpo, cabeza o piernas")
    alto = float(c.anclas_px["suelo"][1] - cuerpo[0])
    cabeza_px = float(cabeza[2] - cabeza[0] + 1)
    return dict(
        alto_px=alto,
        cabeza_px=cabeza_px,
        piernas_px=float(piernas[2] - piernas[0] + 1),
        cabezas=alto / cabeza_px,
        piernas_frac=(piernas[2] - piernas[0] + 1) / alto,
        ancho_px=float(cuerpo[3] - cuerpo[1] + 1),
        ancho_cabeza_px=float(cabeza[3] - cabeza[1] + 1),
    )


def medir(estilo, clase="adulto"):
    """Medidas del render real (píxeles) en todas las direcciones: resumen de la primera + `por_direccion`."""
    ficha = {**armado.FICHA_MINIMA,
             "cuerpo": {**armado.FICHA_MINIMA["cuerpo"], "clase_altura": clase}}
    por_direccion = {d: _medir_direccion(ficha, estilo, d) for d in ESTILOS[estilo]["direcciones"]}
    resumen = dict(next(iter(por_direccion.values())))
    resumen["por_direccion"] = por_direccion
    return resumen


def comparar(estilo, clase="adulto"):
    """Compara el resumen contra el perfil del estilo; `Resultado` con el detalle de cada desvío."""
    m = medir(estilo, clase)
    pr = ESTILOS[estilo]["proporciones"]
    a = anatomia(estilo, clase)
    esperado = dict(alto=alto_objetivo_px(estilo, clase), cabezas=1 / pr["cabeza_frac"],
                    piernas_frac=pr["piernas_frac"],
                    # el perfil no guarda el ancho de cabeza: la cabeza chibi es casi tan ancha como alta, así que
                    # el contrato usa su tamaño nominal (2·r_z) en px; +2 = un píxel de oreja/contorno por lado
                    ancho_cabeza=2 * a.cabeza[2] * uz(estilo) + 2)
    fallas = []

    def pixel(nombre, medido, meta):
        if abs(medido - meta) > TOL_PX:
            fallas.append(f"{nombre}: {medido:.0f} px contra {meta:.1f} esperado (Δ{abs(medido - meta):.1f})")

    def relativo(nombre, medido, meta):
        d = abs(medido - meta) / meta
        if d > TOL_REL:
            fallas.append(f"{nombre}: {medido:.2f} contra {meta:.2f} esperado ({d:.0%} de desvío)")

    pixel("alto_px", m["alto_px"], esperado["alto"])
    relativo("cabezas", m["cabezas"], esperado["cabezas"])
    relativo("piernas_frac", m["piernas_frac"], esperado["piernas_frac"])
    pixel("ancho_cabeza_px", m["ancho_cabeza_px"], esperado["ancho_cabeza"])
    altos = [v["alto_px"] for v in m["por_direccion"].values()]
    if max(altos) - min(altos) > TOL_PX:
        fallas.append(f"alto_px entre direcciones: {max(altos) - min(altos):.1f} px de variación")
    detalle = ("; ".join(fallas) if fallas else
               f"alto {m['alto_px']:.0f} px, {m['cabezas']:.2f} cabezas, piernas {m['piernas_frac']:.0%}, "
               f"ancho de cabeza {m['ancho_cabeza_px']:.0f} px")
    return tests_personaje.Resultado("proporciones", not fallas, detalle, evidencia=fallas)
