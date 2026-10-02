#!/usr/bin/env python3
"""Visor local de skins y animaciones.

Lee la carpeta de salidas (salida/ por defecto) y muestra los GIFs/PNGs
en el navegador. Solo lectura: no renderiza, no edita, no borra.

Uso:
    .venv/bin/python visor.py [--raiz salida] [--raiz output] [--puerto 8765] [--no-abrir]
"""

import argparse
import json
import mimetypes
import sys
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlparse

# Orden de animaciones según sprites_lib.poses.POSES
try:
    from sprites_lib.poses import POSES

    ORDEN_POSES = list(POSES.keys())
except ImportError:
    ORDEN_POSES = ["neutra", "quieto", "caminar_lpc", "saltar", "agachar", "golpear"]

# Orden cenital de direcciones
DIRECCIONES_4 = ["S", "E", "N", "W"]
DIRECCIONES_8 = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
# Orden de estilos conocidos (4 direcciones antes que 8)
ORDEN_ESTILOS = ["stardew", "stardew8"]
EXTENSIONES_PERMITIDAS = {".gif", ".png", ".json"}


def descubrir(raiz: Path) -> list[dict]:
    """Descubre personajes y animaciones bajo una raíz.

    Layout del proyecto: <raíz>/<personaje>/<estilo>/<animación>/. Personaje válido = carpeta con
    al menos una animación válida. Estilo = carpeta intermedia (`stardew` 4 dir, `stardew8` 8 dir).
    Animación válida = carpeta cuyo nombre es el prefijo de archivos (<anim>/ con <anim>_todas.gif
    o <anim>.png). Se acepta también el layout sin estilo (<personaje>/<anim>/) por compatibilidad.
    Se ignoran las carpetas que empiezan con '_' y todo lo que no matchee.
    """
    if not raiz.exists() or not raiz.is_dir():
        return []

    personajes = []
    for entrada in sorted(raiz.iterdir(), key=lambda p: p.name.lower()):
        if not entrada.is_dir() or entrada.name.startswith("_"):
            continue

        animaciones = _descubrir_animaciones(entrada, raiz)
        if animaciones:
            personajes.append(
                {
                    "nombre": entrada.name,
                    "raiz": raiz.name,
                    "animaciones": animaciones,
                }
            )

    return personajes


def _es_animacion(directorio: Path) -> bool:
    """True si `directorio` es una animación: existe <dir>/<dir>_todas.gif o <dir>/<dir>.png."""
    nombre = directorio.name
    return (directorio / f"{nombre}_todas.gif").exists() or (
        directorio / f"{nombre}.png"
    ).exists()


def _leer_animacion(entrada: Path, prefijo: str, estilo, raiz: Path) -> dict:
    """Arma el dict de una animación a partir de su carpeta, con los metadatos del JSON y los GIFs."""
    gif_todas = entrada / f"{prefijo}_todas.gif"
    hoja = entrada / f"{prefijo}.png"
    json_file = entrada / f"{prefijo}.json"
    meta = _leer_meta(json_file)

    if meta and "animations" in meta:
        direcciones = _ordenar_direcciones(list(meta["animations"].keys()))
    else:
        direcciones = _derivar_direcciones(entrada, prefijo)

    cuadros = None
    if meta and "animations" in meta:
        for d in DIRECCIONES_8 if len(direcciones) == 8 else DIRECCIONES_4:
            if d in meta["animations"] and meta["animations"][d]:
                cuadros = len(meta["animations"][d])
                break

    por_direccion = {}
    for d in direcciones:
        gif_d = entrada / f"{prefijo}_{d}.gif"
        if gif_d.exists():
            por_direccion[d] = str(gif_d.relative_to(raiz.parent))

    return {
        "nombre": prefijo,
        "carpeta": entrada.name,
        "estilo": estilo,
        "cuadros": cuadros,
        "fps": meta.get("fps") if meta else None,
        "loop": meta.get("loop") if meta else None,
        "celda": meta.get("cell") if meta else None,
        "direcciones": direcciones,
        "gif": str(gif_todas.relative_to(raiz.parent)) if gif_todas.exists() else None,
        "hoja": str(hoja.relative_to(raiz.parent)) if hoja.exists() else None,
        "json": str(json_file.relative_to(raiz.parent)) if json_file.exists() else None,
        "por_direccion": por_direccion,
    }


def _descubrir_animaciones(personaje_dir: Path, raiz: Path) -> list[dict]:
    """Descubre animaciones dentro de un personaje, con o sin nivel de estilo, en orden de POSES."""
    animaciones = []
    for entrada in sorted(personaje_dir.iterdir(), key=lambda p: p.name.lower()):
        if not entrada.is_dir() or entrada.name.startswith("_"):
            continue

        if _es_animacion(entrada):
            # Layout sin estilo: <personaje>/<animación>/
            animaciones.append(_leer_animacion(entrada, entrada.name, None, raiz))
            continue

        # Layout con estilo: <personaje>/<estilo>/<animación>/
        for anim_dir in sorted(entrada.iterdir(), key=lambda p: p.name.lower()):
            if (
                anim_dir.is_dir()
                and not anim_dir.name.startswith("_")
                and _es_animacion(anim_dir)
            ):
                animaciones.append(
                    _leer_animacion(anim_dir, anim_dir.name, entrada.name, raiz)
                )

    animaciones.sort(key=_sort_key)
    return animaciones


def _sort_key(a: dict):
    """Ordena por pose (POSES primero), luego por estilo (stardew antes que stardew8) y nombre."""
    nombre = a["nombre"]
    pose = ORDEN_POSES.index(nombre) if nombre in ORDEN_POSES else len(ORDEN_POSES)
    estilo = a.get("estilo")
    if estilo is None:
        pos_estilo = -1
    elif estilo in ORDEN_ESTILOS:
        pos_estilo = ORDEN_ESTILOS.index(estilo)
    else:
        pos_estilo = len(ORDEN_ESTILOS)
    return (pose, pos_estilo, nombre)


def _ordenar_direcciones(dirs: list[str]) -> list[str]:
    """Ordena direcciones en orden cenital: S E N W o S SE E NE N NW W SW."""
    if len(dirs) == 8 or any(d in dirs for d in ["SE", "NE", "NW", "SW"]):
        orden = DIRECCIONES_8
    else:
        orden = DIRECCIONES_4
    return [d for d in orden if d in dirs]


def _leer_meta(json_file: Path) -> dict | None:
    """Lee el JSON de metadatos y devuelve el dict 'meta' o None."""
    if not json_file.exists():
        return None
    try:
        data = json.loads(json_file.read_text(encoding="utf-8"))
        return data.get("meta")
    except (json.JSONDecodeError, OSError):
        return None


def _derivar_direcciones(anim_dir: Path, prefijo: str) -> list[str]:
    """Deriva direcciones de los archivos <prefijo>_<D>.gif cuando no hay JSON."""
    direcciones = []
    for d in DIRECCIONES_8:
        if (anim_dir / f"{prefijo}_{d}.gif").exists():
            direcciones.append(d)
    return _ordenar_direcciones(direcciones)


def _a_url(ruta: str) -> str:
    """Convierte una ruta de sistema a URL para la API."""
    return "/archivo/" + ruta.replace("\\", "/")


def _personajes_a_api(personajes: list[dict], raices: list[str]) -> dict:
    """Prepara la respuesta de /api/personajes con URLs en vez de rutas."""
    resultado = []
    for p in personajes:
        animaciones = []
        for a in p["animaciones"]:
            animaciones.append(
                {
                    "nombre": a["nombre"],
                    "carpeta": a["carpeta"],
                    "estilo": a.get("estilo"),
                    "cuadros": a["cuadros"],
                    "fps": a["fps"],
                    "loop": a["loop"],
                    "celda": a["celda"],
                    "direcciones": a["direcciones"],
                    "gif": _a_url(a["gif"]) if a["gif"] else None,
                    "hoja": _a_url(a["hoja"]) if a["hoja"] else None,
                    "json": _a_url(a["json"]) if a["json"] else None,
                    "por_direccion": {
                        d: _a_url(r) for d, r in a["por_direccion"].items()
                    },
                }
            )
        resultado.append(
            {
                "nombre": p["nombre"],
                "raiz": p["raiz"],
                "animaciones": animaciones,
            }
        )
    return {"raices": raices, "personajes": resultado}


HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Visor de Skins</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #1a1a2e;
    color: #eee;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}
header {
    background: #16213e;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    border-bottom: 2px solid #0f3460;
}
h1 { font-size: 1.2rem; color: #e94560; margin-right: 8px; }
select {
    padding: 6px 12px;
    border-radius: 4px;
    border: 1px solid #0f3460;
    background: #1a1a2e;
    color: #eee;
    font-size: 0.95rem;
    cursor: pointer;
}
select:hover { border-color: #e94560; }
.contador { font-size: 0.85rem; color: #888; }
main {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
    gap: 16px;
}
#contenedor-imagen {
    background:
        linear-gradient(45deg, #222 25%, transparent 25%),
        linear-gradient(-45deg, #222 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, #222 75%),
        linear-gradient(-45deg, transparent 75%, #222 75%);
    background-size: 20px 20px;
    background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
    background-color: #1a1a2e;
    border: 2px solid #0f3460;
    border-radius: 8px;
    padding: 20px;
    min-width: 320px;
    min-height: 320px;
    display: flex;
    align-items: center;
    justify-content: center;
}
#imagen {
    max-width: 100%;
    max-height: 70vh;
    image-rendering: pixelated;
}
#datos {
    font-size: 0.85rem;
    color: #aaa;
    text-align: center;
    max-width: 600px;
}
#vistas {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
}
button {
    padding: 6px 14px;
    border-radius: 4px;
    border: 1px solid #0f3460;
    background: #16213e;
    color: #eee;
    cursor: pointer;
    font-size: 0.85rem;
}
button:hover { border-color: #e94560; }
button.activo { background: #e94560; border-color: #e94560; color: #fff; }
#vacio {
    text-align: center;
    color: #888;
    padding: 40px;
}
#vacio code {
    background: #16213e;
    padding: 2px 8px;
    border-radius: 4px;
    color: #e94560;
}
.atajos {
    font-size: 0.75rem;
    color: #666;
    text-align: center;
}
.atajos kbd {
    background: #16213e;
    padding: 2px 6px;
    border-radius: 3px;
    border: 1px solid #0f3460;
}
</style>
</head>
<body>
<header>
    <h1>Visor de Skins</h1>
    <select id="sel-personaje"></select>
    <span class="contador" id="cont-personaje"></span>
    <select id="sel-animacion"></select>
    <span class="contador" id="cont-animacion"></span>
</header>
<main>
    <div id="vistas">
        <button data-vista="todas" class="activo">Todas</button>
        <button data-vista="S">S</button>
        <button data-vista="SE">SE</button>
        <button data-vista="E">E</button>
        <button data-vista="NE">NE</button>
        <button data-vista="N">N</button>
        <button data-vista="NW">NW</button>
        <button data-vista="W">W</button>
        <button data-vista="SW">SW</button>
        <button data-vista="hoja">Hoja</button>
    </div>
    <div id="contenedor-imagen">
        <div id="vacio">
            <p>No hay personajes para mostrar.</p>
            <p>Corré <code>./render_skins.sh</code> para generar skins.</p>
        </div>
        <img id="imagen" style="display:none" alt="">
    </div>
    <div id="datos"></div>
    <div class="atajos">
        <kbd>←</kbd><kbd>→</kbd> personaje &nbsp;
        <kbd>↑</kbd><kbd>↓</kbd> animación &nbsp;
        <kbd>g</kbd> gif/hoja &nbsp;
        <kbd>r</kbd> recargar
    </div>
</main>
<script>
let datos = null;
let idxPersonaje = 0;
let idxAnimacion = 0;
let vista = 'todas';

async function cargar() {
    const resp = await fetch('/api/personajes');
    datos = await resp.json();
    renderizarSelects();
    mostrar();
}

function renderizarSelects() {
    const selP = document.getElementById('sel-personaje');
    const selA = document.getElementById('sel-animacion');
    selP.innerHTML = '';
    selA.innerHTML = '';
    if (!datos || !datos.personajes.length) return;
    datos.personajes.forEach((p, i) => {
        const opt = document.createElement('option');
        opt.value = i;
        opt.textContent = p.nombre;
        selP.appendChild(opt);
    });
    const p = datos.personajes[idxPersonaje];
    p.animaciones.forEach((a, i) => {
        const opt = document.createElement('option');
        opt.value = i;
        const dirs = a.direcciones.length;
        opt.textContent = `${a.estilo ? a.estilo + ' · ' : ''}${a.nombre} (${dirs} dir)`;
        selA.appendChild(opt);
    });
    selP.value = idxPersonaje;
    selA.value = idxAnimacion;
    document.getElementById('cont-personaje').textContent = `${idxPersonaje + 1}/${datos.personajes.length}`;
    document.getElementById('cont-animacion').textContent = `${idxAnimacion + 1}/${p.animaciones.length}`;
}

function mostrar() {
    const img = document.getElementById('imagen');
    const vacio = document.getElementById('vacio');
    const datosDiv = document.getElementById('datos');
    if (!datos || !datos.personajes.length) {
        img.style.display = 'none';
        vacio.style.display = 'block';
        datosDiv.textContent = '';
        return;
    }
    const p = datos.personajes[idxPersonaje];
    const a = p.animaciones[idxAnimacion];
    let url = null;
    if (vista === 'hoja') {
        url = a.hoja;
    } else if (vista === 'todas') {
        url = a.gif || a.hoja;
    } else {
        url = a.por_direccion[vista] || a.gif || a.hoja;
    }
    if (url) {
        img.src = url;
        img.style.display = 'block';
        vacio.style.display = 'none';
    } else {
        img.style.display = 'none';
        vacio.style.display = 'block';
    }
    const partes = [];
    if (a.cuadros != null) partes.push(`${a.cuadros} cuadros`);
    partes.push(`${a.direcciones.length} direcciones`);
    if (a.fps != null) partes.push(`${a.fps} fps`);
    if (a.loop != null) partes.push(a.loop ? 'loop' : 'no loop');
    if (a.celda) partes.push(`celda ${a.celda.w}×${a.celda.h}`);
    datosDiv.textContent = partes.join(' · ');
}

function cambiarPersonaje(delta) {
    if (!datos || !datos.personajes.length) return;
    idxPersonaje = (idxPersonaje + delta + datos.personajes.length) % datos.personajes.length;
    idxAnimacion = 0;
    renderizarSelects();
    mostrar();
}

function cambiarAnimacion(delta) {
    if (!datos || !datos.personajes.length) return;
    const p = datos.personajes[idxPersonaje];
    idxAnimacion = (idxAnimacion + delta + p.animaciones.length) % p.animaciones.length;
    renderizarSelects();
    mostrar();
}

function setVista(v) {
    vista = v;
    document.querySelectorAll('#vistas button').forEach(b => {
        b.classList.toggle('activo', b.dataset.vista === v);
    });
    mostrar();
}

document.getElementById('sel-personaje').addEventListener('change', e => {
    idxPersonaje = parseInt(e.target.value);
    idxAnimacion = 0;
    renderizarSelects();
    mostrar();
});
document.getElementById('sel-animacion').addEventListener('change', e => {
    idxAnimacion = parseInt(e.target.value);
    mostrar();
});
document.querySelectorAll('#vistas button').forEach(b => {
    b.addEventListener('click', () => setVista(b.dataset.vista));
});

document.addEventListener('keydown', e => {
    if (e.target.tagName === 'SELECT') return;
    switch (e.key) {
        case 'ArrowLeft': cambiarPersonaje(-1); break;
        case 'ArrowRight': cambiarPersonaje(1); break;
        case 'ArrowUp': cambiarAnimacion(-1); break;
        case 'ArrowDown': cambiarAnimacion(1); break;
        case 'g': setVista(vista === 'hoja' ? 'todas' : 'hoja'); break;
        case 'r': cargar(); break;
    }
});

cargar();
</script>
</body>
</html>
"""


class VisorHandler(BaseHTTPRequestHandler):
    """Handler HTTP del visor."""

    raices: list[Path] = []

    def log_message(self, format, *args):
        """Silenciar logs de requests."""
        pass

    def _enviar_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _enviar_html(self, html: str):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _enviar_archivo(self, ruta: Path):
        if not ruta.exists() or not ruta.is_file():
            self._404()
            return
        ext = ruta.suffix.lower()
        if ext not in EXTENSIONES_PERMITIDAS:
            self._404()
            return
        # Verificar que está dentro de las raíces permitidas
        if not self._dentro_de_raices(ruta):
            self._404()
            return
        content_type = mimetypes.guess_type(str(ruta))[0] or "application/octet-stream"
        body = ruta.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _dentro_de_raices(self, ruta: Path) -> bool:
        """Verifica que la ruta está dentro de alguna de las raíces permitidas."""
        try:
            ruta_abs = ruta.resolve()
            for raiz in self.raices:
                try:
                    raiz_abs = raiz.resolve()
                    ruta_abs.relative_to(raiz_abs)
                    return True
                except ValueError:
                    continue
        except OSError:
            return False
        return False

    def _404(self):
        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"404")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._enviar_html(HTML)
        elif path == "/api/personajes":
            personajes = []
            for raiz in self.raices:
                personajes.extend(descubrir(raiz))
            raices_nombres = [r.name for r in self.raices]
            self._enviar_json(_personajes_a_api(personajes, raices_nombres))
        elif path.startswith("/archivo/"):
            ruta_relativa = unquote(path[len("/archivo/") :])
            if not ruta_relativa:
                self._404()
                return
            # Buscar en las raíces
            encontrado = None
            for raiz in self.raices:
                candidato = raiz.parent / ruta_relativa
                if candidato.exists() and candidato.is_file():
                    encontrado = candidato
                    break
            if encontrado:
                self._enviar_archivo(encontrado)
            else:
                self._404()
        else:
            self._404()


def main():
    parser = argparse.ArgumentParser(description="Visor local de skins y animaciones")
    parser.add_argument(
        "--raiz", action="append", default=[], help="Carpeta de salidas (repetible)"
    )
    parser.add_argument("--puerto", type=int, default=8765)
    parser.add_argument(
        "--no-abrir", action="store_true", help="No abrir el navegador automáticamente"
    )
    args = parser.parse_args()

    # Raíces: por defecto 'salida', más las pasadas por --raiz
    raices = []
    if not args.raiz:
        raices.append(Path("salida"))
    else:
        for r in args.raiz:
            raices.append(Path(r))

    # Filtrar raíces que no existen
    raices_validas = []
    for r in raices:
        if r.exists() and r.is_dir():
            raices_validas.append(r)
        else:
            print(
                f"Advertencia: la raíz '{r}' no existe o no es una carpeta. Se ignora.",
                file=sys.stderr,
            )

    if not raices_validas:
        print("Error: no hay raíces válidas para mostrar.", file=sys.stderr)
        sys.exit(1)

    # Configurar el handler
    VisorHandler.raices = raices_validas

    # Levantar servidor
    server = HTTPServer(("127.0.0.1", args.puerto), VisorHandler)
    url = f"http://127.0.0.1:{args.puerto}"
    print(f"Visor corriendo en {url}")
    print(f"Raíces: {', '.join(str(r) for r in raices_validas)}")

    if not args.no_abrir:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido.")
        server.shutdown()


if __name__ == "__main__":
    main()
