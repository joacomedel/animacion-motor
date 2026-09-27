"""Genera sprites_lib/MAPA.md: la librería resumida (módulos, funciones públicas, componentes, anclas, estilos)
para no tener que leer el código entero antes de usarla o extenderla.

Uso:  .venv/bin/python -m sprites_lib.mapa        (reescribe MAPA.md; un test avisa si quedó desactualizado)
"""
import ast
import os

AQUI = os.path.dirname(__file__)
RUTA = os.path.join(AQUI, "MAPA.md")
MODULOS = ["escala", "paleta", "estilos", "cuerpo", "poses", "ciclos", "rig", "render3d", "armado", "ficha",
           "tests_personaje", "comparar_estilo", "hoja_modelo", "fotos_control", "exportar", "referencia",
           "analizar", "pixel2d", "lado_a_lado", "componentes/__init__"]


def _primera(doc):
    return (doc or "").strip().split("\n")[0].strip()


def _firma(fn):
    a = ast.unparse(fn.args)
    return f"{fn.name}({a})"


def _modulo(nombre):
    arbol = ast.parse(open(os.path.join(AQUI, nombre + ".py"), encoding="utf-8").read())
    lineas = [f"### `{nombre.replace('/__init__', '')}` — {_primera(ast.get_docstring(arbol))}"]
    for n in arbol.body:
        if isinstance(n, ast.FunctionDef) and not n.name.startswith("_"):
            lineas.append(f"- `{_firma(n)}` {_primera(ast.get_docstring(n))}".rstrip())
        elif isinstance(n, ast.ClassDef) and not n.name.startswith("_"):
            metodos = [m.name for m in n.body if isinstance(m, ast.FunctionDef) and not m.name.startswith("_")]
            extra = f" · métodos: {', '.join(metodos)}" if metodos else ""
            lineas.append(f"- clase `{n.name}` {_primera(ast.get_docstring(n))}{extra}".rstrip())
    return "\n".join(lineas)


def generar():
    from .componentes import REGISTRO
    from .cuerpo import VOCABULARIO
    from .estilos import ACTIVOS, ESTILOS
    from .escala import TAMANOS
    out = ["# Mapa de sprites_lib (generado: `.venv/bin/python -m sprites_lib.mapa`, no editar a mano)", "",
           "Flujo: ficha YAML → `ficha.cargar` → `armado.render_cuadro` (cuerpo base + componentes → "
           "`cuerpo.posar` → `render3d.Escena`) → `Cuadro` (img + buffers) → tests / hoja / exportar.", "",
           "## Estilos", "| estilo | vista | direcciones | adulto px | celda | activo |", "|---|---|---|---|---|---|"]
    for k, e in ESTILOS.items():
        t = TAMANOS[k]
        out.append(f"| {k} | {e['vista']} | {' '.join(e['direcciones'])} | {t['adulto_px']} | "
                   f"{t['celdas']['adulto'][0]}×{t['celdas']['adulto'][1]} | {'sí' if k in ACTIVOS else 'no'} |")
    out += ["", "## Anclas", ", ".join(sorted(VOCABULARIO)), "",
            "## Componentes (tipo · anclas · material por defecto · parámetros)"]
    for tipo, c in sorted(REGISTRO.items()):
        if not type(c).__module__.startswith("sprites_lib.componentes"):
            continue                    # componentes de prueba registrados por los tests
        anclas = ", ".join(c.anclas_validas) or "cualquiera"
        params = ", ".join(f"{k}={v!r}" for k, v in c.params_defecto.items()) or "—"
        out.append(f"- `{tipo}` · {anclas} · {c.material_defecto or '—'} · {params}")
    out += ["", "## Módulos"]
    out += [_modulo(m) + "\n" for m in MODULOS if os.path.exists(os.path.join(AQUI, m + ".py"))]
    return "\n".join(out).rstrip() + "\n"


if __name__ == "__main__":
    open(RUTA, "w", encoding="utf-8").write(generar())
    print(f"→ {RUTA}")
