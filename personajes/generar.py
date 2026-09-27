"""CLI de personajes desde fichas.

  .venv/bin/python -m personajes.generar boceto  <nombre> [--estilo stardew]   (rápido: frente y perfil, sin tests)
  .venv/bin/python -m personajes.generar validar <nombre|ruta.yaml> [--estilo todos]
  .venv/bin/python -m personajes.generar hoja    <nombre> --estilo stardew|volumen|lateral|todos
  .venv/bin/python -m personajes.generar tests   <nombre> --estilo ...
  .venv/bin/python -m personajes.generar aprobar <nombre> --estilo ...   (solo después del OK del usuario)
Códigos de salida: 0 todo OK, 1 fallan tests, 2 ficha inexistente o inválida.
"""
import argparse
import os
import sys

from sprites_lib import fotos_control
from PIL import Image

from sprites_lib.armado import render_cuadro, render_todo
from sprites_lib.escala import celda
from sprites_lib.estilos import ACTIVOS, ESTILOS
from sprites_lib.exportar import exportar_direcciones
from sprites_lib.ficha import FichaInvalida, cargar
from sprites_lib.hoja_modelo import hoja
from sprites_lib.poses import fps
from sprites_lib.tests_personaje import correr_tests, informe_md

SALIDA = "salida"


def _estilos(arg):
    return list(ACTIVOS) if arg == "todos" else arg.split(",")


def _generar(nombre, estilo):
    f = cargar(nombre, estilos=[estilo])
    todo = render_todo(f, estilo)
    sal = os.path.join(SALIDA, f["_nombre"], estilo)
    os.makedirs(sal, exist_ok=True)
    res = correr_tests(f, estilo, todo, sal)
    res.append(fotos_control.comparar(f["_nombre"], estilo, todo, os.path.join(sal, "diferencias")))
    return f, todo, res, sal


def _resumen(estilo, res):
    mal = [r for r in res if not r.ok]
    print(f"[{estilo}] {'OK' if not mal else 'CON FALLAS'}: "
          f"{sum(r.ok and not r.omitido for r in res)} ok, {len(mal)} fallas, {sum(r.omitido for r in res)} omitidos")
    for r in mal:
        print(f"   ✗ {r.regla}: {r.detalle.splitlines()[0] if r.detalle else ''}")
        for e in r.evidencia[:5]:
            print(f"       - {e}")
    return 1 if mal else 0


def cmd_boceto(a):
    """Primer vistazo para pedir feedback: un estilo, frente y perfil, pose quieto, sin tests ni exportación."""
    est = "stardew" if a.estilo == "todos" else a.estilo.split(",")[0]
    f = cargar(a.nombre, estilos=[est])
    dirs = [d for d in ("S", "E", "W") if d in ESTILOS[est]["direcciones"]] or ESTILOS[est]["direcciones"][:2]
    cuadros = [render_cuadro(f, est, "quieto", 0, d).img for d in dirs]
    cw, ch = cuadros[0].size
    z = max(4, 192 // ch)
    hoja = Image.new("RGB", (len(cuadros) * (cw * z + 16) + 16, ch * z + 32), (60, 58, 80))
    for i, im in enumerate(cuadros):
        grande = im.resize((cw * z, ch * z), Image.NEAREST)
        hoja.paste(grande, (16 + i * (cw * z + 16), 16), grande)
    sal = os.path.join(SALIDA, f["_nombre"])
    os.makedirs(sal, exist_ok=True)
    ruta = os.path.join(sal, "boceto.png")
    hoja.save(ruta)
    print(f"boceto ({est}: {', '.join(dirs)}) → {ruta}")
    return 0


def cmd_validar(a):
    for est in _estilos(a.estilo):
        cargar(a.nombre, estilos=[est])
    print(f"ficha {a.nombre!r} válida para: {', '.join(_estilos(a.estilo))}")
    return 0


def cmd_hoja(a):
    codigo = 0
    for est in _estilos(a.estilo):
        f, todo, res, sal = _generar(a.nombre, est)
        hoja(f, est, todo, res, os.path.join(sal, "hoja_modelo.png"))
        with open(os.path.join(sal, "informe.md"), "w", encoding="utf-8") as fh:
            fh.write(informe_md(f, est, res))
        cel = celda(est, f["cuerpo"].get("clase_altura", "adulto"))
        por_dir = {m: [c.img for c in todo[("quieto", m)]] for m in ESTILOS[est]["direcciones"]}
        exportar_direcciones(por_dir, "quieto", sal, fps=fps("quieto"), pivote=(cel["gx"], cel["gy"]))
        print(f"hoja → {os.path.join(sal, 'hoja_modelo.png')}")
        codigo = max(codigo, _resumen(est, res))
    return codigo


def cmd_tests(a):
    codigo = 0
    for est in _estilos(a.estilo):
        _, _, res, _ = _generar(a.nombre, est)
        codigo = max(codigo, _resumen(est, res))
    return codigo


def cmd_aprobar(a):
    for est in _estilos(a.estilo):
        f, todo, res, _ = _generar(a.nombre, est)
        mal = [r for r in res if not r.ok and r.regla != "fotos de control"]
        if mal:
            print(f"[{est}] no se puede aprobar: fallan {', '.join(r.regla for r in mal)}")
            return 1
        print(f"[{est}] aprobado → {fotos_control.guardar(f['_nombre'], est, todo)}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="personajes.generar", description="Personajes consistentes desde fichas")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("boceto", "validar", "hoja", "tests", "aprobar"):
        p = sub.add_parser(n)
        p.add_argument("nombre")
        p.add_argument("--estilo", default="todos")
    a = ap.parse_args(argv)
    try:
        return {"boceto": cmd_boceto, "validar": cmd_validar, "hoja": cmd_hoja, "tests": cmd_tests, "aprobar": cmd_aprobar}[a.cmd](a)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except FichaInvalida as e:
        print(e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
