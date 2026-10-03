"""Fichas y skins sintéticas: el kit arranca sin personajes y los tests se fabrican los suyos.

`heroe` (rastas, túnica, pulsera, ojos) y `robot` (prótesis, muñón con cables, chispa emisiva) cubren los
componentes que los tests ejercitan; `skin_prueba` genera una skin 32×32 con `skins.desde_colores`.
"""

import copy
import os

import yaml

COLORES_SKIN = {
    "piel": "#c8916a",
    "pelo": "#3b2b20",
    "remera": "#3a6ea5",
    "pantalon": "#4a3b5c",
    "calzado": "#5a3a28",
    "iris": "#2e7d6b",
}


def skin_prueba(ruta, **cambios):
    """Skin 32×32 sintética; `cambios` pisa colores de `COLORES_SKIN` (piel, pelo, remera, pantalon, calzado, iris)."""
    from sprites_lib import skins

    return skins.desde_colores({**COLORES_SKIN, **cambios}, str(ruta))


def fichas_dir(base):
    """Crea `<base>/personajes/fichas` (el layout que resuelve `ficha.cargar` por nombre) y devuelve la ruta."""
    carpeta = os.path.join(str(base), "personajes", "fichas")
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def guardar_ficha(carpeta, ficha, nombre):
    """Escribe la ficha como YAML en `carpeta` y devuelve la ruta."""
    ruta = os.path.join(str(carpeta), f"{nombre}.yaml")
    with open(ruta, "w", encoding="utf-8") as fh:
        yaml.safe_dump(ficha, fh, allow_unicode=True, sort_keys=False)
    return ruta


_HEROE = {
    "identidad": {
        "nombre": "Héroe de prueba",
        "concepto": "Personaje sintético de los tests: silueta con rastas largas y túnica abierta.",
        "silueta_clave": "rastas largas + túnica abierta",
    },
    "cuerpo": {
        "base": "humano",
        "clase_altura": "adulto",
        "complexion": "normal",
        "piel": "morena",
        "cabello": "corto",
    },
    "paleta": {
        "piel": {"base": "#8c5638", "por_que": "test"},
        "pelo": {"base": "#e2e2f0", "por_que": "test"},
        "tunica": {"base": "#5c2c96", "por_que": "test"},
        "camisa": {"base": "#362e62", "por_que": "test"},
        "oro": {"base": "#e2aa34", "por_que": "test"},
        "runa": {"base": "#5af0e6", "emisivo": True, "por_que": "test"},
        "pantalon": {"base": "#42366e", "por_que": "test"},
        "bota": {"base": "#62392a", "por_que": "test"},
    },
    "componentes": [
        {
            "tipo": "rastas",
            "ancla": "cabeza",
            "material": "pelo",
            "parametros": {"cantidad": 6, "largo": "hombros", "cuentas": "runa"},
            "por_que": "silueta del test",
            "reglas": ["siempre_visible"],
        },
        {
            "tipo": "vincha",
            "ancla": "frente",
            "material": "oro",
            "parametros": {"gema": "runa"},
            "por_que": "detalle de cabeza del test",
            "reglas": ["visible_si_ancla_visible"],
        },
        {
            "tipo": "pulsera",
            "ancla": "muneca_derecha",
            "material": "oro",
            "por_que": "t_visibilidad la usa para simular que desaparece",
            "reglas": ["visible_si_ancla_visible"],
        },
        {
            "tipo": "tatuaje_runas",
            "ancla": ["brazo_izquierdo", "brazo_derecho"],
            "material": "runa",
            "por_que": "el tatuaje que las rastas tapan de espaldas",
            "reglas": ["visible_si_ancla_visible", "simetrico"],
        },
        {
            "tipo": "tunica_abierta",
            "ancla": "torso",
            "material": "tunica",
            "parametros": {
                "interior": "camisa",
                "ribete": "oro",
                "faldon": "hasta_rodilla",
            },
            "por_que": "ropa principal del test",
        },
        {
            "tipo": "pierna_humana",
            "ancla": ["pierna_izquierda", "pierna_derecha"],
            "material": "pantalon",
            "parametros": {"calzado": "bota"},
            "por_que": "piernas vestidas del test",
        },
        {
            "tipo": "botas",
            "ancla": ["pie_izquierdo", "pie_derecho"],
            "material": "bota",
            "parametros": {"suela": "runa"},
            "por_que": "calzado del test",
            "reglas": ["simetrico"],
        },
        {
            "tipo": "ojos",
            "ancla": "cara",
            "parametros": {"iris": "runa"},
            "por_que": "cara del test",
        },
    ],
    "reglas_globales": [
        "paleta_identica_entre_direcciones",
        "lineas_guia",
        "nada_recortado",
        "tamano_de_clase",
        {"cara_visible_en": ["S", "E", "W"]},
    ],
}

_ROBOT = {
    "identidad": {
        "nombre": "Robot de prueba",
        "concepto": "Personaje sintético de los tests: prótesis, muñón con cables y chispa emisiva.",
        "silueta_clave": "muñón que termina en el codo + cables en la nuca",
    },
    "cuerpo": {
        "base": "humano",
        "clase_altura": "adulto",
        "complexion": "normal",
        "piel": "clara",
        "cabello": "rapado",
        "sustituciones": {
            "brazo_izquierdo": "brazo_robotico",
            "brazo_derecho": "brazo_robotico_amputado",
            "pierna_izquierda": "pierna_robotica",
            "pierna_derecha": "pierna_robotica",
        },
        "ausentes": ["antebrazo_derecho", "muneca_derecha", "mano_derecha"],
    },
    "paleta": {
        "piel": {"base": "#e8b894", "por_que": "test"},
        "metal": {"base": "#8a929c", "por_que": "test"},
        "metal_raya": {"base": "#c4ccd4", "por_que": "test"},
        "ropa": {"base": "#9c4a3c", "por_que": "test"},
        "cuero": {"base": "#5a3a28", "por_que": "test"},
        "cable": {"base": "#2e3238", "por_que": "test"},
        "pelo": {"base": "#3a302a", "por_que": "test"},
        "luz": {"base": "#5cf07a", "emisivo": True, "por_que": "test"},
    },
    "componentes": [
        {
            "tipo": "brazo_robotico",
            "ancla": "brazo_izquierdo",
            "material": "metal",
            "parametros": {
                "juntas": "luz",
                "rayas": "metal_raya",
                "mano": "pinza_3_dedos",
            },
            "por_que": "prótesis completa del test",
            "reglas": ["visible_si_ancla_visible"],
        },
        {
            "tipo": "brazo_robotico_amputado",
            "ancla": "brazo_derecho",
            "material": "metal",
            "parametros": {"termina_en": "codo_derecho"},
            "por_que": "el brazo cortado a la altura del codo",
            "reglas": ["visible_si_ancla_visible", "ausente_mas_alla_de_codo_derecho"],
        },
        {
            "tipo": "munon_cables",
            "ancla": "codo_derecho",
            "material": "cable",
            "parametros": {
                "cables": 3,
                "largo_px": 2,
                "chispa": "luz",
                "chispa_cada_cuadros": 3,
            },
            "por_que": "el muñón con los cables y la chispa",
            "reglas": ["visible_si_ancla_visible"],
        },
        {
            "tipo": "pierna_robotica",
            "ancla": ["pierna_izquierda", "pierna_derecha"],
            "material": "metal",
            "parametros": {
                "juntas": "luz",
                "rodilla": "piston",
                "pie": "bota_metalica",
            },
            "por_que": "piernas mecánicas del test",
            "reglas": ["visible_si_ancla_visible", "simetrico"],
        },
        {
            "tipo": "placa_sien",
            "ancla": "sien_derecha",
            "material": "metal",
            "por_que": "implante lateral del test",
            "reglas": ["visible_si_ancla_visible"],
        },
        {
            "tipo": "cables_nuca",
            "ancla": "nuca",
            "material": "cable",
            "parametros": {"cables": 3, "luz_en_punta": "luz", "largo": "hombros"},
            "por_que": "cables que caen por la nuca",
            "reglas": ["visible_si_ancla_visible"],
        },
        {
            "tipo": "remera_larga_rota",
            "ancla": "torso",
            "material": "ropa",
            "parametros": {"largo": "medio_muslo", "jirones": 3, "sin_mangas": True},
            "por_que": "ropa gastada del test",
        },
        {
            "tipo": "cinturon",
            "ancla": "cintura",
            "material": "cuero",
            "parametros": {"hebilla": "metal"},
            "por_que": "cinturón del test",
        },
        {"tipo": "ojos", "ancla": "cara", "por_que": "cara del test"},
    ],
    "reglas_globales": [
        "paleta_identica_entre_direcciones",
        "lineas_guia",
        "nada_recortado",
        "tamano_de_clase",
        {"cara_visible_en": ["S", "E", "W"]},
    ],
}


def heroe():
    """Ficha (dict) del héroe sintético: lista para `validar`, `render_todo` o `guardar_ficha`."""
    return copy.deepcopy(_HEROE)


def robot():
    """Ficha (dict) del robot sintético: prótesis, muñón con cables y chispa."""
    return copy.deepcopy(_ROBOT)


def vecino():
    """Ficha (dict) con la paleta del héroe corrida a azules: sirve de contraste en `t_distinto`."""
    f = heroe()
    f["identidad"]["nombre"] = "Vecino de prueba"
    for i, nombre in enumerate(sorted(f["paleta"])):
        f["paleta"][nombre] = {
            "base": "#%02x%02x%02x" % (10 + 30 * i, 40 + 25 * i, 200 - 20 * i),
            "por_que": "test",
        }
    f["paleta"]["runa"] = {"base": "#ff2fd0", "emisivo": True, "por_que": "test"}
    return f


def espadachin():
    """Ficha (dict) del héroe con una espada en la mano derecha y un escudo en la izquierda: ejercita el
    componente `objeto` (materiales planos) y que el objeto siga la mano en los ciclos."""
    f = heroe()
    f["identidad"]["nombre"] = "Espadachín de prueba"
    f["identidad"]["silueta_clave"] = "espada en la derecha + escudo en la izquierda"
    f["paleta"]["acero"] = {"base": "#c8d2dc", "por_que": "test"}
    f["paleta"]["cuero"] = {"base": "#5a3a28", "por_que": "test"}
    f["componentes"].append(
        {
            "tipo": "objeto",
            "ancla": "mano_derecha",
            "material": "acero",
            "parametros": {"forma": "espada", "mango": "cuero", "pomo": "oro"},
            "por_que": "espada en la mano derecha",
            "reglas": ["visible_si_ancla_visible"],
        }
    )
    f["componentes"].append(
        {
            "tipo": "objeto",
            "ancla": "mano_izquierda",
            "material": "cuero",
            "parametros": {"forma": "escudo", "detalle": "oro"},
            "por_que": "escudo en la mano izquierda",
            "reglas": ["visible_si_ancla_visible"],
        }
    )
    return f
