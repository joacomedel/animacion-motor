"""Esqueleto base humano: proporciones por estilo y clase, vocabulario fijo de anclas y pose → posiciones 3D.

Convención de lados: derecha = l < 0 (lado cercano a la cámara en la vista principal), izquierda = l > 0.
Las extremidades "A" de los ciclos son las derechas. Unidades: 1 unidad de mundo ≈ 1 px horizontal.
"""
import math
from dataclasses import dataclass

import numpy as np

from .escala import alto_objetivo_px
from .estilos import ESTILOS, uz
from .render3d import ik_3d, v

LADOS = {"derecha": -1, "izquierda": 1}
ANCLAS = (
    "suelo", "cadera_derecha", "cadera_izquierda", "rodilla_derecha", "rodilla_izquierda",
    "tobillo_derecho", "tobillo_izquierdo", "pie_derecho", "pie_izquierdo",
    "cintura", "torso", "pecho", "cuello",
    "hombro_derecho", "hombro_izquierdo", "codo_derecho", "codo_izquierdo",
    "muneca_derecha", "muneca_izquierda", "mano_derecha", "mano_izquierda",
    "cabeza", "coronilla", "cara", "frente", "ojo_derecho", "ojo_izquierdo", "sien_derecha", "sien_izquierda", "nuca",
)
SEGMENTOS = {
    "brazo_derecho": ("hombro_derecho", "codo_derecho", "muneca_derecha", "mano_derecha"),
    "brazo_izquierdo": ("hombro_izquierdo", "codo_izquierdo", "muneca_izquierda", "mano_izquierda"),
    "antebrazo_derecho": ("codo_derecho", "muneca_derecha", "mano_derecha"),
    "antebrazo_izquierdo": ("codo_izquierdo", "muneca_izquierda", "mano_izquierda"),
    "pierna_derecha": ("cadera_derecha", "rodilla_derecha", "tobillo_derecho", "pie_derecho"),
    "pierna_izquierda": ("cadera_izquierda", "rodilla_izquierda", "tobillo_izquierdo", "pie_izquierdo"),
}
VOCABULARIO = set(ANCLAS) | set(SEGMENTOS)
PADRE = {
    "codo_derecho": "hombro_derecho", "codo_izquierdo": "hombro_izquierdo",
    "muneca_derecha": "codo_derecho", "muneca_izquierda": "codo_izquierdo",
    "rodilla_derecha": "cadera_derecha", "rodilla_izquierda": "cadera_izquierda",
    "tobillo_derecho": "rodilla_derecha", "tobillo_izquierdo": "rodilla_izquierda",
}
COMPLEXIONES = {"normal": (1.0, 1.0), "robusto": (1.15, 1.25), "delgado": (.9, .85)}   # (ancho, grosor)


def lado_de(ancla):
    return "derecha" if ancla.endswith(("derecho", "derecha")) else "izquierda"


def masc(lado):
    return "derecho" if lado == "derecha" else "izquierdo"


@dataclass
class Anatomia:
    estilo: str
    clase: str
    H: float
    alto_px: int
    cabeza_u: float
    cabeza: tuple
    cuello_u: float
    hombro_u: float
    hombro_l: float
    pecho_u: float
    pecho: tuple
    pelvis_u: float
    pelvis: tuple
    cadera_u: float
    cadera_l: float
    muslo: float
    canilla: float
    pie: float
    brazo: float
    antebrazo: float
    r_muslo: float
    r_canilla: float
    r_brazo: float
    r_antebrazo: float
    r_mano: float
    r_pie: float
    escala_rig: float
    bajar_punos: float
    paso: float = 1.0          # cuánto del largo de paso del ciclo entra en la celda del estilo


def anatomia(estilo, clase="adulto", complexion="normal"):
    if complexion not in COMPLEXIONES:
        raise ValueError(f"complexión desconocida {complexion!r}; disponibles: {', '.join(COMPLEXIONES)}")
    pr = ESTILOS[estilo]["proporciones"]
    ancho, grosor = COMPLEXIONES[complexion]
    alto_px = alto_objetivo_px(estilo, clase)
    H = alto_px / uz(estilo)
    cab = H * pr["cabeza_frac"]
    ca = pr.get("cabeza_ancho", 1.0)          # fry8: cabeza más angosta que la del chibi (Fry: 14 px en 63)
    cabeza = (cab * .49 * ca, cab * .53 * ancho * ca, cab * .5)
    ancho = ancho * pr.get("cuerpo_ancho", 1.0)   # fry8: hombros y torso más anchos (la caja de la cabeza ya no usa este)
    cuello_u = H - cab * .98
    hombro_u = cuello_u - H * .02
    cadera_u = H * pr["piernas_frac"]
    r_pie = H * .042 * grosor
    muslo = canilla = (cadera_u - r_pie) / 2 * 1.03
    tronco = hombro_u - cadera_u
    brazos = tronco * pr["brazos_frac"]
    return Anatomia(
        estilo=estilo, clase=clase, H=H, alto_px=alto_px,
        cabeza_u=H - cabeza[2], cabeza=cabeza, cuello_u=cuello_u,
        hombro_u=hombro_u, hombro_l=H * pr["hombros_frac"] * ancho,
        pecho_u=cadera_u + tronco * .62, pecho=(H * .085 * grosor, H * .115 * ancho, tronco * .34),
        pelvis_u=cadera_u + H * .03, pelvis=(H * .07 * grosor, H * .1 * ancho, H * .06),
        cadera_u=cadera_u, cadera_l=H * .058 * ancho, muslo=muslo, canilla=canilla, pie=H * .08,
        brazo=brazos * .51, antebrazo=brazos * .49,
        r_muslo=H * .048 * grosor, r_canilla=H * .041 * grosor, r_brazo=H * .035 * grosor,
        r_antebrazo=H * .033 * grosor, r_mano=H * .046 * grosor, r_pie=r_pie,
        escala_rig=(muslo + canilla) / 14.0, bajar_punos=pr["bajar_punos"] * H / 37, paso=pr.get("paso", 1.0),
    )


def fuerza_cara(prop, cam_local):
    """Cuánto se corre la cara hacia la cámara. Los estilos de 8 direcciones pueden dar una fuerza propia a las
    diagonales ('cara_diagonal'): con la de los perfiles los dos ojos quedan iguales y se ve un 3/4 aplastado."""
    f = prop.get("cara_hacia_camara", .9)
    if "cara_perfil" in prop and abs(cam_local[0]) < 1e-6 and abs(cam_local[1]) > 1e-6:      # E / W
        return prop["cara_perfil"]
    if "cara_diagonal" in prop and abs(abs(cam_local[0]) - abs(cam_local[1])) < 1e-6 and abs(cam_local[0]) > 1e-6:
        return prop["cara_diagonal"]
    return f


def giro_cabeza(prop, mira):
    """Ángulo con que se gira la caja de la cabeza para que su silueta mida lo mismo en todas las direcciones
    (look Stardew: la cabeza es un bloque alineado a la pantalla). 0 si el estilo no lo pide."""
    if not prop.get("cabeza_pantalla"):
        return 0.0
    from .render3d import DIRECCIONES_CENITAL
    fx, fy = DIRECCIONES_CENITAL[mira]
    return math.atan2(-fx, fy)


def radios_cabeza(prop, mira, radios):
    """Radios de la caja de la cabeza. 'cabeza_diagonal' (< 1) angosta la cabeza en las 4 diagonales, como los juegos
    de 8 direcciones (de frente y de espalda es ancha, en 3/4 se angosta)."""
    k = prop.get("cabeza_diagonal", 1.0)
    if k != 1.0 and len(mira) == 2:
        rf, rl, rz = radios
        return (rf, rl * k, rz)
    return radios


def desvio_cabeza(prop, mira):
    """Vector local (adelante, izquierda) que corre la cabeza en pantalla 'cabeza_desvio[mira]' px hacia un costado
    (+ = derecha de la pantalla). Sirve para que la cabeza se apoye sobre el torso igual en SE/NE/SW/NW."""
    from .render3d import DIRECCIONES_CENITAL
    dx = prop.get("cabeza_desvio", {}).get(mira, 0.0)
    if not dx:
        return np.zeros(3)
    fx, fy = DIRECCIONES_CENITAL[mira]
    return np.array([dx * fx, dx * fy, 0.0])


def sobre_caja(hc, d, radios, giro, n=3.2, k=1.02):
    """Punto de la superficie de la caja de la cabeza (superelipsoide de radios 'radios' girada 'giro' alrededor de la
    vertical) en la dirección d desde el centro hc. Los ojos se apoyan ahí: si no, con la caja girada quedan flotando
    en el borde de la silueta."""
    cs, sn = math.cos(giro), math.sin(giro)
    R = np.array([[cs, -sn, 0], [sn, cs, 0], [0, 0, 1.0]])
    u = R.T @ np.asarray(d, float)
    t = 1.0 / (np.sum(np.abs(u / np.asarray(radios)) ** n) ** (1.0 / n) + 1e-12)
    return hc + k * (R @ (t * u))


def centro_cara(cam_local, fuerza=.9):
    """Trampa de Stardew: la cara se corre hacia la cámara. De frente queda adelante; de perfil, sobre el costado
    visible (si no, desde el costado solo se ve pelo); de espaldas queda oculta."""
    ch = np.array([cam_local[0], cam_local[1], 0.0])
    n = np.linalg.norm(ch)
    ch = ch / n if n > 1e-9 else ch
    c = np.array([1.0, 0, 0]) + fuerza * ch
    return c / (np.linalg.norm(c) + 1e-9)


def anclas_ausentes(lista):
    """Anclas que no existen: las nombradas y, para un segmento, todo menos su raíz (sin antebrazo queda el codo)."""
    out = set()
    for x in lista or []:
        out.add(x)
        if x in SEGMENTOS:
            out |= set(SEGMENTOS[x][1:])
    return out


def posar(anat, ps, cam_local, mira=None):
    """Posiciones 3D (ejes locales) de todas las anclas para una pose (formato de ciclos.pose / poses.cuadros)."""
    A, k = anat, anat.escala_rig
    esc = A.H / 28.0 * ESTILOS[A.estilo]["proporciones"].get("bob_escala", 1.0)
    sube = -ps["bob"] * .9 * esc
    if ESTILOS[A.estilo]["proporciones"].get("bob_px"):
        # rebote en píxeles ENTEROS: con fracciones (p. ej. 0,84 px) la cabeza, los ojos y las cejas caen en filas
        # distintas según el cuadro y "parpadean"
        px = round(ps["bob"] * .9 * esc * uz(A.estilo))
        sube = -px / uz(A.estilo)
    a = {"suelo": v(0, 0, 0)}
    cad_c = v(0, 0, A.cadera_u + sube)
    for lado, s in LADOS.items():
        m = masc(lado)
        pie, ang = (ps["pie_a"], ps["ang_a"]) if s < 0 else (ps["pie_b"], ps["ang_b"])
        cad = cad_c + v(0, s * A.cadera_l, 0)
        tob = v((pie[0] - 18) * k * A.paso, s * A.cadera_l, (34 - pie[1]) * k + A.r_pie * .3)
        rod = ik_3d(cad, tob, A.muslo, A.canilla, (1.0, 0, 0))          # rodilla adelante
        r = math.radians(ang)
        a[f"cadera_{lado}"], a[f"rodilla_{lado}"] = cad, rod
        a[f"tobillo_{m}"], a[f"pie_{m}"] = tob, tob + v(A.pie * math.cos(r), 0, -A.pie * math.sin(r))
        mp = ps["mano_b"] if s < 0 else ps["mano_a"]      # brazo opuesto a la pierna del mismo lado
        hom = v(-.2 * esc, s * A.hombro_l, A.hombro_u + sube)
        mano = hom + v((mp[0] - 20) * k, s * ps.get("abrir_brazos", .6) * esc, (16 - mp[1]) * k - A.bajar_punos)
        alcance = A.brazo + A.antebrazo
        if np.linalg.norm(mano - hom) > alcance:          # consistencia: los huesos nunca se estiran
            mano = hom + (mano - hom) / np.linalg.norm(mano - hom) * alcance * .999
        codo = ik_3d(hom, mano, A.brazo, A.antebrazo, (-1.0, 0, 0))   # codo atrás
        a[f"hombro_{m}"], a[f"codo_{m}"] = hom, codo
        a[f"muneca_{lado}"], a[f"mano_{lado}"] = codo + (mano - codo) * .8, mano
    rf, rl, rz = A.cabeza
    hc = v(.1 * esc, 0, A.cabeza_u + sube)
    if mira:
        hc = hc + desvio_cabeza(ESTILOS[A.estilo]["proporciones"], mira)
    c = centro_cara(cam_local, fuerza_cara(ESTILOS[A.estilo]["proporciones"], cam_local))
    perp = np.array([-c[1], c[0], 0.0])                    # hacia la izquierda del personaje, sobre la cara
    cara = hc + np.array([c[0] * rf, c[1] * rl, 0.0]) * 1.02
    prop = ESTILOS[A.estilo]["proporciones"]
    sep = prop.get("sep_ojos_diagonal", .31) if mira and len(mira) == 2 else (prop.get("sep_ojos", .31) if mira in ("S", "N") else .31)   # separación de los ojos (fracción de rl)
    ojo_i = cara + perp * rl * sep + v(0, 0, -rz * .24)
    ojo_d = cara - perp * rl * sep + v(0, 0, -rz * .24)
    if mira and prop.get("cabeza_pantalla"):        # caja girada: apoyar cara y ojos sobre la caja real
        rad, g = radios_cabeza(prop, mira, A.cabeza), giro_cabeza(prop, mira)
        base = np.array([c[0] * rf, c[1] * rl, 0.0])
        cara = sobre_caja(hc, base, rad, g)
        ojo_i = sobre_caja(hc, base + perp * rl * sep + v(0, 0, -rz * .24), rad, g)
        ojo_d = sobre_caja(hc, base - perp * rl * sep + v(0, 0, -rz * .24), rad, g)
    a.update(
        cabeza=hc, coronilla=hc + v(0, 0, rz), cara=cara,
        frente=hc + np.array([c[0] * rf, c[1] * rl, 0.0]) + v(0, 0, rz * .36),
        ojo_izquierdo=ojo_i, ojo_derecho=ojo_d,
        sien_derecha=hc + v(rf * .25, -rl * .97, rz * .25), sien_izquierda=hc + v(rf * .25, rl * .97, rz * .25),
        nuca=hc + v(-rf * .9, 0, -rz * .2),
        cuello=v(0, 0, A.cuello_u + sube), torso=v(-.2 * esc, 0, A.pecho_u + sube),
        pecho=v(A.pecho[0] * .9, 0, A.pecho_u + A.pecho[2] * .2 + sube),
        cintura=v(0, 0, A.pelvis_u + A.pelvis[2] * .8 + sube),
    )
    return a
