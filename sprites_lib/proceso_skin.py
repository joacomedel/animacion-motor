"""Proceso de skin: smoke de una skin pintada (carga 32×32, zonas, pulido y determinismo).

Una skin es un PNG de 32×32 que se pinta sobre el muñeco base (`skins/guia.png`); el smoke la renderiza con la
pose simple (`quieto` por defecto) y la pasa por el gate: la skin carga y mide 32×32, `gates.check_zonas` y
`gates.check_pulido` sobre su ficha, y `gates.check_determinismo` del render de esa ficha en esa pose. Es la
primera red antes de aprobar la skin.

El PNG se busca en `skins/<nombre>.png` **de la raíz del kit**, no del cwd (igual que la skin por defecto de
`proceso_anim`): así el comando funciona desde cualquier directorio.

Uso:
  .venv/bin/python -m sprites_lib.proceso_skin smoke <nombre> [--anim quieto] [--estilo stardew]
      → informe VERDE/ROJO de la skin en esa pose (exit 0 VERDE / 1 ROJO)
Animaciones: ver `sprites_lib.poses.POSES`. Estilos: ver `sprites_lib.estilos.ESTILOS`.
Uso incorrecto o skin inexistente: exit 2.
"""
import os
import sys

from . import gates, skins
from .estilos import ESTILOS
from .poses import POSES

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USO = "uso: proceso_skin smoke <nombre> [--anim quieto] [--estilo stardew]"


def _ruta_skin(nombre):
    """PNG de la skin en la raíz del kit (`skins/<nombre>.png`), para que el comando no dependa del cwd."""
    return os.path.join(RAIZ, "skins", f"{nombre}.png")


def check_carga(ruta):
    """La skin carga con `skins.cargar` y mide 32×32 (la medida la valida el propio cargador); cualquier falla de
    lectura o medida queda como `Resultado` rojo con el mensaje del error."""
    try:
        skins.cargar(ruta)
    except (ValueError, OSError) as e:
        return gates.Resultado("skin 32×32", False, str(e))
    return gates.Resultado("skin 32×32", True, f"{ruta}: carga y mide {skins.LADO}×{skins.LADO}")


def correr_gate(ruta, anim="quieto", estilo="stardew"):
    """Veredicto de la skin en esa pose: carga 32×32, zonas y pulido de su ficha, y determinismo del render de esa
    ficha (verifica también su camino de carga).

    Si la skin no carga no se puede armar su ficha: zonas, pulido y determinismo quedan fuera y el veredicto ya es
    ROJO.
    """
    carga = check_carga(ruta)
    checks = [lambda: carga]
    if carga.ok:
        ficha = skins.ficha(ruta)
        checks += [lambda: gates.check_zonas(anim, estilo, ficha=ficha),
                   lambda: gates.check_pulido(anim, estilo, ficha=ficha),
                   lambda: gates.check_determinismo(estilo, pose=anim, ficha=ficha)]
    return gates.correr(checks)


def smoke(nombre, anim="quieto", estilo="stardew"):
    """Corre el gate de la skin y imprime el informe; devuelve 0 VERDE / 1 ROJO."""
    v = correr_gate(_ruta_skin(nombre), anim, estilo)
    print(gates.informe(v))
    return 0 if v.verde else 1


def _opciones(resto, permitidas, por_defecto):
    """Parte las opciones permitidas; error de uso si falta el valor, sobra un argumento o la opción no
    corresponde al subcomando."""
    op = dict(por_defecto)
    i = 0
    while i < len(resto):
        arg = resto[i]
        if not arg.startswith("--") or arg[2:] not in permitidas:
            raise ValueError(f"argumento desconocido: {arg!r}")
        if i + 1 >= len(resto):
            raise ValueError(f"falta el valor de {arg}")
        op[arg[2:]] = resto[i + 1]
        i += 2
    return op


def main(argv=None):
    """CLI del proceso de skin: devuelve 0 VERDE, 1 ROJO y 2 error de uso o skin inexistente."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] != "smoke":
        print(__doc__.strip())
        return 2
    if len(args) < 2 or args[1].startswith("--"):
        print(USO, file=sys.stderr)
        return 2
    nombre = args[1]
    try:
        op = _opciones(args[2:], ("anim", "estilo"), {"anim": "quieto", "estilo": "stardew"})
    except ValueError as e:
        print(f"{USO} ({e})", file=sys.stderr)
        return 2
    if op["estilo"] not in ESTILOS:
        print(f"estilo desconocido: {op['estilo']!r}; disponibles: {', '.join(ESTILOS)}", file=sys.stderr)
        return 2
    if op["anim"] not in POSES:
        print(f"animación desconocida: {op['anim']!r}; disponibles: {', '.join(POSES)}", file=sys.stderr)
        return 2
    ruta = _ruta_skin(nombre)
    if not os.path.isfile(ruta):
        print(f"no está la skin: {ruta}", file=sys.stderr)
        return 2
    return smoke(nombre, op["anim"], op["estilo"])


if __name__ == "__main__":
    raise SystemExit(main())
