"""Proceso de animación: smoke de una animación sobre una skin, con los gates universales.

El smoke renderiza **una** dirección con la skin indicada (por defecto `skins/zonas.png`, el muñeco de zonas) y
la pasa por `gates.check_zonas` (construcción: ninguna alerta MEDIA/ALTA por revisar) y `gates.check_pulido`
(movimiento, limpieza y espejo: ningún hallazgo MAL). Es la primera red antes de validar todas las direcciones.

Uso:
  .venv/bin/python -m sprites_lib.proceso_anim smoke <anim> --estilo <estilo> [--dir D] [--skin RUTA]
      → informe VERDE/ROJO de zonas y pulido en una dirección (exit 0 VERDE / 1 ROJO)
      `--dir` por defecto: la primera dirección del estilo; `--skin` por defecto: skins/zonas.png.
Animaciones: ver `sprites_lib.poses.POSES`. Estilos: ver `sprites_lib.estilos.ESTILOS`.
Uso incorrecto, animación o estilo desconocidos: exit 2.
"""
import os
import sys

from . import gates, skins
from .estilos import ESTILOS
from .poses import POSES

SKIN_DEFECTO = os.path.join("skins", "zonas.png")
USO = "uso: proceso_anim smoke <anim> --estilo <estilo> [--dir D] [--skin RUTA]"


def _opciones(resto):
    """Parte las opciones `--estilo/--dir/--skin`; error de uso si falta el valor o sobra un argumento."""
    op = {"estilo": None, "dir": None, "skin": SKIN_DEFECTO}
    i = 0
    while i < len(resto):
        arg = resto[i]
        if arg not in ("--estilo", "--dir", "--skin"):
            raise ValueError(f"argumento desconocido: {arg!r}")
        if i + 1 >= len(resto):
            raise ValueError(f"falta el valor de {arg}")
        op[arg[2:]] = resto[i + 1]
        i += 2
    return op


def detalle_checks(v):
    """Una línea por check con su `detalle`, para ver el estado de cada gate aunque el veredicto sea VERDE."""
    return "\n".join(f"- {r.regla}: {r.detalle}" for r in v.checks)


def smoke(anim, estilo, direccion=None, skin=SKIN_DEFECTO):
    """Gate de humo de una animación: una dirección con esa skin; imprime el informe y el detalle de cada check,
    y devuelve 0 VERDE / 1 ROJO."""
    ficha = skins.ficha(skin)
    dirs = [direccion or ESTILOS[estilo]["direcciones"][0]]
    v = gates.correr([
        lambda: gates.check_zonas(anim, estilo, ficha=ficha, dirs=dirs),
        lambda: gates.check_pulido(anim, estilo, ficha=ficha, dirs=dirs),
    ])
    print(gates.informe(v))
    print(detalle_checks(v))
    return 0 if v.verde else 1


def main(argv=None):
    """CLI del proceso de animación: devuelve 0 VERDE, 1 ROJO y 2 error de uso o nombre desconocido."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] != "smoke":
        print(__doc__.strip())
        return 2
    if len(args) < 2 or args[1].startswith("--"):
        print(USO, file=sys.stderr)
        return 2
    anim = args[1]
    try:
        op = _opciones(args[2:])
    except ValueError as e:
        print(f"{USO} ({e})", file=sys.stderr)
        return 2
    if op["estilo"] is None:
        print(f"{USO} (falta --estilo)", file=sys.stderr)
        return 2
    estilo = op["estilo"]
    if estilo not in ESTILOS:
        print(f"estilo desconocido: {estilo!r}; disponibles: {', '.join(ESTILOS)}", file=sys.stderr)
        return 2
    if anim not in POSES:
        print(f"animación desconocida: {anim!r}; disponibles: {', '.join(POSES)}", file=sys.stderr)
        return 2
    if op["dir"] is not None and op["dir"] not in ESTILOS[estilo]["direcciones"]:
        print(f"dirección desconocida: {op['dir']!r}; disponibles: {', '.join(ESTILOS[estilo]['direcciones'])}",
              file=sys.stderr)
        return 2
    if not os.path.exists(op["skin"]):
        print(f"no está la skin: {op['skin']}", file=sys.stderr)
        return 2
    return smoke(anim, estilo, op["dir"], op["skin"])


if __name__ == "__main__":
    raise SystemExit(main())
