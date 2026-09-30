"""Tests de consistencia de un personaje sobre todos sus cuadros renderizados (todas las poses y direcciones).
Cada test devuelve un Resultado con la evidencia exacta (pose/dirección/cuadro) para poder corregir."""
import contextlib
import functools
import io
import os
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

from .cuerpo import PADRE, SEGMENTOS
from .escala import alto_objetivo_px, celda
from .estilos import ESTILOS
from .paleta import hex_rgb, paleta_estilo
from .render3d import _oscurecer

CONTORNO = (16, 10, 24)
GUIAS = {"cara", "ojo_derecho", "ojo_izquierdo", "frente", "cintura", "sien_derecha", "sien_izquierda"}
# referencia de altura: lo que rodea la cabeza (vincha en la frente) se mide contra el centro de la cabeza, porque
# el ancla 'frente' se corre hacia la cámara con la trampa de la cara y el aro no
REF_GUIA = {"frente": "cabeza"}
FRENTE = {"stardew": "S", "volumen": "S", "lateral": None}


@dataclass
class Resultado:
    regla: str
    ok: bool
    detalle: str = ""
    evidencia: list = field(default_factory=list)
    omitido: bool = False


def _cuadros(todo):
    for frs in todo.values():
        yield from frs


def _specs(todo):
    return next(_cuadros(todo)).specs


def mascara(cuadro, comp_id):
    """Píxeles del componente, incluidas sus partes ('ojos@cara#ojo_izquierdo' es parte de 'ojos@cara')."""
    n = cuadro.buf["comp_nombres"]
    ids = [k for k, nombre in enumerate(n) if nombre == comp_id or nombre.startswith(comp_id + "#")]
    if not ids:
        return np.zeros(cuadro.buf["comp"].shape, bool)
    return np.isin(cuadro.buf["comp"], ids)


def partes(cuadro, comp_id):
    """El componente y cada una de sus partes, como 'rasgos' que se miden por separado."""
    subs = [nombre for nombre in cuadro.buf["comp_nombres"] if nombre.startswith(comp_id + "#")]
    return subs or [comp_id]


CABEZA = {"cabeza", "coronilla", "cara", "frente", "ojo_derecho", "ojo_izquierdo", "sien_derecha", "sien_izquierda",
          "nuca"}
TRONCO = {"torso", "pecho", "cintura", "cuello"}


def _anclas_anfitrionas(punto):
    """Anclas de las piezas que 'contienen' un punto: el codo está dentro del brazo, la frente dentro de la cabeza."""
    host = {punto} | {seg for seg, pts in SEGMENTOS.items() if punto in pts}
    if punto in CABEZA:
        host.add("cabeza")
    if punto in TRONCO:
        host.add("torso")
    return host


def ancla_visible(cuadro, ancla, tol=None):
    """Un ancla está a la vista si en el píxel donde se proyecta se ve la pieza que la contiene (el brazo para el
    codo, la cabeza para la frente) cerca de ella en profundidad. Si ahí se ve otra cosa (pelo, torso) está tapada
    por la pose: eso no es un olvido."""
    nombre = SEGMENTOS[ancla][1] if ancla in SEGMENTOS else ancla
    x, y, d = cuadro.anclas_px[nombre]
    ix, iy = int(round(x)), int(round(y))
    sol = cuadro.buf["solido"]
    if not (0 <= iy < sol.shape[0] and 0 <= ix < sol.shape[1]) or not sol[iy, ix]:
        return False
    tol = 3.0 * cuadro.escala if tol is None else tol
    if cuadro.buf["depth"][iy, ix] - d > tol:
        return False
    host = _anclas_anfitrionas(nombre)
    anfitriones = {s["id"] for s in cuadro.specs if s["ancla"] in host}
    k = cuadro.buf["comp"][iy, ix]
    visto = cuadro.buf["comp_nombres"][k] if k >= 0 else ""
    base = visto.split("#", 1)[0]
    return (not anfitriones or visto in anfitriones or base in anfitriones or base.endswith(f"@{ancla}")
            or visto.endswith(f"#{ancla}"))           # la parte que dibuja ese ancla (p. ej. ...#ojo_izquierdo)


def _exceptuado(ficha, regla, tipo, mira):
    return any(ex.get("regla") == regla and ex.get("componente") == tipo and mira in (ex.get("direcciones") or [])
               for ex in ficha.get("excepciones") or [])


def _res(regla, fallas, ok_txt):
    return Resultado(regla, not fallas, f"{len(fallas)} casos" if fallas else ok_txt, fallas[:25])


def t_visibilidad(ficha, todo):
    fallas = []
    for s in _specs(todo):
        reglas = set(s["reglas"])
        if not reglas & {"visible_si_ancla_visible", "siempre_visible"}:
            continue
        for c in _cuadros(todo):
            if any(_exceptuado(ficha, r, s["tipo"], c.mira) for r in reglas):
                continue
            if mascara(c, s["id"]).any():
                continue
            if "siempre_visible" in reglas or ancla_visible(c, s["ancla"]):
                fallas.append(f'{s["id"]}: invisible en {c.pose}/{c.mira}/{c.indice} con el ancla a la vista')
    return _res("visibilidad de componentes", fallas, "todos visibles cuando su ancla se ve")


def _dist_segmento(xs, ys, x0, y0, x1, y1):
    px, py = xs - x0, ys - y0
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    t = np.clip((px * dx + py * dy) / L2, 0, 1) if L2 > 1e-9 else np.zeros_like(px, float)
    return np.hypot(px - t * dx, py - t * dy)


def t_ausentes(ficha, todo):
    fallas = []
    for s in _specs(todo):
        for r in s["reglas"]:
            if not r.startswith("ausente_mas_alla_de_"):
                continue
            ancla = r[len("ausente_mas_alla_de_"):]
            padre = PADRE[ancla]
            for c in _cuadros(todo):
                ys, xs = np.nonzero(mascara(c, s["id"]))
                if not len(xs):
                    continue
                (x0, y0, _), (x1, y1, _) = c.anclas_px[padre], c.anclas_px[ancla]
                dist = _dist_segmento(xs.astype(float), ys.astype(float), x0, y0, x1, y1)
                lim = 2.6 * c.escala + 1.5
                if dist.max() > lim:
                    fallas.append(f'{s["id"]}: {int((dist > lim).sum())} px más allá de {ancla} en '
                                  f'{c.pose}/{c.mira}/{c.indice}')
    return _res("partes ausentes", fallas, "nada dibujado donde falta una parte")


def c_anclas(todo):
    return next(_cuadros(todo)).anclas_px


def t_lineas_guia(ficha, todo, tol=1.5):
    fallas = []
    rasgos = []
    for s in _specs(todo):
        if s["ancla"] in GUIAS:
            nombres = sorted({p for c in _cuadros(todo) for p in partes(c, s["id"])})
            for nm in nombres:
                sub = nm.split("#", 1)[1] if "#" in nm else ""
                # una parte que se llama como un ancla ('#ojo_izquierdo') se mide contra esa ancla
                rasgos.append((dict(s, id=nm, ancla=sub if sub in c_anclas(todo) else s["ancla"]), nm))
    for s, _ in rasgos:
        por, cuantos = {}, {}
        for c in _cuadros(todo):
            n = c.buf["comp_nombres"]
            ys = np.nonzero(c.buf["comp"] == n.index(s["id"]))[0] if s["id"] in n else np.array([])
            if len(ys) and ancla_visible(c, s["ancla"]):
                # altura del rasgo respecto de su ancla: en iso/cenital la fila de pantalla también depende de la
                # profundidad (la cara baja o sube al girar), pero el rasgo tiene que estar siempre igual respecto del ancla
                punto = REF_GUIA.get(s["ancla"], SEGMENTOS[s["ancla"]][1] if s["ancla"] in SEGMENTOS else s["ancla"])
                por.setdefault((c.pose, c.indice), {})[c.mira] = float(ys.mean()) - c.anclas_px[punto][1]
                cuantos.setdefault((c.pose, c.indice), {})[c.mira] = len(ys)
        # promedio de todos los cuadros de la pose por dirección: un rasgo de 1-3 px tiene ±1 px de redondeo por
        # cuadro; promediado se compensa y un corrimiento real (≥2 px) se sigue viendo
        agr, agr_n = {}, {}
        for (pose, i), alturas in por.items():
            for mira, y in alturas.items():
                agr.setdefault((pose, "todos"), {}).setdefault(mira, []).append(y)
                agr_n.setdefault((pose, "todos"), {}).setdefault(mira, []).append(cuantos[(pose, i)][mira])
        por = {k: {m: float(np.mean(ys)) for m, ys in d.items()} for k, d in agr.items()}
        cuantos = {k: {m: max(ns) for m, ns in d.items()} for k, d in agr_n.items()}
        for clave, alturas in list(por.items()):
            # solo donde se ve al menos el 40% de su mejor dirección: si apenas asoma, se ve su borde y el promedio se
            # corre; con más exigencia se pierden los perfiles (un ojo en vez de dos)
            tope = max(cuantos[clave].values())
            por[clave] = {m: y for m, y in alturas.items() if cuantos[clave][m] >= .4 * tope}
        for (pose, i), alturas in por.items():
            if len(alturas) > 1 and max(alturas.values()) - min(alturas.values()) > tol:
                fallas.append(f'{s["id"]}: altura respecto de su ancla distinta entre direcciones en {pose}/{i}: '
                              + ", ".join(f"{k} {y:.1f}" for k, y in alturas.items()))
    return _res("líneas guía", fallas, "rasgos a la misma altura en todas las direcciones")


def colores_permitidos(ficha, estilo):
    est = ESTILOS[estilo]
    ok = {CONTORNO}
    for tonos in paleta_estilo(ficha["paleta"], est).values():
        ok |= set(tonos)
        ok.add(_oscurecer(tonos[0], .8))
        ok.add(_oscurecer(tonos[0], est["render"].get("oscurecer", .55)))
    return ok


def t_paleta(ficha, estilo, todo):
    base = colores_permitidos(ficha, estilo)
    extra = set()
    for c in _cuadros(todo):
        a = np.array(c.img)
        cols = {tuple(int(x) for x in px) for px in a[a[..., 3] > 0][:, :3]}
        extra |= cols - base - c.buf["colores_detalle"]
    return Resultado("paleta", not extra, f"colores fuera de paleta: {sorted(extra)[:5]}" if extra
                     else "todos los colores salen de la paleta del personaje")


def t_tamano(ficha, estilo, todo):
    cel = celda(estilo, ficha["cuerpo"].get("clase_altura", "adulto"))
    fallas = []
    for c in _cuadros(todo):
        if c.img.size != (cel["cw"], cel["ch"]):
            fallas.append(f"{c.pose}/{c.mira}: celda {c.img.size} en vez de {(cel['cw'], cel['ch'])}")
            continue
        if c.bob != 0:
            continue
        alto = cel["gy"] - c.anclas_px["coronilla"][1]
        objetivo = alto_objetivo_px(estilo, ficha["cuerpo"].get("clase_altura", "adulto"))
        if abs(alto - objetivo) > 1:
            fallas.append(f"{c.pose}/{c.mira}/{c.indice}: mide {alto:.1f} px y su clase mide {objetivo}")
        filas = np.nonzero((np.array(c.img)[..., 3] > 0).any(1))[0]
        margen = 4 if ESTILOS[estilo]["vista"] == "iso" else 2      # en iso cada pie está a otra profundidad
        if len(filas) and not (cel["gy"] - 1 <= filas.max() <= cel["gy"] + margen):
            fallas.append(f"{c.pose}/{c.mira}/{c.indice}: los pies terminan en la fila {filas.max()}, pivote {cel['gy']}")
    return _res("tamaño y pivote", fallas, "mide lo que dice su clase y apoya en el pivote")


def t_recorte(todo):
    """Arriba no se toca nunca (ahí se cortan pelo y sombreros). A los costados puede llegar el contorno (Stardew
    también lo hace); es recorte solo si el cuerpo mismo llega al borde, porque entonces sigue más allá."""
    fallas = []
    for c in _cuadros(todo):
        op = np.array(c.img)[..., 3] > 0
        sol = c.buf["solido"]
        if op[0].any():
            fallas.append(f"{c.pose}/{c.mira}/{c.indice}: toca el borde superior")
        elif sol[:, 0].any() or sol[:, -1].any():
            fallas.append(f"{c.pose}/{c.mira}/{c.indice}: el cuerpo llega al borde lateral (queda cortado)")
    return _res("recorte", fallas, "nada cortado por los bordes de la celda")


def _regla_global(ficha, nombre):
    for r in ficha.get("reglas_globales") or []:
        if isinstance(r, dict) and nombre in r:
            return r[nombre]
    return None


def t_cara(ficha, estilo, todo):
    dirs = [d for d in (_regla_global(ficha, "cara_visible_en") or []) if d in ESTILOS[estilo]["direcciones"]]
    if not dirs:
        return Resultado("cara visible", True, "sin direcciones que pedir en este estilo: omitido", omitido=True)
    ids = [s["id"] for s in _specs(todo) if s["tipo"] in ("ojos", "visor")]
    fallas = [f"{c.pose}/{c.mira}/{c.indice}: no se ven ojos ni visor" for c in _cuadros(todo)
              if c.mira in dirs and not any(mascara(c, i).any() for i in ids)]
    return _res("cara visible", fallas, f"se lee la cara en {', '.join(dirs)}")


def t_simetria(ficha, estilo, todo):
    frente = FRENTE.get(estilo)
    if not frente:
        return Resultado("simetría", True, "vista sin frente: omitido", omitido=True)
    fallas = []
    grupos = {}
    for s in _specs(todo):
        if "simetrico" in s["reglas"]:
            grupos.setdefault(s["tipo"], []).append(s["id"])
    for tipo, ids in grupos.items():
        for c in todo.get(("quieto", frente), []):
            faltan = [i for i in ids if not mascara(c, i).any()]
            if faltan:
                fallas.append(f"{tipo}: de frente no se ve {', '.join(faltan)} (cuadro {c.indice})")
    return _res("simetría", fallas, "los componentes simétricos se ven de los dos lados")


def t_distinto(ficha):
    otros = _regla_global(ficha, "distinto_de") or []
    if not otros:
        return Resultado("distinto del elenco", True, "sin comparación pedida: omitido", omitido=True)
    from .ficha import cargar
    fallas = []
    mis_emi = [hex_rgb(m["base"]) for m in ficha["paleta"].values() if m.get("emisivo")]
    mis = [hex_rgb(m["base"]) for m in ficha["paleta"].values()]
    for nombre in otros:
        try:
            o = cargar(nombre, validar_=False)
        except FileNotFoundError:
            fallas.append(f"no existe la ficha {nombre!r} para comparar")
            continue
        sus_emi = [hex_rgb(m["base"]) for m in o["paleta"].values() if m.get("emisivo")]
        suyos = [hex_rgb(m["base"]) for m in o["paleta"].values()]
        dist = lambda p, q: float(np.linalg.norm(np.subtract(p, q)))
        if mis_emi and sus_emi and min(dist(p, q) for p in mis_emi for q in sus_emi) < 60:
            fallas.append(f"el color identitario se parece demasiado al de {nombre}")
        parecidos = sum(1 for p in mis if min(dist(p, q) for q in suyos) < 30)
        if parecidos > len(mis) / 2:
            fallas.append(f"{parecidos} de {len(mis)} colores casi iguales a los de {nombre}")
    return _res("distinto del elenco", fallas, f"se distingue de {', '.join(otros)}")


@functools.lru_cache(maxsize=None)
def _metricas_ref(ruta, celda, recorte, _mtime):
    """La referencia no cambia entre tests: se mide una vez por proceso (mtime invalida si se reemplaza)."""
    from .comparar_estilo import metricas
    return metricas(ruta, celda, recorte)[0]


def t_estilo(ficha, estilo, todo, carpeta):
    ref = ESTILOS[estilo].get("referencia")
    if not ref or not os.path.exists(ref["ruta"]):
        return Resultado("estilo vs referencia", True, "sin referencia local: omitido", omitido=True)
    from .comparar_estilo import comparar, metricas
    frames = [c.img for c in _cuadros(todo) if c.pose == "quieto"]
    cw, ch = frames[0].size
    tira = Image.new("RGBA", (cw * len(frames), ch), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        tira.paste(fr, (i * cw, 0))
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "_estilo.png")
    tira.save(ruta)
    r = _metricas_ref(ref["ruta"], tuple(ref["celda"]), tuple(ref["recorte"]) if ref.get("recorte") else None,
                      os.path.getmtime(ref["ruta"]))
    m, _ = metricas(ruta, (cw, ch))
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        fallas = comparar(r, m)
    evid = [f"{k}: referencia {a:.2f}, propio {b:.2f}" for k, a, b in fallas]
    if not ref.get("calibrada", False):
        # sin un control (dos personajes del mismo juego) no se sabe qué métricas miden estilo y cuáles personaje
        return Resultado("estilo vs referencia", True, "sin calibrar (advertencia, no bloquea): "
                         + (f"{len(fallas)} métricas difieren" if fallas else "todo coincide"), evid)
    return Resultado("estilo vs referencia", not fallas, salida.getvalue().strip(), evid)


def correr_tests(ficha, estilo, todo, carpeta):
    return [
        t_visibilidad(ficha, todo), t_ausentes(ficha, todo), t_lineas_guia(ficha, todo),
        t_paleta(ficha, estilo, todo), t_tamano(ficha, estilo, todo), t_recorte(todo),
        t_cara(ficha, estilo, todo), t_simetria(ficha, estilo, todo), t_distinto(ficha),
        t_estilo(ficha, estilo, todo, carpeta),
    ]


def informe_md(ficha, estilo, resultados):
    ok = sum(1 for r in resultados if r.ok and not r.omitido)
    mal = sum(1 for r in resultados if not r.ok)
    om = sum(1 for r in resultados if r.omitido)
    L = [f"# Informe de consistencia — {ficha['identidad']['nombre']} ({estilo})", "",
         f"Resultado: **{'APROBADO' if not mal else 'CON FALLAS'}** — {ok} ok, {mal} fallas, {om} omitidos", "",
         "| Regla | Estado | Detalle |", "|---|---|---|"]
    for r in resultados:
        estado = "omitido" if r.omitido else ("✓" if r.ok else "✗")
        primera = r.detalle.splitlines()[0] if r.detalle else ""
        L.append(f"| {r.regla} | {estado} | {primera.replace('|', '/')} |")
    for r in resultados:
        if r.evidencia:
            L += ["", f"## {r.regla}", *[f"- {e}" for e in r.evidencia]]
    return "\n".join(L) + "\n"
