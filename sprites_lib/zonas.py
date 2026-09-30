"""Zonas del cuerpo por cuadro: dónde está cada parte (cabeza, cada ojo, cada brazo...) y cómo cambia de un cuadro
al siguiente, como TEXTO/JSON para que quien revisa (un LLM que ve mal el detalle de 1 px) lea números en vez de
mirar imágenes.

Clasificación de cada píxel (decisión: por los buffers del render, no por el color de la imagen final):
el render sombrea (3 tonos por material), agrega contorno y dibuja ojos/cejas/boca como detalles con colores del
estilo, así que el color plano de la skin no llega igual a la imagen. En cambio los buffers de `armado.render_cuadro`
dicen, píxel por píxel, qué componente (`comp`), qué pieza (`pieza`) y qué material (`mat`) quedaron a la vista:
  - rasgos: por la parte del componente (`ojos@cara#ojo_izquierdo`, `rostro@cara#ceja_derecha`, `#boca`, `#nariz`);
  - brazo/pierna: pieza 0 = brazo/pierna, pieza 1 = mano/pie (el puño y el pie son piezas propias);
  - cabeza: pieza 1 = orejas (cada una la del lado de la sien más cercana); el resto de la cabeza y el torso se
    separan por material de la skin de zonas (cabeza_frente/cabeza_resto, torso_frente/torso_espalda y el cuello,
    que es piel dentro del torso);
  - otra ficha/skin (modo 'componentes'): cada componente va a la familia de su ancla (cabeza, torso, brazo_x...) y
    dentro de la familia cada píxel toma la zona del muñeco de zonas en el mismo píxel (o el más cercano de esa
    familia): mismo esqueleto y pose, así que la frontera frente/espalda es la del muñeco. Lo que no tiene familia
    (un accesorio en un ancla desconocida) va a 'otro' y se avisa.
Contorno: el contorno interior (líneas entre piezas) ya es un píxel de la pieza en los buffers. El contorno exterior
(el anillo de 1 px fuera del sólido) se asigna a la zona del vecino sólido (4-vecindad) más cercano a cámara, así la
bbox es la silueta que se ve; los rasgos (ojos, cejas, boca) nunca se quedan con contorno: va a la pieza de al lado
o, si solo toca un rasgo, a cabeza_frente. Cada píxel opaco queda en exactamente una zona. El JSON cuenta aparte, por cuadro,
cuántos px de contorno exterior hay (`contorno`).

La plantilla de colores planos (`COLORES`, un color distinto por zona) sale de esta clasificación: `imagen()`.

Uso:  .venv/bin/python -m sprites_lib.zonas --anim caminar_lpc --estilo stardew8 [--dirs S,SE] [--cuadros 0,1,2]
          [--skin skins/<personaje>.png | --ficha nombre] [--json] [--salida ruta.json] [--png]
      → salida/zonas/<estilo>/<anim>.json y .md (el informe de texto también sale por stdout)
"""

import argparse
import json
import os
import re
import sys

import numpy as np

# ------------------------------------------------------------------ umbrales (px de juego; fáciles de cambiar)
UMBRALES = {
    "salto_tronco_dy": 1.0,  # cabeza, cuello, torso y rasgos: el rebote de caminar es de 1 px en y
    "salto_tronco_dx": 1.0,  # ... y no deberían correrse de costado
    "salto_extremidad": 4.0,  # brazos, manos, piernas, pies: distancia del centro entre cuadros consecutivos
    "cambio_px": 0.35,  # cambio relativo de px de una zona entre cuadros consecutivos
    "cambio_px_min": 6,  # ... solo si la zona tiene al menos estos px (las de 1-3 px saltan siempre)
    "sep_ojos": (
        2.0,
        6.0,
    ),  # distancia horizontal entre centros de los ojos (si se ven los dos)
    "ojo_borde_min": 1,  # px de cabeza entre un ojo y el borde de la silueta de la cabeza
    "cabeza_dirs": 2,  # ancho/alto de la cabeza: diferencia máxima con la mediana de las direcciones
    "cabeza_cuadros": 1,  # ... y con la mediana de los cuadros de la misma dirección
    "lado_min_px": 1.5,  # el ancla raíz tiene que estar al menos a esto de la línea central para exigir lado
    "lado_muerto": 0.5,  # zona a menos de esto de la línea central: no tiene lado
    "quieto_px": 0.2,  # en el informe, Δ con |dx|,|dy| <= esto y |dpx| <= 1 se escribe '·'
    "poco_px": 1.0,  # en la tabla completa, zonas sin alertas con Δ máximo <= esto van a una línea corta
    "alertas_por_dir": 25,  # tope de líneas de alerta por dirección en el informe (el JSON las tiene todas)
}
SEV = {3: "ALTA", 2: "MEDIA", 1: "baja"}
# umbrales en px que crecen con el tamaño del personaje (están calibrados para stardew8, adulto de 26 px)
ESCALABLES = (
    "salto_tronco_dy",
    "salto_tronco_dx",
    "salto_extremidad",
    "cabeza_dirs",
    "cabeza_cuadros",
    "lado_min_px",
)


def _umbrales(res):
    k = res.get("escala_umbral", 1.0)
    return (
        UMBRALES
        if k == 1.0
        else {n: (v * k if n in ESCALABLES else v) for n, v in UMBRALES.items()}
    )


# ------------------------------------------------------------------ zonas y colores de la plantilla
DER = (
    "oreja_derecha",
    "ojo_derecho",
    "ceja_derecha",
    "brazo_derecho",
    "mano_derecha",
    "pierna_derecha",
    "pie_derecho",
)
IZQ = tuple(
    z.replace("derecha", "izquierda").replace("derecho", "izquierdo") for z in DER
)
ZONAS = (
    "cabeza_frente",
    "cabeza_resto",
    "oreja_derecha",
    "oreja_izquierda",
    "ojo_derecho",
    "ojo_izquierdo",
    "ceja_derecha",
    "ceja_izquierda",
    "boca_nariz",
    "cuello",
    "torso_frente",
    "torso_espalda",
    "brazo_derecho",
    "mano_derecha",
    "pierna_derecha",
    "pie_derecho",
    "brazo_izquierdo",
    "mano_izquierda",
    "pierna_izquierda",
    "pie_izquierdo",
    "otro",
)
COLORES = {  # derecha cálidos, izquierda fríos (los de skins.COLORES_ZONAS más los rasgos, orejas y cuello)
    "cabeza_frente": "#ffe0b2",
    "cabeza_resto": "#6d4c41",
    "oreja_derecha": "#ff7043",
    "oreja_izquierda": "#26a69a",
    "ojo_derecho": "#ff1744",
    "ojo_izquierdo": "#2979ff",
    "ceja_derecha": "#c0ca33",
    "ceja_izquierda": "#7e57c2",
    "boca_nariz": "#f06292",
    "cuello": "#bcaaa4",
    "torso_frente": "#fafafa",
    "torso_espalda": "#546e7a",
    "brazo_derecho": "#e53935",
    "mano_derecha": "#ff9800",
    "pierna_derecha": "#ad1457",
    "pie_derecho": "#fdd835",
    "brazo_izquierdo": "#1e88e5",
    "mano_izquierda": "#00bcd4",
    "pierna_izquierda": "#3949ab",
    "pie_izquierdo": "#43a047",
    "otro": "#ff00ff",
}
RASGOS = (
    "ojo_derecho",
    "ojo_izquierdo",
    "ceja_derecha",
    "ceja_izquierda",
    "boca_nariz",
)
CABEZA = ("cabeza_frente", "cabeza_resto") + RASGOS  # la cabeza "medida" (sin orejas)
TRONCO = CABEZA + (
    "oreja_derecha",
    "oreja_izquierda",
    "cuello",
    "torso_frente",
    "torso_espalda",
)
FAM_CABEZA, FAM_TORSO = (
    ("cabeza_frente", "cabeza_resto"),
    ("cuello", "torso_frente", "torso_espalda"),
)
PARTES = {
    "ojo_izquierdo": "ojo_izquierdo",
    "ojo_derecho": "ojo_derecho",
    "ceja_izquierda": "ceja_izquierda",
    "ceja_derecha": "ceja_derecha",
    "boca": "boca_nariz",
    "nariz": "boca_nariz",
}
# ancla de un componente → familia de zonas (para accesorios y componentes no base en modo 'componentes')
ANCLA_FAM = {
    **{
        a: FAM_CABEZA
        for a in (
            "cabeza",
            "coronilla",
            "nuca",
            "frente",
            "sien_derecha",
            "sien_izquierda",
        )
    },
    "cara": ("boca_nariz",),
    "ojo_derecho": ("ojo_derecho",),
    "ojo_izquierdo": ("ojo_izquierdo",),
    **{a: FAM_TORSO for a in ("torso", "pecho", "cintura", "cuello")},
}
for _l, _m in (("derecho", "derecha"), ("izquierdo", "izquierda")):
    for _a in ("brazo", "hombro", "codo", "antebrazo"):
        ANCLA_FAM[f"{_a}_{_l}"] = (f"brazo_{_l}", f"mano_{_m}")
    ANCLA_FAM[f"muneca_{_m}"] = ANCLA_FAM[f"mano_{_m}"] = (f"brazo_{_l}", f"mano_{_m}")
    for _a in ("pierna", "cadera"):
        ANCLA_FAM[f"{_a}_{_m}"] = (f"pierna_{_m}", f"pie_{_l}")
    for _a in ("rodilla", "tobillo"):
        ANCLA_FAM[f"{_a}_{_m if _a == 'rodilla' else _l}"] = (
            f"pierna_{_m}",
            f"pie_{_l}",
        )
    ANCLA_FAM[f"pie_{_l}"] = (f"pie_{_l}",)
# lado: ancla raíz que dice de qué lado de la línea central tiene que estar cada zona, y qué línea usar
RAIZ = {}
for _z in DER + IZQ:
    _l = "derecho" if _z in DER else "izquierdo"
    _m = "derecha" if _l == "derecho" else "izquierda"
    RAIZ[_z] = {
        "oreja": f"sien_{_m}",
        "ojo": f"ojo_{_l}",
        "ceja": f"ojo_{_l}",
        "brazo": f"hombro_{_l}",
        "mano": f"hombro_{_l}",
        "pierna": f"cadera_{_m}",
        "pie": f"cadera_{_m}",
    }[_z.split("_")[0]]
CARA_OCULTA = ("N", "NE", "NW")


def _rgb(h):
    return tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))


def _mover(a, dy, dx, relleno):
    out = np.full_like(a, relleno)
    h, w = a.shape
    ys, yd = (
        (slice(0, h - dy), slice(dy, h))
        if dy >= 0
        else (slice(-dy, h), slice(0, h + dy))
    )
    xs, xd = (
        (slice(0, w - dx), slice(dx, w))
        if dx >= 0
        else (slice(-dx, w), slice(0, w + dx))
    )
    out[yd, xd] = a[ys, xs]
    return out


# ------------------------------------------------------------------ personaje por defecto: el muñeco de zonas
def _ruta_plantilla():
    from .skins import plantilla_zonas

    ruta = os.path.join("salida", "zonas", "skin_zonas.png")  # no pisa skins/zonas.png
    if not os.path.exists(ruta):
        plantilla_zonas(ruta)
    return ruta


def ficha_plantilla():
    from . import skins

    return skins.ficha(_ruta_plantilla(), nombre="zonas")


def _mat_zona():
    from .skins import COLORES_ZONAS, material

    out = {}
    for z in ("cabeza_frente", "cabeza_resto", "torso_frente", "torso_espalda"):
        m = material(_rgb(COLORES_ZONAS[z]))
        out[m] = out[m + "_b"] = z
    return out


# ------------------------------------------------------------------ clasificación
def clasificar(cuadro, ficha, estilo, plantilla=None):
    """Mapa de zonas del cuadro: array (alto, ancho) con el índice en ZONAS (-1 = transparente) y la máscara del
    contorno exterior. plantilla=None: la ficha es el muñeco de zonas (frente/espalda por material); si no, es el
    mapa de zonas del muñeco de zonas en el mismo cuadro (frente/espalda prestado de ahí)."""
    from .estilos import ESTILOS
    from .paleta import paleta_estilo

    buf = cuadro.buf
    comp, pieza, mat, solido, depth = (
        buf["comp"],
        buf["pieza"],
        buf["mat"],
        buf["solido"],
        buf["depth"],
    )
    mats = list(paleta_estilo(ficha["paleta"], ESTILOS[estilo]))
    mat_zona = _mat_zona()
    specs = {s["id"]: s for s in cuadro.specs}
    Z = {z: i for i, z in enumerate(ZONAS)}
    zm = np.full(comp.shape, -1)
    familias = []  # (máscara, familia) a resolver por material o por plantilla
    for k, nombre in enumerate(buf["comp_nombres"]):
        m = (comp == k) & solido
        if not nombre or not m.any():
            continue
        base, _, parte = nombre.partition("#")
        if parte in PARTES:
            zm[m] = Z[PARTES[parte]]
            continue
        s = specs.get(base)
        if s is None:
            zm[m] = Z["otro"]
            continue
        tipo, ancla = s["tipo"], s["ancla"]
        kp = pieza - s["pieza_base"]
        if tipo in ("cabeza_skin", "cabeza_humana"):
            orejas = m & (kp == 1)
            if orejas.any():
                ys, xs = np.nonzero(orejas)
                sd, si = (
                    cuadro.anclas_px["sien_derecha"],
                    cuadro.anclas_px["sien_izquierda"],
                )
                dd = (xs - sd[0]) ** 2 + (ys - sd[1]) ** 2
                di = (xs - si[0]) ** 2 + (ys - si[1]) ** 2
                zm[ys, xs] = np.where(
                    dd <= di, Z["oreja_derecha"], Z["oreja_izquierda"]
                )
            familias.append((m & (kp != 1), FAM_CABEZA))
        elif tipo in ("brazo_skin", "brazo_humano", "pierna_skin", "pierna_humana"):
            fam = ANCLA_FAM[ancla]
            zm[m & (kp == 0)] = Z[fam[0]]
            zm[m & (kp != 0)] = Z[fam[1]]
        elif tipo in ("torso_skin", "torso_humano"):
            familias.append((m, FAM_TORSO))
        elif ancla in ANCLA_FAM:
            familias.append((m, ANCLA_FAM[ancla]))
        else:
            zm[m] = Z["otro"]
    for m, fam in familias:
        if len(fam) == 1:
            zm[m] = Z[fam[0]]
        elif plantilla is None:  # muñeco de zonas: el material dice la zona
            ys, xs = np.nonzero(m)
            for y, x in zip(ys, xs):
                nm = mats[mat[y, x]] if mat[y, x] >= 0 else ""
                z = mat_zona.get(nm)
                if (
                    fam is FAM_TORSO and z == "cabeza_frente"
                ):  # piel dentro del torso = cuello
                    z = "cuello"
                zm[y, x] = Z[z] if z in fam else Z["otro"]
        else:  # otra ficha: la zona del muñeco de zonas en ese píxel (o la más cercana)
            ys, xs = np.nonzero(m)
            ids = [Z[z] for z in fam]
            cy, cx = np.nonzero(np.isin(plantilla, ids))
            if not len(cy):
                zm[ys, xs] = ids[0]
                continue
            d = (ys[:, None] - cy[None]) ** 2 + (xs[:, None] - cx[None]) ** 2
            zm[ys, xs] = plantilla[cy[d.argmin(1)], cx[d.argmin(1)]]
    zm[solido & (zm < 0)] = Z["otro"]
    # contorno exterior: zona del vecino sólido más cercano a cámara
    alfa = np.array(cuadro.img.convert("RGBA"))[..., 3] > 0
    anillo = alfa & ~solido
    # (los rasgos de 1-3 px no se quedan con el contorno: es el de la cabeza que tienen debajo)
    mejor_d = np.full(comp.shape, -np.inf)
    rasgo = np.isin(zm, [Z[z] for z in RASGOS])
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        vz, vd = (
            _mover(zm, dy, dx, -1),
            _mover(np.where(solido & ~rasgo, depth, -np.inf), dy, dx, -np.inf),
        )
        ok = anillo & (vz >= 0) & (vd > mejor_d)
        zm[ok], mejor_d[ok] = vz[ok], vd[ok]
    zm[anillo & (zm < 0)] = Z[
        "cabeza_frente"
    ]  # anillo cuyo único vecino sólido es un rasgo
    return zm, anillo


def medir(zm):
    """{zona: {px, bbox [x0,y0,x1,y1], centro [x,y]} | None} para todas las ZONAS ('otro' incluido)."""
    out = {}
    for i, z in enumerate(ZONAS):
        ys, xs = np.nonzero(zm == i)
        out[z] = (
            None
            if not len(xs)
            else {
                "px": int(len(xs)),
                "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                "centro": [round(float(xs.mean()), 1), round(float(ys.mean()), 1)],
            }
        )
    return out


def _union(zm, zonas):
    ys, xs = np.nonzero(np.isin(zm, [ZONAS.index(z) for z in zonas]))
    return (
        None
        if not len(xs)
        else (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    )


def _ojo_borde(zm, anillo, ojo):
    """px de cabeza (sin orejas, sin contorno exterior) entre el ojo y el borde de la silueta, del lado más cercano."""
    cab = np.isin(zm, [ZONAS.index(z) for z in CABEZA]) & ~anillo
    oj = zm == ZONAS.index(ojo)
    mejor = None
    for y in np.unique(np.nonzero(oj)[0]):
        xs, xo = np.nonzero(cab[y])[0], np.nonzero(oj[y])[0]
        g = min(int(xo.min() - xs.min()), int(xs.max() - xo.max()))
        mejor = g if mejor is None else min(mejor, g)
    return mejor


# ------------------------------------------------------------------ análisis de una animación
def analizar(
    anim="caminar_lpc", estilo="stardew8", dirs=None, cuadros=None, ficha=None
):
    """Dict con las zonas por dirección y cuadro, las alertas y los datos del resumen. ficha=None: muñeco de zonas."""
    from .armado import render_cuadro
    from .estilos import ESTILOS
    from .poses import POSES, loop

    tpl = ficha_plantilla()
    modo = "plantilla" if ficha is None else "componentes"
    ficha = tpl if ficha is None else ficha
    dirs = list(dirs or ESTILOS[estilo]["direcciones"])
    ps = list(range(POSES[anim]["n"])) if cuadros is None else list(cuadros)
    from .escala import alto_objetivo_px

    res = {
        "escala_umbral": round(
            alto_objetivo_px(estilo) / alto_objetivo_px("stardew8"), 2
        ),
        "anim": anim,
        "estilo": estilo,
        "personaje": ficha.get("identidad", {}).get("nombre", "?"),
        "modo": modo,
        "loop": bool(loop(anim)) and cuadros is None,
        "zonas": list(ZONAS),
        "umbrales": UMBRALES,
        "direcciones": {},
    }
    extra = {}
    for d in dirs:
        lista = []
        for p in ps:
            c = render_cuadro(ficha, estilo, anim, p, d)
            plantilla = None
            if modo == "componentes":
                plantilla = clasificar(
                    render_cuadro(tpl, estilo, anim, p, d), tpl, estilo
                )[0]
            zm, anillo = clasificar(c, ficha, estilo, plantilla)
            sx, sy, _ = c.anclas_px["suelo"]
            lista.append(
                {
                    "cuadro": p,
                    "pivote": [round(sx), round(sy)],
                    "celda": list(c.img.size),
                    "contorno": int(anillo.sum()),
                    "zonas": medir(zm),
                }
            )
            extra[(d, p)] = dict(
                zm=zm,
                anillo=anillo,
                anclas=c.anclas_px,
                cabeza=_union(zm, CABEZA),
                img=np.array(c.img.convert("RGBA")),
                solido=c.buf["solido"],
                specs=c.specs,
                borde={
                    o: _ojo_borde(zm, anillo, o)
                    for o in ("ojo_derecho", "ojo_izquierdo")
                    if (zm == ZONAS.index(o)).any()
                },
            )
        res["direcciones"][d] = {"cuadros": lista}
    res["alertas"] = alertas(res, extra)
    res["_extra"] = extra
    return res


def _al(sev, d, p, zona, tipo, valor, umbral, texto):
    return {
        "sev": sev,
        "dir": d,
        "cuadro": p,
        "zona": zona,
        "tipo": tipo,
        "valor": valor,
        "umbral": umbral,
        "texto": texto,
    }


def _pares(n, en_loop):
    return [(i, i + 1) for i in range(n - 1)] + (
        [(n - 1, 0)] if en_loop and n > 2 else []
    )


FALSAS = {
    "diminuta": "zona de <= %d px que aparece/desaparece: cuantización del sombreado, no un defecto",
    "perfil": "en E/W el ojo cercano está en el borde de la silueta por diseño del perfil",
    "area_visible": "el centro se mueve porque cambió el área visible (>25 %% de px: brazo que tapa o textura que rota), no la pieza",
    "extremidad_en_movimiento": "brazo/mano/pierna/pie: su área visible cambia al caminar (se gira, se tapa); es esperable",
    "tapada_por_su_par": "la mano/pie desaparece justo donde está su par: lo tapa la otra pierna/brazo al cruzarse",
    "cambio_minimo": "la zona cambió <= 2 px en absoluto: en zonas chicas (orejas) eso ya pasa el 35 %% por el rebote",
    "pie_al_piso": "contorno del pie tocando el borde de abajo: el pivote está a 2 px del borde por diseño",
}


def _px_torso_cambia(cs, idx, m, rel=0.15):
    """El torso visible (frente + espalda) cambia >= 15 % de px entre los dos cuadros: el brazo lo tapa o lo destapa."""

    def px(i):
        z = cs[idx[int(i)]]["zonas"]
        return sum(z[k]["px"] for k in ("torso_frente", "torso_espalda") if z[k])

    a, b = px(m.group(1)), px(m.group(2))
    return a > 0 and abs(b - a) / a >= rel


def _tapada_por_su_par(cs, idx, m, zona, dist=3.5):
    """Mano o pie que desaparece y su par (izquierda/derecha) está a <= 3,5 px de donde estaba: lo tapa la otra pierna/brazo."""
    if zona.split("_")[0] not in ("mano", "pie"):
        return False
    par = (
        zona.replace("derecha", "izquierda").replace("derecho", "izquierdo")
        if "der" in zona
        else zona.replace("izquierda", "derecha").replace("izquierdo", "derecho")
    )
    antes = cs[idx[int(m.group(1))]]["zonas"].get(zona)
    otro = cs[idx[int(m.group(2))]]["zonas"].get(par)
    return bool(
        antes
        and otro
        and np.hypot(
            antes["centro"][0] - otro["centro"][0],
            antes["centro"][1] - otro["centro"][1],
        )
        <= dist
    )


def marcar_falsas(out, res):
    """Agrega a cada alerta el campo 'fp' (None = por revisar; texto = falsa conocida y por qué). Las falsas NO se
    borran: se muestran aparte, con su motivo, para poder discutir la regla. Cada regla salió de mirar los datos
    (ver .claude/skills/sprite-revisar). Agregar una regla acá solo si se comprobó que la alerta no es un defecto."""
    U = _umbrales(res)
    for a in out:
        a["fp"] = None
        d, p = a["dir"], a["cuadro"]
        cs = res["direcciones"][d]["cuadros"] if d in res["direcciones"] else []
        idx = {c["cuadro"]: i for i, c in enumerate(cs)}
        m = re.search(r"c(\d+)(?:→| a )c(\d+)", a["texto"] or "")
        if m and p is not None and int(m.group(1)) in idx and int(m.group(2)) in idx:
            va = cs[idx[int(m.group(1))]]["zonas"].get(a["zona"])
            vb = cs[idx[int(m.group(2))]]["zonas"].get(a["zona"])
            pxa, pxb = (va["px"] if va else 0), (vb["px"] if vb else 0)
        else:
            pxa = pxb = None
        if (
            a["tipo"] in ("aparece", "desaparece")
            and pxa is not None
            and max(pxa, pxb) <= U["cambio_px_min"]
        ):
            a["fp"] = "diminuta"
        elif a["tipo"] == "ojo_borde" and d in ("E", "W"):
            a["fp"] = "perfil"
        elif (
            a["tipo"] == "salto"
            and a["zona"].startswith("torso")
            and m
            and _px_torso_cambia(cs, idx, m)
        ):
            a["fp"] = "area_visible"
        elif a["tipo"] == "salto" and pxa and abs(pxb - pxa) / max(pxa, 1) > 0.25:
            a["fp"] = "area_visible"
        elif a["tipo"] == "cambio_px" and pxa is not None and abs(pxb - pxa) <= 2:
            a["fp"] = "cambio_minimo"
        elif (
            a["tipo"] == "cambio_px"
            and a["zona"].startswith("torso")
            and m
            and _px_torso_cambia(cs, idx, m)
        ):
            a["fp"] = "area_visible"
        elif (
            a["tipo"] == "desaparece"
            and m
            and _tapada_por_su_par(cs, idx, m, a["zona"])
        ):
            a["fp"] = "tapada_por_su_par"
        elif a["tipo"] == "cambio_px" and a["zona"].split("_")[0] in (
            "brazo",
            "mano",
            "pierna",
            "pie",
        ):
            a["fp"] = "extremidad_en_movimiento"
        elif a["tipo"] == "borde_abajo":
            a["fp"] = "pie_al_piso"


def alertas(res, extra):
    U, out = _umbrales(res), []
    dirs = list(res["direcciones"])
    cab_dir = {}
    piv = {}
    for d in dirs:
        cs = res["direcciones"][d]["cuadros"]
        n = len(cs)
        pares = _pares(n, res["loop"])
        for z in ZONAS:
            vals = [c["zonas"][z] for c in cs]
            presente = [v is not None for v in vals]
            if z == "otro":
                for c, v in zip(cs, vals):
                    if v:
                        out.append(
                            _al(
                                1,
                                d,
                                c["cuadro"],
                                z,
                                "sin_zona",
                                v["px"],
                                0,
                                f"{v['px']} px sin zona (bbox {v['bbox']})",
                            )
                        )
                continue
            if z in RASGOS[:2] and d in CARA_OCULTA:
                for c, v in zip(cs, vals):
                    if v:
                        out.append(
                            _al(
                                3,
                                d,
                                c["cuadro"],
                                z,
                                "ojo_de_espaldas",
                                v["px"],
                                0,
                                f"ojo visible de espaldas ({v['px']} px en {v['centro']})",
                            )
                        )
            if not any(presente):
                continue
            for a, b in pares:
                va, vb, pa, pb = vals[a], vals[b], cs[a]["cuadro"], cs[b]["cuadro"]
                if (va is None) != (vb is None):
                    ojo = z.startswith("ojo")
                    sev = (
                        2 if ojo else (3 if z in CABEZA + FAM_TORSO[1:] else 1)
                    )  # cuello/orejas: se tapan solos
                    que = "aparece" if va is None else "desaparece"
                    out.append(
                        _al(
                            sev,
                            d,
                            pb,
                            z,
                            "ojo_parpadea" if ojo else que,
                            vb["px"] if vb else 0,
                            0,
                            f"{que} de c{pa} a c{pb}",
                        )
                    )
                    continue
                if va is None:
                    continue
                dx, dy = (
                    vb["centro"][0] - va["centro"][0],
                    vb["centro"][1] - va["centro"][1],
                )
                if z in TRONCO:
                    # el rebote del cuerpo mueve el ancla de la zona: solo cuenta lo que se mueve de más que ella
                    anc = (
                        "cuello"
                        if z == "cuello"
                        else ("torso" if z.startswith("torso") else "cabeza")
                    )
                    aa, ab = (
                        extra[(d, pa)]["anclas"][anc],
                        extra[(d, pb)]["anclas"][anc],
                    )
                    rdx, rdy = dx - (ab[0] - aa[0]), dy - (ab[1] - aa[1])
                    if (
                        abs(rdy) > U["salto_tronco_dy"] + 1e-6
                        or abs(rdx) > U["salto_tronco_dx"] + 1e-6
                    ):
                        out.append(
                            _al(
                                2,
                                d,
                                pb,
                                z,
                                "salto",
                                [round(rdx, 1), round(rdy, 1)],
                                [U["salto_tronco_dx"], U["salto_tronco_dy"]],
                                f"salto c{pa}→c{pb} dx={rdx:+.1f} dy={rdy:+.1f} (ya sin el movimiento de su ancla) > ±{U['salto_tronco_dx']:g},±{U['salto_tronco_dy']:g}",
                            )
                        )
                elif np.hypot(dx, dy) > U["salto_extremidad"]:
                    out.append(
                        _al(
                            1,
                            d,
                            pb,
                            z,
                            "salto",
                            round(float(np.hypot(dx, dy)), 1),
                            U["salto_extremidad"],
                            f"salto c{pa}→c{pb} {np.hypot(dx, dy):.1f} px > {U['salto_extremidad']:g}",
                        )
                    )
                ca, cb = va["px"], vb["px"]
                if (
                    max(ca, cb) >= U["cambio_px_min"]
                    and abs(cb - ca) / max(ca, 1) > U["cambio_px"]
                ):
                    out.append(
                        _al(
                            1,
                            d,
                            pb,
                            z,
                            "cambio_px",
                            [ca, cb],
                            U["cambio_px"],
                            f"px c{pa}→c{pb} {ca}→{cb} ({(cb - ca) / ca:+.0%}) > ±{U['cambio_px']:.0%}",
                        )
                    )
            # lado respecto de la línea central (cabeza para rasgos y orejas, torso para extremidades)
            if z in RAIZ:
                lados = []
                for c, v in zip(cs, vals):
                    an = extra[(d, c["cuadro"])]["anclas"]
                    linea = an[
                        "cabeza"
                        if z.split("_")[0] in ("ojo", "ceja", "oreja")
                        else "torso"
                    ][0]
                    r = an[RAIZ[z]][0] - linea
                    esp = 0 if abs(r) < U["lado_min_px"] else int(np.sign(r))
                    lado = (
                        None
                        if v is None
                        else (
                            0
                            if abs(v["centro"][0] - linea) < U["lado_muerto"]
                            else int(np.sign(v["centro"][0] - linea))
                        )
                    )
                    lados.append(
                        (
                            lado,
                            esp,
                            None if v is None else round(v["centro"][0] - linea, 1),
                        )
                    )
                for a, b in pares:
                    (la, _, _), (lb, eb, xb) = lados[a], lados[b]
                    if la and lb and la != lb and eb and lb != eb:
                        out.append(
                            _al(
                                3,
                                d,
                                cs[b]["cuadro"],
                                z,
                                "lado_cruzado",
                                xb,
                                U["lado_min_px"],
                                f"cruza la línea central c{cs[a]['cuadro']}→c{cs[b]['cuadro']}: queda a "
                                f"{xb:+.1f} px y su ancla {RAIZ[z]} está del otro lado",
                            )
                        )
        # ojos: separación y distancia al borde de la cabeza
        for c in cs:
            zz, p = c["zonas"], c["cuadro"]
            if zz["ojo_derecho"] and zz["ojo_izquierdo"]:
                sep = abs(
                    zz["ojo_izquierdo"]["centro"][0] - zz["ojo_derecho"]["centro"][0]
                )
                lo, hi = U["sep_ojos"]
                if not lo <= sep <= hi:
                    out.append(
                        _al(
                            2,
                            d,
                            p,
                            "ojos",
                            "sep_ojos",
                            round(sep, 1),
                            [lo, hi],
                            f"separación de ojos {sep:.1f} fuera de [{lo:g},{hi:g}]",
                        )
                    )
            for o, g in extra[(d, p)]["borde"].items():
                if g is not None and g < U["ojo_borde_min"]:
                    out.append(
                        _al(
                            2,
                            d,
                            p,
                            o,
                            "ojo_borde",
                            g,
                            U["ojo_borde_min"],
                            f"ojo a {g} px del borde de la cabeza (mín {U['ojo_borde_min']})",
                        )
                    )
            e = extra[(d, p)]
            if e["cabeza"]:
                x0, y0, x1, y1 = e["cabeza"]
                cab_dir.setdefault(d, []).append((p, x1 - x0 + 1, y1 - y0 + 1))
            piv[(d, p)] = tuple(c["pivote"])
            # borde de la celda
            zm = e["zm"]
            h, w = zm.shape
            for lado, sl in (
                ("arriba", zm[0]),
                ("abajo", zm[h - 1]),
                ("izquierda", zm[:, 0]),
                ("derecha", zm[:, w - 1]),
            ):
                ids = sorted({int(i) for i in sl[sl >= 0]})
                if ids:
                    # arriba se cortan pelo y sombreros (grave); abajo es el contorno del pie junto al piso (leve)
                    out.append(
                        _al(
                            {"arriba": 3, "abajo": 1}.get(lado, 2),
                            d,
                            p,
                            ",".join(ZONAS[i] for i in ids),
                            f"borde_{lado}",
                            int((sl >= 0).sum()),
                            0,
                            f"{int((sl >= 0).sum())} px opacos tocan el borde {lado}",
                        )
                    )
    # cabeza: entre cuadros de una dirección y entre direcciones
    med_dir = {}
    for d, lst in cab_dir.items():
        mw, mh = (
            float(np.median([w for _, w, _ in lst])),
            float(np.median([h for _, _, h in lst])),
        )
        med_dir[d] = (mw, mh)
        for p, w, h in lst:
            if abs(w - mw) > U["cabeza_cuadros"] or abs(h - mh) > U["cabeza_cuadros"]:
                out.append(
                    _al(
                        2,
                        d,
                        p,
                        "cabeza",
                        "cabeza_tamano_cuadros",
                        [w, h],
                        U["cabeza_cuadros"],
                        f"cabeza {w}x{h} vs mediana de {d} {mw:g}x{mh:g} (±{U['cabeza_cuadros']})",
                    )
                )
    if len(med_dir) > 1:
        gw = float(np.median([w for w, _ in med_dir.values()]))
        gh = float(np.median([h for _, h in med_dir.values()]))
        for d, (w, h) in med_dir.items():
            if abs(w - gw) > U["cabeza_dirs"] or abs(h - gh) > U["cabeza_dirs"]:
                out.append(
                    _al(
                        2,
                        d,
                        None,
                        "cabeza",
                        "cabeza_tamano_dirs",
                        [w, h],
                        U["cabeza_dirs"],
                        f"cabeza {w:g}x{h:g} vs mediana de las direcciones {gw:g}x{gh:g} (±{U['cabeza_dirs']})",
                    )
                )
    if piv:
        vals = list(piv.values())
        moda = max(set(vals), key=vals.count)
        for (d, p), v in piv.items():
            if v != moda:
                out.append(
                    _al(
                        3,
                        d,
                        p,
                        "pivote",
                        "pivote",
                        list(v),
                        list(moda),
                        f"pivote {v} ≠ {moda} del resto",
                    )
                )
    marcar_falsas(out, res)
    orden = {d: i for i, d in enumerate(dirs)}
    out.sort(
        key=lambda a: (
            -a["sev"],
            orden[a["dir"]],
            -1 if a["cuadro"] is None else a["cuadro"],
            a["zona"],
        )
    )
    return out


# ------------------------------------------------------------------ informe de texto
def _n(x):
    x = round(float(x), 1)
    return "%g" % (0.0 if x == 0 else x)


def _s(x):
    x = round(float(x), 1)
    return "0" if x == 0 else "%+g" % x


def _gen(a):
    """Descripción de una alerta sin los datos de un cuadro puntual (para agrupar varios cuadros en una línea)."""
    t, u = a["tipo"], a["umbral"]
    if t == "salto":
        return (
            f"salto de centro dx,dy > ±{u[0]:g},±{u[1]:g}"
            if isinstance(u, list)
            else f"salto de centro (px) > {u:g}"
        )
    textos = {
        "cambio_px": f"px antes,después cambia > ±{u:.0%}"
        if not isinstance(u, list)
        else "",
        "aparece": "aparece (px) respecto del cuadro anterior",
        "desaparece": "desaparece respecto del anterior",
        "ojo_parpadea": "el ojo aparece/desaparece entre cuadros (px)",
        "ojo_borde": f"px de cabeza entre el ojo y el borde < {u}",
        "ojo_de_espaldas": "ojo visible de espaldas (px)",
        "sep_ojos": f"separación de ojos fuera de {u}",
        "sin_zona": "px sin zona",
        "lado_cruzado": "cruza la línea central contra su ancla raíz (x respecto de la línea)",
        "cabeza_tamano_cuadros": f"cabeza ancho,alto lejos de la mediana de la dirección (±{u})",
        "pivote": f"pivote distinto del resto {u}",
    }
    if t.startswith("borde_"):
        return f"px opacos tocan el borde {t[6:]}"
    return textos.get(t) or a["texto"]


def _grupos(mias, n_cuadros):
    """Alertas iguales (misma severidad, zona y tipo) en varios cuadros → una sola línea con la lista de cuadros."""
    g = {}
    for a in mias:
        g.setdefault((a["sev"], a["zona"], a["tipo"]), []).append(a)
    lineas = []
    for (sev, zona, _), lst in g.items():
        cs = [a["cuadro"] for a in lst if a["cuadro"] is not None]
        if not cs:
            cu = ""
        elif len(cs) == n_cuadros and n_cuadros > 2:
            cu = " todos"
        else:
            cu = " " + ",".join(f"c{c}" for c in cs)
        txt = lst[0]["texto"]
        if len(lst) > 1:
            vals = [json.dumps(a["valor"], separators=(",", ":")) for a in lst]
            txt = f"{_gen(lst[0])}: " + (
                f"valores {' '.join(vals)}"
                if len(set(vals)) > 1
                else f"valor {vals[0]} (×{len(lst)})"
            )
        lineas.append(f"- [{SEV[sev]}]{cu} {zona}: {txt}")
    return lineas


def _tabla(filas):
    anchos = [max(len(f[k]) for f in filas) for k in range(len(filas[0]))]
    return [
        " ".join(
            x.rjust(w) if k else x.ljust(w) for k, (x, w) in enumerate(zip(f, anchos))
        ).rstrip()
        for f in filas
    ]


def informe(res, completo=False):
    """Texto compacto para un LLM: por dirección, ALERTAS primero (agrupadas por zona y tipo) y la tabla de centros
    por cuadro con su Δ al siguiente; si la dirección no tiene alertas (y no se pide completo), una línea por zona
    con el centro del c0, el Δ máximo y el rango de px. Al final, el resumen entre direcciones."""
    todas = res["alertas"]
    al = [a for a in todas if not a.get("fp")]
    falsas = [a for a in todas if a.get("fp")]
    q = UMBRALES["quieto_px"]
    cuenta = {s_: sum(a["sev"] == s_ for a in al) for s_ in (3, 2, 1)}
    L = [
        f"# zonas · {res['anim']} · {res['estilo']} · {res['personaje']} ({res['modo']})",
        f"{len(al)} alertas por revisar (alta {cuenta[3]}, media {cuenta[2]}, baja {cuenta[1]}) + {len(falsas)} falsas conocidas "
        f"(marcadas aparte, ver 'conocidas'). px de la celda (x→der, y→abajo). "
        f"Δ al cuadro siguiente{' (el último vuelve al c0)' if res['loop'] else ''} = dx,dy[,dpx si |dpx|>1]; "
        f"'·' = sin cambio (≤{q:g} px); +z/-z = la zona aparece/desaparece. Tabla completa solo en direcciones con "
        f"alertas MEDIA/ALTA (--completo para todas).",
    ]
    for d, info in res["direcciones"].items():
        cs = info["cuadros"]
        c0 = cs[0]
        L += [
            "",
            f"## {d} · celda {c0['celda'][0]}x{c0['celda'][1]} · pivote {c0['pivote'][0]},{c0['pivote'][1]}",
            "ALERTAS",
        ]
        mias = [a for a in al if a["dir"] == d]
        lineas = _grupos(mias, len(cs)) or ["sin alertas"]
        tope = UMBRALES["alertas_por_dir"]
        L += lineas[:tope] + (
            [f"- ... y {len(lineas) - tope} más (ver JSON)"]
            if len(lineas) > tope
            else []
        )
        fd = [a for a in falsas if a["dir"] == d]
        if fd:
            cnt = {}
            for a in fd:
                cnt[a["fp"]] = cnt.get(a["fp"], 0) + 1
            L.append(
                "conocidas (falsas, no accionar): "
                + "; ".join(f"{n}× {k}" for k, n in cnt.items())
            )
        pares = _pares(len(cs), res["loop"])
        fijas, filas, breves, poco = [], [], [], []
        for z in ZONAS:
            vals = [c["zonas"][z] for c in cs]
            if all(v is None for v in vals):
                continue
            cen = [
                "-" if v is None else f"{_n(v['centro'][0])},{_n(v['centro'][1])}"
                for v in vals
            ]
            deltas, mdx, mdy = [], 0.0, 0.0
            for a, b in pares:
                va, vb = vals[a], vals[b]
                if va is None or vb is None:
                    deltas.append(
                        "-"
                        if va is None and vb is None
                        else ("+z" if va is None else "-z")
                    )
                    continue
                dx, dy = (
                    vb["centro"][0] - va["centro"][0],
                    vb["centro"][1] - va["centro"][1],
                )
                mdx, mdy = max(mdx, abs(dx)), max(mdy, abs(dy))
                dp = vb["px"] - va["px"]
                deltas.append(
                    "·"
                    if abs(dx) <= q and abs(dy) <= q and abs(dp) <= 1
                    else f"{_s(dx)},{_s(dy)}" + (f",{dp:+d}" if abs(dp) > 1 else "")
                )
            pxs = [v["px"] for v in vals if v]
            if None not in vals and all(x == "·" for x in deltas):
                fijas.append(
                    f"{z} {cen[0]} ({min(pxs)}-{max(pxs)}px)"
                    if min(pxs) != max(pxs)
                    else f"{z} {cen[0]} ({pxs[0]}px)"
                )
                continue
            aus = sum(v is None for v in vals)
            breve = (
                f"{z} {next(c for c in cen if c != '-')} Δmáx {_n(mdx)},{_n(mdy)} px {min(pxs)}-{max(pxs)}"
                + (f" ausente en {aus}/{len(vals)}" if aus else "")
            )
            con_alerta = any(z in a["zona"].split(",") for a in mias)
            if con_alerta or aus or max(mdx, mdy) > UMBRALES["poco_px"]:
                filas += [[z] + cen, ["  Δ"] + deltas + [""] * (len(cen) - len(deltas))]
                breves.append(breve)
            else:
                poco.append(breve)
        if completo or any(a["sev"] >= 2 for a in mias):
            if filas:
                L.append("centros x,y por cuadro; debajo, Δ al siguiente")
                L += _tabla([["zona"] + [f"c{c['cuadro']}" for c in cs]] + filas)
        else:
            poco = breves + poco
        if poco:
            L.append(
                "se mueven poco o sin alertas (centro del primer cuadro visible, Δ máximo |dx|,|dy|, rango de px):"
            )
            L += poco
        if fijas:
            L.append("fijas: " + "; ".join(fijas))
    # resumen entre direcciones (cuadro 0 de cada una)
    dirs = list(res["direcciones"])
    ex = res.get("_extra", {})
    L += ["", "## Resumen entre direcciones (primer cuadro): ancho x alto de bbox / px"]
    filas = [["zona"] + dirs]
    fila_cab = ["cabeza(unión)"]
    for d in dirs:
        c = res["direcciones"][d]["cuadros"][0]
        b = ex.get((d, c["cuadro"]), {}).get("cabeza")
        fila_cab.append("-" if not b else f"{b[2] - b[0] + 1}x{b[3] - b[1] + 1}")
    filas.append(fila_cab)
    for z in ZONAS:
        vals = [res["direcciones"][d]["cuadros"][0]["zonas"][z] for d in dirs]
        if all(v is None for v in vals):
            continue
        filas.append(
            [z]
            + [
                "-"
                if v is None
                else "%dx%d/%d"
                % (
                    v["bbox"][2] - v["bbox"][0] + 1,
                    v["bbox"][3] - v["bbox"][1] + 1,
                    v["px"],
                )
                for v in vals
            ]
        )
    L += _tabla(filas)
    L.append(
        "ojos (primer cuadro): sep = |x ojo_izq - x ojo_der|; borde = px de cabeza entre el ojo y el borde "
        "de la silueta (ojo_der/ojo_izq)"
    )
    partes_ = []
    for d in dirs:
        c = res["direcciones"][d]["cuadros"][0]
        zz = c["zonas"]
        sep = (
            "-"
            if not (zz["ojo_derecho"] and zz["ojo_izquierdo"])
            else _n(
                abs(zz["ojo_izquierdo"]["centro"][0] - zz["ojo_derecho"]["centro"][0])
            )
        )
        br = ex.get((d, c["cuadro"]), {}).get("borde", {})
        partes_.append(
            f"{d} sep {sep} borde {br.get('ojo_derecho', '-')}/{br.get('ojo_izquierdo', '-')}"
        )
    L.append("; ".join(partes_))
    return "\n".join(L) + "\n"


def para_json(res):
    return {k: v for k, v in res.items() if not k.startswith("_")}


# ------------------------------------------------------------------ plantilla de colores planos (revisión humana)
def imagen(zm, anillo=None):
    """PNG RGBA de un mapa de zonas: cada zona con su color plano de COLORES (el contorno exterior, más oscuro)."""
    from PIL import Image

    a = np.zeros(zm.shape + (4,), np.uint8)
    for i, z in enumerate(ZONAS):
        a[zm == i] = (*_rgb(COLORES[z]), 255)
    if anillo is not None:
        a[anillo, :3] = (a[anillo, :3] * 0.55).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def png(res, ruta, zoom=6):
    """Una fila por dirección, una columna por cuadro, con los colores planos de zona."""
    from PIL import Image, ImageDraw

    dirs = list(res["direcciones"])
    ps = [c["cuadro"] for c in res["direcciones"][dirs[0]]["cuadros"]]
    ex = res["_extra"]
    h, w = ex[(dirs[0], ps[0])]["zm"].shape
    M = 22
    im = Image.new(
        "RGB", (M + len(ps) * w * zoom, M + len(dirs) * h * zoom), (28, 26, 40)
    )
    dr = ImageDraw.Draw(im)
    for j, p in enumerate(ps):
        dr.text((M + j * w * zoom + 2, 4), f"c{p}", fill=(255, 255, 255))
    for i, d in enumerate(dirs):
        dr.text((2, M + i * h * zoom + 4), d, fill=(255, 255, 255))
        for j, p in enumerate(ps):
            g = imagen(ex[(d, p)]["zm"], ex[(d, p)]["anillo"]).resize(
                (w * zoom, h * zoom), Image.NEAREST
            )
            im.paste(g, (M + j * w * zoom, M + i * h * zoom), g)
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    im.save(ruta)
    return ruta


# ------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="python -m sprites_lib.zonas", description=__doc__.split("\n")[0]
    )
    ap.add_argument("--anim", default="caminar_lpc")
    ap.add_argument("--estilo", default="stardew8")
    ap.add_argument("--dirs", help="p. ej. S,SE (por defecto todas las del estilo)")
    ap.add_argument("--cuadros", help="p. ej. 0,1,2 (por defecto todos)")
    ap.add_argument("--skin", help="PNG de skin 32x32 (en vez del muñeco de zonas)")
    ap.add_argument(
        "--ficha", help="ficha YAML (nombre o ruta) en vez del muñeco de zonas"
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="imprimir el JSON en vez del informe de texto",
    )
    ap.add_argument("--salida", help="ruta del JSON (el .md va al lado)")
    ap.add_argument(
        "--png",
        action="store_true",
        help="además, PNG con los colores de zona (revisión humana)",
    )
    ap.add_argument(
        "--completo",
        action="store_true",
        help="tabla de centros también en direcciones sin alertas",
    )
    a = ap.parse_args(argv)
    ficha = None
    if a.skin:
        from . import skins

        ficha = skins.ficha(a.skin)
    elif a.ficha:
        from .ficha import cargar

        ficha = cargar(a.ficha)
    res = analizar(
        a.anim,
        a.estilo,
        a.dirs.split(",") if a.dirs else None,
        [int(x) for x in a.cuadros.split(",")] if a.cuadros else None,
        ficha,
    )
    origen = a.skin or a.ficha
    nombre = (
        a.anim
        if ficha is None
        else f"{a.anim}_{os.path.splitext(os.path.basename(origen))[0]}"
    )
    ruta = a.salida or os.path.join("salida", "zonas", a.estilo, nombre + ".json")
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    js = json.dumps(para_json(res), ensure_ascii=False, separators=(",", ":"))
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(js)
    txt = informe(res, a.completo)
    with open(os.path.splitext(ruta)[0] + ".md", "w", encoding="utf-8") as fh:
        fh.write(txt)
    if a.png:
        print("→", png(res, os.path.splitext(ruta)[0] + "_zonas.png"), file=sys.stderr)
    print(js if a.json else txt)
    print("→", ruta, file=sys.stderr)
    return res


if __name__ == "__main__":
    main()
