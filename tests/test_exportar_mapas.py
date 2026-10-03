"""Tests de exportación de normal map y material map (task-024)."""
import json

import numpy as np
from PIL import Image

from sprites_lib.armado import FICHA_MINIMA, render_cuadro
from sprites_lib import exportar


def test_normal_map_size_and_lam(tmp_path):
    """El normal map coincide en tamaño con el sprite; píxeles con lam alto dan normal hacia la luz."""
    cu = render_cuadro(FICHA_MINIMA, "stardew", "quieto", 0, "S")
    base = exportar.exportar([cu.img], "test", str(tmp_path), buffers=[cu.buf])

    sprite = Image.open(base + ".png")
    normal = Image.open(base + "_normal.png")
    material = Image.open(base + "_material.png")
    assert normal.size == sprite.size
    assert material.size == sprite.size

    with open(base + ".json") as fh:
        meta = json.load(fh)
    assert meta["meta"]["normal_map"] == "test_normal.png"
    assert meta["meta"]["material_map"] == "test_material.png"
    assert "materiales" in meta["meta"]

    buf = cu.buf
    lam = buf['lam']
    normal_arr = np.asarray(normal)[..., :3].astype(float) / 127.5 - 1
    luz = cu.cam.luz
    alto = lam > 0.8
    if alto.any():
        n = normal_arr[alto]
        dot = n @ luz
        assert (dot > 0.7).all()


def test_sin_buffers_sin_mapas(tmp_path):
    """Sin buffers no se generan mapas y el JSON no los referencia (retrocompatibilidad)."""
    cu = render_cuadro(FICHA_MINIMA, "stardew", "quieto", 0, "S")
    base = exportar.exportar([cu.img], "test", str(tmp_path))

    assert not (tmp_path / "test_normal.png").exists()
    assert not (tmp_path / "test_material.png").exists()
    with open(base + ".json") as fh:
        meta = json.load(fh)
    assert "normal_map" not in meta["meta"]
    assert "material_map" not in meta["meta"]
    assert "materiales" not in meta["meta"]


def test_exportar_direcciones_con_buffers(tmp_path):
    """exportar_direcciones con buffers genera mapas por dirección y el JSON los referencia."""
    dirs = ("S", "E")
    por_dir, bufs = {}, {}
    for d in dirs:
        cu = render_cuadro(FICHA_MINIMA, "stardew", "quieto", 0, d)
        por_dir[d] = [cu.img]
        bufs[d] = [cu.buf]
    base = exportar.exportar_direcciones(por_dir, "test", str(tmp_path), buffers=bufs)

    for d in dirs:
        assert (tmp_path / f"test_{d}_normal.png").exists()
        assert (tmp_path / f"test_{d}_material.png").exists()
    with open(base + ".json") as fh:
        meta = json.load(fh)
    assert meta["meta"]["normal_map"] == {d: f"test_{d}_normal.png" for d in dirs}
    assert meta["meta"]["material_map"] == {d: f"test_{d}_material.png" for d in dirs}
    assert "materiales" in meta["meta"]
