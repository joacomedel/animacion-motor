"""Proceso de skin: smoke, aprobar y lote de una skin pintada.

Una skin es un PNG de 32×32 que se pinta sobre el muñeco base (`skins/guia.png`); el smoke la renderiza con la
pose simple (`quieto` por defecto) y la pasa por el gate: la skin carga y mide 32×32, `gates.check_zonas` y
`gates.check_pulido` sobre su ficha, y `gates.check_determinismo` del render de esa ficha en esa pose. Es la
primera red antes de aprobar la skin.

`aprobar` corre ese gate y, si está VERDE (o hay `--excepcion`), congela `aprobados/skins/<nombre>/` con la hoja y
el `smoke.gif` de `quieto` en todas las direcciones del estilo, `metricas.json` (el veredicto) y `estado.json`
—este último al final, como marca del congelado—. `lote` recorre las animaciones aprobadas del estilo
(`aprobados/animaciones`), les corre el gate de zonas, pulido y deriva del ciclo, exporta las VERDE al formato del
juego (`skins.salida_juego`) y junta el informe en `docs/diagnostico/zonas/lote_<nombre>.md`; una animación ROJA no corta el
lote: queda listada sin exportar y el exit es 1.

El PNG se busca en `skins/<nombre>.png` **de la raíz del kit**, no del cwd (igual que la skin por defecto de
`proceso_anim`): así el comando funciona desde cualquier directorio.

Uso:
  .venv/bin/python -m sprites_lib.proceso_skin smoke <nombre> [--anim quieto] [--estilo stardew]
      → informe VERDE/ROJO de la skin en esa pose (exit 0 VERDE / 1 ROJO)
  .venv/bin/python -m sprites_lib.proceso_skin aprobar <nombre> [--estilo stardew] [--excepcion MOTIVO]
      → congela la skin aprobada en aprobados/skins/<nombre>/ (exit 0/1)
  .venv/bin/python -m sprites_lib.proceso_skin lote <nombre> [--estilo stardew] [--raiz output]
      → exporta las animaciones aprobadas y escribe docs/diagnostico/zonas/lote_<nombre>.md (exit 0/1)
Animaciones: ver `sprites_lib.poses.POSES`. Estilos: ver `sprites_lib.estilos.ESTILOS`.
Uso incorrecto, nombre de skin inválido o skin inexistente: exit 2.
"""

import os
import re
import sys

from . import armado, estado, exportar, gates, proceso_anim, skins
from .estilos import ESTILOS
from .poses import POSES, fps, loop, offset_y

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_APROBADOS = os.path.join("aprobados", "skins")
RAIZ_ANIMACIONES = os.path.join("aprobados", "animaciones")
RAIZ_INFORMES = os.path.join("docs", "diagnostico", "zonas")
NOMBRE = re.compile(r"^[a-z0-9_]+$")
USO = (
    "uso: proceso_skin smoke <nombre> [--anim quieto] [--estilo stardew]\n"
    "     proceso_skin aprobar <nombre> [--estilo stardew] [--excepcion MOTIVO]\n"
    "     proceso_skin lote <nombre> [--estilo stardew] [--raiz output]"
)


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
    return gates.Resultado(
        "skin 32×32", True, f"{ruta}: carga y mide {skins.LADO}×{skins.LADO}"
    )


def check_continuidad(ruta):
    """La espalda de cada zona de la skin cierra: la columna 0 y la última son el mismo texel (u da la vuelta en
    la espalda). Una costura abierta se ve como una línea dura en las vistas N/NE/NW. Ver `skins.continuidad`."""
    malas = skins.continuidad(ruta)
    return gates.Resultado(
        "costura de la espalda",
        not malas,
        f"{len(skins.ZONAS)} zonas cierran"
        if not malas
        else f"{len(malas)} zonas con costura abierta",
        [f"{zona}: {filas} filas no cierran" for zona, filas in malas],
    )


def correr_gate(ruta, anim="quieto", estilo="stardew"):
    """Veredicto de la skin en esa pose: carga 32×32, costura de la espalda, zonas y pulido de su ficha, y
    determinismo del render de esa ficha (verifica también su camino de carga).

    Si la skin no carga no se puede armar su ficha: el resto de los checks quedan fuera y el veredicto ya es
    ROJO.
    """
    carga = check_carga(ruta)
    checks = [lambda: carga]
    if carga.ok:
        ficha = skins.ficha(ruta)
        checks += [
            lambda: check_continuidad(ruta),
            lambda: gates.check_zonas(anim, estilo, ficha=ficha),
            lambda: gates.check_pulido(anim, estilo, ficha=ficha),
            lambda: gates.check_determinismo(estilo, pose=anim, ficha=ficha),
        ]
    return gates.correr(checks)


def smoke(nombre, anim="quieto", estilo="stardew"):
    """Corre el gate de la skin y imprime el informe; devuelve 0 VERDE / 1 ROJO."""
    v = correr_gate(_ruta_skin(nombre), anim, estilo)
    print(gates.informe(v))
    return 0 if v.verde else 1


def fuentes_skin(nombre):
    """Fuentes de la skin para congelar/derivar: el PNG y, si existe, el script que la pinta
    (`skins/pintar_<nombre>.py`)."""
    fuentes = {"skin": estado.hash_archivo(_ruta_skin(nombre))}
    script = os.path.join(RAIZ, "skins", f"pintar_{nombre}.py")
    if os.path.isfile(script):
        fuentes["pintar"] = estado.hash_archivo(script)
    return fuentes


def _por_dir_quieto(ruta, estilo):
    """Frames de `quieto` en todas las direcciones del estilo con la ficha de la skin: el mismo render que
    `skins.salida_juego` (incluida la paleta del estilo: fija si el estilo la declara), para la hoja y el
    `smoke.gif` congelados."""
    ficha = skins.ficha(ruta)
    n = POSES["quieto"]["n"]
    por_dir = {
        m: [armado.render_cuadro(ficha, estilo, "quieto", p, m).img for p in range(n)]
        for m in ESTILOS[estilo]["direcciones"]
    }
    skins.ajustar_a_paleta_fija(por_dir, estilo)
    return por_dir


def _exportar_quieto(ruta, nombre, estilo, carpeta):
    """Escribe en `carpeta` la hoja `<nombre>.png` y un GIF por dirección; el GIF de todas las direcciones queda
    como `smoke.gif`, el archivo que marca la aprobación de la skin."""
    por_dir = _por_dir_quieto(ruta, estilo)
    oy = offset_y("quieto")
    base = exportar.exportar_direcciones(
        por_dir,
        nombre,
        carpeta,
        fps=fps("quieto"),
        zoom=6,
        pivote=armado.pivote(estilo, pose="quieto"),
        loop=loop("quieto"),
        extra={"offset_y": oy} if oy else None,
    )
    os.replace(base + "_todas.gif", os.path.join(carpeta, "smoke.gif"))


def aprobar(nombre, estilo="stardew", excepcion=None):
    """Corre el gate de `smoke` y, si está VERDE o hay `excepcion`, congela la skin en `aprobados/skins/<nombre>/`
    (hoja, `smoke.gif`, `metricas.json` y `estado.json` último); ROJO sin excepción no escribe nada.

    Una skin que no carga no se puede renderizar: ni con `excepcion` se congela.
    """
    ruta = _ruta_skin(nombre)
    v = correr_gate(ruta, "quieto", estilo)
    print(gates.informe(v))
    if not v.verde and not excepcion:
        print(
            '\nROJO: no se congeló nada (para aprobar igual hace falta --excepcion "motivo")'
        )
        return 1
    if not check_carga(ruta).ok:
        print(
            "\nROJO: la skin no carga, así que no hay nada que congelar ni con --excepcion"
        )
        return 1
    if not v.verde:
        print(f"\nROJO con excepción: {excepcion}")
    carpeta = os.path.join(RAIZ_APROBADOS, nombre)
    os.makedirs(carpeta, exist_ok=True)
    _exportar_quieto(ruta, nombre, estilo, carpeta)
    gates.guardar(v, os.path.join(carpeta, "metricas.json"))
    estado.escribir(
        carpeta, nombre, fuentes_skin(nombre), "metricas.json", nota=excepcion
    )
    print(
        f"→ {carpeta} (congelado: hoja, smoke.gif, metricas.json y estado.json"
        + (f"; con excepción: {excepcion}" if excepcion else "")
        + ")"
    )
    return 0


def _gate_animacion(item, estilo, ficha):
    """Gate de una animación aprobada: zonas y pulido en todas las direcciones y deriva contra la fuente del ciclo
    (la misma que congeló `proceso_anim.aprobar`)."""
    anim = item["nombre"]
    return gates.correr(
        [
            lambda: gates.check_zonas(anim, estilo, ficha=ficha),
            lambda: gates.check_pulido(anim, estilo, ficha=ficha),
            lambda: gates.check_deriva(
                item["estado"], proceso_anim.fuentes_actuales(anim)
            ),
        ]
    )


def _informe_lote(nombre, estilo, raiz, filas):
    """Escribe `docs/diagnostico/zonas/lote_<nombre>.md`: por animación, el veredicto del gate y el destino del export (o el
    motivo por el que no se exportó)."""
    rojas = sum(1 for fila in filas if not fila["verde"])
    lineas = [
        f"# Lote {nombre}/{estilo}",
        "",
        f"- skin: `{_ruta_skin(nombre)}`",
        f"- export: `{raiz}/<nombre>/<estilo>/<anim>/`",
        f"- animaciones: {len(filas)} ({rojas} rojas)",
        "",
    ]
    for fila in filas:
        lineas += [f"## {fila['anim']}", "", "```", fila["informe"], "```", ""]
        if fila["error"]:
            lineas.append(f"sin exportar (excepción al exportar: {fila['error']})")
        elif fila["export"]:
            lineas.append(f"→ {fila['export']} (export)")
        else:
            lineas.append("sin exportar (gate ROJO)")
        lineas.append("")
    ruta = os.path.join(RAIZ_INFORMES, f"lote_{nombre}.md")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas))
    return ruta


def lote(nombre, estilo="stardew", raiz="output"):
    """Exporta en formato del juego todas las animaciones aprobadas del estilo con esta skin.

    Por animación corre el gate (zonas, pulido y deriva) y, si está VERDE, exporta con `skins.salida_juego`; una
    ROJA no corta el lote: queda listada sin exportar en `docs/diagnostico/zonas/lote_<nombre>.md` y el exit final es 1.
    Devuelve 0 si todas son VERDE y 1 si alguna falla o no hay animaciones aprobadas.
    """
    aprobadas = [a for a in estado.listar(RAIZ_ANIMACIONES) if a["estilo"] == estilo]
    if not aprobadas:
        print(f"no hay animaciones aprobadas para {estilo}")
        return 1
    ruta = _ruta_skin(nombre)
    try:
        ficha = skins.ficha(ruta)
    except (ValueError, OSError) as e:
        print(f"skin inválida: {e}", file=sys.stderr)
        return 1
    estado_skin = estado.leer(os.path.join(RAIZ_APROBADOS, nombre))
    if estado_skin:
        r = gates.check_deriva(estado_skin, fuentes_skin(nombre))
        if not r.ok:
            print(
                f"la skin cambió desde su aprobación: re-validar y re-aprobar ({r.detalle})",
                file=sys.stderr,
            )
            return 1
    else:
        print("advertencia: skin sin aprobar: se exporta igual", file=sys.stderr)
    filas, fallan = [], 0
    for item in aprobadas:
        anim = item["nombre"]
        v = _gate_animacion(item, estilo, ficha)
        verde, export, error = v.verde, None, None
        if verde:
            try:
                export = skins.salida_juego(ruta, anim, estilo, raiz=raiz, cuadros=True)
            except Exception as e:
                verde, error = False, str(e)
        if not verde:
            fallan += 1
        filas.append(
            {
                "anim": anim,
                "verde": verde,
                "informe": gates.informe(v),
                "export": export,
                "error": error,
            }
        )
        print(f"{anim}: {'VERDE' if verde else 'ROJO'}")
    print(f"→ {_informe_lote(nombre, estilo, raiz, filas)} (informe)")
    return 1 if fallan else 0


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
    """CLI del proceso de skin: devuelve 0 VERDE, 1 ROJO y 2 error de uso, nombre inválido o skin inexistente."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in ("smoke", "aprobar", "lote"):
        print(__doc__.strip())
        return 2
    cmd = args[0]
    if len(args) < 2 or args[1].startswith("--"):
        print(USO, file=sys.stderr)
        return 2
    nombre = args[1]
    permitidas = {
        "smoke": ("anim", "estilo"),
        "aprobar": ("estilo", "excepcion"),
        "lote": ("estilo", "raiz"),
    }
    por_defecto = {
        "smoke": {"anim": "quieto", "estilo": "stardew"},
        "aprobar": {"estilo": "stardew", "excepcion": None},
        "lote": {"estilo": "stardew", "raiz": "output"},
    }
    try:
        op = _opciones(args[2:], permitidas[cmd], por_defecto[cmd])
    except ValueError as e:
        print(f"{USO} ({e})", file=sys.stderr)
        return 2
    if not NOMBRE.fullmatch(nombre):
        print(
            f"nombre de skin inválido: {nombre!r} (solo minúsculas, dígitos y _)",
            file=sys.stderr,
        )
        return 2
    if op["estilo"] not in ESTILOS:
        print(
            f"estilo desconocido: {op['estilo']!r}; disponibles: {', '.join(ESTILOS)}",
            file=sys.stderr,
        )
        return 2
    if cmd == "smoke" and op["anim"] not in POSES:
        print(
            f"animación desconocida: {op['anim']!r}; disponibles: {', '.join(POSES)}",
            file=sys.stderr,
        )
        return 2
    ruta = _ruta_skin(nombre)
    if not os.path.isfile(ruta):
        print(f"no está la skin: {ruta}", file=sys.stderr)
        return 2
    if cmd == "smoke":
        return smoke(nombre, op["anim"], op["estilo"])
    if cmd == "aprobar":
        return aprobar(nombre, op["estilo"], op["excepcion"])
    return lote(nombre, op["estilo"], op["raiz"])


if __name__ == "__main__":
    raise SystemExit(main())
