"""Modo pulido: lo que hace que una animación se vea BONITA (no solo bien construida), medido en números y texto.

`zonas` encuentra errores de construcción (un ojo en el borde, una zona que desaparece). Esto mide tres familias de
cosas que el ojo nota sobre el GIF aunque la construcción esté bien, y las devuelve como texto/JSON baratos de leer:
  1. movimiento  amplitud del balanceo de manos/pies contra la referencia LPC, oposición brazo-pierna, simetría del
                 ciclo (segunda mitad = primera con lados cambiados), cierre del loop, suavidad (quiebres de
                 trayectoria) y rebote de la cabeza;
  2. limpieza    sobre la imagen del PERSONAJE REAL: píxeles sueltos, espinas de 1 px, rasgos que se salen de la
                 silueta, relleno que toca el fondo (contorno roto), agujeros, píxeles de color llamativo aislados,
                 parpadeo de un color, paleta por dirección;
  3. espejo      E↔W, SE↔SW, NE↔NW y S, N consigo mismas: el alfa del par espejado tiene que coincidir salvo
                 asimetrías declaradas (componentes distintos a cada lado, `cabeza_desvio` del estilo).
Regla de espejo (comprobada con caminar_lpc/stardew8): espejo de (x, cuadro p) = (2·pivote_x − x, cuadro
(p + desfase) % n). Con el desfase del ciclo la diferencia de alfa en E↔W, S y N es 0-1 px; sin él, 60-70 px.

Cada hallazgo: {familia, sev (3 MAL, 2 REVISAR, 1 leve), dir, cuadro, zona, px [x,y] | None, tipo, valor, umbral,
texto (qué significa para el ojo), fp (None | motivo de falsa conocida)}. Las falsas se marcan, no se borran.

Uso:  .venv/bin/python -m sprites_lib.pulido --anim caminar_lpc --estilo stardew8 [--skin skins/<personaje>.png | --ficha x]
          [--dirs S,E] [--json] [--salida ruta.json]
      → salida/zonas/<estilo>/<anim>[_<skin>]_pulido.json y .md (el informe también sale por stdout)
"""

import argparse
import json
import os
import sys

import numpy as np

from . import zonas as Z

# ------------------------------------------------------------------ umbrales (px de juego; fáciles de cambiar)
UMBRALES_PULIDO = {
    # movimiento
    "amplitud_tol": 0.35,  # rango de x de mano/pie en perfil: ± esto (relativo) alrededor del objetivo LPC
    "oposicion_ok": -0.5,  # correlación mano-pie del mismo lado: <= esto = opuestos (bien); >= 0 = van juntos (mal)
    "oposicion_rango_min": 2.0,  # px mínimos de recorrido de mano y pie en el eje para poder medir la oposición
    "simetria_px": 1.5,  # |dev lado A en p − dev lado B en p+n/2| (px, trayectorias sin su media)
    "oclusion_rel": 0.25,  # si el px de la zona difiere más que esto entre los dos cuadros, el centro no es fiable
    "cierre_factor": 1.5,  # distancia último→primero <= esto × el mayor paso entre cuadros consecutivos (+1 px)
    "retroceso_px": 0.75,  # paso mínimo (px) para contar un "ida-vuelta-ida" de un cuadro como quiebre
    "acel_lpc_factor": 1.25,  # segunda diferencia > esto × la máxima de LPC (6 px en 45,5 de alto) es brusca...
    "acel_factor": 2.5,  # ... si además es >= esto × la mediana de la zona
    "rebote_px": (1, 2),  # rango de la altura de la coronilla en un ciclo de paso (px)
    # limpieza
    "contraste": 90.0,  # distancia RGB mínima entre una mancha y TODO lo que la rodea para ser llamativa
    "igual": 30.0,  # distancia RGB máxima entre píxeles de una misma mancha
    "mancha_px": 3,
    "entre_min": 50.0,  # si el color de la mancha está a menos de esto del segmento RGB entre dos vecinos, es un
    # tono de transición (medido: transiciones <= 37, acentos reales >= 88)              # tamaño máximo de una mancha (px): más grande ya es una forma, no un punto
    "parpadeo_px": 3,  # un color con <= estos px que está en un cuadro y en ninguno de sus dos vecinos
    # espejo
    "espejo_zona_px": 1,  # px de diferencia por zona tolerados (cuantización)
    "espejo_total_px": 8,  # px de diferencia no esperables en un cuadro que ya es grave
}
SEVP = {3: "MAL", 2: "REVISAR", 1: "leve"}
ESPEJO = {"E": "W", "SE": "SW", "NE": "NW", "S": "S", "N": "N"}
PERFIL = ("E", "W")
FALSAS_PULIDO = {
    "punta_de_contorno": "espina que es el contorno exterior envolviendo una punta de 1 px (mano, pie, nariz de perfil): así se cierra la línea",
    "rasgo_de_cara": "ojo/ceja/boca dentro de la cara: son detalles aislados por diseño (solo importa si tocan el fondo)",
    "oclusion": "el centro de la zona se corre porque la tapa otra pieza (px distinto > 25 %% entre los cuadros comparados)",
    "desvio_de_estilo": "la cabeza no es espejo exacto porque el estilo corre la cabeza distinto en cada diagonal (cabeza_desvio)",
    "asimetria_declarada": "la ficha pone componentes distintos a cada lado (brazo de metal, muñón): esa zona no tiene por qué espejarse",
    "tono_de_material": "color de un tono (sombra/base/luz) de un material del personaje: el sombreado depende de la luz y de la dirección",
    "tono_intermedio": "la mancha es un tono entre dos colores vecinos (transición pelo-piel, sombreado): no salta a la vista",
    "extremidad_en_movimiento": "tono de sombreado de 1-3 px que cambia en un brazo/pierna/mano/pie: la pieza gira y se tapa al caminar",
    "tono_vecino": "el color que titila es parecido a un vecino (dist. RGB < contraste): a 1 px el ojo no ve el cambio",
    "pie_al_piso": "mancha en la última fila de la celda: el pivote deja el pie a 2 px del borde y la celda corta su contorno",
    "animacion_asimetrica": "la animación mueve distinto cada lado (el ciclo trae mano_b/pie_b, p. ej. un golpe con un brazo): al espejar se intercambian",
    "ya_en_zonas": "el mismo cambio ya lo reporta zonas.py (aparece/desaparece/parpadea) en esa zona y cuadro",
}


def _h(fam, sev, d, p, zona, tipo, valor, umbral, texto, px=None, fp=None):
    return {
        "familia": fam,
        "sev": sev,
        "dir": d,
        "cuadro": p,
        "zona": zona,
        "px": px,
        "tipo": tipo,
        "valor": valor,
        "umbral": umbral,
        "texto": texto,
        "fp": fp,
    }


def _lado_opuesto(z):
    if "derech" in z:
        return z.replace("derecha", "izquierda").replace("derecho", "izquierdo")
    if "izquierd" in z:
        return z.replace("izquierda", "derecha").replace("izquierdo", "derecho")
    return z


# ------------------------------------------------------------------ referencia LPC
# asset del kit: se resuelve contra la raíz del paquete (no contra el cwd), como el default de skins de proceso_anim
REF_LPC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "referencias",
    "caminar",
    "lpc_E_huesos.json",
)


def referencia_lpc(ruta=REF_LPC):
    """Amplitud del balanceo en la referencia LPC de perfil (E), relativa al alto del personaje (piso − coronilla):
    rango de x de la mano cercana y del tobillo cercano sobre los 8 cuadros del ciclo (c1..c8)."""
    with open(ruta) as fh:
        cs = [c for c in json.load(fh)["cuadros"] if c["c"] >= 1]
    alto = float(np.median([c["piso"] - c["top"] for c in cs]))
    mx = [c["mano_A"][0] for c in cs]
    px = [c["tob_A"][0] for c in cs]
    mb = [c["mano_B"][0] for c in cs if c["mano_B"]]

    def acel(t):
        return max(
            abs(t[(i + 1) % len(t)] - 2 * t[i] + t[i - 1]) for i in range(len(t))
        )

    return {
        "alto": alto,
        "mano": (max(mx) - min(mx)) / alto,
        "pie": (max(px) - min(px)) / alto,
        "mano_lejana": (max(mb) - min(mb)) / alto,
        "acel": max(acel(mx), acel(px)) / alto,
        "fuente": ruta + " (mano_A, tob_A y mano_B visible, cuadros 1-8)",
    }


# ------------------------------------------------------------------ 1. movimiento
def _tray(cs, z, k):
    return [None if c["zonas"][z] is None else c["zonas"][z]["centro"][k] for c in cs]


def _pxs(cs, z):
    return [0 if c["zonas"][z] is None else c["zonas"][z]["px"] for c in cs]


def _corr(a, b):
    ok = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(ok) < 4:
        return None
    x, y = np.array(ok).T
    if x.std() < 1e-6 or y.std() < 1e-6:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def movimiento(res, zres_alertas, desfase):
    U, H, med = UMBRALES_PULIDO, [], {}
    en_loop = res["loop"]
    ex = res["_extra"]
    lpc = referencia_lpc()
    dirs = list(res["direcciones"])
    n = len(res["direcciones"][dirs[0]]["cuadros"])
    paso = (
        en_loop and desfase and n == 2 * desfase
    )  # ciclo de paso: segunda mitad = primera cambiada
    med["ciclo_de_paso"] = bool(paso)
    med["lpc"] = lpc
    saltos_zonas = {
        (a["dir"], a["cuadro"], a["zona"]) for a in zres_alertas if a["tipo"] == "salto"
    }
    for d in dirs:
        cs = res["direcciones"][d]["cuadros"]
        md = med.setdefault(d, {})
        piv = cs[0]["pivote"]
        alto = float(
            np.median(
                [
                    piv[1]
                    - int(np.nonzero(ex[(d, c["cuadro"])]["img"][..., 3])[0].min())
                    for c in cs
                ]
            )
        )
        md["alto"] = alto
        # --- amplitud (solo perfil): el lado que se ve en todos los cuadros es el que cuenta
        if paso and d in PERFIL:
            for tipo, zs in (
                ("mano", ("mano_derecha", "mano_izquierda")),
                ("pie", ("pie_derecho", "pie_izquierdo")),
            ):
                for z in zs:
                    xs = [x for x in _tray(cs, z, 0) if x is not None]
                    if len(xs) < 2:
                        continue
                    rng = max(xs) - min(xs)
                    md[f"amplitud_{z}"] = round(rng, 1)
                    completo = len(xs) == n
                    # la mano que se tapa detrás del cuerpo es la lejana: su objetivo es la mano_B visible de LPC
                    obj = (
                        lpc["mano_lejana"]
                        if tipo == "mano" and not completo
                        else lpc[tipo]
                    ) * alto
                    rel = rng / obj - 1
                    if abs(rel) <= U["amplitud_tol"]:
                        continue
                    poco = rel < 0
                    ojo = (
                        "braceo corto/tieso: el brazo casi no se balancea"
                        if poco and tipo == "mano"
                        else "pasos cortos: camina arrastrando los pies"
                        if poco
                        else "braceo exagerado: parece que marcha"
                        if tipo == "mano"
                        else "pasos exagerados: zancadas de más"
                    )
                    H.append(
                        _h(
                            "movimiento",
                            2 if completo else 1,
                            d,
                            None,
                            z,
                            "amplitud",
                            round(rng, 1),
                            [
                                round(obj * (1 - U["amplitud_tol"]), 1),
                                round(obj * (1 + U["amplitud_tol"]), 1),
                            ],
                            f"recorrido x {rng:.1f} px vs objetivo LPC {obj:.1f} px ({obj / alto:.3f} × alto {alto:g}; "
                            f"{rel:+.0%}) → {ojo}"
                            + (
                                ""
                                if completo
                                else f" [lado lejano, visible {len(xs)}/{n} cuadros; objetivo = mano_B de LPC]"
                            ),
                        )
                    )
        # --- oposición brazo-pierna (mismo lado, eje de avance en pantalla)
        if paso:
            k = 1 if d in ("S", "N") else 0
            for lado in ("derecha", "izquierda"):
                zm_, zp = (
                    f"mano_{lado}",
                    "pie_" + ("derecho" if lado == "derecha" else "izquierdo"),
                )
                tm, tp = _tray(cs, zm_, k), _tray(cs, zp, k)
                vm, vp = (
                    [x for x in tm if x is not None],
                    [x for x in tp if x is not None],
                )
                if (
                    len(vm) < 4
                    or len(vp) < 4
                    or min(max(vm) - min(vm), max(vp) - min(vp))
                    < U["oposicion_rango_min"]
                ):
                    continue
                r = _corr(tm, tp)
                if r is None:
                    continue
                md[f"oposicion_{lado}"] = round(r, 2)
                if r >= 0:
                    H.append(
                        _h(
                            "movimiento",
                            3,
                            d,
                            None,
                            f"{zm_}+{zp}",
                            "oposicion",
                            round(r, 2),
                            U["oposicion_ok"],
                            f"mano y pie del mismo lado van JUNTOS (correlación {r:+.2f} en {'y' if k else 'x'}) → "
                            f"camina como robot (ambladura): el brazo tiene que ir opuesto a su pierna",
                        )
                    )
                elif r > U["oposicion_ok"]:
                    H.append(
                        _h(
                            "movimiento",
                            1,
                            d,
                            None,
                            f"{zm_}+{zp}",
                            "oposicion",
                            round(r, 2),
                            U["oposicion_ok"],
                            f"oposición débil mano-pie (correlación {r:+.2f}) → el braceo no acompaña bien al paso",
                        )
                    )
        # --- simetría del ciclo (p vs p+n/2 con lados cambiados, trayectorias sin su media)
        if paso:
            sx = (
                -1 if d in ("S", "N") else 1
            )  # de frente/espalda el lado izquierdo se mueve espejado en x
            peor = 0.0
            for z in ("mano_derecha", "pie_derecho", "brazo_derecho", "pierna_derecha"):
                zo = _lado_opuesto(z)
                for k, sg in ((0, sx), (1, 1)):
                    ta, tb = _tray(cs, z, k), _tray(cs, zo, k)
                    ma = (
                        np.mean([x for x in ta if x is not None])
                        if any(x is not None for x in ta)
                        else None
                    )
                    mb = (
                        np.mean([x for x in tb if x is not None])
                        if any(x is not None for x in tb)
                        else None
                    )
                    if ma is None or mb is None:
                        continue
                    pa, pb = _pxs(cs, z), _pxs(cs, zo)
                    parcial = (
                        None in ta or None in tb
                    )  # media sesgada: la zona se tapa en algún cuadro
                    for p in range(n):
                        q = (p + desfase) % n
                        if ta[p] is None or tb[q] is None:
                            continue
                        dif = abs((ta[p] - ma) - sg * (tb[q] - mb))
                        if dif <= U["simetria_px"]:
                            continue
                        ocl = (
                            parcial
                            or abs(pa[p] - pb[q]) / max(pa[p], pb[q], 1)
                            > U["oclusion_rel"]
                        )
                        peor = max(peor, 0 if ocl else dif)
                        H.append(
                            _h(
                                "movimiento",
                                2,
                                d,
                                cs[p]["cuadro"],
                                f"{z}/{zo}",
                                "simetria_ciclo",
                                round(dif, 1),
                                U["simetria_px"],
                                f"{'x' if k == 0 else 'y'}: {z} en c{cs[p]['cuadro']} y {zo} en c{cs[q]['cuadro']} difieren "
                                f"{dif:.1f} px (px {pa[p]} vs {pb[q]}) → un paso no es igual al otro: se ve rengo",
                                fp="oclusion" if ocl else None,
                            )
                        )
            md["simetria_peor_px"] = round(peor, 1)
        # --- rebote: altura de la coronilla por cuadro
        top = [
            ex[(d, c["cuadro"])]["cabeza"][1]
            if ex[(d, c["cuadro"])]["cabeza"]
            else None
            for c in cs
        ]
        md["coronilla_y"] = top
        vt = [t for t in top if t is not None]
        if vt and paso:
            amp = max(vt) - min(vt)
            lo, hi = U["rebote_px"]
            if not lo <= amp <= hi:
                H.append(
                    _h(
                        "movimiento",
                        2,
                        d,
                        None,
                        "cabeza",
                        "rebote",
                        amp,
                        [lo, hi],
                        f"la cabeza sube y baja {amp} px en el ciclo → "
                        + (
                            "no rebota: el paso se ve deslizado, sin peso"
                            if amp < lo
                            else "rebota de más: parece que salta"
                        ),
                    )
                )
            irreg = [
                c["cuadro"]
                for p, c in enumerate(cs)
                if top[p] is not None
                and top[(p + desfase) % n] is not None
                and top[p] != top[(p + desfase) % n]
            ]
            if irreg:
                H.append(
                    _h(
                        "movimiento",
                        2,
                        d,
                        irreg[0],
                        "cabeza",
                        "rebote_irregular",
                        [top[p] for p in range(n)],
                        "y[p] = y[p+n/2]",
                        f"el rebote no se repite en los dos pasos (coronilla y por cuadro {top}) → cojea",
                    )
                )
        # --- cierre del loop y suavidad (trayectorias de manos, pies y cabeza)
        claves = (
            "mano_derecha",
            "mano_izquierda",
            "pie_derecho",
            "pie_izquierdo",
            "cabeza_resto",
        )
        if en_loop and n > 2:
            pasos = []
            for p in range(n):
                q = (p + 1) % n
                tot = 0.0
                for z in claves:
                    a, b = cs[p]["zonas"][z], cs[q]["zonas"][z]
                    if a and b:
                        tot += np.hypot(
                            b["centro"][0] - a["centro"][0],
                            b["centro"][1] - a["centro"][1],
                        )
                pasos.append(tot)
            cierre, resto = pasos[-1], max(pasos[:-1])
            md["cierre_px"], md["paso_max_px"] = round(cierre, 1), round(resto, 1)
            if cierre > U["cierre_factor"] * resto + 1:
                H.append(
                    _h(
                        "movimiento",
                        2,
                        d,
                        cs[0]["cuadro"],
                        ",".join(claves),
                        "cierre_loop",
                        round(cierre, 1),
                        round(U["cierre_factor"] * resto + 1, 1),
                        f"del último cuadro al primero hay {cierre:.1f} px de movimiento (suma de manos/pies/cabeza) contra "
                        f"{resto:.1f} del peor par consecutivo → el loop da un tirón al repetirse",
                    )
                )
        acel_max = U["acel_lpc_factor"] * lpc["acel"] * alto
        md["acel_max_px"] = round(acel_max, 1)
        for z in claves:
            for k in (0, 1):
                t = _tray(cs, z, k)
                pares = range(n) if en_loop else range(1, n - 1)
                acel = {}
                for p in pares:
                    a, b, c = t[(p - 1) % n], t[p], t[(p + 1) % n]
                    if None in (a, b, c):
                        continue
                    acel[p] = (c - 2 * b + a, b - a, c - b)
                if not acel:
                    continue
                mediana = float(np.median([abs(v[0]) for v in acel.values()]))
                pxz = _pxs(cs, z)
                for p, (ac, v1, v2) in acel.items():
                    ida_vuelta = (
                        v1 * v2 < 0 and min(abs(v1), abs(v2)) >= U["retroceso_px"]
                    )
                    brusca = abs(ac) >= acel_max and abs(ac) >= U["acel_factor"] * max(
                        mediana, 0.3
                    )
                    if not (ida_vuelta or brusca):
                        continue
                    # ida-vuelta en un extremo del recorrido es el cambio de sentido normal del balanceo (después
                    # sigue en el sentido de la vuelta); es quiebre si la vuelta dura un solo cuadro (se frena o retoma)
                    if ida_vuelta:
                        c2 = t[(p + 2) % n] if (en_loop or p + 2 < n) else None
                        if c2 is None or (c2 - t[(p + 1) % n]) * v2 > 0:
                            ida_vuelta = False
                    if not (ida_vuelta or brusca):
                        continue
                    vec = [pxz[(p - 1) % n], pxz[p], pxz[(p + 1) % n]]
                    ocl = (max(vec) - min(vec)) / max(max(vec), 1) > U["oclusion_rel"]
                    ya = any(
                        (d, cs[i % n]["cuadro"], z) in saltos_zonas for i in (p, p + 1)
                    )
                    eje = "xy"[k]
                    H.append(
                        _h(
                            "movimiento",
                            2 if ida_vuelta else 1,
                            d,
                            cs[p]["cuadro"],
                            z,
                            "quiebre" if ida_vuelta else "aceleracion",
                            round(ac, 1),
                            U["retroceso_px"]
                            if ida_vuelta
                            else [
                                round(acel_max, 1),
                                round(U["acel_factor"] * mediana, 1),
                            ],
                            (
                                f"{eje}: va {v1:+.1f}, vuelve {v2:+.1f} y sigue: tiembla un cuadro (jitter)"
                                if ida_vuelta
                                else f"{eje}: aceleración {ac:+.1f} px (mediana {mediana:.1f}) → la trayectoria quiebra en este cuadro"
                            ),
                            fp="ya_en_zonas" if ya else ("oclusion" if ocl else None),
                        )
                    )
    return H, med


# ------------------------------------------------------------------ 2. limpieza de píxeles
def _vecinos4(m, borde=False):
    p = np.pad(m, 1, constant_values=borde)
    return p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]


CABEZA_Y_OREJAS = set(Z.CABEZA) | {"oreja_derecha", "oreja_izquierda"}


def _toca(m, y, x):
    h, w = m.shape
    return any(
        m[yy, xx]
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
        if 0 <= yy < h and 0 <= xx < w
    )


def _grupo_color(rgb, grupo):
    return np.mean([rgb[y, x].astype(float) for y, x in grupo], 0)


def _hex(c):
    return "#%02x%02x%02x" % tuple(int(v) for v in c[:3])


def _manchas(rgb, al):
    """Manchas de color llamativas: grupos (8-conexos) de <= mancha_px píxeles opacos de color parecido entre sí
    (distancia RGB < 'igual') cuyo color está lejos (>= 'contraste') de TODOS los píxeles opacos que los rodean.
    Devuelve [(lista de (y, x), color medio, distancia mínima al entorno)]."""
    U = UMBRALES_PULIDO
    h, w = al.shape
    f = rgb.astype(float)
    visto = np.zeros(al.shape, bool)
    out = []
    for y0, x0 in np.argwhere(al):
        if visto[y0, x0]:
            continue
        grupo, pila = [], [(int(y0), int(x0))]
        visto[y0, x0] = True
        while pila:
            y, x = pila.pop()
            grupo.append((y, x))
            if len(grupo) > U["mancha_px"]:
                break
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if (
                        0 <= yy < h
                        and 0 <= xx < w
                        and al[yy, xx]
                        and not visto[yy, xx]
                        and np.sqrt(((f[yy, xx] - f[y0, x0]) ** 2).sum()) < U["igual"]
                    ):
                        visto[yy, xx] = True
                        pila.append((yy, xx))
        if len(grupo) > U["mancha_px"]:
            continue
        g = set(grupo)
        col = np.mean([f[y, x] for y, x in grupo], 0)
        borde = {
            (y + dy, x + dx)
            for y, x in grupo
            for dy in (-1, 0, 1)
            for dx in (-1, 0, 1)
            if 0 <= y + dy < h
            and 0 <= x + dx < w
            and al[y + dy, x + dx]
            and (y + dy, x + dx) not in g
        }
        if not borde:
            continue
        dmin = float(min(np.sqrt(((f[y, x] - col) ** 2).sum()) for y, x in borde))
        if dmin >= U["contraste"]:
            vec = [np.array(c, float) for c in {tuple(f[y, x]) for y, x in borde}]
            entre = min(
                (
                    _dist_segmento(col, a, b)
                    for i, a in enumerate(vec)
                    for b in vec[i + 1 :]
                ),
                default=999.0,
            )
            out.append((grupo, col, round(dmin), round(entre)))
    return out


def _dist_segmento(c, a, b):
    """Distancia RGB de c al segmento a-b: chica = c es un tono intermedio entre dos vecinos (transición)."""
    ab = b - a
    t = float(np.clip(((c - a) @ ab) / max(float(ab @ ab), 1e-9), 0, 1))
    return float(np.linalg.norm(c - (a + t * ab)))


def limpieza(res, ficha, estilo, zres_alertas):
    from .paleta import paleta_estilo
    from .estilos import ESTILOS
    from .tests_personaje import colores_permitidos

    U, H = UMBRALES_PULIDO, []
    ex = res["_extra"]
    permitidos = {tuple(int(v) for v in c) for c in colores_permitidos(ficha, estilo)}
    tonos = {}
    for m, ts in paleta_estilo(ficha["paleta"], ESTILOS[estilo]).items():
        for t in ts:
            tonos.setdefault(tuple(int(v) for v in t), m)
    ya = {
        (a["dir"], a["cuadro"], a["zona"])
        for a in zres_alertas
        if a["tipo"] in ("aparece", "desaparece", "ojo_parpadea", "cambio_px")
    }
    rasgos = [Z.ZONAS.index(z) for z in Z.RASGOS]
    paletas, med = {}, {}
    for d, info in res["direcciones"].items():
        cs = info["cuadros"]
        n = len(cs)
        conteo = []  # por cuadro: {color: [(x, y), ...]}
        manchas = {}  # (zona, color) → [(cuadro, px, dist, en_borde, rasgo)]
        for c in cs:
            p = c["cuadro"]
            e = ex[(d, p)]
            img, zm, anillo, sol = e["img"], e["zm"], e["anillo"], e["solido"]
            al = img[..., 3] > 0
            rgb = img[..., :3]
            zn = lambda y, x: Z.ZONAS[zm[y, x]] if zm[y, x] >= 0 else "-"
            n4 = _vecinos4(al)
            fondo4 = (
                _vecinos4(~al, borde=False) > 0
            )  # toca un transparente (el borde de la celda no cuenta)
            for y, x in np.argwhere(al & (n4 == 0)):
                H.append(
                    _h(
                        "limpieza",
                        3,
                        d,
                        p,
                        zn(y, x),
                        "suelto",
                        _hex(rgb[y, x]),
                        "0 vecinos",
                        f"píxel {_hex(rgb[y, x])} flotando sin tocar nada → se ve como una mota suelta",
                        px=[int(x), int(y)],
                    )
                )
            for y, x in np.argwhere(al & (n4 == 1)):
                H.append(
                    _h(
                        "limpieza",
                        2,
                        d,
                        p,
                        zn(y, x),
                        "espina",
                        _hex(rgb[y, x]),
                        "1 vecino",
                        f"píxel {_hex(rgb[y, x])} que asoma de la silueta tocando un solo píxel → pelito/espina",
                        px=[int(x), int(y)],
                        fp="punta_de_contorno" if anillo[y, x] else None,
                    )
                )
            afuera = _vecinos4(anillo | ~al, borde=True)
            for y, x in np.argwhere(np.isin(zm, rasgos) & (fondo4 | (afuera >= 2))):
                H.append(
                    _h(
                        "limpieza",
                        3 if zn(y, x).startswith("ojo") else 2,
                        d,
                        p,
                        zn(y, x),
                        "rasgo_fuera",
                        _hex(rgb[y, x]),
                        "< 2 lados de contorno/fondo",
                        f"{zn(y, x)} ({_hex(rgb[y, x])}) tiene {int(afuera[y, x])} de sus 4 lados en el contorno exterior o el "
                        f"fondo: el rasgo sobresale de la silueta de la cabeza → "
                        + (
                            "un píxel de ojo pegado afuera de la cara"
                            if zn(y, x).startswith("ojo")
                            else "queda sobre el contorno y se confunde con él (la cara pierde el rasgo)"
                        ),
                        px=[int(x), int(y)],
                    )
                )
            for y, x in np.argwhere(sol & fondo4 & ~np.isin(zm, rasgos)):
                H.append(
                    _h(
                        "limpieza",
                        2,
                        d,
                        p,
                        zn(y, x),
                        "contorno_roto",
                        _hex(rgb[y, x]),
                        "contorno de 1 px",
                        f"el relleno ({_hex(rgb[y, x])}) toca el fondo sin contorno → hueco en la línea de la silueta",
                        px=[int(x), int(y)],
                    )
                )
            for y, x in np.argwhere(~al & (_vecinos4(al) == 4)):
                H.append(
                    _h(
                        "limpieza",
                        2,
                        d,
                        p,
                        "-",
                        "agujero",
                        "transparente",
                        "4 vecinos opacos",
                        "píxel transparente rodeado de opacos → agujerito en el sprite",
                        px=[int(x), int(y)],
                    )
                )
            for grupo, col, dmin, entre in _manchas(rgb, al):
                zs = [Z.ZONAS[zm[y, x]] for y, x in grupo]
                z = max(set(zs), key=zs.count)
                borde_sil = any(anillo[y, x] or fondo4[y, x] for y, x in grupo)
                es_rasgo = all(zm[y, x] in rasgos for y, x in grupo)
                if all(y == al.shape[0] - 1 for y, x in grupo):
                    es_rasgo = (
                        "piso"  # la celda corta el contorno del pie (ver FALSAS_PULIDO)
                    )
                manchas.setdefault((z, _hex(_grupo_color(rgb, grupo))), []).append(
                    (p, grupo, dmin, borde_sil, es_rasgo, entre)
                )
            cols = {}
            for y, x in np.argwhere(al):
                cols.setdefault(tuple(int(v) for v in rgb[y, x]), []).append(
                    (int(x), int(y))
                )
            conteo.append(cols)
        for (z, col), lst in manchas.items():
            cu = sorted({m[0] for m in lst})
            p0, g0 = lst[0][0], lst[0][1]
            dmax = max(m[2] for m in lst)
            intermedio = max(m[5] for m in lst) < U["entre_min"]
            en_borde = any(m[3] for m in lst)
            piso = all(m[4] == "piso" for m in lst)
            es_rasgo = all(m[4] is True for m in lst)
            cabeza = z in CABEZA_Y_OREJAS
            sev = 2 if (cabeza or en_borde) and not es_rasgo else 1
            H.append(
                _h(
                    "limpieza",
                    sev,
                    d,
                    p0,
                    z,
                    "mancha",
                    dmax,
                    U["contraste"],
                    f"mancha de {len(g0)} px {col} distinta de todo lo que la rodea (dist. RGB {dmax}) en "
                    f"{','.join(f'c{c}' for c in cu)} ({len(cu)}/{n})"
                    + (
                        " en el borde de la silueta"
                        if en_borde
                        else " dentro de la pieza"
                    )
                    + (" sobre la cabeza" if cabeza else "")
                    + (
                        " → punto de color suelto que distrae (¿mota o detalle a propósito?)"
                        if sev == 2
                        else " → detalle aislado; si es de la skin a propósito (rodilla, raya de metal), dejarlo"
                    ),
                    px=[int(g0[0][1]), int(g0[0][0])],
                    fp="pie_al_piso"
                    if piso
                    else "rasgo_de_cara"
                    if es_rasgo and not en_borde
                    else ("tono_intermedio" if intermedio else None),
                )
            )
        # paleta de la dirección
        todos = set().union(*[set(c) for c in conteo])
        paletas[d] = todos
        # parpadeo de un color
        for i, cols in enumerate(conteo):
            if n < 3 or (not res["loop"] and i in (0, n - 1)):
                continue
            ant, sig = conteo[(i - 1) % n], conteo[(i + 1) % n]
            for col, pos in cols.items():
                if len(pos) <= U["parpadeo_px"] and col not in ant and col not in sig:
                    x, y = pos[0]
                    z = Z.ZONAS[ex[(d, cs[i]["cuadro"])]["zm"][y, x]]
                    p = cs[i]["cuadro"]
                    e = ex[(d, p)]
                    al_ = e["img"][..., 3] > 0
                    f_ = e["img"][..., :3].astype(float)
                    vec = [
                        f_[yy, xx]
                        for yy in range(max(0, y - 1), min(al_.shape[0], y + 2))
                        for xx in range(max(0, x - 1), min(al_.shape[1], x + 2))
                        if (yy, xx) != (y, x) and al_[yy, xx]
                    ]
                    dvec = min(
                        (
                            float(np.sqrt(((v - np.array(col, float)) ** 2).sum()))
                            for v in vec
                        ),
                        default=999,
                    )
                    fp = (
                        "ya_en_zonas"
                        if (d, p, z) in ya or (d, cs[(i + 1) % n]["cuadro"], z) in ya
                        else "extremidad_en_movimiento"
                        if z.split("_")[0] in ("brazo", "mano", "pierna", "pie")
                        else "tono_vecino"
                        if dvec < U["contraste"]
                        else None
                    )
                    H.append(
                        _h(
                            "limpieza",
                            1 if col in tonos else 2,
                            d,
                            p,
                            z,
                            "parpadeo",
                            _hex(col),
                            U["parpadeo_px"],
                            f"el color {_hex(col)} ({len(pos)} px) aparece solo en c{p}, no en c{cs[(i - 1) % n]['cuadro']} "
                            f"ni en c{cs[(i + 1) % n]['cuadro']} → titila un cuadro",
                            px=[x, y],
                            fp=fp,
                        )
                    )
        med[d] = {"colores": len(todos)}
    # paleta entre direcciones
    for d, cols in paletas.items():
        otros = (
            set().union(*[c for k, c in paletas.items() if k != d])
            if len(paletas) > 1
            else cols
        )
        excl = sorted(cols - otros)
        med[d]["exclusivos"] = [_hex(c) for c in excl]
        for c in excl:
            fuera = c not in permitidos
            H.append(
                _h(
                    "limpieza",
                    2 if fuera else 1,
                    d,
                    None,
                    "-",
                    "color_exclusivo",
                    _hex(c),
                    "en otra dirección",
                    f"el color {_hex(c)} solo aparece en {d}"
                    + (
                        " y no es de la paleta del personaje → un tono raro que cambia el look de esa dirección"
                        if fuera
                        else f" (tono de '{tonos.get(c, '?')}')"
                    ),
                    fp=None if fuera else "tono_de_material",
                )
            )
    return H, med


# ------------------------------------------------------------------ 3. espejo entre direcciones
def _asimetrias_declaradas(specs):
    """Familias de zonas que la ficha hace distintas a cada lado: tipo de componente en un ancla y no en su espejo."""
    from .cuerpo import lado_de

    por = {}
    for s in specs:
        por.setdefault(s["ancla"], set()).add(
            s["tipo"].replace("_derecho", "").replace("_izquierdo", "")
        )
    zonas_ = set()
    for ancla, tipos in por.items():
        if not lado_de(ancla):
            continue
        otra = _lado_opuesto(ancla)
        if por.get(otra, set()) != tipos:
            for a in (ancla, otra):
                zonas_ |= set(Z.ANCLA_FAM.get(a, ()))
    return zonas_ | {_lado_opuesto(z) for z in zonas_}


def espejo(res, estilo, desfase, asimetrica=False):
    """asimetrica: la animación mueve distinto los lados A y B (el ciclo trae 'mano_b'/'pie_b', p. ej. golpear): el
    espejo intercambia los lados, así que las extremidades no tienen por qué coincidir (cabeza y torso sí)."""
    from .estilos import ESTILOS

    U, H, med = UMBRALES_PULIDO, [], {}
    extremidad = {
        z for z in Z.ZONAS if z.split("_")[0] in ("brazo", "mano", "pierna", "pie")
    }
    ex = res["_extra"]
    desvio = ESTILOS[estilo].get("proporciones", {}).get("cabeza_desvio", {}) or {}
    cab = set(Z.CABEZA) | {"oreja_derecha", "oreja_izquierda"}
    for a, b in ESPEJO.items():
        if a not in res["direcciones"] or b not in res["direcciones"]:
            continue
        ca, cb = res["direcciones"][a]["cuadros"], res["direcciones"][b]["cuadros"]
        n = len(ca)
        asim_desvio = (
            abs(desvio.get(a, 0) + desvio.get(b, 0)) > 1e-6 if a != b else False
        )
        tot = []
        for i, c in enumerate(ca):
            p, q = c["cuadro"], cb[(i + desfase) % n]["cuadro"]
            ea, eb = ex[(a, p)], ex[(b, q)]
            declaradas = _asimetrias_declaradas(ea["specs"])
            pivx = c["pivote"][0]
            A = ea["img"][..., 3] > 0
            h, w = A.shape
            xs = 2 * pivx - np.arange(w)  # columna espejada de cada columna
            ok = (xs >= 0) & (xs < w)
            B = np.zeros_like(A)
            zb = np.full(A.shape, -1)
            B[:, ok] = (eb["img"][..., 3] > 0)[:, xs[ok]]
            zb[:, ok] = eb["zm"][:, xs[ok]]
            dif = A ^ B
            tot.append(int(dif.sum()))
            por = {}
            for y, x in np.argwhere(dif):
                z = (
                    Z.ZONAS[ea["zm"][y, x]]
                    if A[y, x]
                    else _lado_opuesto(Z.ZONAS[zb[y, x]])
                )
                por.setdefault(z, []).append((int(x), int(y)))
            inesperado = 0
            for z, pos in sorted(por.items(), key=lambda kv: -len(kv[1])):
                if len(pos) <= U["espejo_zona_px"]:
                    continue
                fp = (
                    "asimetria_declarada"
                    if z in declaradas
                    else "animacion_asimetrica"
                    if asimetrica and z in extremidad
                    else "desvio_de_estilo"
                    if asim_desvio and z in cab
                    else None
                )
                if fp is None:
                    inesperado += len(pos)
                H.append(
                    _h(
                        "espejo",
                        2,
                        a,
                        p,
                        z,
                        "espejo",
                        len(pos),
                        U["espejo_zona_px"],
                        f"{a} c{p} vs {b} c{q} espejado: {z} difiere en {len(pos)} px (p. ej. {pos[0][0]},{pos[0][1]}) "
                        f"→ la pose no es la misma de un lado que del otro: al girar el personaje 'cambia'",
                        px=list(pos[0]),
                        fp=fp,
                    )
                )
            if inesperado > U["espejo_total_px"]:
                H.append(
                    _h(
                        "espejo",
                        3,
                        a,
                        p,
                        "total",
                        "espejo_total",
                        inesperado,
                        U["espejo_total_px"],
                        f"{a} c{p} vs {b} c{q}: {inesperado} px de silueta distinta sin asimetría declarada → "
                        f"se nota que un lado está dibujado distinto",
                    )
                )
        med[f"{a}-{b}"] = {
            "dif_px_por_cuadro": tot,
            "regla": f"x' = 2·pivote_x − x, cuadro (p + {desfase}) % {n}",
        }
    return H, med


# ------------------------------------------------------------------ análisis completo
def analizar(anim="caminar_lpc", estilo="stardew8", dirs=None, ficha=None):
    """Hallazgos de pulido (movimiento, limpieza, espejo) + medidas + resumen. ficha=None: muñeco de zonas."""
    from .poses import POSES

    res = Z.analizar(anim, estilo, dirs, None, ficha)
    desfase = int(POSES[anim].get("desfase", 0) or 0)
    ficha_real = ficha if ficha is not None else Z.ficha_plantilla()
    h1, m1 = movimiento(res, res["alertas"], desfase)
    h2, m2 = limpieza(res, ficha_real, estilo, res["alertas"])
    h3, m3 = espejo(
        res,
        estilo,
        desfase,
        asimetrica=any(k in POSES[anim] for k in ("mano_b", "pie_b")),
    )
    hall = h1 + h2 + h3
    orden = {d: i for i, d in enumerate(res["direcciones"])}
    hall.sort(
        key=lambda a: (
            a["fp"] is not None,
            -a["sev"],
            a["familia"],
            orden.get(a["dir"], 99),
            -1 if a["cuadro"] is None else a["cuadro"],
        )
    )
    pul = {
        "anim": anim,
        "estilo": estilo,
        "personaje": res["personaje"],
        "modo": res["modo"],
        "loop": res["loop"],
        "desfase": desfase,
        "umbrales": UMBRALES_PULIDO,
        "hallazgos": hall,
        "medidas": {"movimiento": m1, "limpieza": m2, "espejo": m3},
        "alertas_zonas": {
            "por_revisar": sum(1 for a in res["alertas"] if not a["fp"]),
            "altas_medias": sum(
                1 for a in res["alertas"] if not a["fp"] and a["sev"] >= 2
            ),
        },
    }
    pul["resumen"] = resumen(pul)
    pul["_zonas"] = res
    return pul


def resumen(pul):
    reales = [h for h in pul["hallazgos"] if not h["fp"]]
    notas = {}
    for fam in ("movimiento", "limpieza", "espejo"):
        f = [h for h in reales if h["familia"] == fam]
        notas[fam] = (
            "MAL"
            if any(h["sev"] == 3 for h in f)
            else ("REVISAR" if any(h["sev"] == 2 for h in f) else "OK")
        )

    def peso(h):
        u = h["umbral"]
        v = h["valor"]
        r = (
            abs(v) / abs(u)
            if isinstance(v, (int, float)) and isinstance(u, (int, float)) and u
            else 1.0
        )
        return (h["sev"], r)

    # los 3 más importantes: uno por (familia, tipo) para no repetir el mismo defecto en 8 cuadros
    top, vistos = [], set()
    for h in sorted(reales, key=peso, reverse=True):
        k = (h["familia"], h["tipo"], h["zona"])
        if k in vistos:
            continue
        vistos.add(k)
        top.append(h)
        if len(top) == 3:
            break
    return {
        "notas": notas,
        "top": top,
        "por_revisar": len(reales),
        "falsas": len(pul["hallazgos"]) - len(reales),
    }


# ------------------------------------------------------------------ informe de texto
def _linea(h):
    donde = (
        h["dir"]
        + ("" if h["cuadro"] is None else f" c{h['cuadro']}")
        + ("" if not h["px"] else f" @{h['px'][0]},{h['px'][1]}")
    )
    return f"- [{SEVP[h['sev']]}] {h['familia']}/{h['tipo']} {donde} {h['zona']}: {h['texto']} (valor {json.dumps(h['valor'], ensure_ascii=False)}, umbral {json.dumps(h['umbral'], ensure_ascii=False)})"


def informe(pul, max_por_grupo=6, max_leves=3):
    r = pul["resumen"]
    L = [
        f"# pulido · {pul['anim']} · {pul['estilo']} · {pul['personaje']} ({pul['modo']})"
    ]
    if pul["modo"] == "plantilla":
        L.append(
            "AVISO: sin --skin/--ficha la limpieza se mide sobre el MUÑECO DE ZONAS (colores planos), no sobre un personaje real."
        )
    az = pul["alertas_zonas"]
    if az["altas_medias"]:
        L.append(
            f"AVISO: zonas.py tiene {az['altas_medias']} alertas de construcción ALTA/MEDIA sin resolver: arreglarlas antes de pulir."
        )
    L += [
        "",
        "## Resumen de pulido",
        " · ".join(f"{k} {v}" for k, v in r["notas"].items())
        + f"  ({r['por_revisar']} hallazgos por revisar, {r['falsas']} falsas conocidas)",
        "Por dónde empezar:",
    ]
    L += [_linea(h) for h in r["top"]] or ["- nada por revisar"]
    mm = pul["medidas"]["movimiento"]
    L += ["", "## Medidas"]
    lpc = mm["lpc"]
    L.append(
        f"objetivo LPC (de {lpc['fuente']}): recorrido x mano {lpc['mano']:.3f}·alto, pie {lpc['pie']:.3f}·alto "
        f"(alto LPC {lpc['alto']:g} px); ciclo de paso: {'sí' if mm['ciclo_de_paso'] else 'no'} (desfase {pul['desfase']})"
    )
    for d, md in mm.items():
        if d not in pul["medidas"]["limpieza"]:
            continue
        extra = ", ".join(
            f"{k} {v}" for k, v in md.items() if k not in ("alto", "coronilla_y")
        )
        L.append(
            f"{d}: alto {md['alto']:g}, coronilla y {md['coronilla_y']}"
            + (f", {extra}" if extra else "")
        )
    ml = pul["medidas"]["limpieza"]
    L.append(
        "colores por dirección: "
        + "; ".join(
            f"{d} {m['colores']}"
            + (f" (exclusivos {' '.join(m['exclusivos'])})" if m["exclusivos"] else "")
            for d, m in ml.items()
        )
    )
    for k, m in pul["medidas"]["espejo"].items():
        L.append(
            f"espejo {k}: dif. de alfa por cuadro {m['dif_px_por_cuadro']} ({m['regla']})"
        )
    reales = [h for h in pul["hallazgos"] if not h["fp"]]
    for fam in ("movimiento", "limpieza", "espejo"):
        f = [h for h in reales if h["familia"] == fam]
        L += ["", f"## {fam} · {r['notas'][fam]}"]
        if not f:
            L.append("sin hallazgos por revisar")
        grupos = {}
        for h in f:
            grupos.setdefault((h["tipo"], h["sev"]), []).append(h)
        for (tipo, sev), lst in grupos.items():
            tope = max_por_grupo if sev >= 2 else max_leves
            L += [_linea(h) for h in lst[:tope]]
            if len(lst) > tope:
                L.append(
                    f"- ... y {len(lst) - tope} más de {tipo} [{SEVP[sev]}] (ver JSON)"
                )
    falsas = [h for h in pul["hallazgos"] if h["fp"]]
    if falsas:
        cnt = {}
        for h in falsas:
            cnt.setdefault((h["familia"], h["tipo"], h["fp"]), 0)
            cnt[(h["familia"], h["tipo"], h["fp"])] += 1
        L += ["", "## Falsas conocidas (no accionar; motivo en FALSAS_PULIDO)"]
        L += [
            f"- {n}× {fa}/{t}: {fp}"
            for (fa, t, fp), n in sorted(cnt.items(), key=lambda kv: -kv[1])
        ]
    return "\n".join(L) + "\n"


def para_json(pul):
    return {k: v for k, v in pul.items() if not k.startswith("_")}


# ------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="python -m sprites_lib.pulido", description=__doc__.split("\n")[0]
    )
    ap.add_argument("--anim", default="caminar_lpc")
    ap.add_argument("--estilo", default="stardew8")
    ap.add_argument(
        "--dirs",
        help="p. ej. E,W (por defecto todas las del estilo; el espejo necesita los pares)",
    )
    ap.add_argument("--skin", help="PNG de skin 32x32 (personaje real)")
    ap.add_argument("--ficha", help="ficha YAML (nombre o ruta)")
    ap.add_argument(
        "--json", action="store_true", help="imprimir el JSON en vez del informe"
    )
    ap.add_argument("--salida", help="ruta del JSON (el .md va al lado)")
    a = ap.parse_args(argv)
    ficha = None
    if a.skin:
        from . import skins

        ficha = skins.ficha(a.skin)
    elif a.ficha:
        from .ficha import cargar

        ficha = cargar(a.ficha)
    pul = analizar(a.anim, a.estilo, a.dirs.split(",") if a.dirs else None, ficha)
    origen = a.skin or a.ficha
    nombre = (
        a.anim
        if ficha is None
        else f"{a.anim}_{os.path.splitext(os.path.basename(origen))[0]}"
    )
    ruta = a.salida or os.path.join(
        "salida", "zonas", a.estilo, nombre + "_pulido.json"
    )
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    js = json.dumps(
        para_json(pul), ensure_ascii=False, separators=(",", ":"), default=str
    )
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(js)
    txt = informe(pul)
    with open(os.path.splitext(ruta)[0] + ".md", "w", encoding="utf-8") as fh:
        fh.write(txt)
    print(js if a.json else txt)
    print("→", ruta, file=sys.stderr)
    return pul


if __name__ == "__main__":
    main()
