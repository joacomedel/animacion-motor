"""Perfiles de estilo: cómo se "ve" un sprite, independiente de qué personaje es y de cómo se mueve.

Claves de cada perfil:
  vista        'iso' (Camara, 8 direcciones), 'cenital' (CamaraCenital, 4) o 'lateral' (CamaraLateral, E/W)
  direcciones  direcciones que se generan, en el orden de la hoja
  render       parámetros de Escena.render(estilo=...)
  proporciones fracciones del alto H del personaje: cabeza, cadera (piernas), hombros, brazos (sobre el tronco);
               forma de la cabeza, cuánto se bajan los puños (px a H=37), cuánto se corre la cara hacia la
               cámara (trampa de Stardew: .9; en plataformas la cara mira hacia adelante: .1) y dirección de la luz
  tonos        regla de derivación de sombra/luz: (multiplicador, color hacia el que se corre, mezcla)
  ojos         'stardew' (pestaña + blanco + iris) o 'punto' (blanco + pupila)
  referencia   sprite de referencia para comparar_estilo (None = sin referencia); calibrada=True solo si sus
               métricas se validaron con un control (dos personajes del mismo juego): si no, solo advierte
  celda        (solo stardew/volumen) compatibilidad con los generadores por ficha; la escala real está en escala.py
Los números medidos y el razonamiento quedan en CRITERIOS_ANIMACION.md.
"""


def _luces_default():
    """Luces key/fill/rim + AO de contacto (task-021). Por defecto apagadas para no romper PNGs."""
    return dict(activas=False, fill=dict(dir=(0.5, -0.3, 0.4), color=(180, 160, 200), intensidad=0.35),
                rim=dict(dir=(0.3, -0.6, 0.5), color=(255, 250, 230), intensidad=0.5),
                ao_contacto=dict(activo=False, factor=0.6))

# Paletas fijas compartidas por estilo (`render.paleta_fija`): todo sprite del estilo sale de esa lista
# (task-017). Si faltan, el color se deriva por personaje como siempre.
# PLOT50 — justauserr13, top-down cozy: https://lospec.com/palette-list/plot50
PALETA_PLOT50 = [
    "#e39a86",
    "#d07a66",
    "#b85c4a",
    "#3d1f18",
    "#e2c39a",
    "#d9b48c",
    "#c89b6d",
    "#4a3526",
    "#b07a4a",
    "#a06a3d",
    "#7a4e2a",
    "#443527",
    "#f0d2b2",
    "#bfa07a",
    "#8b6a45",
    "#2b221a",
    "#8fd18a",
    "#5fb36a",
    "#3f8a4d",
    "#1f2a1f",
    "#9fd7f0",
    "#6fa3b0",
    "#3b86a8",
    "#183c52",
    "#a7d3e0",
    "#4c7f8f",
    "#1a2f36",
    "#c9b08a",
    "#a88c6a",
    "#7d664b",
    "#c2c6c9",
    "#9aa3a8",
    "#6f767c",
    "#2a2f33",
    "#4f5459",
    "#3a3f44",
    "#262a2e",
    "#121417",
    "#b9b2a8",
    "#8f877c",
    "#6a635a",
    "#3a352f",
    "#d6b7a1",
    "#b78a6a",
    "#8a5c42",
    "#3b2a22",
    "#f2a6b3",
    "#cfd6d6",
    "#f7f3ea",
    "#3b2f4a",
]
# Resurrect 64 — Kerrie Lake, dark fantasy RPG: https://lospec.com/palette-list/resurrect-64
PALETA_RESURRECT64 = [
    "#2e222f",
    "#3e3546",
    "#625565",
    "#966c6c",
    "#ab947a",
    "#694f62",
    "#7f708a",
    "#9babb2",
    "#c7dcd0",
    "#ffffff",
    "#6e2727",
    "#b33831",
    "#ea4f36",
    "#f57d4a",
    "#ae2334",
    "#e83b3b",
    "#fb6b1d",
    "#f79617",
    "#f9c22b",
    "#7a3045",
    "#9e4539",
    "#cd683d",
    "#e6904e",
    "#fbb954",
    "#4c3e24",
    "#676633",
    "#a2a947",
    "#d5e04b",
    "#fbff86",
    "#165a4c",
    "#239063",
    "#1ebc73",
    "#91db69",
    "#cddf6c",
    "#313638",
    "#374e4a",
    "#547e64",
    "#92a984",
    "#b2ba90",
    "#0b5e65",
    "#0b8a8f",
    "#0eaf9b",
    "#30e1b9",
    "#8ff8e2",
    "#323353",
    "#484a77",
    "#4d65b4",
    "#4d9be6",
    "#8fd3ff",
    "#45293f",
    "#6b3e75",
    "#905ea9",
    "#a884f3",
    "#eaaded",
    "#753c54",
    "#a24b6f",
    "#cf657f",
    "#ed8099",
    "#831c5d",
    "#c32454",
    "#f04f78",
    "#f68181",
    "#fca790",
    "#fdcbb0",
]
# Fry (CC0) — los 14 colores medidos de la referencia `referencias/8dir/fry_40x64`.
PALETA_FRY14 = [
    "#f8f8b8",
    "#262523",
    "#f888a8",
    "#b04078",
    "#482050",
    "#304050",
    "#6880b0",
    "#f8d080",
    "#c88068",
    "#a0c0f8",
    "#904058",
    "#584030",
    "#d8c090",
    "#907860",
]

ESTILOS = {
    "volumen": dict(
        descripcion="Pre-renderizado tipo Diablo II/Isometric Hero: volumen marcado, contorno negro por pieza.",
        vista="iso",
        direcciones=["SE", "E", "NE", "N", "NW", "W", "SW", "S"],
        celda=dict(cw=56, ch=60, gx=26, gy=52),
        render=dict(
            umbrales=(0.28, 0.66), contorno="negro", interior="negro", sombreado="luz",
            luces=_luces_default(),
            paleta_fija=PALETA_RESURRECT64,
        ),
        proporciones=dict(
            cabezas=3.3,
            cabeza_frac=0.30,
            piernas_frac=0.41,
            hombros_frac=0.146,
            brazos_frac=1.0,
            forma_cabeza="esfera",
            bajar_punos=2.5,
            cara_hacia_camara=0.9,
            luz=(0.4, -0.45, 0.8),
        ),
        tonos=dict(sombra=(0.58, (20, 20, 60), 0.2), luz=(1.25, (255, 250, 230), 0.15)),
        ojos="punto",
        referencia=None,
        paleta="3 tonos por material bien separados; contorno casi negro azulado",
        ciclos=["correr", "quieto"],
    ),
    "stardew": dict(
        descripcion="Stardew Valley: cenital 3/4, chibi, sombreado plano, contorno de color (selout).",
        vista="cenital",
        direcciones=["S", "E", "N", "W"],
        celda=dict(cw=16, ch=32, gx=8, gy=30),
        render=dict(
            umbrales=(0.12, 0.82),
            contorno="color",
            interior="color",
            oscurecer=0.45,
            sombreado="borde",
            luces=_luces_default(),
            paleta_fija=PALETA_PLOT50,
        ),
        proporciones=dict(
            cabezas=2.2,
            cabeza_frac=0.36,
            piernas_frac=0.29,
            hombros_frac=0.12,
            brazos_frac=0.74,
            forma_cabeza="caja",
            bajar_punos=0,
            cara_hacia_camara=0.55,
            luz=(-0.25, 0.75, 0.6),  # .9 dejaba el perfil de frente
            paso=0.7,
            # rebote en píxeles ENTEROS: sin esto el bob (~0.8 px de mundo) se redondea a 0 y caminar/saltar
            # quedan sin rebote (el analizador daba rebote [0,0,0,...]; la referencia de Stardew rebota 1 px al
            # pisar). Con fracciones, además, la pestaña/ceja caen en filas distintas según el cuadro y parpadean.
            # Mismo arreglo que ya tenía stardew8 (estilos.py, abajo).
            bob_px=True,
        ),  # celda de 16 px: el paso completo de LPC saca el pie de la celda
        tonos=dict(
            sombra=(0.66, (70, 40, 120), 0.25), luz=(1.22, (255, 236, 160), 0.2)
        ),
        ojos="stardew",
        referencia=dict(
            ruta="referencias/stardew/abigail.png",
            celda=(16, 32),
            recorte=(0, 0, 64, 128),
            calibrada=True,
        ),  # control Abigail vs Wizard (CRITERIOS_ANIMACION.md)
        paleta="saturada y cálida; 3-4 tonos por material con corrimiento de tono (sombras hacia violeta, "
        "luces hacia amarillo); contorno = tono más oscuro del mismo material, nunca negro puro "
        "(salvo materiales negros); 20-30 colores por cuadro",
        ciclos=["caminar", "quieto"],
    ),
    "lateral": dict(
        descripcion="Plataformas tipo Mega Man X: de perfil, cabeza grande, contorno negro, 3 tonos marcados.",
        vista="lateral",
        direcciones=["E", "W"],
        render=dict(
            umbrales=(0.15, 0.8), contorno="negro", interior="negro", sombreado="borde",
            luces=_luces_default(),
        ),
        proporciones=dict(
            cabezas=2.2,
            cabeza_frac=0.40,
            piernas_frac=0.32,
            hombros_frac=0.12,
            brazos_frac=1.16,
            forma_cabeza="caja",
            bajar_punos=0,
            cara_hacia_camara=0.1,
            luz=(-0.35, 0.55, 0.8),
        ),
        tonos=dict(sombra=(0.6, (20, 30, 80), 0.2), luz=(1.25, (255, 250, 230), 0.15)),
        ojos="stardew",
        referencia=dict(
            ruta="sprites_x/animaciones/02_quieto.png",
            celda=(30, 34),
            recorte=None,
            calibrada=False,
        ),  # falta un control: segunda referencia del mismo juego
        paleta="rampas de 3-5 tonos por material; contorno negro también por dentro",
        ciclos=["correr", "quieto"],
    ),
    "lpc": dict(
        descripcion="Solo verificación: el muñeco al tamaño y proporciones de la referencia LPC (cabeza 45%), "
        "para comparar plantillas de movimiento hueso por hueso y silueta contra silueta.",
        vista="lateral",
        direcciones=["E", "W"],  # LPC de perfil: los dos pies sobre la misma línea
        render=dict(
            umbrales=(0.12, 0.82),
            contorno="negro",
            interior="color",
            oscurecer=0.45,
            sombreado="borde",
            luces=_luces_default(),
        ),
        proporciones=dict(
            cabezas=2.2,
            cabeza_frac=0.45,
            piernas_frac=0.30,
            hombros_frac=0.12,
            brazos_frac=1.2,
            forma_cabeza="esfera",
            bajar_punos=0,
            cara_hacia_camara=0.55,
            luz=(-0.25, 0.75, 0.6),
        ),
        tonos=dict(
            sombra=(0.66, (70, 40, 120), 0.25), luz=(1.22, (255, 236, 160), 0.2)
        ),
        ojos="punto",
        referencia=None,
        paleta="piel base de LPC",
        ciclos=["caminar_lpc"],
    ),
}

# mismo look que stardew (cenital 3/4, sombreado plano, contorno de color) pero con las 4 diagonales: 8 direcciones
ESTILOS["stardew8"] = {
    **ESTILOS["stardew"],
    "proporciones": {
        **ESTILOS["stardew"]["proporciones"],
        "cara_diagonal": 0.45,
        "sep_ojos_diagonal": 0.45,
        "ojos_umbral": 0.05,
        # 0.5: la cara se apoya más al frente, así el perfil E/W se lee de costado (pelo atrás, un solo ojo).
        # 0.9 empujaba la cara casi de frente a la cámara y el perfil se veía como un 3/4 con los dos ojos.
        "cara_perfil": 0.5,
        "sin_boca_diagonal": True,
        "bob_px": True,
        "cabeza_pantalla": True,
        "cabeza_diagonal": 0.85,
        "cabeza_desvio": {"SE": 0.9, "NE": -0.2, "SW": -0.9, "NW": 0.2},
    },
    "direcciones": ["S", "SE", "E", "NE", "N", "NW", "W", "SW"],
    # Fry (CC0) usa 14 colores en toda su hoja; el render daba ~70. 28 casi no se distingue (20 pierde ojos)
    "render": {**ESTILOS["stardew"]["render"], "paleta_max": 28},
    "descripcion": "Stardew Valley en 8 direcciones (sin volumen): igual que stardew + diagonales.",
}

# boceto tipo Fry (CC0): personaje grande (~58 px), cabeza ~30%, cuerpo ancho, pocos colores; misma cámara que stardew8
ESTILOS["fry8"] = {
    **ESTILOS["stardew8"],
    "proporciones": {
        k: v for k, v in ESTILOS["stardew8"]["proporciones"].items() if k != "paso"
    }
    | {
        "cabeza_frac": 0.30,
        "hombros_frac": 0.125,
        "piernas_frac": 0.27,
        "cabeza_ancho": 0.72,
        "cuerpo_ancho": 1.3,
        "bob_escala": 0.5,
        "paso": 0.55,
        "sep_ojos": 0.55,
        "sep_ojos_diagonal": 0.33,
    },
    "render": {
        **ESTILOS["stardew8"]["render"],
        "paleta_max": 16,
        "paleta_fija": PALETA_FRY14,
    },
    "referencia": None,
    "ojos": "fry",
    "descripcion": "Boceto tipo Fry (referencias/8dir/fry_40x64): grande, cabeza ~30%, 16 colores.",
}

# estilos que se generan por defecto ("--estilo todos"); volumen queda disponible pero el usuario prefiere stardew
ACTIVOS = ["stardew", "lateral"]
# estilos que no son del juego: solo sirven para verificar plantillas contra su referencia (no se validan en fichas)
VERIFICACION = ["lpc", "fry8"]  # fry8: boceto, todavía sin componentes declarados

_UZ = {"iso": 0.92, "cenital": 0.92, "lateral": 1.0}


def uz(estilo):
    """Cuántos px de pantalla ocupa 1 unidad de altura del mundo en ese estilo."""
    return _UZ[ESTILOS[estilo]["vista"]]


def crear_camara(estilo, mira, celda):
    """Cámara del estilo para una dirección y una celda (ver escala.celda)."""
    from .render3d import Camara, CamaraCenital, CamaraLateral

    e = ESTILOS[estilo]
    if mira not in e["direcciones"]:
        raise ValueError(
            f"{mira!r} no es una dirección del estilo {estilo}: {', '.join(e['direcciones'])}"
        )
    luz = e["proporciones"]["luz"]
    clase = {"iso": Camara, "cenital": CamaraCenital, "lateral": CamaraLateral}[
        e["vista"]
    ]
    return clase(mira, luz=luz, **celda)
