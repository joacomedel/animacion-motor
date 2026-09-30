"""Proceso de estilo: medir el muñeco base contra su referencia, validar el perfil y congelarlo al aprobarlo.

El gate de un estilo (fuente: `estilos.ESTILOS[estilo]` + `escala.TAMANOS[estilo]`) corre el contrato numérico del
muñeco, el determinismo del render, la comparación con la referencia local (si está calibrada) y la deriva contra
la última aprobación. Aprobar congela `aprobados/estilos/<estilo>/` (`control.png`, `metricas.json`, `estado.json`
— este último al final, como marca del congelado) y propone `docs/estilos/<estilo>.md` si todavía no existe.

Uso:
  .venv/bin/python -m sprites_lib.proceso_estilo medir <estilo>      → métricas de la referencia y del muñeco (no escribe)
  .venv/bin/python -m sprites_lib.proceso_estilo validar <estilo>    → informe VERDE/ROJO del gate (exit 0/1)
  .venv/bin/python -m sprites_lib.proceso_estilo aprobar <estilo> [--excepcion MOTIVO]
                                                                     → congela el estilo (exit 0/1)
Estilos disponibles: ver `sprites_lib.estilos`. Uso incorrecto o estilo desconocido: exit 2.
"""
import json
import os
import sys
import tempfile

from PIL import Image

from . import armado, comparar_estilo, estado, gates, lado_a_lado, proporciones
from .escala import TAMANOS
from .estilos import ESTILOS
from .poses import POSES

RAIZ_ESTILOS = os.path.join("aprobados", "estilos")
RAIZ_DOCS = os.path.join("docs", "estilos")


def _carpeta(estilo):
    return os.path.join(RAIZ_ESTILOS, estilo)


def fuentes_actuales(estilo):
    """Fuentes del estilo para el hash de deriva: perfil completo y escala (hash estable por claves ordenadas)."""
    return {"perfil": estado.hash_obj(ESTILOS[estilo]), "escala": estado.hash_obj(TAMANOS[estilo])}


def _tira_muneco(estilo, pose="quieto"):
    """Tira RGBA con el muñeco base en todas las direcciones y cuadros de la pose (referencia propia del gate)."""
    frames = [armado.render_cuadro(armado.FICHA_MINIMA, estilo, pose, p, m).img
              for m in ESTILOS[estilo]["direcciones"] for p in range(POSES[pose]["n"])]
    cw, ch = frames[0].size
    tira = Image.new("RGBA", (cw * len(frames), ch), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        tira.paste(fr, (i * cw, 0))
    return tira, cw, ch


def _metricas_tira(tira, celda):
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "tira.png")
        tira.save(ruta)
        return comparar_estilo.metricas(ruta, celda)[0]


def _metricas_referencia(ref):
    return comparar_estilo.metricas(ref["ruta"], tuple(ref["celda"]),
                                    tuple(ref["recorte"]) if ref.get("recorte") else None)[0]


def check_referencia(estilo):
    """Resultado de comparar el muñeco base con la referencia calibrada del estilo (omitido si no hay datos)."""
    ref = ESTILOS[estilo].get("referencia")
    if not ref or not ref.get("calibrada"):
        return gates.Resultado("estilo vs referencia", True, "sin referencia calibrada: omitido", omitido=True)
    if not os.path.exists(ref["ruta"]):
        return gates.Resultado("estilo vs referencia", True, f"no está {ref['ruta']}: omitido", omitido=True)
    tira, cw, ch = _tira_muneco(estilo)
    fallas = [f for f in comparar_estilo.comparar_detalle(_metricas_referencia(ref), _metricas_tira(tira, (cw, ch)))
              if f["bloqueante"]]
    evidencia = [f"{f['metrica']}: referencia {f['referencia']:.2f}, muñeco {f['propio']:.2f}" for f in fallas]
    detalle = (f"{len(fallas)} métricas bloqueantes fuera de tolerancia contra {ref['ruta']}" if fallas else
               f"el muñeco coincide con {ref['ruta']} en todas las métricas bloqueantes")
    return gates.Resultado("estilo vs referencia", not fallas, detalle, evidencia)


def correr_gate(estilo):
    """Veredicto del estilo: contrato del muñeco, determinismo, referencia calibrada y deriva de las fuentes."""
    return gates.correr([
        lambda: proporciones.comparar(estilo),
        lambda: gates.check_determinismo(estilo),
        lambda: check_referencia(estilo),
        lambda: gates.check_deriva(estado.leer(_carpeta(estilo)), fuentes_actuales(estilo)),
    ])


def medir(estilo):
    """Imprime las métricas de la referencia (si hay) y las del muñeco; no escribe nada."""
    ref = ESTILOS[estilo].get("referencia")
    if ref and os.path.exists(ref["ruta"]):
        rm = _metricas_referencia(ref)
        print(f"referencia {ref['ruta']}:")
        for k, v in rm.items():
            print(f"  {k:12s} {v:8.2f}")
    else:
        print(f"{estilo}: sin referencia local")
    m = proporciones.medir(estilo)
    print(f"\nmuñeco {estilo}: alto {m['alto_px']:.0f} px, {m['cabezas']:.2f} cabezas, "
          f"piernas {m['piernas_frac']:.0%}, ancho de cabeza {m['ancho_cabeza_px']:.0f} px, ancho {m['ancho_px']:.0f} px")
    for d, v in m["por_direccion"].items():
        print(f"  {d}: alto {v['alto_px']:.0f} px, cabeza {v['cabeza_px']:.0f}, piernas {v['piernas_px']:.0f}, "
              f"ancho {v['ancho_px']:.0f}")
    return m


def validar(estilo):
    """Imprime el informe del gate; devuelve 0 si es VERDE y 1 si es ROJO."""
    v = correr_gate(estilo)
    print(gates.informe(v))
    return 0 if v.verde else 1


def _control(estilo, tira, cw, ch, carpeta):
    """Comparativa `lado_a_lado` de la referencia (si está en disco) contra el muñeco, dirección por dirección."""
    ref = ESTILOS[estilo].get("referencia")
    hay = bool(ref and os.path.exists(ref["ruta"]))
    n = POSES["quieto"]["n"]
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "muneco.png")
        tira.save(ruta)
        items = []
        for i in range(len(ESTILOS[estilo]["direcciones"])):
            if hay:
                rx, ry = (ref.get("recorte") or (0, 0))[:2]
                rcw, rch = ref["celda"]
                items.append(f"{ref['ruta']}:{rx},{ry + i * rch},{rcw},{rch}")
            items.append(f"{ruta}:{i * n * cw},0,{cw},{ch}")
        return lado_a_lado.lado_a_lado(os.path.join(carpeta, "control.png"), items)


def _metricas_json(estilo, veredicto, tira, celda, medidas, carpeta):
    """Guarda las métricas del gate + las de referencia y propias (si hay referencia en disco)."""
    datos = {"estilo": estilo, "verde": veredicto.verde, "informe": gates.informe(veredicto),
             "checks": [vars(r) for r in veredicto.checks], "medidas": medidas}
    ref = ESTILOS[estilo].get("referencia")
    if ref and os.path.exists(ref["ruta"]):
        datos["referencia"] = _metricas_referencia(ref)
        datos["propias"] = _metricas_tira(tira, celda)
    ruta = os.path.join(carpeta, "metricas.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return ruta


def _doc_esqueleto(estilo, medidas):
    """Esqueleto en markdown de la ficha del estilo: medidas, reglas del perfil y placeholders a completar a mano."""
    e = ESTILOS[estilo]
    ref = e.get("referencia") or {}
    lineas = [
        f"# Estilo `{estilo}`",
        "",
        e["descripcion"],
        "",
        "## Medidas del muñeco (contrato numérico)",
        "",
        f"- alto {medidas['alto_px']:.0f} px; {medidas['cabezas']:.2f} cabezas; piernas {medidas['piernas_frac']:.0%}; "
        f"ancho de cabeza {medidas['ancho_cabeza_px']:.0f} px; ancho {medidas['ancho_px']:.0f} px",
        f"- pose `quieto` en las direcciones {' '.join(e['direcciones'])}",
        "",
        "## Reglas del perfil",
        "",
        f"- vista `{e['vista']}`; celdas por clase en `escala.TAMANOS[{estilo!r}]`",
        f"- render: `{e['render']}`",
        f"- proporciones: `{e['proporciones']}`",
        f"- tonos: `{e['tonos']}`; ojos: `{e['ojos']}`",
        f"- paleta: {e['paleta']}",
        "",
    ]
    if ref:
        lineas += [f"- referencia: `{ref['ruta']}` celda {ref['celda']} recorte {ref.get('recorte')}; "
                   f"calibrada={ref.get('calibrada', False)}", ""]
    lineas += [
        "## Trampas conocidas",
        "",
        "- <!-- completar a mano: qué confunde a este estilo y cómo se corrige -->",
        "",
        "## Umbrales",
        "",
        "<!-- completar a mano: tolerancias de `comparar_estilo.TOL` calibradas para este estilo -->",
        "",
    ]
    return "\n".join(lineas)


def aprobar(estilo, excepcion=None):
    """Congela el estilo (control, métricas, doc si falta y `estado.json` último); ROJO sin excepción no escribe."""
    v = correr_gate(estilo)
    print(gates.informe(v))
    if not v.verde and not excepcion:
        print('\nROJO: no se congeló nada (para aprobar igual hace falta --excepcion "motivo")')
        return 1
    if not v.verde:
        print(f"\nROJO con excepción: {excepcion}")
    carpeta = _carpeta(estilo)
    os.makedirs(carpeta, exist_ok=True)
    tira, cw, ch = _tira_muneco(estilo)
    medidas = proporciones.medir(estilo)
    _control(estilo, tira, cw, ch, carpeta)
    _metricas_json(estilo, v, tira, (cw, ch), medidas, carpeta)
    ruta_doc = os.path.join(RAIZ_DOCS, f"{estilo}.md")
    if not os.path.exists(ruta_doc):
        os.makedirs(RAIZ_DOCS, exist_ok=True)
        with open(ruta_doc, "w", encoding="utf-8") as f:
            f.write(_doc_esqueleto(estilo, medidas))
        print(f"→ {ruta_doc} (esqueleto, completar a mano)")
    estado.escribir(carpeta, estilo, fuentes_actuales(estilo), "metricas.json", nota=excepcion)
    print(f"→ {carpeta} (congelado" + (f" con excepción: {excepcion}" if excepcion else "") + ")")
    return 0


def main(argv=None):
    """CLI del proceso de estilo: devuelve 0 VERDE, 1 ROJO y 2 error de uso o estilo desconocido."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in ("medir", "validar", "aprobar"):
        print(__doc__.strip())
        return 2
    cmd, resto = args[0], args[1:]
    excepcion = None
    if "--excepcion" in resto:
        i = resto.index("--excepcion")
        if cmd != "aprobar" or i + 1 >= len(resto):
            print('uso: proceso_estilo aprobar <estilo> [--excepcion "motivo"]', file=sys.stderr)
            return 2
        excepcion = resto[i + 1]
        resto = resto[:i] + resto[i + 2:]
    if len(resto) != 1:
        print("uso: proceso_estilo medir|validar|aprobar <estilo>", file=sys.stderr)
        return 2
    estilo = resto[0]
    if estilo not in ESTILOS:
        print(f"estilo desconocido: {estilo!r}; disponibles: {', '.join(ESTILOS)}", file=sys.stderr)
        return 2
    if cmd == "medir":
        medir(estilo)
        return 0
    if cmd == "validar":
        return validar(estilo)
    return aprobar(estilo, excepcion)


if __name__ == "__main__":
    raise SystemExit(main())
