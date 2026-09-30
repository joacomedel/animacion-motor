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
  celda        (solo stardew/volumen) compatibilidad con personajes/mago_*.py; la escala real está en escala.py
Los números medidos y el razonamiento quedan en CRITERIOS_ANIMACION.md.
"""

ESTILOS = {
    "volumen": dict(
        descripcion="Pre-renderizado tipo Diablo II/Isometric Hero: volumen marcado, contorno negro por pieza.",
        vista="iso", direcciones=["SE", "E", "NE", "N", "NW", "W", "SW", "S"],
        celda=dict(cw=56, ch=60, gx=26, gy=52),
        render=dict(umbrales=(.28, .66), contorno="negro", interior="negro", sombreado="luz"),
        proporciones=dict(cabezas=3.3, cabeza_frac=.30, piernas_frac=.41, hombros_frac=.146, brazos_frac=1.0,
                          forma_cabeza="esfera", bajar_punos=2.5, cara_hacia_camara=.9, luz=(.4, -.45, .8)),
        tonos=dict(sombra=(.58, (20, 20, 60), .2), luz=(1.25, (255, 250, 230), .15)),
        ojos="punto", referencia=None,
        paleta="3 tonos por material bien separados; contorno casi negro azulado",
        ciclos=["correr", "quieto"],
    ),
    "stardew": dict(
        descripcion="Stardew Valley: cenital 3/4, chibi, sombreado plano, contorno de color (selout).",
        vista="cenital", direcciones=["S", "E", "N", "W"],
        celda=dict(cw=16, ch=32, gx=8, gy=30),
        render=dict(umbrales=(.12, .82), contorno="color", interior="color", oscurecer=.45, sombreado="borde"),
        proporciones=dict(cabezas=2.2, cabeza_frac=.36, piernas_frac=.29, hombros_frac=.12, brazos_frac=.74,
                          forma_cabeza="caja", bajar_punos=0, cara_hacia_camara=.55, luz=(-.25, .75, .6),   # .9 dejaba el perfil de frente
                          paso=.7),        # celda de 16 px: el paso completo de LPC saca el pie de la celda
        tonos=dict(sombra=(.66, (70, 40, 120), .25), luz=(1.22, (255, 236, 160), .2)),
        ojos="stardew",
        referencia=dict(ruta="referencias/stardew/abigail.png", celda=(16, 32), recorte=(0, 0, 64, 128),
                        calibrada=True,    # control Abigail vs Wizard (CRITERIOS_ANIMACION.md)
                        # sujeto de la comparación de estilo: un personaje vestido; el muñeco desnudo no tiene
                        # el detalle dibujado (mechones, ropa) que miden las métricas de comparar_estilo
                        especimen="skins/mago.png"),
        paleta="saturada y cálida; 3-4 tonos por material con corrimiento de tono (sombras hacia violeta, "
               "luces hacia amarillo); contorno = tono más oscuro del mismo material, nunca negro puro "
               "(salvo materiales negros); 20-30 colores por cuadro",
        ciclos=["caminar", "quieto"],
    ),
    "lateral": dict(
        descripcion="Plataformas tipo Mega Man X: de perfil, cabeza grande, contorno negro, 3 tonos marcados.",
        vista="lateral", direcciones=["E", "W"],
        render=dict(umbrales=(.15, .8), contorno="negro", interior="negro", sombreado="borde"),
        proporciones=dict(cabezas=2.2, cabeza_frac=.40, piernas_frac=.32, hombros_frac=.12, brazos_frac=1.16,
                          forma_cabeza="caja", bajar_punos=0, cara_hacia_camara=.1, luz=(-.35, .55, .8)),
        tonos=dict(sombra=(.6, (20, 30, 80), .2), luz=(1.25, (255, 250, 230), .15)),
        ojos="stardew",
        referencia=dict(ruta="sprites_x/animaciones/02_quieto.png", celda=(30, 34), recorte=None,
                        calibrada=False),  # falta un control: segunda referencia del mismo juego
        paleta="rampas de 3-5 tonos por material; contorno negro también por dentro",
        ciclos=["correr", "quieto"],
    ),
    "lpc": dict(
        descripcion="Solo verificación: el muñeco al tamaño y proporciones de la referencia LPC (cabeza 45%), "
                    "para comparar plantillas de movimiento hueso por hueso y silueta contra silueta.",
        vista="lateral", direcciones=["E", "W"],       # LPC de perfil: los dos pies sobre la misma línea
        render=dict(umbrales=(.12, .82), contorno="negro", interior="color", oscurecer=.45, sombreado="borde"),
        proporciones=dict(cabezas=2.2, cabeza_frac=.45, piernas_frac=.30, hombros_frac=.12, brazos_frac=1.2,
                          forma_cabeza="esfera", bajar_punos=0, cara_hacia_camara=.55, luz=(-.25, .75, .6)),
        tonos=dict(sombra=(.66, (70, 40, 120), .25), luz=(1.22, (255, 236, 160), .2)),
        ojos="punto", referencia=None, paleta="piel base de LPC", ciclos=["caminar_lpc"],
    ),
}

# mismo look que stardew (cenital 3/4, sombreado plano, contorno de color) pero con las 4 diagonales: 8 direcciones
ESTILOS["stardew8"] = {**ESTILOS["stardew"],
                       "proporciones": {**ESTILOS["stardew"]["proporciones"], "cara_diagonal": .45, "sep_ojos_diagonal": .45, "ojos_umbral": .05, "cara_perfil": .9, "sin_boca_diagonal": True, "bob_px": True, "cabeza_pantalla": True,
                                     "cabeza_diagonal": .85,
                                     "cabeza_desvio": {"SE": 0.9, "NE": -0.2, "SW": -1.0, "NW": 0.1}},
                       "direcciones": ["S", "SE", "E", "NE", "N", "NW", "W", "SW"],
                       # Fry (CC0) usa 14 colores en toda su hoja; el render daba ~70. 28 casi no se distingue (20 pierde ojos)
                       "render": {**ESTILOS["stardew"]["render"], "paleta_max": 28},
                       "descripcion": "Stardew Valley en 8 direcciones (sin volumen): igual que stardew + diagonales."}

# boceto tipo Fry (CC0): personaje grande (~58 px), cabeza ~30%, cuerpo ancho, pocos colores; misma cámara que stardew8
ESTILOS["fry8"] = {**ESTILOS["stardew8"],
                   "proporciones": {k: v for k, v in ESTILOS["stardew8"]["proporciones"].items() if k != "paso"}
                   | {"cabeza_frac": .30, "hombros_frac": .125, "piernas_frac": .27,
                                                                                    "cabeza_ancho": .72, "cuerpo_ancho": 1.3, "bob_escala": .5, "paso": .55,
                                                                                    "sep_ojos": .55, "sep_ojos_diagonal": .33},
                   "render": {**ESTILOS["stardew8"]["render"], "paleta_max": 16},
                   "referencia": None, "ojos": "fry",
                   "descripcion": "Boceto tipo Fry (referencias/8dir/fry_40x64): grande, cabeza ~30%, 16 colores."}

# estilos que se generan por defecto ("--estilo todos"); volumen queda disponible pero el usuario prefiere stardew
ACTIVOS = ["stardew", "lateral"]
# estilos que no son del juego: solo sirven para verificar plantillas contra su referencia (no se validan en fichas)
VERIFICACION = ["lpc", "fry8"]     # fry8: boceto, todavía sin componentes declarados

_UZ = {"iso": .92, "cenital": .92, "lateral": 1.0}


def uz(estilo):
    """Cuántos px de pantalla ocupa 1 unidad de altura del mundo en ese estilo."""
    return _UZ[ESTILOS[estilo]["vista"]]


def crear_camara(estilo, mira, celda):
    """Cámara del estilo para una dirección y una celda (ver escala.celda)."""
    from .render3d import Camara, CamaraCenital, CamaraLateral
    e = ESTILOS[estilo]
    if mira not in e["direcciones"]:
        raise ValueError(f"{mira!r} no es una dirección del estilo {estilo}: {', '.join(e['direcciones'])}")
    luz = e["proporciones"]["luz"]
    clase = {"iso": Camara, "cenital": CamaraCenital, "lateral": CamaraLateral}[e["vista"]]
    return clase(mira, luz=luz, **celda)
