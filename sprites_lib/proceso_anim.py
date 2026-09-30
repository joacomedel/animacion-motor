"""Proceso de animación: smoke, validar y aprobar una animación sobre una skin, con los gates universales.

El smoke renderiza **una** dirección con la skin indicada y la pasa por `gates.check_zonas` (construcción: ninguna
alerta MEDIA/ALTA por revisar) y `gates.check_pulido` (movimiento, limpieza y espejo: ningún hallazgo MAL). Es la
primera red antes de validar todas las direcciones. `validar` renderiza todas las direcciones y corre el gate
completo (zonas, pulido, determinismo, deriva del ciclo, plantilla contra la referencia y fotos de control si hay
cuadros congelados). `aprobar` corre el mismo gate y, si está VERDE (o hay `--excepcion`), congela
`aprobados/animaciones/<anim>/<estilo>/` (cuadros de control, `metricas.json` y `estado.json`, este último como
marca del congelado) y exporta la fuente a `salida/animaciones/<anim>/<estilo>/`.

El default de `--skin` es un asset del kit (`skins/zonas.png`) y se resuelve contra la raíz del paquete, no contra
el directorio de trabajo: así el comando funciona desde cualquier cwd. Los artefactos de trabajo (`aprobados/` y
`salida/`) sí quedan relativos al cwd, que es donde el proceso los congela.

Uso:
  .venv/bin/python -m sprites_lib.proceso_anim smoke <anim> --estilo <estilo> [--dir D] [--skin RUTA]
      → informe VERDE/ROJO de zonas y pulido en una dirección (exit 0 VERDE / 1 ROJO)
      `--dir` por defecto: la primera dirección del estilo.
  .venv/bin/python -m sprites_lib.proceso_anim validar <anim> --estilo <estilo> [--skin RUTA]
      → gate completo de todas las direcciones (exit 0 VERDE / 1 ROJO)
  .venv/bin/python -m sprites_lib.proceso_anim aprobar <anim> --estilo <estilo> [--skin RUTA] [--excepcion MOTIVO]
      → congela la animación aprobada y exporta la fuente (exit 0/1)
Animaciones: ver `sprites_lib.poses.POSES`. Estilos: ver `sprites_lib.estilos.ESTILOS`.
Uso incorrecto, animación o estilo desconocidos: exit 2.
"""
import json
import os
import re
import sys

from . import armado, comparar_plantilla, estado, exportar, fotos_control, gates, poses, pulido, skins
from .estilos import ESTILOS
from .poses import POSES

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIN_DEFECTO = os.path.join(RAIZ, "skins", "zonas.png")
RAIZ_APROBADOS = os.path.join("aprobados", "animaciones")
RAIZ_SALIDA = os.path.join("salida", "animaciones")
REFERENCIAS = {"caminar_lpc": "lpc"}
NOMBRE = re.compile(r"^[a-z0-9_]+$")
USO = ("uso: proceso_anim smoke <anim> --estilo <estilo> [--dir D] [--skin RUTA]\n"
       "     proceso_anim validar <anim> --estilo <estilo> [--skin RUTA]\n"
       "     proceso_anim aprobar <anim> --estilo <estilo> [--skin RUTA] [--excepcion MOTIVO]")


def _opciones(resto, permitidas=("estilo", "dir", "skin")):
    """Parte las opciones permitidas (`--estilo/--dir/--skin/--excepcion`); error de uso si falta el valor,
    sobra un argumento o la opción no corresponde al subcomando."""
    op = {k: None for k in permitidas}
    op["skin"] = SKIN_DEFECTO
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


def fuentes_actuales(anim):
    """Fuentes de la animación para el hash de deriva: el ciclo entero (hash estable por claves ordenadas)."""
    return {"ciclo": estado.hash_obj(POSES[anim])}


def _carpeta(anim, estilo):
    return os.path.join(RAIZ_APROBADOS, anim, estilo)


def _dif(anim, estilo):
    return os.path.join(RAIZ_SALIDA, anim, estilo, "diferencias")


def _todo(anim, estilo, ficha):
    """Cuadros renderizados de la animación en todas las direcciones del estilo (para control y export)."""
    return {m: [armado.render_cuadro(ficha, estilo, anim, p, m) for p in range(POSES[anim]["n"])]
            for m in ESTILOS[estilo]["direcciones"]}


def _errs(f):
    return [e for k, e in f["err"].items() if k not in comparar_plantilla.SIN_META]


def check_plantilla(anim):
    """Compara el ciclo contra su referencia (`REFERENCIAS`): exige error medio de huesos ≤ `TOL_MEDIO` px; el
    peor caso y la silueta quedan como información. Sin referencia declarada queda omitido."""
    ref = REFERENCIAS.get(anim)
    if ref is None:
        return gates.Resultado(f"plantilla {anim}", True, "sin referencia: omitido", omitido=True)
    res = comparar_plantilla.medir(estilo=ref, pose=anim, mira="E")
    errs = [e for f in res["filas"] for e in _errs(f)]
    medio, peor = sum(errs) / len(errs), max(errs)
    ious = [f["iou"] for f in res["filas"]]
    ok = medio <= comparar_plantilla.TOL_MEDIO
    detalle = (f"medio {medio:.1f} px (meta ≤ {comparar_plantilla.TOL_MEDIO:.1f}; "
               f"peor {peor:.1f} px y silueta {sum(ious) / len(ious):.2f} informativos): {'OK' if ok else 'FALLA'}")
    return gates.Resultado(f"plantilla {anim}/{ref}", ok, detalle,
                           [f"c{f['cuadro']}: peor {max(_errs(f)):.1f} px, IoU {f['iou']:.2f}"
                            for f in res["filas"]])


def correr_gate(anim, estilo, ficha, todo=None, control=True):
    """Veredicto de la animación: zonas y pulido en todas las direcciones, determinismo, deriva del ciclo,
    plantilla contra la referencia y (con `control`) comparación con las fotos congeladas."""
    if todo is None:
        todo = _todo(anim, estilo, ficha)
    checks = [
        lambda: gates.check_zonas(anim, estilo, ficha=ficha),
        lambda: gates.check_pulido(anim, estilo, ficha=ficha),
        lambda: gates.check_determinismo(estilo, pose=anim),
        lambda: gates.check_deriva(estado.leer(_carpeta(anim, estilo)), fuentes_actuales(anim)),
        lambda: check_plantilla(anim),
    ]
    if control:
        checks.append(lambda: fotos_control.comparar(anim, estilo, todo, _dif(anim, estilo), raiz=RAIZ_APROBADOS))
    return gates.correr(checks)


def validar(anim, estilo, skin=SKIN_DEFECTO):
    """Renderiza todas las direcciones y corre el gate completo; imprime informe y detalle; 0 VERDE / 1 ROJO."""
    ficha = skins.ficha(skin)
    v = correr_gate(anim, estilo, ficha)
    print(gates.informe(v))
    print(detalle_checks(v))
    return 0 if v.verde else 1


def _metricas_json(anim, estilo, ficha, veredicto, carpeta):
    """Guarda `metricas.json`: gate, alertas de zonas por dirección, pulido y fps/loop del ciclo. Las alertas
    salen del análisis de zonas que `pulido.analizar` ya dejó en `_zonas`, para no repetir el render."""
    pul = pulido.analizar(anim=anim, estilo=estilo, ficha=ficha)
    alertas = {d: [a for a in pul["_zonas"]["alertas"] if a["dir"] == d] for d in ESTILOS[estilo]["direcciones"]}
    datos = {"anim": anim, "estilo": estilo, "verde": veredicto.verde, "informe": gates.informe(veredicto),
             "checks": [vars(r) for r in veredicto.checks], "fps": poses.fps(anim), "loop": poses.loop(anim),
             "alertas_por_direccion": alertas, "pulido": pul["resumen"]}
    ruta = os.path.join(carpeta, "metricas.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return ruta


def _exportar(anim, estilo, todo):
    """Exporta la hoja con una fila por dirección, el JSON con pivote/fps/loop y los GIF a `salida/animaciones`."""
    oy = poses.offset_y(anim)
    por_dir = {m: [c.img for c in frs] for m, frs in todo.items()}
    return exportar.exportar_direcciones(por_dir, anim, os.path.join(RAIZ_SALIDA, anim, estilo),
                                         fps=poses.fps(anim), pivote=armado.pivote(estilo, pose=anim),
                                         loop=poses.loop(anim),
                                         extra={"offset_y": oy} if oy is not None else None)


def aprobar(anim, estilo, skin=SKIN_DEFECTO, excepcion=None):
    """Corre el gate y, si está VERDE (o hay `excepcion`), congela control/métricas/estado y exporta la fuente;
    ROJO sin excepción no escribe nada. `estado.json` queda último, como marca del congelado."""
    ficha = skins.ficha(skin)
    todo = _todo(anim, estilo, ficha)
    v = correr_gate(anim, estilo, ficha, todo=todo, control=False)
    print(gates.informe(v))
    print(detalle_checks(v))
    if not v.verde and not excepcion:
        print('\nROJO: no se congeló nada (para aprobar igual hace falta --excepcion "motivo")')
        return 1
    if not v.verde:
        print(f"\nROJO con excepción: {excepcion}")
    carpeta = _carpeta(anim, estilo)
    os.makedirs(carpeta, exist_ok=True)
    fotos_control.guardar(anim, estilo, todo, raiz=RAIZ_APROBADOS)
    _metricas_json(anim, estilo, ficha, v, carpeta)
    print(f"→ {_exportar(anim, estilo, todo)} (export)")
    estado.escribir(carpeta, f"{anim}/{estilo}", fuentes_actuales(anim), "metricas.json", nota=excepcion)
    print(f"→ {carpeta} (congelado" + (f" con excepción: {excepcion}" if excepcion else "") + ")")
    return 0


def main(argv=None):
    """CLI del proceso de animación: devuelve 0 VERDE, 1 ROJO y 2 error de uso o nombre desconocido."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in ("smoke", "validar", "aprobar"):
        print(__doc__.strip())
        return 2
    cmd = args[0]
    if len(args) < 2 or args[1].startswith("--"):
        print(USO, file=sys.stderr)
        return 2
    anim = args[1]
    permitidas = {"smoke": ("estilo", "dir", "skin"), "validar": ("estilo", "skin"),
                  "aprobar": ("estilo", "skin", "excepcion")}[cmd]
    try:
        op = _opciones(args[2:], permitidas)
    except ValueError as e:
        print(f"{USO} ({e})", file=sys.stderr)
        return 2
    if op["estilo"] is None:
        print(f"{USO} (falta --estilo)", file=sys.stderr)
        return 2
    estilo = op["estilo"]
    if not NOMBRE.fullmatch(anim):
        print(f"nombre de animación inválido: {anim!r} (solo minúsculas, dígitos y _)", file=sys.stderr)
        return 2
    if anim not in POSES:
        print(f"animación desconocida: {anim!r}; disponibles: {', '.join(POSES)}", file=sys.stderr)
        return 2
    if not NOMBRE.fullmatch(estilo):
        print(f"estilo inválido: {estilo!r} (solo minúsculas, dígitos y _)", file=sys.stderr)
        return 2
    if estilo not in ESTILOS:
        print(f"estilo desconocido: {estilo!r}; disponibles: {', '.join(ESTILOS)}", file=sys.stderr)
        return 2
    if not os.path.exists(op["skin"]):
        print(f"no está la skin: {op['skin']}", file=sys.stderr)
        return 2
    if cmd == "smoke":
        if op["dir"] is not None and op["dir"] not in ESTILOS[estilo]["direcciones"]:
            print(f"dirección desconocida: {op['dir']!r}; disponibles: {', '.join(ESTILOS[estilo]['direcciones'])}",
                  file=sys.stderr)
            return 2
        return smoke(anim, estilo, op["dir"], op["skin"])
    if cmd == "validar":
        return validar(anim, estilo, op["skin"])
    return aprobar(anim, estilo, op["skin"], op["excepcion"])


if __name__ == "__main__":
    raise SystemExit(main())
