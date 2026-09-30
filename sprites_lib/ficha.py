"""Fichas de personaje: cargar el YAML y validarlo antes de generar nada. Los errores dicen qué está mal y,
si es un nombre mal escrito, sugieren el correcto (como el validador del generador LPC)."""
import difflib
import os

import yaml

from .componentes import REGISTRO
from .cuerpo import COMPLEXIONES, PADRE, SEGMENTOS, VOCABULARIO, anclas_ausentes
from .escala import CLASES
from .estilos import ESTILOS, VERIFICACION
from .paleta import HEX

CARPETA = os.path.join("personajes", "fichas")
TOPES = {"identidad", "cuerpo", "paleta", "componentes", "reglas_globales", "excepciones", "decisiones",
         "objeciones_resueltas", "creditos", "estilos"}
CLAVES_CUERPO = {"base", "clase_altura", "complexion", "piel", "cabello", "sustituciones", "ausentes"}
CLAVES_COMP = {"tipo", "ancla", "material", "parametros", "por_que", "reglas", "nuevo"}
CABELLOS = {"calvo", "rapado", "corto", "cresta"}
REGLAS_COMP = {"visible_si_ancla_visible", "siempre_visible", "simetrico"}
REGLAS_GLOBALES = {"paleta_identica_entre_direcciones", "lineas_guia", "nada_recortado", "tamano_de_clase",
                   "cara_visible_en", "distinto_de"}


class FichaInvalida(ValueError):
    def __init__(self, errores):
        self.errores = list(errores)
        super().__init__("ficha inválida:\n- " + "\n- ".join(self.errores))


def _sug(x, opciones):
    m = difflib.get_close_matches(str(x).replace("ñ", "n"), list(opciones), n=1, cutoff=.6)
    return f" (¿quisiste decir {m[0]!r}?)" if m else ""


def _lista(x):
    return list(x) if isinstance(x, (list, tuple)) else [x]


def _regla_ok(r):
    if r in REGLAS_COMP:
        return True
    if isinstance(r, str) and r.startswith("ausente_mas_alla_de_"):
        return r[len("ausente_mas_alla_de_"):] in PADRE
    return False


def validar(f, estilos=None):
    e = []
    if not isinstance(f, dict):
        return ["la ficha no es un diccionario YAML"]
    for k in ("identidad", "cuerpo", "paleta", "componentes"):
        if k not in f:
            e.append(f"falta la sección {k!r}")
    if e:
        return e
    for k in sorted(set(f) - TOPES):
        e.append(f"sección desconocida {k!r}{_sug(k, TOPES)}")
    for k in ("nombre", "concepto", "silueta_clave"):
        if not (f["identidad"] or {}).get(k):
            e.append(f"identidad.{k} está vacío")
    cu = f["cuerpo"] or {}
    for k in sorted(set(cu) - CLAVES_CUERPO):
        e.append(f"cuerpo: clave desconocida {k!r}{_sug(k, CLAVES_CUERPO)}")
    if cu.get("base") != "humano":
        e.append(f"cuerpo.base {cu.get('base')!r} no soportado (por ahora solo 'humano')")
    if cu.get("clase_altura", "adulto") not in CLASES:
        e.append(f"cuerpo.clase_altura {cu.get('clase_altura')!r} no existe{_sug(cu.get('clase_altura'), CLASES)}")
    if cu.get("complexion", "normal") not in COMPLEXIONES:
        e.append(f"cuerpo.complexion {cu.get('complexion')!r} no existe{_sug(cu.get('complexion'), COMPLEXIONES)}")
    if cu.get("cabello", "corto") not in CABELLOS:
        e.append(f"cuerpo.cabello {cu.get('cabello')!r} no existe; opciones: {', '.join(sorted(CABELLOS))}")
    for aus in cu.get("ausentes") or []:
        if aus not in VOCABULARIO:
            e.append(f"cuerpo.ausentes: {aus!r} no existe{_sug(aus, VOCABULARIO)}")
    ausentes = anclas_ausentes(cu.get("ausentes"))
    pal = f["paleta"] or {}
    for nom, m in pal.items():
        if not isinstance(m, dict) or not HEX.match(str(m.get("base", ""))):
            e.append(f"paleta.{nom}: 'base' tiene que ser un color #rrggbb")
    if "piel" not in pal:
        e.append("paleta: falta el material 'piel' (lo usan cara y manos)")
    if cu.get("cabello", "corto") == "corto" and "pelo" not in pal:
        e.append("paleta: falta 'pelo' (cabello: corto)")
    materiales = set(pal) | {f"{m}_b" for m in pal} | ({"mano"} if "piel" in pal else set())
    estilos = estilos or f.get("estilos") or [k for k in ESTILOS if k not in VERIFICACION]
    for est in estilos:
        if est not in ESTILOS:
            e.append(f"estilo desconocido {est!r}{_sug(est, ESTILOS)}")
    vistos = set()
    tipos_ficha = set()
    for i, c in enumerate(f["componentes"] or []):
        donde = f"componentes[{i}]"
        if not isinstance(c, dict):
            e.append(f"{donde}: tiene que ser un diccionario")
            continue
        for k in sorted(set(c) - CLAVES_COMP):
            e.append(f"{donde}: clave desconocida {k!r}{_sug(k, CLAVES_COMP)}")
        t = c.get("tipo")
        if t not in REGISTRO:
            e.append(f"{donde}: componente {t!r} no existe{_sug(t, REGISTRO)}")
            continue
        tipos_ficha.add(t)
        comp = REGISTRO[t]
        donde = f"{donde} ({t})"
        if not c.get("por_que"):
            e.append(f"{donde}: falta 'por_que' (toda decisión de diseño se explica)")
        for an in _lista(c.get("ancla")):
            if an not in VOCABULARIO:
                e.append(f"{donde}: ancla {an!r} no existe{_sug(an, VOCABULARIO)}")
            elif comp.anclas_validas and an not in comp.anclas_validas:
                e.append(f"{donde}: no se puede poner en {an!r}; válidas: {', '.join(comp.anclas_validas)}")
            elif an in ausentes:
                e.append(f"{donde}: el ancla {an!r} está ausente en cuerpo.ausentes")
            if (t, an) in vistos:
                e.append(f"{donde}: está repetido en {an!r}")
            vistos.add((t, an))
        mat = c.get("material") or comp.material_defecto
        if mat and mat not in materiales:
            e.append(f"{donde}: el material {mat!r} no está en la paleta{_sug(mat, materiales)}")
        params = c.get("parametros") or {}
        for k, val in params.items():
            if k not in comp.params_defecto:
                e.append(f"{donde}: parámetro desconocido {k!r}{_sug(k, comp.params_defecto)}")
            elif k in comp.params_material and val is not None and val not in materiales:
                e.append(f"{donde}: parámetros.{k} = {val!r} no es un material de la paleta")
        for r in c.get("reglas") or []:
            if not _regla_ok(r):
                e.append(f"{donde}: regla desconocida {r!r}{_sug(r, REGLAS_COMP)}")
        for est in estilos:
            if est in ESTILOS and est not in comp.estilos:
                e.append(f"{donde}: no soporta el estilo {est!r} (soporta: {', '.join(comp.estilos)})")
    for seg, tipo in (cu.get("sustituciones") or {}).items():
        if seg not in SEGMENTOS or seg.startswith("antebrazo"):
            e.append(f"cuerpo.sustituciones: {seg!r} no es un segmento sustituible (brazo_*/pierna_*)")
        if tipo not in REGISTRO:
            e.append(f"cuerpo.sustituciones.{seg}: componente {tipo!r} no existe{_sug(tipo, REGISTRO)}")
        elif (tipo, seg) not in vistos:
            e.append(f"cuerpo.sustituciones.{seg}: no hay un componente {tipo!r} con ancla {seg!r} en componentes")
    todas_dirs = {d for est in ESTILOS.values() for d in est["direcciones"]}
    for r in f.get("reglas_globales") or []:
        nombre = next(iter(r)) if isinstance(r, dict) else r
        if nombre not in REGLAS_GLOBALES:
            e.append(f"reglas_globales: regla desconocida {nombre!r}{_sug(nombre, REGLAS_GLOBALES)}")
        elif nombre == "cara_visible_en":
            for d in r[nombre]:
                if d not in todas_dirs:
                    e.append(f"reglas_globales.cara_visible_en: dirección desconocida {d!r}")
    for i, ex in enumerate(f.get("excepciones") or []):
        if ex.get("regla") not in REGLAS_COMP:
            e.append(f"excepciones[{i}]: regla desconocida {ex.get('regla')!r}")
        if ex.get("componente") not in tipos_ficha:
            e.append(f"excepciones[{i}]: excepción sobre {ex.get('componente')!r}, que no está en componentes")
        if not ex.get("motivo"):
            e.append(f"excepciones[{i}]: falta 'motivo' (una desviación sin motivo es un error)")
        for d in ex.get("direcciones") or []:
            if d not in todas_dirs:
                e.append(f"excepciones[{i}]: dirección desconocida {d!r}")
    if (f["identidad"] or {}).get("referencias") and not f.get("creditos"):
        e.append("creditos: la ficha declara referencias y no tiene créditos")
    return e


def cargar(ruta_o_nombre, validar_=True, estilos=None):
    ruta = ruta_o_nombre if ruta_o_nombre.endswith((".yaml", ".yml")) else os.path.join(CARPETA, f"{ruta_o_nombre}.yaml")
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"no existe la ficha {ruta}")
    try:
        with open(ruta, encoding="utf-8") as fh:
            f = yaml.safe_load(fh)
    except yaml.YAMLError as ex:
        raise FichaInvalida([f"YAML mal formado en {ruta}: {ex}"])
    if validar_:
        errs = validar(f, estilos)
        if errs:
            raise FichaInvalida(errs)
    f["_ruta"] = ruta
    f["_nombre"] = os.path.splitext(os.path.basename(ruta))[0]
    return f
