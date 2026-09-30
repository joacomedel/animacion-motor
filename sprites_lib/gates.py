"""Motor de gates: corre checks y arma un veredicto VERDE/ROJO con evidencia para el agente."""
import hashlib
import json
from dataclasses import dataclass

from . import armado, estado, pulido, zonas
from .estilos import ESTILOS
from .tests_personaje import Resultado

__all__ = ["Resultado", "Veredicto", "correr", "informe", "guardar", "check_determinismo", "check_deriva",
           "check_zonas", "check_pulido"]


@dataclass
class Veredicto:
    verde: bool
    checks: list[Resultado]


def correr(checks):
    """Ejecuta cada check (callable sin argumentos); si uno explota, ese check queda rojo con la excepción."""
    resultados = []
    for check in checks:
        regla = getattr(check, "__name__", type(check).__name__)
        try:
            resultados.append(check())
        except Exception as e:
            resultados.append(Resultado(regla=regla, ok=False, detalle=f"excepción: {e}"))
    return Veredicto(verde=all(r.ok or r.omitido for r in resultados), checks=resultados)


def informe(v):
    """Texto legible: primera línea `VERDE (n/m)` o `ROJO (k fallan)`, y después cada fallo con hasta 5 evidencias."""
    fallan = [r for r in v.checks if not (r.ok or r.omitido)]
    pasan = sum(1 for r in v.checks if r.ok or r.omitido)
    lineas = [f"VERDE ({pasan}/{len(v.checks)})" if v.verde else f"ROJO ({len(fallan)} fallan)"]
    for r in fallan:
        lineas.append(f"- {r.regla}: {r.detalle}")
        lineas.extend(f"  evidencia: {e}" for e in r.evidencia[:5])
    return "\n".join(lineas)


def guardar(v, ruta):
    """Escribe el veredicto en `ruta` como JSON (`verde`, `informe` legible y un objeto por check); devuelve la ruta."""
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump({"verde": v.verde, "informe": informe(v), "checks": [vars(r) for r in v.checks]},
                  f, ensure_ascii=False, indent=2)
    return ruta


def check_determinismo(estilo, pose="quieto", mira=None, veces=2):
    """Renderiza la ficha mínima `veces` veces en el mismo (pose, mira) y compara los píxeles entre corridas."""
    mira = mira or ESTILOS[estilo]["direcciones"][0]
    huellas = []
    for _ in range(veces):
        img = armado.render_cuadro(armado.FICHA_MINIMA, estilo, pose, 0, mira).img
        huellas.append(hashlib.sha256(img.tobytes()).hexdigest()[:12])
    distintas = len(set(huellas))
    detalle = (f"{estilo}/{pose}/{mira}: {veces} renders idénticos" if distintas == 1 else
               f"{estilo}/{pose}/{mira}: {distintas} resultados distintos en {veces} renders")
    return Resultado("determinismo", distintas == 1, detalle, [f"corrida {i + 1}: {h}" for i, h in enumerate(huellas)])


def check_deriva(estado_dict, fuentes, regla="deriva"):
    """Compara las fuentes actuales contra las aprobadas; sin aprobación previa el check queda omitido (pasa)."""
    if not estado_dict:
        return Resultado(regla, ok=True, omitido=True, detalle="sin aprobación previa")
    claves = estado.deriva(estado_dict, fuentes)
    if not claves:
        return Resultado(regla, ok=True, detalle="sin cambios")
    guardadas = estado_dict.get("fuentes", {})
    evidencia = [f"{k}: {guardadas.get(k, '—')} → {fuentes.get(k, '—')}" for k in claves]
    return Resultado(regla, ok=False, detalle=f"cambió: {', '.join(claves)}", evidencia=evidencia)


def _texto_alerta(a):
    donde = a["dir"] + ("" if a["cuadro"] is None else f" c{a['cuadro']}")
    return f"{donde} {a['zona']}: {a['texto']}"


def _texto_hallazgo(h):
    donde = h["dir"] + ("" if h["cuadro"] is None else f" c{h['cuadro']}")
    return f"{h['familia']}/{h['tipo']} {donde} {h['zona']}: {h['texto']}"


def _borde_cortado(res, alerta):
    """Si la alerta de borde la toca el sólido (el cuerpo se recorta). El contorno exterior de 1 px que roza el
    marco no recorta nada: la silueta queda a 1 px del borde y no bloquea el gate (se ve en `quieto`/`stardew`)."""
    if not alerta["tipo"].startswith("borde_"):
        return True
    extra = (res.get("_extra") or {}).get((alerta["dir"], alerta["cuadro"]))
    if extra is None:
        return True
    solido = extra["solido"]
    linea = {"arriba": solido[0], "abajo": solido[-1],
             "izquierda": solido[:, 0], "derecha": solido[:, -1]}.get(alerta["tipo"][len("borde_"):])
    return True if linea is None else bool(linea.any())


def check_zonas(anim, estilo, ficha=None, dirs=None):
    """Gate de zonas: ninguna alerta MEDIA/ALTA por revisar (sin `fp`), contando las de borde solo si el sólido
    toca el marco. `zonas.marcar_falsas` deja `fp` con el motivo de las falsas conocidas (o None si hay que revisar)."""
    res = zonas.analizar(anim=anim, estilo=estilo, ficha=ficha, dirs=dirs)
    zonas.marcar_falsas(res["alertas"], res)      # idempotente (analizar ya marcó): el gate no depende de eso
    por_revisar = [a for a in res["alertas"] if a["sev"] >= 2 and a["fp"] is None and _borde_cortado(res, a)]
    return Resultado(regla=f"zonas {anim}/{estilo}", ok=not por_revisar,
                     detalle=f"{len(por_revisar)} por revisar", evidencia=[_texto_alerta(a) for a in por_revisar])


def check_pulido(anim, estilo, ficha=None, dirs=None):
    """Gate de pulido: ningún hallazgo MAL por revisar (sin `fp`) en movimiento, limpieza ni espejo; los REVISAR
    quedan listados como evidencia para el informe."""
    pul = pulido.analizar(anim=anim, estilo=estilo, ficha=ficha, dirs=dirs)
    reales = [h for h in pul["hallazgos"] if h["fp"] is None]
    mal = [h for h in reales if h["sev"] == 3]
    revisar = [h for h in reales if h["sev"] == 2]
    return Resultado(regla=f"pulido {anim}/{estilo}", ok=not mal,
                     detalle=f"{len(mal)} MAL, {len(revisar)} REVISAR",
                     evidencia=[_texto_hallazgo(h) for h in mal + revisar])
