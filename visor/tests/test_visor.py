"""Tests para el visor de skins y animaciones."""

import http.client
import json
import sys
import threading
from http.server import HTTPServer
from pathlib import Path

import pytest

# Agregar el directorio padre al path para poder importar visor
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import visor


def _crear_animacion(
    directorio: Path,
    nombre: str,
    con_gif_todas: bool = True,
    con_json: bool = True,
    direcciones: list[str] = None,
    carpeta: str = None,
):
    """Helper para crear una animación con sus archivos."""
    if direcciones is None:
        direcciones = ["S", "E", "N", "W"]
    if carpeta is None:
        carpeta = nombre
    anim_dir = directorio / carpeta
    anim_dir.mkdir(parents=True, exist_ok=True)

    if con_gif_todas:
        (anim_dir / f"{nombre}_todas.gif").write_bytes(b"GIF89a")

    (anim_dir / f"{nombre}.png").write_bytes(b"\x89PNG")

    if con_json:
        meta = {
            "fps": 10,
            "loop": True,
            "cell": {"w": 16, "h": 32},
            "animations": {
                d: [f"{nombre}_{d}_0", f"{nombre}_{d}_1"] for d in direcciones
            },
        }
        (anim_dir / f"{nombre}.json").write_text(json.dumps({"meta": meta}))

    for d in direcciones:
        (anim_dir / f"{nombre}_{d}.gif").write_bytes(b"GIF89a")

    return anim_dir


class TestDescubrir:
    """Tests para la función descubrir()."""

    def test_layout_real_personaje_con_4dir_y_8dir(self, tmp_path):
        """Layout real: mago/stardew/caminar_lpc/ (4 dir) y mago/stardew8/caminar_lpc/ (8 dir)."""
        raiz = tmp_path / "salida"
        raiz.mkdir()
        personaje = raiz / "aldeano_bosque"
        personaje.mkdir()

        stardew = personaje / "stardew"
        stardew.mkdir()
        _crear_animacion(stardew, "caminar_lpc", direcciones=["S", "E", "N", "W"])

        stardew8 = personaje / "stardew8"
        stardew8.mkdir()
        _crear_animacion(
            stardew8,
            "caminar_lpc",
            direcciones=["S", "SE", "E", "NE", "N", "NW", "W", "SW"],
        )

        resultado = visor.descubrir(raiz)

        assert len(resultado) == 1
        p = resultado[0]
        assert p["nombre"] == "aldeano_bosque"
        assert p["raiz"] == "salida"

        # Dos animaciones con el mismo nombre, estilo distinto
        anims = p["animaciones"]
        assert len(anims) == 2

        # stardew (4 dir) primero, stardew8 (8 dir) después
        assert anims[0]["nombre"] == "caminar_lpc"
        assert anims[0]["estilo"] == "stardew"
        assert anims[0]["direcciones"] == ["S", "E", "N", "W"]
        assert anims[0]["cuadros"] == 2
        assert anims[0]["fps"] == 10
        assert anims[0]["loop"] is True
        assert anims[0]["celda"] == {"w": 16, "h": 32}

        assert anims[1]["nombre"] == "caminar_lpc"
        assert anims[1]["estilo"] == "stardew8"
        assert anims[1]["direcciones"] == ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
        assert anims[1]["cuadros"] == 2

    def test_ignora_review_skins_zonas_y_archivos_de_ficha(self, tmp_path):
        """Ignora _review/, skins/, zonas/ y archivos de ficha sueltos en una carpeta de estilo."""
        raiz = tmp_path / "salida"
        raiz.mkdir()

        # Personaje válido: mago/stardew/neutra/
        personaje = raiz / "mago"
        personaje.mkdir()
        (personaje / "stardew").mkdir()
        _crear_animacion(personaje / "stardew", "neutra")

        # _review: debe ignorarse
        review = raiz / "_review"
        review.mkdir()
        _crear_animacion(review, "neutra")

        # skins/mago: layout viejo, debe ignorarse
        skins = raiz / "skins" / "mago"
        skins.mkdir(parents=True)
        (skins / "neutra.png").write_bytes(b"\x89PNG")

        # zonas/stardew8: informes, debe ignorarse
        zonas = raiz / "zonas" / "stardew8"
        zonas.mkdir(parents=True)
        (zonas / "quieto.png").write_bytes(b"\x89PNG")

        # aldeano/stardew8/quieto.png: salida de ficha (archivos sueltos, sin carpeta de animación)
        aldeano = raiz / "aldeano"
        (aldeano / "stardew8").mkdir(parents=True)
        (aldeano / "stardew8" / "quieto.png").write_bytes(b"\x89PNG")
        (aldeano / "stardew8" / "quieto_todas.gif").write_bytes(b"GIF89a")

        resultado = visor.descubrir(raiz)

        assert len(resultado) == 1
        assert resultado[0]["nombre"] == "mago"

    def test_raiz_vacia(self, tmp_path):
        """Raíz vacía → lista vacía."""
        raiz = tmp_path / "salida"
        raiz.mkdir()
        assert visor.descubrir(raiz) == []

    def test_raiz_inexistente(self, tmp_path):
        """Raíz que no existe → lista vacía."""
        raiz = tmp_path / "no_existe"
        assert visor.descubrir(raiz) == []

    def test_animacion_sin_gif_todas(self, tmp_path):
        """Animación sin _todas.gif → gif is None y hoja presente."""
        raiz = tmp_path / "salida"
        raiz.mkdir()
        personaje = raiz / "mago"
        personaje.mkdir()

        _crear_animacion(personaje, "neutra", con_gif_todas=False)

        resultado = visor.descubrir(raiz)
        assert len(resultado) == 1
        a = resultado[0]["animaciones"][0]
        assert a["gif"] is None
        assert a["hoja"] is not None

    def test_animacion_sin_json(self, tmp_path):
        """Animación sin JSON → se muestra igual, sin metadatos."""
        raiz = tmp_path / "salida"
        raiz.mkdir()
        personaje = raiz / "mago"
        personaje.mkdir()

        _crear_animacion(personaje, "neutra", con_json=False)

        resultado = visor.descubrir(raiz)
        assert len(resultado) == 1
        a = resultado[0]["animaciones"][0]
        assert a["cuadros"] is None
        assert a["fps"] is None
        assert a["loop"] is None
        assert a["celda"] is None
        # Sin JSON, direcciones se derivan de archivos
        assert a["direcciones"] == ["S", "E", "N", "W"]


class TestHTTP:
    """Tests para el servidor HTTP."""

    @pytest.fixture
    def servidor(self, tmp_path):
        """Levanta un servidor en puerto efímero con datos de prueba."""
        raiz = tmp_path / "salida"
        raiz.mkdir()
        personaje = raiz / "mago"
        personaje.mkdir()
        stardew = personaje / "stardew"
        stardew.mkdir()
        _crear_animacion(stardew, "neutra")
        _crear_animacion(stardew, "caminar_lpc", direcciones=["S", "E", "N", "W"])
        stardew8 = personaje / "stardew8"
        stardew8.mkdir()
        _crear_animacion(
            stardew8,
            "caminar_lpc",
            direcciones=["S", "SE", "E", "NE", "N", "NW", "W", "SW"],
        )

        visor.VisorHandler.raices = [raiz]
        server = HTTPServer(("127.0.0.1", 0), visor.VisorHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield server
        server.shutdown()
        thread.join()

    def _get(self, server, path):
        """Hace un GET y devuelve (status, headers, body)."""
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port)
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read()
        headers = dict(resp.getheaders())
        conn.close()
        return resp.status, headers, body

    def test_api_personajes(self, servidor):
        """GET /api/personajes → 200 y el personaje esperado."""
        status, headers, body = self._get(servidor, "/api/personajes")
        assert status == 200
        data = json.loads(body)
        assert "raices" in data
        assert "personajes" in data
        assert len(data["personajes"]) == 1
        assert data["personajes"][0]["nombre"] == "mago"

    def test_index(self, servidor):
        """GET / → 200 con HTML."""
        status, headers, body = self._get(servidor, "/")
        assert status == 200
        assert b"Visor" in body

    def test_archivo_path_traversal(self, servidor):
        """GET /archivo/../../etc/passwd → 404."""
        status, _, _ = self._get(servidor, "/archivo/../../etc/passwd")
        assert status == 404

    def test_archivo_extension_no_permitida(self, servidor, tmp_path):
        """GET /archivo/<raiz>/x.txt → 404."""
        raiz = tmp_path / "salida"
        (raiz / "x.txt").write_text("hola")
        status, _, _ = self._get(servidor, "/archivo/salida/x.txt")
        assert status == 404

    def test_archivo_gif(self, servidor):
        """GET /archivo/<raiz>/<personaje>/<estilo>/<anim>/<anim>_todas.gif → 200 con image/gif."""
        status, headers, body = self._get(
            servidor, "/archivo/salida/mago/stardew/neutra/neutra_todas.gif"
        )
        assert status == 200
        assert headers.get("Content-Type") == "image/gif"

    def test_ruta_desconocida(self, servidor):
        """Cualquier otra ruta → 404."""
        status, _, _ = self._get(servidor, "/ruta/inexistente")
        assert status == 404
