"""Motor de gates: corre checks y arma un veredicto VERDE/ROJO con evidencia para el agente."""
import hashlib
import json
from dataclasses import dataclass

from . import armado, estado
from .estilos import ESTILOS
from .tests_personaje import Resultado

__all__ = ["Resultado", "Veredicto", "correr", "informe", "guardar", "check_determinismo", "check_deriva"]


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
