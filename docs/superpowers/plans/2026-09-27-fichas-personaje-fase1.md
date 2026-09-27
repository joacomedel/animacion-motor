# Fichas de personaje — Fase 1: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generar la hoja de modelo (poses neutra + quieto, todas las direcciones) de cualquier personaje a partir de su ficha YAML, en los estilos stardew, volumen y lateral, con tests automáticos de consistencia y fotos de control.

**Architecture:** La ficha (YAML) describe quién es y qué lleva; se valida contra un vocabulario fijo de anclas y un registro de componentes. `armado` expande la ficha a componentes (cuerpo base humano + los de la ficha), posa el esqueleto base (`cuerpo`) con una pose (`poses`) y dibuja todo con el motor 3D único (`render3d`, ahora también con cámara lateral y buffer de componente). `tests_personaje` verifica las reglas sobre los cuadros renderizados; `hoja_modelo` arma la imagen de aprobación; `fotos_control` congela lo aprobado. `personajes/generar.py` es la CLI.

**Tech Stack:** Python 3.11 (`.venv`), numpy, Pillow, scipy (ya instalados), PyYAML y pytest (se instalan en la Tarea 1).

**Spec:** `docs/superpowers/specs/2026-09-26-fichas-personaje-design.md`

## Global Constraints

- Ejecutar todo desde la raíz del proyecto con `.venv/bin/python ...` (único comando con permiso automático). Tests: `.venv/bin/python -m pytest`.
- Identificadores, mensajes y documentación en español; nombres de anclas sin tildes ni ñ (`muneca_derecha`, `rinon`…).
- Convención de lados: **derecha = l < 0** (cercana a la cámara en la vista principal), izquierda = l > 0. Las extremidades "A" de los ciclos son las derechas.
- Anclas masculinas/femeninas tal cual el vocabulario: `hombro_derecho`, `codo_derecho`, `tobillo_derecho`, `pie_derecho`, `ojo_derecho` / `cadera_derecha`, `rodilla_derecha`, `muneca_derecha`, `mano_derecha`, `sien_derecha`.
- Tamaños: stardew celda 16×32, adulto 26 px, pivote (8, 30); volumen 56×60, adulto 36 px, pivote (28, 52); lateral 40×40, adulto 33 px, pivote (20, 38). Clases: nino 0.75, adulto 1.0, grande 1.25, gigante 1.6.
- Salidas generadas en `salida/` (ignorado por git). Fotos de control aprobadas en `personajes/aprobados/<nombre>/<estilo>/` (**versionado**).
- `referencias/` y `sprites_x/animaciones/` no están en git: si faltan, el test de estilo se marca "omitido", nunca falla por eso.
- Mantener funcionando `personajes/mago_lateral.py`, `mago_iso.py` y `mago_stardew.py` (compatibilidad de `render3d` y `estilos`).
- CLI: código de salida 0 = todo OK, 1 = fallan tests, 2 = ficha inexistente o inválida (sin traceback).
- Subagentes: elegir modelo explícitamente según CLAUDE.md del usuario (mecánica → barato, integración → estándar, revisión final → el más capaz).

## Review Focus

1. **Ancla o componente mal escrito en la ficha** (p. ej. `muñeca_derecha`, `brazo_derecha`, `cabeza_humanna`) → error de validación que sugiere el nombre correcto. Test en Tarea 5.
2. **Accesorio puesto sobre una parte ausente** (pulsera en `muneca_derecha` con `antebrazo_derecho` ausente) → error de validación, no un sprite sin pulsera. Test en Tarea 5.
3. **Accesorio chico que desaparece por redondeo en algún cuadro/dirección** → el test de visibilidad lo reporta con pose, dirección y cuadro exactos. Test en Tarea 8.
4. **CLI con ficha inexistente o YAML roto** → mensaje claro y código 2, sin traceback. Test en Tarea 9.
5. **Personaje de clase grande o gigante** → usa la celda mayor del estilo, no se recorta y mide lo que dice su clase. Tests en Tareas 1 y 4.

---

## Mapa de archivos

| Archivo | Responsabilidad |
|---|---|
| `pytest.ini` | configuración de tests (raíz como `pythonpath`) |
| `sprites_lib/escala.py` (nuevo) | clases de altura, alto objetivo y celda estándar por estilo |
| `sprites_lib/paleta.py` (nuevo) | hex → RGB, derivación de 3 tonos por estilo, variantes `_b` y `mano` |
| `sprites_lib/estilos.py` (reescritura compatible) | perfiles: vista, direcciones, render, proporciones, tonos, ojos, referencia; `uz()`, `crear_camara()` |
| `sprites_lib/render3d.py` (modificar) | `CamaraLateral`, buffer de componente, `conservar` en primitivas, `recorte` en faldón, `render(buffers=True)` |
| `sprites_lib/cuerpo.py` (nuevo) | vocabulario de anclas, segmentos, `anatomia()`, `posar()`, `centro_cara()`, `anclas_ausentes()` |
| `sprites_lib/poses.py` (nuevo) | poses `neutra` y `quieto` como datos; `cuadros()` |
| `sprites_lib/componentes/__init__.py` (nuevo) | `Componente`, `registrar`, `REGISTRO`, `Contexto`, `entrar()` |
| `sprites_lib/componentes/humano.py` (nuevo) | cuerpo base: `cabeza_humana`, `ojos`, `torso_humano`, `brazo_humano`, `pierna_humana` |
| `sprites_lib/componentes/mago.py` (nuevo) | `rastas`, `vincha`, `pulsera`, `tatuaje_runas`, `tunica_abierta`, `botas` |
| `sprites_lib/componentes/robot.py` (nuevo) | `brazo_robotico`, `brazo_robotico_amputado`, `munon_cables`, `pierna_robotica`, `visor`, `placa_sien`, `cables_nuca` |
| `sprites_lib/componentes/ropa.py` (nuevo) | `remera_larga_rota`, `cinturon` |
| `sprites_lib/armado.py` (nuevo) | ficha → specs → escena → `Cuadro`; `render_cuadro()`, `render_todo()` |
| `sprites_lib/ficha.py` (nuevo) | cargar YAML y validar; `FichaInvalida` |
| `sprites_lib/tests_personaje.py` (nuevo) | tests de consistencia, `Resultado`, `correr_tests()`, `informe_md()` |
| `sprites_lib/hoja_modelo.py` (nuevo) | imagen de la hoja de modelo |
| `sprites_lib/fotos_control.py` (nuevo) | guardar y comparar poses aprobadas |
| `personajes/generar.py` (nuevo) | CLI `validar` / `hoja` / `tests` / `aprobar` |
| `personajes/fichas/mago.yaml` (nuevo), `clast.yaml` (modificar) | fichas de prueba |
| `.claude/skills/sprite-personaje/SKILL.md` (nuevo) | entrevista + flujo completo |
| `CLAUDE.md`, `CRITERIOS_ANIMACION.md` (modificar) | documentación |
| `tests/test_*.py` (nuevos) | tests de cada tarea |

---

### Task 1: Escala, paleta y perfiles de estilo

**Files:**
- Create: `pytest.ini`, `sprites_lib/escala.py`, `sprites_lib/paleta.py`, `tests/test_escala_paleta.py`
- Modify: `sprites_lib/estilos.py` (reescritura compatible: conserva la clave `celda` de `stardew` y `volumen`)

**Interfaces:**
- Produces: `escala.CLASES`, `escala.alto_objetivo_px(estilo, clase="adulto") -> int`, `escala.celda(estilo, clase="adulto") -> dict(cw, ch, gx, gy)`, `escala.EscalaError`; `paleta.HEX` (regex), `paleta.hex_rgb(h) -> (r,g,b)`, `paleta.tonos(base_rgb, regla, emisivo=False) -> (sombra, base, luz)`, `paleta.paleta_estilo(paleta_ficha, estilo_dict) -> {material: (s,b,l)}` (agrega `<mat>_b` para cada material y `mano` si hay `piel`); `estilos.ESTILOS[nombre]` con claves `vista`, `direcciones`, `render`, `proporciones`, `tonos`, `ojos`, `referencia`; `estilos.uz(estilo) -> float`.

- [ ] **Step 1: Instalar dependencias de desarrollo** (pide permiso al usuario: instala en el `.venv`, no toca el sistema)

Run: `uv pip install --python .venv/bin/python pyyaml pytest`
Expected: `+ pytest`, `+ pyyaml` instalados.

- [ ] **Step 2: Crear `pytest.ini`**

```ini
[pytest]
testpaths = tests
pythonpath = .
```

- [ ] **Step 3: Escribir los tests que fallan** — `tests/test_escala_paleta.py`

```python
import pytest

from sprites_lib.escala import EscalaError, alto_objetivo_px, celda
from sprites_lib.estilos import ESTILOS, uz
from sprites_lib.paleta import hex_rgb, paleta_estilo, tonos


def lum(c):
    return .3 * c[0] + .59 * c[1] + .11 * c[2]


def test_alto_por_clase():
    assert alto_objetivo_px("stardew") == 26
    assert alto_objetivo_px("stardew", "grande") == 32
    assert alto_objetivo_px("lateral") == 33
    assert alto_objetivo_px("volumen") == 36


def test_celda_pivote_en_los_pies():
    assert celda("stardew") == dict(cw=16, ch=32, gx=8, gy=30)
    assert celda("volumen") == dict(cw=56, ch=60, gx=28, gy=52)
    assert celda("lateral") == dict(cw=40, ch=40, gx=20, gy=38)


def test_todas_las_clases_entran_en_su_celda():
    for est in ("stardew", "volumen", "lateral"):
        for clase in ("nino", "adulto", "grande", "gigante"):
            c = celda(est, clase)
            assert c["gy"] - alto_objetivo_px(est, clase) >= 3, (est, clase)   # aire arriba para pelo/sombrero


def test_errores_claros():
    with pytest.raises(EscalaError, match="clase de altura desconocida"):
        alto_objetivo_px("stardew", "enano")
    with pytest.raises(EscalaError, match="estilo sin escala"):
        celda("pixar")


def test_estilos_tienen_lo_necesario():
    for nombre, e in ESTILOS.items():
        for k in ("vista", "direcciones", "render", "proporciones", "tonos", "ojos", "referencia"):
            assert k in e, (nombre, k)
        for k in ("cabeza_frac", "piernas_frac", "hombros_frac", "brazos_frac", "forma_cabeza", "bajar_punos", "luz"):
            assert k in e["proporciones"], (nombre, k)
    assert ESTILOS["lateral"]["direcciones"] == ["E", "W"]
    assert ESTILOS["stardew"]["celda"] == dict(cw=16, ch=32, gx=8, gy=30)    # compatibilidad con mago_stardew.py


def test_uz_por_vista():
    assert uz("lateral") == 1.0 and uz("stardew") == .92 and uz("volumen") == .92


def test_tonos_ordenados_por_luz():
    s, b, l = tonos((140, 86, 56), ESTILOS["stardew"]["tonos"])
    assert lum(s) < lum(b) < lum(l)


def test_sombra_stardew_corre_a_violeta():
    s, b, _ = tonos((140, 86, 56), ESTILOS["stardew"]["tonos"])
    assert s[2] - s[0] > b[2] * .66 - b[0] * .66      # más azul que un oscurecido simple


def test_emisivo_no_se_oscurece():
    s, b, l = tonos((90, 240, 230), ESTILOS["stardew"]["tonos"], emisivo=True)
    assert s == b and lum(l) >= lum(b)


def test_paleta_estilo_agrega_variantes():
    p = paleta_estilo({"piel": {"base": "#8c5638"}, "pelo": {"base": "#e2e2f0"}}, ESTILOS["stardew"])
    assert {"piel", "pelo", "piel_b", "pelo_b", "mano"} <= set(p)
    assert lum(p["mano"][1]) > lum(p["piel"][1])        # la mano es un tono más clara: el puño se lee


def test_hex_invalido():
    with pytest.raises(ValueError, match="#rrggbb"):
        hex_rgb("rojo")
```

- [ ] **Step 4: Correr y ver que fallan**

Run: `.venv/bin/python -m pytest tests/test_escala_paleta.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'sprites_lib.escala'`.

- [ ] **Step 5: Crear `sprites_lib/escala.py`**

```python
"""Escala del juego: el mismo personaje mide lo mismo en todos los estilos de su clase, y todas las
celdas de un estilo tienen el pivote (los pies) en el mismo lugar."""

CLASES = {"nino": .75, "adulto": 1.0, "grande": 1.25, "gigante": 1.6}

TAMANOS = {
    # adulto_px: alto en pantalla de un adulto (pies → coronilla, sin pelo parado)
    "stardew": dict(adulto_px=26, pie_desde_abajo=2,
                    celdas={"nino": (16, 32), "adulto": (16, 32), "grande": (32, 48), "gigante": (32, 64)}),
    "volumen": dict(adulto_px=36, pie_desde_abajo=8,
                    celdas={"nino": (56, 60), "adulto": (56, 60), "grande": (72, 76), "gigante": (88, 96)}),
    "lateral": dict(adulto_px=33, pie_desde_abajo=2,
                    celdas={"nino": (40, 40), "adulto": (40, 40), "grande": (48, 52), "gigante": (64, 64)}),
}


class EscalaError(ValueError):
    pass


def _t(estilo):
    if estilo not in TAMANOS:
        raise EscalaError(f"estilo sin escala: {estilo!r}; disponibles: {', '.join(TAMANOS)}")
    return TAMANOS[estilo]


def alto_objetivo_px(estilo, clase="adulto"):
    t = _t(estilo)
    if clase not in CLASES:
        raise EscalaError(f"clase de altura desconocida: {clase!r}; disponibles: {', '.join(CLASES)}")
    return round(t["adulto_px"] * CLASES[clase])


def celda(estilo, clase="adulto"):
    t = _t(estilo)
    alto_objetivo_px(estilo, clase)                 # valida la clase
    cw, ch = t["celdas"][clase]
    return dict(cw=cw, ch=ch, gx=cw // 2, gy=ch - t["pie_desde_abajo"])
```

- [ ] **Step 6: Crear `sprites_lib/paleta.py`**

```python
"""Paleta de un personaje por estilo: la ficha da solo el tono base de cada material; el estilo deriva
sombra y luz con su propio corrimiento de tono (p. ej. Stardew: sombras a violeta, luces a amarillo)."""
import re

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def hex_rgb(h):
    if not isinstance(h, str) or not HEX.match(h):
        raise ValueError(f"color inválido {h!r}: tiene que ser #rrggbb")
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _mezclar(c, hacia, t):
    return tuple(max(0, min(255, round(a + (b - a) * t))) for a, b in zip(c, hacia))


def _mult(c, k):
    return tuple(max(0, min(255, round(v * k))) for v in c)


def tonos(base, regla, emisivo=False):
    """(sombra, base, luz). Los emisivos (runas, visor) no se oscurecen: brillan igual en todos lados."""
    base = tuple(base)
    if emisivo:
        return (base, base, _mezclar(base, (255, 255, 255), .35))
    ks, hs, ms = regla["sombra"]
    kl, hl, ml = regla["luz"]
    return (_mezclar(_mult(base, ks), hs, ms), base, _mezclar(_mult(base, kl), hl, ml))


def paleta_estilo(paleta_ficha, estilo):
    """{material: (sombra, base, luz)}. Agrega '<material>_b' (variante un poco más oscura para texturas:
    mechones, pliegues) y 'mano' (piel un tono más clara) si la ficha no la define."""
    regla = estilo["tonos"]
    out = {}
    for nombre, m in paleta_ficha.items():
        base = hex_rgb(m["base"])
        emi = bool(m.get("emisivo", False))
        out[nombre] = tonos(base, regla, emi)
        if not nombre.endswith("_b"):
            out.setdefault(f"{nombre}_b", tonos(_mult(base, .86), regla, emi))
    if "piel" in paleta_ficha and "mano" not in paleta_ficha:
        out["mano"] = tonos(_mezclar(hex_rgb(paleta_ficha["piel"]["base"]), (255, 255, 255), .12), regla)
    return out
```

- [ ] **Step 7: Reescribir `sprites_lib/estilos.py`** (compatible: mantiene `celda` y `render` de antes)

```python
"""Perfiles de estilo: cómo se "ve" un sprite, independiente de qué personaje es y de cómo se mueve.

Claves de cada perfil:
  vista        'iso' (Camara, 8 direcciones), 'cenital' (CamaraCenital, 4) o 'lateral' (CamaraLateral, E/W)
  direcciones  direcciones que se generan, en el orden de la hoja
  render       parámetros de Escena.render(estilo=...)
  proporciones fracciones del alto H del personaje: cabeza, cadera (piernas), hombros, brazos (sobre el tronco);
               forma de la cabeza, cuánto se bajan los puños (px a H=37) y dirección de la luz
  tonos        regla de derivación de sombra/luz: (multiplicador, color hacia el que se corre, mezcla)
  ojos         'stardew' (pestaña + blanco + iris) o 'punto' (blanco + pupila)
  referencia   sprite de referencia para comparar_estilo (None = sin referencia)
  celda        (solo stardew/volumen) compatibilidad con personajes/mago_*.py; la escala real está en escala.py
Los números medidos y el razonamiento quedan en CRITERIOS_ANIMACION.md.
"""

ESTILOS = {
    "volumen": dict(
        descripcion="Pre-renderizado tipo Diablo II/Isometric Hero: volumen marcado, contorno negro por pieza.",
        vista="iso", direcciones=["SE", "E", "NE", "N", "NW", "W", "SW", "S"],
        celda=dict(cw=56, ch=60, gx=26, gy=52),
        render=dict(umbrales=(.28, .66), contorno="negro", interior="negro", sombreado="luz"),
        proporciones=dict(cabezas=3.3, cabeza_frac=.30, piernas_frac=.41, hombros_frac=.146, brazos_frac=1.0,
                          forma_cabeza="esfera", bajar_punos=2.5, luz=(.4, -.45, .8)),
        tonos=dict(sombra=(.58, (20, 20, 60), .2), luz=(1.25, (255, 250, 230), .15)),
        ojos="punto", referencia=None,
        paleta="3 tonos por material bien separados; contorno casi negro azulado",
        ciclos=["correr", "quieto"],
    ),
    "stardew": dict(
        descripcion="Stardew Valley: cenital 3/4, chibi, sombreado plano, contorno de color (selout).",
        vista="cenital", direcciones=["S", "E", "N", "W"],
        celda=dict(cw=16, ch=32, gx=8, gy=30),
        render=dict(umbrales=(.12, .82), contorno="color", interior="color", oscurecer=.45, sombreado="borde"),
        proporciones=dict(cabezas=2.2, cabeza_frac=.36, piernas_frac=.29, hombros_frac=.12, brazos_frac=.74,
                          forma_cabeza="caja", bajar_punos=0, luz=(-.25, .75, .6)),
        tonos=dict(sombra=(.66, (70, 40, 120), .25), luz=(1.22, (255, 236, 160), .2)),
        ojos="stardew",
        referencia=dict(ruta="referencias/stardew/abigail.png", celda=(16, 32), recorte=(0, 0, 64, 128)),
        paleta="saturada y cálida; 3-4 tonos por material con corrimiento de tono (sombras hacia violeta, "
               "luces hacia amarillo); contorno = tono más oscuro del mismo material, nunca negro puro "
               "(salvo materiales negros); 20-30 colores por cuadro",
        ciclos=["caminar", "quieto"],
    ),
    "lateral": dict(
        descripcion="Plataformas tipo Mega Man X: de perfil, cabeza grande, contorno negro, 3 tonos marcados.",
        vista="lateral", direcciones=["E", "W"],
        render=dict(umbrales=(.25, .7), contorno="negro", interior="negro", sombreado="luz"),
        proporciones=dict(cabezas=2.2, cabeza_frac=.40, piernas_frac=.32, hombros_frac=.12, brazos_frac=1.16,
                          forma_cabeza="caja", bajar_punos=0, luz=(-.35, .55, .8)),
        tonos=dict(sombra=(.6, (20, 30, 80), .2), luz=(1.25, (255, 250, 230), .15)),
        ojos="stardew",
        referencia=dict(ruta="sprites_x/animaciones/02_quieto.png", celda=(30, 34), recorte=None),
        paleta="rampas de 3-5 tonos por material; contorno negro también por dentro",
        ciclos=["correr", "quieto"],
    ),
}

_UZ = {"iso": .92, "cenital": .92, "lateral": 1.0}


def uz(estilo):
    """Cuántos px de pantalla ocupa 1 unidad de altura del mundo en ese estilo."""
    return _UZ[ESTILOS[estilo]["vista"]]
```

- [ ] **Step 8: Correr los tests**

Run: `.venv/bin/python -m pytest tests/test_escala_paleta.py -q`
Expected: `11 passed`.

- [ ] **Step 9: Verificar que los personajes viejos siguen funcionando**

Run: `.venv/bin/python -m personajes.mago_stardew --anim quieto && .venv/bin/python -m personajes.mago_iso --anim quieto --dir SE`
Expected: `listo → salida/mago_stardew/quieto` y `listo → salida/mago_iso/quieto`.

- [ ] **Step 10: Commit**

```bash
git add pytest.ini sprites_lib/escala.py sprites_lib/paleta.py sprites_lib/estilos.py tests/test_escala_paleta.py
git commit -m "Escala del juego, derivación de paleta por estilo y perfil lateral"
```

---

### Task 2: Motor — cámara lateral, buffer de componente y máscaras

**Files:**
- Modify: `sprites_lib/render3d.py` (clase `Escena` completa; agregar `CamaraLateral` después de `CamaraCenital`)
- Modify: `sprites_lib/estilos.py` (agregar `crear_camara`)
- Test: `tests/test_render3d.py`

**Interfaces:**
- Consumes: `estilos.ESTILOS`, `escala.celda`.
- Produces: `render3d.CamaraLateral(mira="E"|"W", cw, ch, gx, gy, kz=1.0, luz)`; `Escena.componente: str` (asignar antes de dibujar); primitivas `esfera/elipsoide/caja(..., conservar=None)` con `conservar(dirs) -> bool array`; `faldon(..., recorte=None)` con `recorte(dirs, t) -> bool array`; `Escena.detalle(p, col)` guarda el componente actual; `Escena.render(..., buffers=False)` → imagen, o `(imagen, buf)` con `buf = dict(depth, mat, pieza, comp, solido, comp_nombres, colores_detalle)`; `estilos.crear_camara(estilo, mira, celda) -> cámara` (ValueError si la dirección no es del estilo).

- [ ] **Step 1: Escribir los tests que fallan** — `tests/test_render3d.py`

```python
import numpy as np
import pytest

from sprites_lib.escala import celda
from sprites_lib.estilos import crear_camara
from sprites_lib.render3d import Camara, CamaraCenital, CamaraLateral, Escena, v

PAL = {"a": ((50, 50, 50), (100, 100, 100), (200, 200, 200)), "b": ((50, 0, 0), (150, 0, 0), (250, 0, 0))}


def opacos(img):
    return int((np.array(img)[..., 3] > 0).sum())


def test_lateral_mira_derecha():
    cam = CamaraLateral("E", cw=40, ch=40, gx=20, gy=38)
    x0, y0, _ = cam.proyectar(v(0, 0, 0))
    x1, y1, _ = cam.proyectar(v(5, 0, 10))
    assert x1 - x0 == pytest.approx(5) and y0 - y1 == pytest.approx(10)


def test_lateral_oeste_espeja():
    cam = CamaraLateral("W", cw=40, ch=40, gx=20, gy=38)
    x, _, _ = cam.proyectar(v(5, 0, 0))
    assert x == pytest.approx(15)


def test_lateral_lado_derecho_mas_cerca_mirando_al_este():
    cam = CamaraLateral("E", cw=40, ch=40, gx=20, gy=38)
    _, _, d_der = cam.proyectar(v(0, -2, 0))
    _, _, d_izq = cam.proyectar(v(0, 2, 0))
    assert d_der > d_izq


def test_lateral_rechaza_otras_direcciones():
    with pytest.raises(ValueError, match="E o W"):
        CamaraLateral("S")


def test_crear_camara_por_vista():
    assert isinstance(crear_camara("volumen", "SE", celda("volumen")), Camara)
    assert type(crear_camara("stardew", "S", celda("stardew"))) is CamaraCenital
    assert isinstance(crear_camara("lateral", "E", celda("lateral")), CamaraLateral)
    with pytest.raises(ValueError, match="no es una dirección"):
        crear_camara("stardew", "SE", celda("stardew"))


def test_buffer_de_componente_y_detalles():
    esc = Escena(crear_camara("stardew", "S", celda("stardew")), PAL)
    esc.componente = "cuerpo"
    esc.esfera(v(0, 0, 10), 3, "a")
    esc.componente = "gema"
    esc.detalle(v(3.2, 0, 10), (1, 2, 3))
    img, buf = esc.render(buffers=True)
    nombres = buf["comp_nombres"]
    assert (buf["comp"] == nombres.index("cuerpo")).sum() > 10
    assert (buf["comp"] == nombres.index("gema")).sum() == 1
    assert (1, 2, 3) in buf["colores_detalle"]
    assert buf["solido"].sum() == (buf["mat"] >= 0).sum()


def test_render_sin_buffers_devuelve_imagen():
    esc = Escena(crear_camara("stardew", "S", celda("stardew")), PAL)
    esc.esfera(v(0, 0, 10), 3, "a")
    assert esc.render().size == (16, 32)


def test_conservar_recorta_la_primitiva():
    completa = Escena(crear_camara("volumen", "S", celda("volumen")), PAL)
    completa.esfera(v(0, 0, 20), 8, "a")
    media = Escena(crear_camara("volumen", "S", celda("volumen")), PAL)
    media.esfera(v(0, 0, 20), 8, "a", conservar=lambda d: d[..., 2] > 0)
    assert 0 < opacos(media.render()) < opacos(completa.render())


def test_faldon_recorte():
    todo = lambda d: np.ones(d.shape[:-1], bool)
    a = Escena(crear_camara("volumen", "S", celda("volumen")), PAL)
    a.faldon(v(0, 0, 20), v(0, 0, 6), 5, 7, "a", conservar=todo)
    b = Escena(crear_camara("volumen", "S", celda("volumen")), PAL)
    b.faldon(v(0, 0, 20), v(0, 0, 6), 5, 7, "a", conservar=todo, recorte=lambda d, t: t < .5)
    assert 0 < opacos(b.render()) < opacos(a.render())


def test_escena_vacia():
    img, buf = Escena(crear_camara("stardew", "S", celda("stardew")), PAL).render(buffers=True)
    assert opacos(img) == 0 and not buf["solido"].any()
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/bin/python -m pytest tests/test_render3d.py -q`
Expected: FAIL con `ImportError: cannot import name 'CamaraLateral'`.

- [ ] **Step 3: Agregar `CamaraLateral`** en `sprites_lib/render3d.py`, inmediatamente después de la clase `CamaraCenital`

```python
DIRECCIONES_LATERAL = ("E", "W")


class CamaraLateral(CamaraCenital):
    """Vista de costado ortográfica (plataformas): sin inclinación; x = adelante, y = −arriba.
    Es una cámara cenital con ky = 0: la profundidad es el eje sur (el lado derecho del personaje queda más
    cerca mirando al E)."""

    def __init__(self, mira="E", cw=40, ch=40, gx=20, gy=38, kz=1.0, luz=(-.35, .55, .8)):
        if mira not in DIRECCIONES_LATERAL:
            raise ValueError(f"la vista lateral solo admite E o W, no {mira!r}")
        super().__init__(mira, cw=cw, ch=ch, gx=gx, gy=gy, ky=0.0, kz=kz, luz=luz)
```

- [ ] **Step 4: Reemplazar la clase `Escena` completa** en `sprites_lib/render3d.py` por esta versión (mismo comportamiento para los personajes existentes + componente, máscaras y buffers)

```python
class Escena:
    """Acumula puntos de superficie (posición, normal, material, pieza, componente) en ejes locales."""

    def __init__(self, camara, paleta):
        self.cam, self.pal = camara, paleta
        self.mats = list(paleta)
        self.P, self.Nn, self.M, self.K, self.C = [], [], [], [], []
        self.pieza = 0          # cambiarlo antes de agregar cada parte: da contorno entre piezas distintas
        self.componente = ""    # qué componente de la ficha está dibujando (buffer de componente)
        self.comp_nombres = [""]
        self.detalles = []      # (punto local, color RGB, componente) de 1 px

    def _cid(self):
        if self.componente not in self.comp_nombres:
            self.comp_nombres.append(self.componente)
        return self.comp_nombres.index(self.componente)

    def _mid(self, mat, shape):
        if isinstance(mat, str):
            return np.full(shape, self.mats.index(mat))
        nombres = np.asarray(mat)
        out = np.zeros(nombres.shape, int)
        for nm in np.unique(nombres):
            out[nombres == nm] = self.mats.index(nm)
        return out

    def _add(self, pts, nrm, mat, mascara=None):
        pts, nrm = pts.reshape(-1, 3), nrm.reshape(-1, 3)
        m = self._mid(mat, pts.shape[:1]) if isinstance(mat, str) else self._mid(mat, None).reshape(-1)
        if mascara is not None:
            k = np.asarray(mascara, bool).reshape(-1)
            pts, nrm, m = pts[k], nrm[k], m[k]
        self.P.append(pts); self.Nn.append(nrm); self.M.append(m)
        self.K.append(np.full(len(pts), self.pieza)); self.C.append(np.full(len(pts), self._cid()))

    # -------------------------------------------------------------- primitivas
    def esfera(self, c, r, mat, conservar=None):
        """mat: nombre, o función(dirs)->array de nombres. conservar(dirs)->bool deja solo una parte."""
        d = _esfera_dirs(r)
        self._add(np.asarray(c) + r * d, d, mat if isinstance(mat, str) else mat(d),
                  None if conservar is None else conservar(d))

    def elipsoide(self, c, radios, mat, conservar=None):
        radios = np.asarray(radios, float)
        d = _esfera_dirs(radios.max())
        nrm = d / radios; nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        self._add(np.asarray(c) + d * radios, nrm, mat if isinstance(mat, str) else mat(d),
                  None if conservar is None else conservar(d))

    def caja(self, c, radios, mat, n=3.0, conservar=None):
        """Superelipsoide: n=2 es un elipsoide; n=3-4 es una caja redondeada. Las siluetas con lados rectos se
        leen como dibujadas a mano; las esferas perfectas "gritan 3D"."""
        radios = np.asarray(radios, float)
        d = _esfera_dirs(radios.max())
        q = np.sign(d) * np.abs(d) ** (2.0 / n)
        nrm = np.sign(d) * np.abs(d) ** (2.0 - 2.0 / n) / radios
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-9
        self._add(np.asarray(c) + q * radios, nrm, mat if isinstance(mat, str) else mat(d),
                  None if conservar is None else conservar(d))

    def capsula(self, a, b, r, mat, tapas=True):
        a, b = np.asarray(a, float), np.asarray(b, float)
        ax = b - a; L = np.linalg.norm(ax) + 1e-9; ax /= L
        e1 = np.cross(ax, [0, 0, 1.0])
        if np.linalg.norm(e1) < 1e-3:
            e1 = np.cross(ax, [1.0, 0, 0])
        e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1)
        t, ang = np.meshgrid(np.linspace(0, L, int(L / .3) + 2),
                             np.linspace(0, 2 * math.pi, max(8, int(2 * math.pi * r / .3)), endpoint=False))
        d = np.cos(ang)[..., None] * e1 + np.sin(ang)[..., None] * e2
        self._add(a + t[..., None] * ax + r * d, d, mat)
        if tapas:
            self.esfera(a, r, mat); self.esfera(b, r, mat)

    def faldon(self, arriba, abajo, r1, r2, mat, conservar=lambda d: d[..., 0] < .35, recorte=None):
        """Tronco de cono (túnica, capa, falda). conservar(dirs) decide qué ángulos existen (por defecto abierto
        adelante); recorte(dirs, t) saca partes según la altura t∈[0,1] (jirones, dobladillo irregular)."""
        arriba, abajo = np.asarray(arriba, float), np.asarray(abajo, float)
        t, ang = np.meshgrid(np.linspace(0, 1, 26), np.linspace(0, 2 * math.pi, 64, endpoint=False))
        d = np.stack([np.cos(ang), np.sin(ang), np.zeros_like(ang)], -1)
        c = arriba + t[..., None] * (abajo - arriba)
        r = (r1 + (r2 - r1) * t)[..., None]
        m = np.asarray(conservar(d), bool)
        if recorte is not None:
            m = m & np.asarray(recorte(d, t), bool)
        nrm = d + np.array([0, 0, .35]); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        mats = mat if isinstance(mat, str) else mat(d, t)[m]   # mat(d, t): pliegues por ángulo/altura
        self._add((c + r * d)[m], nrm[m], mats)

    def detalle(self, p, col):
        self.detalles.append((np.asarray(p, float), tuple(int(x) for x in col), self.componente))

    # -------------------------------------------------------------- render
    def render(self, contorno=(16, 10, 24), salto=3.2, salto_pieza=.8, estilo=None, buffers=False):
        """estilo (ver sprites_lib/estilos.py): umbrales de tonos, contorno 'negro'|'color'
        (el tono más oscuro del material vecino), interior 'negro'|'color'|'ninguno', sombreado 'luz'|'borde'.
        buffers=True devuelve además (depth, mat, pieza, comp, solido, comp_nombres, colores_detalle)."""
        est = dict(umbrales=(.28, .66), contorno="negro", interior="negro", oscurecer=.55, sombreado="luz")
        est.update(estilo or {})
        cw, ch = self.cam.cw, self.cam.ch
        depth = np.full((ch, cw), -1e9); mat = np.full((ch, cw), -1); pieza = np.full((ch, cw), -1)
        comp = np.full((ch, cw), -1); lam = np.zeros((ch, cw))
        img = np.zeros((ch, cw, 4), np.uint8)
        colores_detalle = set()
        if self.P:
            P = np.concatenate(self.P); Nn = np.concatenate(self.Nn)
            M = np.concatenate(self.M); K = np.concatenate(self.K); C = np.concatenate(self.C)
            x, y, d = self.cam.proyectar(P)
            xi, yi = np.round(x).astype(int), np.round(y).astype(int)
            ok = (xi >= 0) & (xi < cw) & (yi >= 0) & (yi < ch)
            xi, yi, d, Nn, M, K, C = (arr[ok] for arr in (xi, yi, d, Nn, M, K, C))
            o = np.argsort(d, kind="stable")              # lo más cercano a cámara queda último y gana
            xi, yi, d, Nn, M, K, C = (arr[o] for arr in (xi, yi, d, Nn, M, K, C))
            depth[yi, xi] = d; mat[yi, xi] = M; pieza[yi, xi] = K; comp[yi, xi] = C
            lam[yi, xi] = np.clip(self.cam.a_mundo(Nn) @ self.cam.luz, 0, 1)
        nivel = None
        if est["sombreado"] == "borde":
            # como lo haría un artista: tono base plano; luz en el borde superior/izquierdo de cada pieza y
            # sombra en el inferior/derecho (y donde la luz real es muy baja)
            nivel = np.ones((ch, cw), int)
            distinto = lambda dy, dx: _mover(pieza, dy, dx, -1) != pieza
            luz_b = distinto(1, 0) | distinto(0, 1)          # vecino de arriba o de la izquierda es otra pieza
            som_b = distinto(-1, 0) | distinto(0, -1)
            nivel[luz_b & ~som_b] = 2
            nivel[som_b & ~luz_b] = 0
            nivel[lam < est["umbrales"][0]] = 0
        u1, u2 = est["umbrales"]
        for k, nm in enumerate(self.mats):
            tonos = self.pal[nm]
            if nivel is not None:
                for lvl in range(3):
                    img[(mat == k) & (nivel == lvl)] = (*tonos[lvl], 255)
                continue
            for lvl, (lo, hi) in enumerate(((-1, u1), (u1, u2), (u2, 2))):
                img[(mat == k) & (lam > lo) & (lam <= hi)] = (*tonos[lvl], 255)
        solido = mat >= 0
        interior = np.zeros_like(solido)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nd = _mover(depth, dy, dx, -1e9)
            npz = _mover(pieza, dy, dx, -1)
            interior |= solido & (nd - depth > salto)
            interior |= solido & (npz >= 0) & (npz != pieza) & (nd - depth > salto_pieza)
        if est["interior"] == "negro":
            img[interior] = (*contorno, 255)
        elif est["interior"] == "color":                  # línea con el tono oscuro de la pieza de atrás
            for k, nm in enumerate(self.mats):
                img[interior & (mat == k)] = (*_oscurecer(self.pal[nm][0], .8), 255)
        for p, col, cn in self.detalles:
            px, py, pd = self.cam.proyectar(p)
            ix, iy = int(round(float(px))), int(round(float(py)))
            if 0 <= ix < cw and 0 <= iy < ch and solido[iy, ix] and pd >= depth[iy, ix] - 1.3:
                img[iy, ix] = (*col, 255)
                comp[iy, ix] = self.comp_nombres.index(cn) if cn in self.comp_nombres else comp[iy, ix]
                colores_detalle.add(col)
        grow = solido.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            grow |= _mover(solido, dy, dx, False)
        anillo = grow & ~solido
        if est["contorno"] == "color":                    # "selout": cada borde toma el tono oscuro de su material
            vecino = np.full(mat.shape, -1)
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nm_ = _mover(mat, dy, dx, -1)
                vecino = np.where((vecino < 0) & (nm_ >= 0), nm_, vecino)
            for k, nm in enumerate(self.mats):
                img[anillo & (vecino == k)] = (*_oscurecer(self.pal[nm][0], est["oscurecer"]), 255)
        else:
            img[anillo] = (*contorno, 255)
        im = Image.fromarray(img, "RGBA")
        if not buffers:
            return im
        return im, dict(depth=depth, mat=mat, pieza=pieza, comp=comp, solido=solido,
                        comp_nombres=list(self.comp_nombres), colores_detalle=colores_detalle)
```

- [ ] **Step 5: Agregar `crear_camara`** al final de `sprites_lib/estilos.py`

```python
def crear_camara(estilo, mira, celda):
    """Cámara del estilo para una dirección y una celda (ver escala.celda)."""
    from .render3d import Camara, CamaraCenital, CamaraLateral
    e = ESTILOS[estilo]
    if mira not in e["direcciones"]:
        raise ValueError(f"{mira!r} no es una dirección del estilo {estilo}: {', '.join(e['direcciones'])}")
    luz = e["proporciones"]["luz"]
    clase = {"iso": Camara, "cenital": CamaraCenital, "lateral": CamaraLateral}[e["vista"]]
    return clase(mira, luz=luz, **celda)
```

- [ ] **Step 6: Correr los tests del motor y los anteriores**

Run: `.venv/bin/python -m pytest -q`
Expected: `21 passed`.

- [ ] **Step 7: Verificar los personajes viejos** (el motor cambió)

Run: `.venv/bin/python -m personajes.mago_stardew --anim caminar && .venv/bin/python -m personajes.mago_iso --anim correr --dir SE && .venv/bin/python -m sprites_lib.comparar_estilo referencias/stardew/abigail.png 16x32 salida/mago_stardew/caminar/caminar.png 16x32 --ref-recorte 0,0,64,128 | sed -n 3,15p`
Expected: los dos `listo →` y las mismas métricas que antes del cambio (planitud 0.32, bandas 38.16, recorte 0.00).

- [ ] **Step 8: Commit**

```bash
git add sprites_lib/render3d.py sprites_lib/estilos.py tests/test_render3d.py
git commit -m "Motor: cámara lateral, buffer de componente, máscaras en primitivas y faldón"
```

---

### Task 3: Esqueleto base, anclas y poses

**Files:**
- Create: `sprites_lib/cuerpo.py`, `sprites_lib/poses.py`, `tests/test_cuerpo_poses.py`

**Interfaces:**
- Consumes: `escala.alto_objetivo_px`, `estilos.ESTILOS`, `estilos.uz`, `render3d.ik_sagital`, `render3d.v`, `ciclos.QUIETO`, `ciclos.pose`.
- Produces: `cuerpo.ANCLAS` (tupla), `cuerpo.SEGMENTOS` (dict segmento → anclas desde la raíz), `cuerpo.VOCABULARIO` (set), `cuerpo.PADRE` (ancla → ancla padre), `cuerpo.COMPLEXIONES`, `cuerpo.Anatomia` (dataclass), `cuerpo.anatomia(estilo, clase="adulto", complexion="normal") -> Anatomia`, `cuerpo.centro_cara(cam_local) -> np.ndarray`, `cuerpo.posar(anat, ps, cam_local) -> dict[str, np.ndarray]`, `cuerpo.anclas_ausentes(lista) -> set`, `cuerpo.lado_de(ancla) -> "derecha"|"izquierda"`, `cuerpo.masc(lado) -> "derecho"|"izquierdo"`; `poses.POSES`, `poses.cuadros(nombre) -> list[dict]` (cada ps con `bob, bob_prev, pie_a, ang_a, pie_b, ang_b, mano_a, mano_b, fase, abrir_brazos, cuadro`), `poses.fps(nombre)`.

- [ ] **Step 1: Escribir los tests que fallan** — `tests/test_cuerpo_poses.py`

```python
import numpy as np
import pytest

from sprites_lib.cuerpo import (ANCLAS, PADRE, SEGMENTOS, VOCABULARIO, anatomia, anclas_ausentes, centro_cara,
                                lado_de, masc, posar)
from sprites_lib.estilos import uz
from sprites_lib.poses import POSES, cuadros

FRENTE = np.array([1.0, 0, 0])


def test_anatomia_mide_el_alto_de_la_escala():
    for est in ("stardew", "volumen", "lateral"):
        A = anatomia(est)
        assert A.H * uz(est) == pytest.approx(A.alto_px)


def test_clase_grande_mide_mas():
    assert anatomia("stardew", "grande").H > anatomia("stardew").H


def test_complexion_desconocida():
    with pytest.raises(ValueError, match="complexión"):
        anatomia("stardew", complexion="gordito")


def test_posar_da_todas_las_anclas():
    a = posar(anatomia("stardew"), cuadros("quieto")[0], FRENTE)
    assert set(ANCLAS) <= set(a)


def test_coronilla_a_la_altura_del_personaje():
    A = anatomia("lateral")
    a = posar(A, cuadros("neutra")[0], FRENTE)
    assert a["coronilla"][2] == pytest.approx(A.H)


def test_lados():
    a = posar(anatomia("stardew"), cuadros("quieto")[0], FRENTE)
    assert a["hombro_derecho"][1] < 0 < a["hombro_izquierdo"][1]
    assert a["cadera_derecha"][1] < 0 < a["cadera_izquierda"][1]


def test_huesos_miden_lo_que_dice_la_anatomia():
    A = anatomia("volumen")
    a = posar(A, cuadros("quieto")[0], FRENTE)
    assert np.linalg.norm(a["rodilla_derecha"] - a["cadera_derecha"]) == pytest.approx(A.muslo, abs=.01)
    assert np.linalg.norm(a["codo_izquierdo"] - a["hombro_izquierdo"]) == pytest.approx(A.brazo, abs=.01)


def test_neutra_abre_los_brazos():
    A = anatomia("stardew")
    neutra = posar(A, cuadros("neutra")[0], FRENTE)["mano_izquierda"][1]
    quieto = posar(A, cuadros("quieto")[0], FRENTE)["mano_izquierda"][1]
    assert neutra > quieto


def test_la_cara_sigue_a_la_camara():
    A = anatomia("stardew")
    de_frente = posar(A, cuadros("quieto")[0], FRENTE)
    camara_a_la_derecha = posar(A, cuadros("quieto")[0], np.array([0.0, -1.0, .3]))
    assert camara_a_la_derecha["cara"][1] < de_frente["cara"][1]
    assert np.linalg.norm(centro_cara(FRENTE) - FRENTE) < 1e-9


def test_anclas_ausentes_conserva_la_raiz():
    aus = anclas_ausentes(["antebrazo_derecho"])
    assert {"antebrazo_derecho", "muneca_derecha", "mano_derecha"} <= aus
    assert "codo_derecho" not in aus


def test_vocabulario_y_padres():
    assert "brazo_derecho" in VOCABULARIO and "muneca_derecha" in VOCABULARIO
    assert PADRE["codo_derecho"] == "hombro_derecho" and PADRE["muneca_derecha"] == "codo_derecho"
    assert SEGMENTOS["pierna_izquierda"][0] == "cadera_izquierda"
    assert lado_de("codo_derecho") == "derecha" and masc("izquierda") == "izquierdo"


def test_poses():
    assert set(POSES) == {"neutra", "quieto"}
    assert [ps["bob"] for ps in cuadros("quieto")] == [0, 0, 1, 1]
    assert [ps["cuadro"] for ps in cuadros("quieto")] == [0, 1, 2, 3]
    with pytest.raises(KeyError, match="pose desconocida"):
        cuadros("bailar")
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/bin/python -m pytest tests/test_cuerpo_poses.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'sprites_lib.cuerpo'`.

- [ ] **Step 3: Crear `sprites_lib/cuerpo.py`**

```python
"""Esqueleto base humano: proporciones por estilo y clase, vocabulario fijo de anclas y pose → posiciones 3D.

Convención de lados: derecha = l < 0 (lado cercano a la cámara en la vista principal), izquierda = l > 0.
Las extremidades "A" de los ciclos son las derechas. Unidades: 1 unidad de mundo ≈ 1 px horizontal.
"""
import math
from dataclasses import dataclass

import numpy as np

from .escala import alto_objetivo_px
from .estilos import ESTILOS, uz
from .render3d import ik_sagital, v

LADOS = {"derecha": -1, "izquierda": 1}
ANCLAS = (
    "suelo", "cadera_derecha", "cadera_izquierda", "rodilla_derecha", "rodilla_izquierda",
    "tobillo_derecho", "tobillo_izquierdo", "pie_derecho", "pie_izquierdo",
    "cintura", "torso", "pecho", "cuello",
    "hombro_derecho", "hombro_izquierdo", "codo_derecho", "codo_izquierdo",
    "muneca_derecha", "muneca_izquierda", "mano_derecha", "mano_izquierda",
    "cabeza", "coronilla", "cara", "frente", "ojo_derecho", "ojo_izquierdo", "sien_derecha", "sien_izquierda", "nuca",
)
SEGMENTOS = {
    "brazo_derecho": ("hombro_derecho", "codo_derecho", "muneca_derecha", "mano_derecha"),
    "brazo_izquierdo": ("hombro_izquierdo", "codo_izquierdo", "muneca_izquierda", "mano_izquierda"),
    "antebrazo_derecho": ("codo_derecho", "muneca_derecha", "mano_derecha"),
    "antebrazo_izquierdo": ("codo_izquierdo", "muneca_izquierda", "mano_izquierda"),
    "pierna_derecha": ("cadera_derecha", "rodilla_derecha", "tobillo_derecho", "pie_derecho"),
    "pierna_izquierda": ("cadera_izquierda", "rodilla_izquierda", "tobillo_izquierdo", "pie_izquierdo"),
}
VOCABULARIO = set(ANCLAS) | set(SEGMENTOS)
PADRE = {
    "codo_derecho": "hombro_derecho", "codo_izquierdo": "hombro_izquierdo",
    "muneca_derecha": "codo_derecho", "muneca_izquierda": "codo_izquierdo",
    "rodilla_derecha": "cadera_derecha", "rodilla_izquierda": "cadera_izquierda",
    "tobillo_derecho": "rodilla_derecha", "tobillo_izquierdo": "rodilla_izquierda",
}
COMPLEXIONES = {"normal": (1.0, 1.0), "robusto": (1.15, 1.25), "delgado": (.9, .85)}   # (ancho, grosor)


def lado_de(ancla):
    return "derecha" if ancla.endswith(("derecho", "derecha")) else "izquierda"


def masc(lado):
    return "derecho" if lado == "derecha" else "izquierdo"


@dataclass
class Anatomia:
    estilo: str
    clase: str
    H: float
    alto_px: int
    cabeza_u: float
    cabeza: tuple
    cuello_u: float
    hombro_u: float
    hombro_l: float
    pecho_u: float
    pecho: tuple
    pelvis_u: float
    pelvis: tuple
    cadera_u: float
    cadera_l: float
    muslo: float
    canilla: float
    pie: float
    brazo: float
    antebrazo: float
    r_muslo: float
    r_canilla: float
    r_brazo: float
    r_antebrazo: float
    r_mano: float
    r_pie: float
    escala_rig: float
    bajar_punos: float


def anatomia(estilo, clase="adulto", complexion="normal"):
    if complexion not in COMPLEXIONES:
        raise ValueError(f"complexión desconocida {complexion!r}; disponibles: {', '.join(COMPLEXIONES)}")
    pr = ESTILOS[estilo]["proporciones"]
    ancho, grosor = COMPLEXIONES[complexion]
    alto_px = alto_objetivo_px(estilo, clase)
    H = alto_px / uz(estilo)
    cab = H * pr["cabeza_frac"]
    cabeza = (cab * .49, cab * .53 * ancho, cab * .5)
    cuello_u = H - cab * .98
    hombro_u = cuello_u - H * .02
    cadera_u = H * pr["piernas_frac"]
    r_pie = H * .042 * grosor
    muslo = canilla = (cadera_u - r_pie) / 2 * 1.03
    tronco = hombro_u - cadera_u
    brazos = tronco * pr["brazos_frac"]
    return Anatomia(
        estilo=estilo, clase=clase, H=H, alto_px=alto_px,
        cabeza_u=H - cabeza[2], cabeza=cabeza, cuello_u=cuello_u,
        hombro_u=hombro_u, hombro_l=H * pr["hombros_frac"] * ancho,
        pecho_u=cadera_u + tronco * .62, pecho=(H * .085 * grosor, H * .115 * ancho, tronco * .34),
        pelvis_u=cadera_u + H * .03, pelvis=(H * .07 * grosor, H * .1 * ancho, H * .06),
        cadera_u=cadera_u, cadera_l=H * .058 * ancho, muslo=muslo, canilla=canilla, pie=H * .08,
        brazo=brazos * .51, antebrazo=brazos * .49,
        r_muslo=H * .048 * grosor, r_canilla=H * .041 * grosor, r_brazo=H * .035 * grosor,
        r_antebrazo=H * .033 * grosor, r_mano=H * .046 * grosor, r_pie=r_pie,
        escala_rig=(muslo + canilla) / 14.0, bajar_punos=pr["bajar_punos"] * H / 37,
    )


def centro_cara(cam_local):
    """Trampa de Stardew: la cara se corre hacia la cámara. De frente queda adelante; de perfil, sobre el costado
    visible (si no, desde el costado solo se ve pelo); de espaldas queda oculta."""
    ch = np.array([cam_local[0], cam_local[1], 0.0])
    n = np.linalg.norm(ch)
    ch = ch / n if n > 1e-9 else ch
    c = np.array([1.0, 0, 0]) + .9 * ch
    return c / (np.linalg.norm(c) + 1e-9)


def anclas_ausentes(lista):
    """Anclas que no existen: las nombradas y, para un segmento, todo menos su raíz (sin antebrazo queda el codo)."""
    out = set()
    for x in lista or []:
        out.add(x)
        if x in SEGMENTOS:
            out |= set(SEGMENTOS[x][1:])
    return out


def posar(anat, ps, cam_local):
    """Posiciones 3D (ejes locales) de todas las anclas para una pose (formato de ciclos.pose / poses.cuadros)."""
    A, k = anat, anat.escala_rig
    esc = A.H / 28.0
    sube = -ps["bob"] * .9 * esc
    a = {"suelo": v(0, 0, 0)}
    cad_c = v(0, 0, A.cadera_u + sube)
    for lado, s in LADOS.items():
        m = masc(lado)
        pie, ang = (ps["pie_a"], ps["ang_a"]) if s < 0 else (ps["pie_b"], ps["ang_b"])
        cad = cad_c + v(0, s * A.cadera_l, 0)
        tob = v((pie[0] - 18) * k, s * A.cadera_l, (34 - pie[1]) * k + A.r_pie * .3)
        rod = ik_sagital(cad, tob, A.muslo, A.canilla, +1)
        r = math.radians(ang)
        a[f"cadera_{lado}"], a[f"rodilla_{lado}"] = cad, rod
        a[f"tobillo_{m}"], a[f"pie_{m}"] = tob, tob + v(A.pie * math.cos(r), 0, -A.pie * math.sin(r))
        mp = ps["mano_b"] if s < 0 else ps["mano_a"]      # brazo opuesto a la pierna del mismo lado
        hom = v(-.2 * esc, s * A.hombro_l, A.hombro_u + sube)
        mano = hom + v((mp[0] - 20) * k, s * ps.get("abrir_brazos", .6) * esc, (16 - mp[1]) * k - A.bajar_punos)
        codo = ik_sagital(hom, mano, A.brazo, A.antebrazo, -1)
        a[f"hombro_{m}"], a[f"codo_{m}"] = hom, codo
        a[f"muneca_{lado}"], a[f"mano_{lado}"] = codo + (mano - codo) * .8, mano
    rf, rl, rz = A.cabeza
    hc = v(.1 * esc, 0, A.cabeza_u + sube)
    c = centro_cara(cam_local)
    perp = np.array([-c[1], c[0], 0.0])                    # hacia la izquierda del personaje, sobre la cara
    cara = hc + np.array([c[0] * rf, c[1] * rl, 0.0]) * 1.02
    a.update(
        cabeza=hc, coronilla=hc + v(0, 0, rz), cara=cara,
        frente=hc + np.array([c[0] * rf, c[1] * rl, 0.0]) + v(0, 0, rz * .36),
        ojo_izquierdo=cara + perp * rl * .31 + v(0, 0, -rz * .24),
        ojo_derecho=cara - perp * rl * .31 + v(0, 0, -rz * .24),
        sien_derecha=hc + v(rf * .25, -rl * .97, rz * .25), sien_izquierda=hc + v(rf * .25, rl * .97, rz * .25),
        nuca=hc + v(-rf * .9, 0, -rz * .2),
        cuello=v(0, 0, A.cuello_u + sube), torso=v(-.2 * esc, 0, A.pecho_u + sube),
        pecho=v(A.pecho[0] * .9, 0, A.pecho_u + A.pecho[2] * .2 + sube),
        cintura=v(0, 0, A.pelvis_u + A.pelvis[2] * .8 + sube),
    )
    return a
```

- [ ] **Step 4: Crear `sprites_lib/poses.py`**

```python
"""Poses clave como datos (mismo formato que los ciclos: rig lateral, piso y=34, cadera x=18).
Fase 1: 'neutra' (pose A de construcción) y 'quieto' (respiración). Las animaciones de la fase 2 serán
secuencias de poses clave aprobadas."""
from .ciclos import QUIETO
from .ciclos import pose as _pose

NEUTRA = dict(
    nombre="neutra", n=1, fps=1, desfase=0, fuente="pose A de construcción: brazos separados, piernas juntas",
    bob=[0], pie=[(18, 32.5)], pie_ang=[0], mano=dict(cx=20, ax=0, y0=27.5, ay=0), lag_faldon=1,
    abrir_brazos=2.2,
)
POSES = {"neutra": NEUTRA, "quieto": QUIETO}


def cuadros(nombre):
    if nombre not in POSES:
        raise KeyError(f"pose desconocida {nombre!r}; disponibles: {', '.join(POSES)}")
    c = POSES[nombre]
    out = []
    for p in range(c["n"]):
        ps = _pose(c, p)
        ps["abrir_brazos"] = c.get("abrir_brazos", .6)
        ps["cuadro"] = p
        out.append(ps)
    return out


def fps(nombre):
    return POSES[nombre]["fps"]
```

- [ ] **Step 5: Correr los tests**

Run: `.venv/bin/python -m pytest tests/test_cuerpo_poses.py -q`
Expected: `12 passed`.

- [ ] **Step 6: Commit**

```bash
git add sprites_lib/cuerpo.py sprites_lib/poses.py tests/test_cuerpo_poses.py
git commit -m "Esqueleto base con vocabulario fijo de anclas y poses neutra/quieto"
```

---

### Task 4: Componentes base humanos y armado

**Files:**
- Create: `sprites_lib/componentes/__init__.py`, `sprites_lib/componentes/humano.py`, `sprites_lib/armado.py`, `tests/test_armado.py`
- Create (vacíos por ahora, se llenan en Tareas 6 y 7): `sprites_lib/componentes/mago.py`, `sprites_lib/componentes/robot.py`, `sprites_lib/componentes/ropa.py` con solo el docstring

**Interfaces:**
- Consumes: todo lo de las Tareas 1–3.
- Produces: `componentes.REGISTRO: dict[tipo, Componente]`, `componentes.registrar` (decorador de clase), `componentes.Componente` (atributos `tipo, anclas_validas, estilos, params_defecto, params_material, material_defecto`; método `dibujar(esc, ctx, spec)`), `componentes.Contexto` (dataclass: `anat, a, ps, estilo, est, cam_local, paleta, mira, ausentes, pieza_base, cuadro`; métodos `ausente(nombre)`, `escala()`), `componentes.entrar(esc, ctx, spec, k=0)`, `componentes.perpendicular(eje)`; `armado.BASE_HUMANO`, `armado.expandir(ficha) -> list[spec]` (spec = dict `tipo, ancla, material, parametros, reglas, id, pieza_base, por_que`), `armado.Cuadro` (dataclass: `img, buf, anclas_px, specs, mira, pose, indice, cam, anat, escala, bob`), `armado.render_cuadro(ficha, estilo, pose, p, mira) -> Cuadro`, `armado.render_todo(ficha, estilo, poses=("neutra","quieto")) -> dict[(pose, mira), list[Cuadro]]`.

- [ ] **Step 1: Escribir los tests que fallan** — `tests/test_armado.py`

```python
import numpy as np

from sprites_lib.armado import expandir, render_cuadro
from sprites_lib.componentes import REGISTRO
from sprites_lib.escala import celda
from sprites_lib.estilos import ESTILOS

FICHA = {
    "identidad": {"nombre": "Prueba", "concepto": "humano de prueba", "silueta_clave": "ninguna"},
    "cuerpo": {"base": "humano", "clase_altura": "adulto", "cabello": "corto"},
    "paleta": {"piel": {"base": "#c89070"}, "pelo": {"base": "#302018"}},
    "componentes": [],
}


def pix(c, comp_id):
    n = c.buf["comp_nombres"]
    return int((c.buf["comp"] == n.index(comp_id)).sum()) if comp_id in n else 0


def test_registro_tiene_el_cuerpo_base():
    for t in ("cabeza_humana", "ojos", "torso_humano", "brazo_humano", "pierna_humana"):
        assert t in REGISTRO


def test_expandir_agrega_el_cuerpo_base():
    specs = expandir(FICHA)
    ids = {s["id"] for s in specs}
    assert len(specs) == 7
    assert {"brazo_humano@brazo_derecho", "pierna_humana@pierna_izquierda", "ojos@cara"} <= ids
    assert len({s["pieza_base"] for s in specs}) == 7


def test_componente_propio_reemplaza_al_base():
    f = dict(FICHA, componentes=[{"tipo": "pierna_humana", "ancla": ["pierna_izquierda", "pierna_derecha"],
                                  "material": "pelo", "por_que": "pantalón oscuro"}])
    specs = expandir(f)
    piernas = [s for s in specs if s["tipo"] == "pierna_humana"]
    assert len(specs) == 7 and len(piernas) == 2 and all(s["material"] == "pelo" for s in piernas)


def test_sustitucion_quita_el_componente_base():
    f = dict(FICHA, cuerpo=dict(FICHA["cuerpo"], sustituciones={"brazo_derecho": "brazo_humano"}),
             componentes=[{"tipo": "brazo_humano", "ancla": "brazo_derecho", "material": "pelo", "por_que": "x"}])
    brazos = [s for s in expandir(f) if s["ancla"] == "brazo_derecho"]
    assert len(brazos) == 1 and brazos[0]["material"] == "pelo"


def test_render_en_los_tres_estilos_y_todas_las_direcciones():
    for est in ("stardew", "volumen", "lateral"):
        for mira in ESTILOS[est]["direcciones"]:
            c = render_cuadro(FICHA, est, "quieto", 0, mira)
            assert c.img.size == (celda(est)["cw"], celda(est)["ch"])
            assert pix(c, "torso_humano@torso") > 0 and pix(c, "cabeza_humana@cabeza") > 0, (est, mira)


def test_de_frente_se_ven_brazos_piernas_y_ojos():
    c = render_cuadro(FICHA, "stardew", "quieto", 0, "S")
    for i in ("brazo_humano@brazo_derecho", "brazo_humano@brazo_izquierdo",
              "pierna_humana@pierna_derecha", "pierna_humana@pierna_izquierda", "ojos@cara"):
        assert pix(c, i) > 0, i


def test_el_puno_es_pieza_propia():
    c = render_cuadro(FICHA, "volumen", "quieto", 0, "S")
    n = c.buf["comp_nombres"]
    m = c.buf["comp"] == n.index("brazo_humano@brazo_derecho")
    assert len(set(c.buf["pieza"][m].tolist())) >= 2      # brazo y puño con contorno entre ellos


def test_antebrazo_ausente_no_se_dibuja():
    f = dict(FICHA, cuerpo=dict(FICHA["cuerpo"], ausentes=["antebrazo_derecho"]))
    c = render_cuadro(f, "stardew", "quieto", 0, "S")
    n = c.buf["comp_nombres"]
    ys = np.nonzero(c.buf["comp"] == n.index("brazo_humano@brazo_derecho"))[0]
    assert ys.max() <= c.anclas_px["codo_derecho"][1] + 2.5


def test_clase_grande_usa_su_celda():
    f = dict(FICHA, cuerpo=dict(FICHA["cuerpo"], clase_altura="grande"))
    c = render_cuadro(f, "stardew", "quieto", 0, "S")
    assert c.img.size == (32, 48)
    alto = celda("stardew", "grande")["gy"] - c.anclas_px["coronilla"][1]
    assert abs(alto - c.anat.alto_px) <= 1
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/bin/python -m pytest tests/test_armado.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'sprites_lib.armado'`.

- [ ] **Step 3: Crear `sprites_lib/componentes/__init__.py`**

```python
"""Biblioteca de componentes: cada pieza de un personaje (cabeza, brazo robótico, pulsera...) sabe dibujarse
en su ancla con primitivas del motor 3D. Las lecciones de CRITERIOS_ANIMACION.md viven acá, en el código:
así se aplican siempre, sin depender de que alguien se acuerde."""
from dataclasses import dataclass, field

import numpy as np

REGISTRO = {}


class Componente:
    tipo = ""
    anclas_validas = ()             # vacío = cualquiera del vocabulario
    estilos = ("stardew", "volumen", "lateral")
    params_defecto = {}
    params_material = ()            # parámetros cuyo valor tiene que ser un material de la paleta (o None)
    material_defecto = None         # material si la ficha no indica uno

    def dibujar(self, esc, ctx, spec):
        raise NotImplementedError


def registrar(cls):
    if not cls.tipo:
        raise ValueError(f"{cls.__name__}: falta 'tipo'")
    if cls.tipo in REGISTRO:
        raise ValueError(f"componente duplicado: {cls.tipo}")
    REGISTRO[cls.tipo] = cls()
    return cls


@dataclass
class Contexto:
    anat: object
    a: dict
    ps: dict
    estilo: str
    est: dict
    cam_local: np.ndarray
    paleta: dict
    mira: str
    ausentes: frozenset = field(default_factory=frozenset)
    pieza_base: int = 0
    cuadro: int = 0

    def ausente(self, nombre):
        return nombre in self.ausentes

    def escala(self):
        """1.0 en un adulto stardew: para dimensionar detalles de forma consistente entre estilos."""
        return self.anat.H / 28.0


def entrar(esc, ctx, spec, k=0):
    """Marca lo que se dibuje a continuación como parte de este componente y de su pieza k."""
    esc.componente = spec["id"]
    esc.pieza = ctx.pieza_base + k


def perpendicular(eje):
    """Un vector unitario perpendicular a eje (si el eje es vertical, usa el lateral)."""
    p = np.cross(eje, [0, 0, 1.0])
    if np.linalg.norm(p) < 1e-3:
        p = np.array([0.0, 1.0, 0.0])
    return p / np.linalg.norm(p)


from . import humano, mago, robot, ropa  # noqa: E402,F401  (registra todos los componentes)
```

- [ ] **Step 4: Crear los tres módulos provisorios** (se completan en las Tareas 6 y 7)

`sprites_lib/componentes/mago.py`:
```python
"""Componentes del mago (se completan en la Tarea 6)."""
```

`sprites_lib/componentes/robot.py`:
```python
"""Componentes robóticos (se completan en la Tarea 7)."""
```

`sprites_lib/componentes/ropa.py`:
```python
"""Componentes de ropa (se completan en la Tarea 7)."""
```

- [ ] **Step 5: Crear `sprites_lib/componentes/humano.py`**

```python
"""Cuerpo base humano: cabeza, rostro, torso, brazos y piernas. Cada estilo cambia formas; las lecciones
aplicadas: puño como pieza propia y más grande que el antebrazo, cabeza cuadrada en estilos no volumétricos,
cara corrida hacia la cámara (se lee de perfil), ojos de 2 px en Stardew."""
import numpy as np

from ..cuerpo import centro_cara, lado_de, masc
from ..render3d import v
from . import Componente, entrar, registrar

BLANCO = (250, 250, 250)


def _oscuro(c, k):
    return tuple(int(x * k) for x in c)


@registrar
class CabezaHumana(Componente):
    tipo = "cabeza_humana"
    anclas_validas = ("cabeza",)
    params_defecto = {"cabello": "corto"}
    material_defecto = "piel"

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        c = centro_cara(ctx.cam_local)
        corto = spec["parametros"]["cabello"] == "corto"

        def mat(d):
            m = np.full(d.shape[:-1], "piel", dtype=object)
            if corto:
                frente = d[..., 0] * c[0] + d[..., 1] * c[1]
                ang = np.arctan2(d[..., 1], -d[..., 0])
                pelo = np.where((np.floor(ang * 7 / np.pi) % 2) == 0, "pelo", "pelo_b")     # mechones
                m = np.where((frente > .62) & (d[..., 2] < .42), "piel", pelo).astype(object)
            return m

        if ctx.est["proporciones"]["forma_cabeza"] == "caja":
            esc.caja(ctx.a["cabeza"], ctx.anat.cabeza, mat, n=3.2)
        else:
            esc.elipsoide(ctx.a["cabeza"], ctx.anat.cabeza, mat)


@registrar
class Ojos(Componente):
    tipo = "ojos"
    anclas_validas = ("cara",)
    params_defecto = {"solo": None, "iris": None}
    params_material = ("iris",)

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        p, pal, s = spec["parametros"], ctx.paleta, ctx.escala()
        oscuro = _oscuro(pal["piel"][0], .45)
        iris = pal[p["iris"]][1] if p["iris"] else (44, 34, 48)
        izq, der = ctx.a["ojo_izquierdo"], ctx.a["ojo_derecho"]
        perp = (izq - der) / (np.linalg.norm(izq - der) + 1e-9)
        for nombre, e, lado in (("ojo_izquierdo", izq, 1), ("ojo_derecho", der, -1)):
            if p["solo"] and nombre != p["solo"]:
                continue
            if ctx.est["ojos"] == "stardew":
                esc.detalle(e + v(0, 0, 1.0 * s), oscuro)              # pestaña
                esc.detalle(e, BLANCO)
                esc.detalle(e - perp * lado * .9 * s, iris)             # iris hacia el centro de la cara
            else:
                esc.detalle(e, BLANCO)
                esc.detalle(e - perp * lado * .6 * s, oscuro)
        esc.detalle(ctx.a["cara"] + v(0, 0, -ctx.anat.cabeza[2] * .55), _oscuro(pal["piel"][0], .8))   # boca


@registrar
class TorsoHumano(Componente):
    tipo = "torso_humano"
    anclas_validas = ("torso",)
    material_defecto = "piel"

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        A, a, m = ctx.anat, ctx.a, spec["material"]
        esc.elipsoide(a["torso"], A.pecho, m)
        esc.elipsoide(a["cintura"] + v(0, 0, -A.pelvis[2] * .8), A.pelvis, m)
        esc.capsula(a["cuello"] + v(0, 0, -A.H * .05), a["cuello"] + v(0, 0, A.H * .035), A.H * .056, "piel", tapas=False)


@registrar
class BrazoHumano(Componente):
    tipo = "brazo_humano"
    anclas_validas = ("brazo_derecho", "brazo_izquierdo")
    material_defecto = "piel"

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s = masc(lado)
        A, a, m = ctx.anat, ctx.a, spec["material"]
        hom, codo, mano = a[f"hombro_{s}"], a[f"codo_{s}"], a[f"mano_{lado}"]
        entrar(esc, ctx, spec, 0)
        esc.capsula(hom, codo, A.r_brazo, m)
        if ctx.ausente(f"antebrazo_{lado}"):
            return
        esc.capsula(codo, mano, A.r_antebrazo, m)
        if not ctx.ausente(f"mano_{lado}"):
            entrar(esc, ctx, spec, 1)                   # el puño es pieza propia: tiene contorno propio
            esc.esfera(mano + (mano - codo) * .06, A.r_mano, "mano")


@registrar
class PiernaHumana(Componente):
    tipo = "pierna_humana"
    anclas_validas = ("pierna_derecha", "pierna_izquierda")
    params_defecto = {"calzado": None}
    params_material = ("calzado",)
    material_defecto = "piel"

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s = masc(lado)
        A, a, m = ctx.anat, ctx.a, spec["material"]
        entrar(esc, ctx, spec, 0)
        esc.capsula(a[f"cadera_{lado}"], a[f"rodilla_{lado}"], A.r_muslo, m)
        esc.capsula(a[f"rodilla_{lado}"], a[f"tobillo_{s}"], A.r_canilla, m)
        entrar(esc, ctx, spec, 1)
        esc.capsula(a[f"tobillo_{s}"], a[f"pie_{s}"], A.r_pie, spec["parametros"]["calzado"] or m)
```

- [ ] **Step 6: Crear `sprites_lib/armado.py`**

```python
"""Armado: ficha → lista de componentes (cuerpo base + los de la ficha) → escena → cuadros renderizados."""
from dataclasses import dataclass

from .componentes import REGISTRO, Contexto
from .cuerpo import anatomia, anclas_ausentes, posar
from .escala import celda
from .estilos import ESTILOS, crear_camara
from .paleta import paleta_estilo
from .poses import cuadros
from .render3d import Escena

BASE_HUMANO = [("cabeza_humana", "cabeza"), ("ojos", "cara"), ("torso_humano", "torso"),
               ("brazo_humano", "brazo_izquierdo"), ("brazo_humano", "brazo_derecho"),
               ("pierna_humana", "pierna_izquierda"), ("pierna_humana", "pierna_derecha")]


def _lista(x):
    return list(x) if isinstance(x, (list, tuple)) else [x]


def expandir(ficha):
    """Specs finales, una por (tipo, ancla): cuerpo base (salvo sustituciones o componentes propios del mismo
    tipo y ancla) + componentes de la ficha. Cada spec lleva id, material, parámetros completos y pieza_base."""
    cu = ficha.get("cuerpo", {})
    propios = [{**c, "ancla": an} for c in ficha.get("componentes", []) for an in _lista(c["ancla"])]
    ocupadas = {(p["tipo"], p["ancla"]) for p in propios}
    sustituidas = set((cu.get("sustituciones") or {}).keys())
    base = []
    for tipo, an in BASE_HUMANO:
        if an in sustituidas or (tipo, an) in ocupadas:
            continue
        b = {"tipo": tipo, "ancla": an}
        if tipo == "cabeza_humana":
            b["parametros"] = {"cabello": cu.get("cabello", "corto")}
        base.append(b)
    specs = []
    for i, s in enumerate(base + propios):
        comp = REGISTRO[s["tipo"]]
        specs.append(dict(
            tipo=s["tipo"], ancla=s["ancla"], material=s.get("material") or comp.material_defecto,
            parametros={**comp.params_defecto, **(s.get("parametros") or {})},
            reglas=list(s.get("reglas") or []), id=f'{s["tipo"]}@{s["ancla"]}', pieza_base=(i + 1) * 10,
            por_que=s.get("por_que", ""),
        ))
    return specs


@dataclass
class Cuadro:
    img: object
    buf: dict
    anclas_px: dict
    specs: list
    mira: str
    pose: str
    indice: int
    cam: object
    anat: object
    escala: float
    bob: int


def render_cuadro(ficha, estilo, pose, p, mira):
    cu = ficha["cuerpo"]
    clase = cu.get("clase_altura", "adulto")
    anat = anatomia(estilo, clase, cu.get("complexion", "normal"))
    cam = crear_camara(estilo, mira, celda(estilo, clase))
    est = ESTILOS[estilo]
    pal = paleta_estilo(ficha["paleta"], est)
    ps = cuadros(pose)[p]
    a = posar(anat, ps, cam.cam_local)
    aus = frozenset(anclas_ausentes(cu.get("ausentes")))
    esc = Escena(cam, pal)
    specs = expandir(ficha)
    for s in specs:
        ctx = Contexto(anat=anat, a=a, ps=ps, estilo=estilo, est=est, cam_local=cam.cam_local, paleta=pal,
                       mira=mira, ausentes=aus, pieza_base=s["pieza_base"], cuadro=ps["cuadro"])
        REGISTRO[s["tipo"]].dibujar(esc, ctx, s)
    img, buf = esc.render(estilo=est["render"], buffers=True)
    anclas_px = {k: tuple(float(x) for x in cam.proyectar(val)) for k, val in a.items()}
    return Cuadro(img=img, buf=buf, anclas_px=anclas_px, specs=specs, mira=mira, pose=pose, indice=p, cam=cam,
                  anat=anat, escala=anat.H / 28.0, bob=ps["bob"])


def render_todo(ficha, estilo, poses=("neutra", "quieto")):
    out = {}
    for pn in poses:
        for mira in ESTILOS[estilo]["direcciones"]:
            out[(pn, mira)] = [render_cuadro(ficha, estilo, pn, p, mira) for p in range(len(cuadros(pn)))]
    return out
```

- [ ] **Step 7: Correr los tests**

Run: `.venv/bin/python -m pytest tests/test_armado.py -q`
Expected: `9 passed`. Si `test_de_frente_se_ven_brazos_piernas_y_ojos` falla por los ojos, revisar que `ojos@cara` quede con píxeles con `render(buffers=True)` (los detalles marcan el buffer solo si son visibles).

- [ ] **Step 8: Mirar el resultado** (control visual, no automático)

Run: `.venv/bin/python -c "from sprites_lib.armado import render_cuadro; from tests.test_armado import FICHA; from sprites_lib.lado_a_lado import lado_a_lado; import os; os.makedirs('salida/_prueba',exist_ok=True); [render_cuadro(FICHA,e,'quieto',0,m).img.save(f'salida/_prueba/{e}_{m}.png') for e,m in (('stardew','S'),('stardew','E'),('lateral','E'),('volumen','SE'))]; print(lado_a_lado('salida/_prueba/cmp.png', ['salida/_prueba/stardew_S.png:0,0,16,32','salida/_prueba/stardew_E.png:0,0,16,32','salida/_prueba/lateral_E.png:0,0,40,40','salida/_prueba/volumen_SE.png:0,0,56,60'], 8))"`
Luego abrir `salida/_prueba/cmp.png` con Read: tiene que verse un humano con cabeza, torso, brazos con puños y piernas, sin partes flotando.

- [ ] **Step 9: Commit**

```bash
git add sprites_lib/componentes sprites_lib/armado.py tests/test_armado.py
git commit -m "Componentes base humanos y armado ficha → cuadros"
```

---

### Task 5: Carga y validación de fichas

**Files:**
- Create: `sprites_lib/ficha.py`, `tests/test_ficha.py`

**Interfaces:**
- Consumes: `componentes.REGISTRO`, `cuerpo.VOCABULARIO/SEGMENTOS/COMPLEXIONES/PADRE/anclas_ausentes`, `escala.CLASES`, `estilos.ESTILOS`, `paleta.HEX`.
- Produces: `ficha.FichaInvalida(errores: list[str])` (atributo `.errores`), `ficha.validar(f, estilos=None) -> list[str]`, `ficha.cargar(ruta_o_nombre, validar_=True, estilos=None) -> dict` (agrega `_ruta` y `_nombre`), `ficha.CARPETA = "personajes/fichas"`.

- [ ] **Step 1: Escribir los tests que fallan** — `tests/test_ficha.py`

```python
import copy

import pytest

from sprites_lib.componentes import Componente, registrar, REGISTRO
from sprites_lib.ficha import FichaInvalida, cargar, validar

if "_prueba_muneca" not in REGISTRO:
    @registrar
    class _PruebaMuneca(Componente):
        tipo = "_prueba_muneca"
        anclas_validas = ("muneca_derecha", "muneca_izquierda")
        estilos = ("stardew",)
        material_defecto = "piel"
        params_defecto = {"grosor": 1.0}

        def dibujar(self, esc, ctx, spec):
            pass

BASE = {
    "identidad": {"nombre": "Prueba", "concepto": "humano de prueba", "silueta_clave": "ninguna"},
    "cuerpo": {"base": "humano", "clase_altura": "adulto", "cabello": "corto"},
    "paleta": {"piel": {"base": "#c89070"}, "pelo": {"base": "#302018"}},
    "componentes": [{"tipo": "_prueba_muneca", "ancla": "muneca_derecha", "por_que": "prueba"}],
}


def f(**cambios):
    x = copy.deepcopy(BASE)
    for ruta, valor in cambios.items():
        d = x
        partes = ruta.split("__")
        for p in partes[:-1]:
            d = d[int(p)] if isinstance(d, list) else d[p]
        d[int(partes[-1]) if isinstance(d, list) else partes[-1]] = valor
    return x


def errores(ficha, **kw):
    return "\n".join(validar(ficha, **kw))


def test_ficha_valida():
    assert validar(BASE, estilos=["stardew"]) == []


def test_falta_seccion():
    x = copy.deepcopy(BASE); del x["paleta"]
    assert "falta la sección 'paleta'" in errores(x)


def test_ancla_mal_escrita_sugiere():
    e = errores(f(componentes__0__ancla="muneca_derecho"), estilos=["stardew"])
    assert "no existe" in e and "muneca_derecha" in e


def test_ancla_con_enie_sugiere():
    assert "muneca_derecha" in errores(f(componentes__0__ancla="muñeca_derecha"), estilos=["stardew"])


def test_componente_inexistente_sugiere():
    e = errores(f(componentes__0__tipo="_prueba_munecca"))
    assert "no existe" in e and "_prueba_muneca" in e


def test_ancla_no_valida_para_el_componente():
    assert "no se puede poner en 'cabeza'" in errores(f(componentes__0__ancla="cabeza"), estilos=["stardew"])


def test_accesorio_en_parte_ausente():
    x = f(cuerpo__ausentes=["antebrazo_derecho"])
    assert "está ausente" in errores(x, estilos=["stardew"])


def test_estilo_no_soportado():
    assert "no soporta el estilo 'lateral'" in errores(BASE, estilos=["lateral"])


def test_material_no_definido():
    assert "material 'oro' no está en la paleta" in errores(f(componentes__0__material="oro"), estilos=["stardew"])


def test_parametro_desconocido():
    e = errores(f(componentes__0__parametros={"grosro": 2}), estilos=["stardew"])
    assert "parámetro desconocido 'grosro'" in e and "grosor" in e


def test_color_invalido():
    assert "#rrggbb" in errores(f(paleta__piel={"base": "rosado"}), estilos=["stardew"])


def test_regla_desconocida():
    assert "regla desconocida" in errores(f(componentes__0__reglas=["visible_siempre"]), estilos=["stardew"])


def test_falta_por_que():
    x = copy.deepcopy(BASE); del x["componentes"][0]["por_que"]
    assert "falta 'por_que'" in errores(x, estilos=["stardew"])


def test_sustitucion_sin_componente():
    assert "no hay un componente" in errores(f(cuerpo__sustituciones={"brazo_derecho": "brazo_humano"}),
                                             estilos=["stardew"])


def test_excepcion_de_componente_inexistente():
    x = f(excepciones=[{"regla": "visible_si_ancla_visible", "componente": "pulsera", "direcciones": ["W"],
                        "motivo": "x"}])
    assert "excepción sobre 'pulsera'" in errores(x, estilos=["stardew"])


def test_falta_pelo_con_cabello_corto():
    x = copy.deepcopy(BASE); del x["paleta"]["pelo"]
    assert "falta 'pelo'" in errores(x, estilos=["stardew"])


def test_cargar_inexistente():
    with pytest.raises(FileNotFoundError, match="no existe la ficha"):
        cargar("nadie_se_llama_asi")


def test_cargar_yaml_mal_formado(tmp_path):
    ruta = tmp_path / "rota.yaml"
    ruta.write_text("identidad: [sin cerrar\n", encoding="utf-8")
    with pytest.raises(FichaInvalida, match="YAML mal formado"):
        cargar(str(ruta))
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/bin/python -m pytest tests/test_ficha.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'sprites_lib.ficha'`.

- [ ] **Step 3: Crear `sprites_lib/ficha.py`**

```python
"""Fichas de personaje: cargar el YAML y validarlo antes de generar nada. Los errores dicen qué está mal y,
si es un nombre mal escrito, sugieren el correcto (como el validador del generador LPC)."""
import difflib
import os

import yaml

from .componentes import REGISTRO
from .cuerpo import COMPLEXIONES, PADRE, SEGMENTOS, VOCABULARIO, anclas_ausentes
from .escala import CLASES
from .estilos import ESTILOS
from .paleta import HEX

CARPETA = os.path.join("personajes", "fichas")
TOPES = {"identidad", "cuerpo", "paleta", "componentes", "reglas_globales", "excepciones", "decisiones",
         "objeciones_resueltas", "creditos", "estilos"}
CLAVES_CUERPO = {"base", "clase_altura", "complexion", "piel", "cabello", "sustituciones", "ausentes"}
CLAVES_COMP = {"tipo", "ancla", "material", "parametros", "por_que", "reglas", "nuevo"}
CABELLOS = {"rapado", "corto"}
REGLAS_COMP = {"visible_si_ancla_visible", "siempre_visible", "simetrico"}
REGLAS_GLOBALES = {"paleta_identica_entre_direcciones", "lineas_guia", "nada_recortado", "tamano_de_clase",
                   "cara_visible_en", "distinto_de"}


class FichaInvalida(ValueError):
    def __init__(self, errores):
        self.errores = list(errores)
        super().__init__("ficha inválida:\n- " + "\n- ".join(self.errores))


def _sug(x, opciones):
    m = difflib.get_close_matches(str(x).replace("ñ", "n"), list(opciones), n=1, cutoff=.6)
    return f" (¿quisiste decir {m[0]!r}?)" if m else ""


def _lista(x):
    return list(x) if isinstance(x, (list, tuple)) else [x]


def _regla_ok(r):
    if r in REGLAS_COMP:
        return True
    if isinstance(r, str) and r.startswith("ausente_mas_alla_de_"):
        return r[len("ausente_mas_alla_de_"):] in PADRE
    return False


def validar(f, estilos=None):
    e = []
    if not isinstance(f, dict):
        return ["la ficha no es un diccionario YAML"]
    for k in ("identidad", "cuerpo", "paleta", "componentes"):
        if k not in f:
            e.append(f"falta la sección {k!r}")
    if e:
        return e
    for k in sorted(set(f) - TOPES):
        e.append(f"sección desconocida {k!r}{_sug(k, TOPES)}")
    for k in ("nombre", "concepto", "silueta_clave"):
        if not (f["identidad"] or {}).get(k):
            e.append(f"identidad.{k} está vacío")
    cu = f["cuerpo"] or {}
    for k in sorted(set(cu) - CLAVES_CUERPO):
        e.append(f"cuerpo: clave desconocida {k!r}{_sug(k, CLAVES_CUERPO)}")
    if cu.get("base") != "humano":
        e.append(f"cuerpo.base {cu.get('base')!r} no soportado (por ahora solo 'humano')")
    if cu.get("clase_altura", "adulto") not in CLASES:
        e.append(f"cuerpo.clase_altura {cu.get('clase_altura')!r} no existe{_sug(cu.get('clase_altura'), CLASES)}")
    if cu.get("complexion", "normal") not in COMPLEXIONES:
        e.append(f"cuerpo.complexion {cu.get('complexion')!r} no existe{_sug(cu.get('complexion'), COMPLEXIONES)}")
    if cu.get("cabello", "corto") not in CABELLOS:
        e.append(f"cuerpo.cabello {cu.get('cabello')!r} no existe; opciones: {', '.join(sorted(CABELLOS))}")
    for aus in cu.get("ausentes") or []:
        if aus not in VOCABULARIO:
            e.append(f"cuerpo.ausentes: {aus!r} no existe{_sug(aus, VOCABULARIO)}")
    ausentes = anclas_ausentes(cu.get("ausentes"))
    pal = f["paleta"] or {}
    for nom, m in pal.items():
        if not isinstance(m, dict) or not HEX.match(str(m.get("base", ""))):
            e.append(f"paleta.{nom}: 'base' tiene que ser un color #rrggbb")
    if "piel" not in pal:
        e.append("paleta: falta el material 'piel' (lo usan cara y manos)")
    if cu.get("cabello", "corto") == "corto" and "pelo" not in pal:
        e.append("paleta: falta 'pelo' (cabello: corto)")
    materiales = set(pal) | {f"{m}_b" for m in pal} | ({"mano"} if "piel" in pal else set())
    estilos = estilos or f.get("estilos") or list(ESTILOS)
    for est in estilos:
        if est not in ESTILOS:
            e.append(f"estilo desconocido {est!r}{_sug(est, ESTILOS)}")
    vistos = set()
    tipos_ficha = set()
    for i, c in enumerate(f["componentes"] or []):
        donde = f"componentes[{i}]"
        if not isinstance(c, dict):
            e.append(f"{donde}: tiene que ser un diccionario")
            continue
        for k in sorted(set(c) - CLAVES_COMP):
            e.append(f"{donde}: clave desconocida {k!r}{_sug(k, CLAVES_COMP)}")
        t = c.get("tipo")
        if t not in REGISTRO:
            e.append(f"{donde}: componente {t!r} no existe{_sug(t, REGISTRO)}")
            continue
        tipos_ficha.add(t)
        comp = REGISTRO[t]
        donde = f"{donde} ({t})"
        if not c.get("por_que"):
            e.append(f"{donde}: falta 'por_que' (toda decisión de diseño se explica)")
        for an in _lista(c.get("ancla")):
            if an not in VOCABULARIO:
                e.append(f"{donde}: ancla {an!r} no existe{_sug(an, VOCABULARIO)}")
            elif comp.anclas_validas and an not in comp.anclas_validas:
                e.append(f"{donde}: no se puede poner en {an!r}; válidas: {', '.join(comp.anclas_validas)}")
            elif an in ausentes:
                e.append(f"{donde}: el ancla {an!r} está ausente en cuerpo.ausentes")
            if (t, an) in vistos:
                e.append(f"{donde}: está repetido en {an!r}")
            vistos.add((t, an))
        mat = c.get("material") or comp.material_defecto
        if mat and mat not in materiales:
            e.append(f"{donde}: el material {mat!r} no está en la paleta{_sug(mat, materiales)}")
        params = c.get("parametros") or {}
        for k, val in params.items():
            if k not in comp.params_defecto:
                e.append(f"{donde}: parámetro desconocido {k!r}{_sug(k, comp.params_defecto)}")
            elif k in comp.params_material and val is not None and val not in materiales:
                e.append(f"{donde}: parámetros.{k} = {val!r} no es un material de la paleta")
        for r in c.get("reglas") or []:
            if not _regla_ok(r):
                e.append(f"{donde}: regla desconocida {r!r}{_sug(r, REGLAS_COMP)}")
        for est in estilos:
            if est in ESTILOS and est not in comp.estilos:
                e.append(f"{donde}: no soporta el estilo {est!r} (soporta: {', '.join(comp.estilos)})")
    for seg, tipo in (cu.get("sustituciones") or {}).items():
        if seg not in SEGMENTOS or seg.startswith("antebrazo"):
            e.append(f"cuerpo.sustituciones: {seg!r} no es un segmento sustituible (brazo_*/pierna_*)")
        if tipo not in REGISTRO:
            e.append(f"cuerpo.sustituciones.{seg}: componente {tipo!r} no existe{_sug(tipo, REGISTRO)}")
        elif (tipo, seg) not in vistos:
            e.append(f"cuerpo.sustituciones.{seg}: no hay un componente {tipo!r} con ancla {seg!r} en componentes")
    todas_dirs = {d for est in ESTILOS.values() for d in est["direcciones"]}
    for r in f.get("reglas_globales") or []:
        nombre = next(iter(r)) if isinstance(r, dict) else r
        if nombre not in REGLAS_GLOBALES:
            e.append(f"reglas_globales: regla desconocida {nombre!r}{_sug(nombre, REGLAS_GLOBALES)}")
        elif nombre == "cara_visible_en":
            for d in r[nombre]:
                if d not in todas_dirs:
                    e.append(f"reglas_globales.cara_visible_en: dirección desconocida {d!r}")
    for i, ex in enumerate(f.get("excepciones") or []):
        if ex.get("regla") not in REGLAS_COMP:
            e.append(f"excepciones[{i}]: regla desconocida {ex.get('regla')!r}")
        if ex.get("componente") not in tipos_ficha:
            e.append(f"excepciones[{i}]: excepción sobre {ex.get('componente')!r}, que no está en componentes")
        if not ex.get("motivo"):
            e.append(f"excepciones[{i}]: falta 'motivo' (una desviación sin motivo es un error)")
        for d in ex.get("direcciones") or []:
            if d not in todas_dirs:
                e.append(f"excepciones[{i}]: dirección desconocida {d!r}")
    if (f["identidad"] or {}).get("referencias") and not f.get("creditos"):
        e.append("creditos: la ficha declara referencias y no tiene créditos")
    return e


def cargar(ruta_o_nombre, validar_=True, estilos=None):
    ruta = ruta_o_nombre if ruta_o_nombre.endswith((".yaml", ".yml")) else os.path.join(CARPETA, f"{ruta_o_nombre}.yaml")
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"no existe la ficha {ruta}")
    try:
        with open(ruta, encoding="utf-8") as fh:
            f = yaml.safe_load(fh)
    except yaml.YAMLError as ex:
        raise FichaInvalida([f"YAML mal formado en {ruta}: {ex}"])
    if validar_:
        errs = validar(f, estilos)
        if errs:
            raise FichaInvalida(errs)
    f["_ruta"] = ruta
    f["_nombre"] = os.path.splitext(os.path.basename(ruta))[0]
    return f
```

- [ ] **Step 4: Correr los tests**

Run: `.venv/bin/python -m pytest tests/test_ficha.py -q`
Expected: `18 passed`.

- [ ] **Step 5: Commit**

```bash
git add sprites_lib/ficha.py tests/test_ficha.py
git commit -m "Carga y validación de fichas con sugerencias de nombres"
```

---

### Task 6: Componentes y ficha del mago

**Files:**
- Modify: `sprites_lib/componentes/mago.py` (reemplazar el docstring provisorio por el módulo completo)
- Create: `personajes/fichas/mago.yaml`, `tests/test_componentes_mago.py`

**Interfaces:**
- Consumes: `componentes.Componente/registrar/entrar`, `cuerpo.lado_de/masc`, `render3d.v`.
- Produces: tipos registrados `rastas`, `vincha`, `pulsera`, `tatuaje_runas`, `tunica_abierta`, `botas` y la ficha `mago`.

- [ ] **Step 1: Escribir los tests que fallan** — `tests/test_componentes_mago.py`

```python
import pytest

from sprites_lib.armado import render_todo
from sprites_lib.ficha import cargar


def pix(c, i):
    n = c.buf["comp_nombres"]
    return int((c.buf["comp"] == n.index(i)).sum()) if i in n else 0


@pytest.fixture(scope="module")
def mago():
    return cargar("mago")


def test_ficha_del_mago_es_valida(mago):
    assert mago["_nombre"] == "mago"


@pytest.mark.parametrize("estilo", ["stardew", "volumen", "lateral"])
def test_cada_componente_se_ve_en_alguna_direccion(mago, estilo):
    todo = render_todo(mago, estilo, poses=("quieto",))
    specs = next(iter(todo.values()))[0].specs
    for s in specs:
        total = sum(pix(c, s["id"]) for frs in todo.values() for c in frs)
        assert total > 0, (estilo, s["id"])


def test_pulsera_se_ve_de_frente_en_stardew(mago):
    c = render_todo(mago, "stardew", poses=("quieto",))[("quieto", "S")][0]
    assert pix(c, "pulsera@muneca_derecha") >= 1
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/bin/python -m pytest tests/test_componentes_mago.py -q`
Expected: FAIL con `FileNotFoundError: no existe la ficha personajes/fichas/mago.yaml`.

- [ ] **Step 3: Escribir `sprites_lib/componentes/mago.py`**

```python
"""Componentes del mago: rastas, vincha, pulsera, tatuajes rúnicos, túnica abierta y botas.
Lecciones aplicadas: las rastas nacen FUERA del volumen de la cabeza (si no, quedan tapadas) y tienen
1 cuadro de retraso; la túnica va abierta adelante (se ven las piernas) y con pliegues (detalle dibujado);
las mangas separan brazo y torso."""
import numpy as np

from ..cuerpo import lado_de, masc
from ..render3d import v
from . import Componente, entrar, registrar


@registrar
class Rastas(Componente):
    tipo = "rastas"
    anclas_validas = ("cabeza",)
    material_defecto = "pelo"
    params_defecto = {"cantidad": 6, "largo": "hombros", "cuentas": None}
    params_material = ("cuentas",)

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        A, p, s = ctx.anat, spec["parametros"], ctx.escala()
        rf, rl, rz = A.cabeza
        hc = ctx.a["cabeza"]
        n = max(2, int(p["cantidad"]))
        pasos = {"corto": 2, "hombros": 4, "cintura": 6}[p["largo"]]
        bob, prev = ctx.ps["bob"], ctx.ps["bob_prev"]
        for i in range(n):
            ang = np.pi * (.5 + i / (n - 1))              # de un costado a otro pasando por la nuca
            pts = [hc + v(np.cos(ang) * rf * 1.1, np.sin(ang) * rl * 1.02, rz * .15)]
            for j in range(1, pasos + 1):
                sw = np.sin(j * .9 - ctx.ps["fase"] * 2 * np.pi + i) * .35 * s
                pts.append(pts[-1] + v(-.35 * s + sw, np.sin(ang) * .06 * s, -1.55 * s - (prev - bob) * .2 * s))
            mat = spec["material"] if i % 2 else f'{spec["material"]}_b'
            for q0, q1 in zip(pts, pts[1:]):
                esc.capsula(q0, q1, .95 * s, mat)
            if p["cuentas"] and i in (0, n - 1):
                esc.detalle(pts[-1] + ctx.cam_local * .9 * s + v(0, 0, -.6 * s), ctx.paleta[p["cuentas"]][1])


@registrar
class Vincha(Componente):
    tipo = "vincha"
    anclas_validas = ("frente",)
    material_defecto = "oro"
    params_defecto = {"gema": None}
    params_material = ("gema",)

    def dibujar(self, esc, ctx, spec):
        entrar(esc, ctx, spec)
        A, hc = ctx.anat, ctx.a["cabeza"]
        banda = lambda d: np.abs(d[..., 2] - .47) < .08
        radios = tuple(r * 1.05 for r in A.cabeza)
        if ctx.est["proporciones"]["forma_cabeza"] == "caja":
            esc.caja(hc, radios, spec["material"], n=3.2, conservar=banda)
        else:
            esc.elipsoide(hc, radios, spec["material"], conservar=banda)
        g = spec["parametros"]["gema"]
        if g:
            fr = ctx.a["frente"]
            esc.detalle(fr + (fr - hc) * .08 + v(0, 0, A.cabeza[2] * .1), ctx.paleta[g][1])


@registrar
class Pulsera(Componente):
    tipo = "pulsera"
    anclas_validas = ("muneca_derecha", "muneca_izquierda")
    material_defecto = "oro"
    params_defecto = {"grosor": 1.0}

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"])
        a, A, s = ctx.a, ctx.anat, ctx.escala()
        eje = a[f"mano_{lado}"] - a[f"codo_{masc(lado)}"]
        u = eje / (np.linalg.norm(eje) + 1e-9)
        m = a[spec["ancla"]]
        largo = max(.12 * np.linalg.norm(eje), 1.0 * s)                 # nunca menos de ~1 px de ancho
        entrar(esc, ctx, spec)
        esc.capsula(m - u * largo / 2, m + u * largo / 2, A.r_antebrazo + .35 * s * spec["parametros"]["grosor"],
                    spec["material"], tapas=False)


@registrar
class TatuajeRunas(Componente):
    tipo = "tatuaje_runas"
    anclas_validas = ("brazo_derecho", "brazo_izquierdo")
    material_defecto = "runa"
    params_defecto = {"puntos_por_segmento": 1}

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s_ = masc(lado)
        A, a = ctx.anat, ctx.a
        col = ctx.paleta[spec["material"]][1]
        n = max(1, int(spec["parametros"]["puntos_por_segmento"]))
        segs = [(a[f"hombro_{s_}"], a[f"codo_{s_}"], A.r_brazo)]
        if not ctx.ausente(f"antebrazo_{lado}"):
            segs.append((a[f"codo_{s_}"], a[f"muneca_{lado}"], A.r_antebrazo))
        entrar(esc, ctx, spec)
        for q0, q1, r in segs:
            for k in (np.linspace(.3, .8, n) if n > 1 else [.5]):
                esc.detalle(q0 + (q1 - q0) * k + ctx.cam_local * r, col)


@registrar
class TunicaAbierta(Componente):
    tipo = "tunica_abierta"
    anclas_validas = ("torso",)
    material_defecto = "tunica"
    params_defecto = {"interior": None, "ribete": None, "faldon": "hasta_rodilla", "mangas": True}
    params_material = ("interior", "ribete")

    def dibujar(self, esc, ctx, spec):
        A, a, m, p, s = ctx.anat, ctx.a, spec["material"], spec["parametros"], ctx.escala()

        def mat_torso(d):
            adel, lat = d[..., 0], np.abs(d[..., 1])
            out = np.full(d.shape[:-1], m, dtype=object)
            if p["interior"]:
                out[(adel > .2) & (lat < .38)] = p["interior"]
            if p["ribete"]:
                out[(adel > .2) & (lat >= .38) & (lat < .5)] = p["ribete"]
            return out

        entrar(esc, ctx, spec, 0)
        esc.elipsoide(a["torso"], tuple(r * 1.08 for r in A.pecho), mat_torso)
        esc.elipsoide(a["cintura"] + v(0, 0, -A.pelvis[2] * .8), tuple(r * 1.08 for r in A.pelvis), m)
        sube = a["cintura"][2] - (A.pelvis_u + A.pelvis[2] * .8)
        lag = np.sin(2 * np.pi * (ctx.ps["fase"] - .1) * 2)
        hasta = {"hasta_rodilla": A.cadera_u * .45, "medio_muslo": A.cadera_u * .7, "tobillo": A.cadera_u * .12}[p["faldon"]]
        pliegue = lambda d, t: np.where((np.floor(np.arctan2(d[..., 1], d[..., 0]) * 5 / np.pi) % 2) == 0,
                                        m, f"{m}_b").astype(object)
        esc.faldon(a["cintura"], v(-A.H * .05 - .6 * lag * s, 0, hasta + sube), A.pelvis[1] * 1.0,
                   A.pelvis[1] * 1.3, pliegue)
        if p["mangas"]:
            for k, s_ in enumerate(("derecho", "izquierdo")):
                entrar(esc, ctx, spec, 1 + k)                    # la manga separa brazo y torso
                hom, codo = a[f"hombro_{s_}"], a[f"codo_{s_}"]
                esc.capsula(hom, hom + (codo - hom) * .6, A.r_brazo + .25 * s, m)


@registrar
class Botas(Componente):
    tipo = "botas"
    anclas_validas = ("pie_derecho", "pie_izquierdo")
    material_defecto = "bota"
    params_defecto = {"suela": None}
    params_material = ("suela",)

    def dibujar(self, esc, ctx, spec):
        s_ = masc(lado_de(spec["ancla"]))
        A, a, s = ctx.anat, ctx.a, ctx.escala()
        tob, pie = a[f"tobillo_{s_}"], a[f"pie_{s_}"]
        entrar(esc, ctx, spec)
        esc.capsula(tob, pie, A.r_pie * 1.12, spec["material"])
        esc.capsula(tob, tob + v(0, 0, A.canilla * .35), A.r_canilla * 1.15, spec["material"], tapas=False)
        if spec["parametros"]["suela"]:
            col = ctx.paleta[spec["parametros"]["suela"]][1]
            for k in np.linspace(0, 1, 4):
                esc.detalle(tob + (pie - tob) * k + v(0, 0, -A.r_pie * 1.12 + .25 * s) + ctx.cam_local * .6 * s, col)
```

- [ ] **Step 4: Crear `personajes/fichas/mago.yaml`**

```yaml
# Ficha del mago de las runas — migrada desde personajes/mago_*.py (2026-09-27)
identidad:
  nombre: "Mago de las runas"
  concepto: >
    Hechicero viajero que mezcla magia antigua con tecnología rúnica. Tranquilo y sabio,
    pero ágil: corre en vez de volar.
  rol: jugable
  silueta_clave: "rastas blancas largas + túnica abierta"

cuerpo:
  base: humano
  clase_altura: adulto
  complexion: normal
  piel: morena
  cabello: corto

paleta:
  piel:     {base: "#8c5638", por_que: "tez morena"}
  pelo:     {base: "#e2e2f0", por_que: "rastas blancas: edad y sabiduría"}
  tunica:   {base: "#5c2c96", por_que: "violeta = magia en todo el juego"}
  camisa:   {base: "#362e62", por_que: "interior oscuro: hace resaltar el ribete"}
  oro:      {base: "#e2aa34", por_que: "metal de sus amuletos; contrasta con el violeta"}
  runa:     {base: "#5af0e6", emisivo: true, por_que: "energía rúnica: el único color que brilla"}
  pantalon: {base: "#42366e", por_que: "se separa de la túnica sin competir"}
  bota:     {base: "#62392a", por_que: "cuero de viaje"}

componentes:
  - tipo: rastas
    ancla: cabeza
    material: pelo
    parametros: {cantidad: 6, largo: hombros, cuentas: runa}
    por_que: "rasgo principal de su silueta"
    reglas: [siempre_visible]
  - tipo: vincha
    ancla: frente
    material: oro
    parametros: {gema: runa}
    por_que: "amuleto que canaliza las runas"
    reglas: [visible_si_ancla_visible]
  - tipo: pulsera
    ancla: muneca_derecha
    material: oro
    por_que: "regalo de su maestro; nunca se la saca"
    reglas: [visible_si_ancla_visible]
  - tipo: tatuaje_runas
    ancla: [brazo_izquierdo, brazo_derecho]
    material: runa
    por_que: "runas tatuadas: su magia vive en el cuerpo"
    reglas: [visible_si_ancla_visible, simetrico]
  - tipo: tunica_abierta
    ancla: torso
    material: tunica
    parametros: {interior: camisa, ribete: oro, faldon: hasta_rodilla}
    por_que: "abierta para correr; el ribete dorado la distingue de lejos"
  - tipo: pierna_humana
    ancla: [pierna_izquierda, pierna_derecha]
    material: pantalon
    parametros: {calzado: bota}
    por_que: "pantalón de viaje"
  - tipo: botas
    ancla: [pie_izquierdo, pie_derecho]
    material: bota
    parametros: {suela: runa}
    por_que: "suelas rúnicas: deja huellas de luz"
    reglas: [simetrico]
  - tipo: ojos
    ancla: cara
    parametros: {iris: runa}
    por_que: "ojos cian: la magia se le nota en la mirada"

reglas_globales:
  - paleta_identica_entre_direcciones
  - lineas_guia
  - nada_recortado
  - tamano_de_clase
  - cara_visible_en: [S, E, W, SE, SW]
  - distinto_de: [clast]

creditos: []
```

- [ ] **Step 5: Correr los tests**

Run: `.venv/bin/python -m pytest tests/test_componentes_mago.py -q`
Expected: `5 passed`. Si falla `distinto_de: [clast]` por validación: la ficha `clast` todavía no pasa (Tarea 7); `validar` no carga otras fichas, así que no debería fallar por eso.

- [ ] **Step 6: Commit**

```bash
git add sprites_lib/componentes/mago.py personajes/fichas/mago.yaml tests/test_componentes_mago.py
git commit -m "Componentes y ficha del mago"
```

---

### Task 7: Componentes y ficha de Clast

**Files:**
- Modify: `sprites_lib/componentes/robot.py`, `sprites_lib/componentes/ropa.py` (módulos completos), `personajes/fichas/clast.yaml` (agregar `por_que` faltantes)
- Create: `tests/test_componentes_clast.py`

**Interfaces:**
- Consumes: `componentes.*`, `cuerpo.lado_de/masc`, `render3d.v`.
- Produces: tipos `brazo_robotico`, `brazo_robotico_amputado`, `munon_cables`, `pierna_robotica`, `visor`, `placa_sien`, `cables_nuca`, `remera_larga_rota`, `cinturon`.

- [ ] **Step 1: Escribir los tests que fallan** — `tests/test_componentes_clast.py`

```python
import numpy as np
import pytest

from sprites_lib.armado import render_cuadro, render_todo
from sprites_lib.ficha import cargar


def mask(c, i):
    n = c.buf["comp_nombres"]
    return (c.buf["comp"] == n.index(i)) if i in n else np.zeros(c.buf["comp"].shape, bool)


@pytest.fixture(scope="module")
def clast():
    return cargar("clast")


def test_ficha_de_clast_es_valida(clast):
    assert clast["identidad"]["nombre"] == "Clast"


@pytest.mark.parametrize("estilo", ["stardew", "volumen", "lateral"])
def test_cada_componente_se_ve_en_alguna_direccion(clast, estilo):
    todo = render_todo(clast, estilo, poses=("quieto",))
    specs = next(iter(todo.values()))[0].specs
    for s in specs:
        assert sum(int(mask(c, s["id"]).sum()) for frs in todo.values() for c in frs) > 0, (estilo, s["id"])


def test_no_tiene_brazos_ni_piernas_humanos(clast):
    ids = {s["id"] for s in render_cuadro(clast, "stardew", "quieto", 0, "S").specs}
    assert not any(i.startswith(("brazo_humano", "pierna_humana")) for i in ids)


def test_brazo_amputado_termina_en_el_codo(clast):
    c = render_cuadro(clast, "lateral", "neutra", 0, "E")
    ys = np.nonzero(mask(c, "brazo_robotico_amputado@brazo_derecho"))[0]
    assert ys.max() <= c.anclas_px["codo_derecho"][1] + 2.6 * c.escala + 1.5


def test_la_chispa_parpadea(clast):
    luz = tuple(int(x) for x in c0_luz(clast))
    brilla = [luz in render_cuadro(clast, "lateral", "quieto", p, "E").buf["colores_detalle"] for p in range(4)]
    assert brilla[0] and not all(brilla)


def c0_luz(clast):
    from sprites_lib.estilos import ESTILOS
    from sprites_lib.paleta import paleta_estilo
    return paleta_estilo(clast["paleta"], ESTILOS["lateral"])["luz"][2]
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/bin/python -m pytest tests/test_componentes_clast.py -q`
Expected: FAIL con `FichaInvalida` (componentes `brazo_robotico`… no existen).

- [ ] **Step 3: Escribir `sprites_lib/componentes/robot.py`**

```python
"""Componentes robóticos: prótesis de brazo y pierna, brazo amputado, muñón con cables, visor, placa y cables.
Lección aplicada: detalles chicos (visor, chispa) con tamaño mínimo en px y color emisivo para que se lean a 16 px."""
import numpy as np

from ..cuerpo import lado_de, masc
from ..render3d import v
from . import Componente, entrar, perpendicular, registrar


def _hacia_afuera(p, centro):
    d = p - centro
    return d / (np.linalg.norm(d) + 1e-9)


def _detalles_metal(esc, ctx, p, segmentos, juntas):
    if p.get("rayas"):
        col = ctx.paleta[p["rayas"]][1]
        for q0, q1, r in segmentos:
            esc.detalle(q0 + (q1 - q0) * .5 + ctx.cam_local * r, col)
    if p.get("juntas"):
        col = ctx.paleta[p["juntas"]][1]
        for j, r in juntas:
            esc.detalle(j + ctx.cam_local * r, col)


@registrar
class BrazoRobotico(Componente):
    tipo = "brazo_robotico"
    anclas_validas = ("brazo_derecho", "brazo_izquierdo")
    material_defecto = "metal"
    params_defecto = {"juntas": None, "rayas": None, "mano": "pinza_3_dedos"}
    params_material = ("juntas", "rayas")

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s_ = masc(lado)
        A, a, m, p = ctx.anat, ctx.a, spec["material"], spec["parametros"]
        hom, codo, mano = a[f"hombro_{s_}"], a[f"codo_{s_}"], a[f"mano_{lado}"]
        entrar(esc, ctx, spec, 0)
        esc.esfera(hom, A.r_brazo * 1.3, m)                          # rótula del hombro
        esc.capsula(hom, codo, A.r_brazo * .95, m)
        esc.esfera(codo, A.r_brazo * 1.1, m)
        esc.capsula(codo, mano, A.r_antebrazo * .95, m)
        _detalles_metal(esc, ctx, p, [(hom, codo, A.r_brazo), (codo, mano, A.r_antebrazo)], [(codo, A.r_brazo * 1.1)])
        entrar(esc, ctx, spec, 1)                                    # mano = pieza propia
        eje = (mano - codo) / (np.linalg.norm(mano - codo) + 1e-9)
        if p["mano"] == "pinza_3_dedos":
            lat = perpendicular(eje)
            esc.esfera(mano, A.r_mano * .8, m)
            for off in (-.6, .6):
                esc.capsula(mano, mano + eje * A.r_mano * 1.4 + lat * off * A.r_mano, A.r_mano * .32, m)
            esc.capsula(mano, mano + eje * A.r_mano * 1.1 - np.cross(lat, eje) * A.r_mano * .8, A.r_mano * .32, m)
        else:
            esc.esfera(mano, A.r_mano, m)


@registrar
class BrazoRoboticoAmputado(Componente):
    tipo = "brazo_robotico_amputado"
    anclas_validas = ("brazo_derecho", "brazo_izquierdo")
    material_defecto = "metal"
    params_defecto = {"termina_en": None, "juntas": None}
    params_material = ("juntas",)

    def dibujar(self, esc, ctx, spec):
        s_ = masc(lado_de(spec["ancla"]))
        A, a, m = ctx.anat, ctx.a, spec["material"]
        hom, codo = a[f"hombro_{s_}"], a[f"codo_{s_}"]
        entrar(esc, ctx, spec)
        esc.esfera(hom, A.r_brazo * 1.3, m)
        esc.capsula(hom, codo, A.r_brazo * .95, m)
        esc.esfera(codo, A.r_brazo * 1.05, m)                        # termina en el codo: tapa rota
        _detalles_metal(esc, ctx, spec["parametros"], [], [(hom, A.r_brazo * 1.3)])


@registrar
class MunonCables(Componente):
    tipo = "munon_cables"
    anclas_validas = ("codo_derecho", "codo_izquierdo", "rodilla_derecha", "rodilla_izquierda")
    material_defecto = "cable"
    params_defecto = {"cables": 3, "largo_px": 2, "chispa": None, "chispa_cada_cuadros": 3}
    params_material = ("chispa",)

    def dibujar(self, esc, ctx, spec):
        an = spec["ancla"]; lado = lado_de(an)
        a, e, p = ctx.a, ctx.escala(), spec["parametros"]
        padre = a[f"hombro_{masc(lado)}"] if an.startswith("codo") else a[f"cadera_{lado}"]
        eje = (a[an] - padre) / (np.linalg.norm(a[an] - padre) + 1e-9)
        perp = perpendicular(eje)
        n = max(1, int(p["cables"]))
        entrar(esc, ctx, spec)
        puntas = []
        for i in range(n):
            t = (i - (n - 1) / 2) / max(1, n - 1)
            fin = a[an] + eje * (p["largo_px"] * e + ctx.anat.r_brazo) + perp * t * 1.2 * e + v(0, 0, -.6 * e * abs(t))
            esc.capsula(a[an], fin, .38 * e, spec["material"])
            puntas.append(fin)
        if p["chispa"] and ctx.cuadro % max(1, int(p["chispa_cada_cuadros"])) == 0:
            esc.detalle(puntas[0] + ctx.cam_local * .5 * e, ctx.paleta[p["chispa"]][2])


@registrar
class PiernaRobotica(Componente):
    tipo = "pierna_robotica"
    anclas_validas = ("pierna_derecha", "pierna_izquierda")
    material_defecto = "metal"
    params_defecto = {"juntas": None, "rodilla": "piston", "pie": "bota_metalica"}
    params_material = ("juntas",)

    def dibujar(self, esc, ctx, spec):
        lado = lado_de(spec["ancla"]); s_ = masc(lado)
        A, a, m, p, e = ctx.anat, ctx.a, spec["material"], spec["parametros"], ctx.escala()
        cad, rod, tob, pie = a[f"cadera_{lado}"], a[f"rodilla_{lado}"], a[f"tobillo_{s_}"], a[f"pie_{s_}"]
        entrar(esc, ctx, spec, 0)
        esc.esfera(cad, A.r_muslo * 1.1, m)
        esc.capsula(cad, rod, A.r_muslo * .9, m)
        esc.esfera(rod, A.r_muslo * .95, m)
        esc.capsula(rod, tob, A.r_canilla * .95, m)
        if p["rodilla"] == "piston":
            esc.capsula(cad + (rod - cad) * .45 + v(A.r_muslo * .9, 0, 0),
                        rod + (tob - rod) * .45 + v(A.r_canilla * .9, 0, 0), .35 * e, m)
        _detalles_metal(esc, ctx, p, [], [(rod, A.r_muslo * .95)])
        entrar(esc, ctx, spec, 1)
        esc.esfera(tob, A.r_canilla * 1.05, m)
        esc.capsula(tob, pie, A.r_pie * 1.15, m)


@registrar
class Visor(Componente):
    tipo = "visor"
    anclas_validas = ("ojo_derecho", "ojo_izquierdo")
    material_defecto = "metal"
    params_defecto = {"lente": None, "tamano_min_px": 2}
    params_material = ("lente",)

    def dibujar(self, esc, ctx, spec):
        o, hc, e, p = ctx.a[spec["ancla"]], ctx.a["cabeza"], ctx.escala(), spec["parametros"]
        afuera = _hacia_afuera(o, hc)
        entrar(esc, ctx, spec)
        esc.caja(o + afuera * .3 * e, (1.0 * e, 1.2 * e, .9 * e), spec["material"], n=3.0)
        if p["lente"]:
            n = max(1, int(p["tamano_min_px"]))
            for k in range(n):
                esc.detalle(o + afuera * 1.3 * e + v(0, 0, (k - (n - 1) / 2) * e), ctx.paleta[p["lente"]][1])


@registrar
class PlacaSien(Componente):
    tipo = "placa_sien"
    anclas_validas = ("sien_derecha", "sien_izquierda")
    material_defecto = "metal"

    def dibujar(self, esc, ctx, spec):
        o, e = ctx.a[spec["ancla"]], ctx.escala()
        afuera = _hacia_afuera(o, ctx.a["cabeza"])
        entrar(esc, ctx, spec)
        esc.caja(o + afuera * .25 * e, (1.3 * e, .6 * e, 1.4 * e), spec["material"], n=4.0)
        esc.detalle(o + afuera * .9 * e, ctx.paleta[spec["material"]][2])        # remache


@registrar
class CablesNuca(Componente):
    tipo = "cables_nuca"
    anclas_validas = ("nuca",)
    material_defecto = "cable"
    params_defecto = {"cables": 2, "luz_en_punta": None}
    params_material = ("luz_en_punta",)

    def dibujar(self, esc, ctx, spec):
        o, e, p = ctx.a["nuca"], ctx.escala(), spec["parametros"]
        n = max(1, int(p["cables"]))
        entrar(esc, ctx, spec)
        for i in range(n):
            lat = (i - (n - 1) / 2) * 1.4 * e
            fin = o + v(-1.6 * e, lat, -2.2 * e)
            esc.capsula(o + v(-.2 * e, lat, 0), fin, .42 * e, spec["material"])
            if p["luz_en_punta"]:
                esc.detalle(fin + ctx.cam_local * .4 * e, ctx.paleta[p["luz_en_punta"]][1])
```

- [ ] **Step 4: Escribir `sprites_lib/componentes/ropa.py`**

```python
"""Ropa genérica: remera larga rota y cinturón. La prenda grande con jirones se lee mejor a baja resolución
que varias prendas chicas; las costuras son detalle dibujado (evita el look liso de render)."""
import numpy as np

from ..render3d import v
from . import Componente, entrar, registrar


@registrar
class RemeraLargaRota(Componente):
    tipo = "remera_larga_rota"
    anclas_validas = ("torso",)
    material_defecto = "ropa"
    params_defecto = {"largo": "medio_muslo", "jirones": 3, "sin_mangas": True}

    def dibujar(self, esc, ctx, spec):
        A, a, m, p, s = ctx.anat, ctx.a, spec["material"], spec["parametros"], ctx.escala()
        costuras = lambda d: np.where((np.floor((d[..., 2] + 1) * 4) % 2) == 0, m, f"{m}_b").astype(object)
        entrar(esc, ctx, spec, 0)
        esc.elipsoide(a["torso"], tuple(r * 1.1 for r in A.pecho), costuras)
        esc.elipsoide(a["cintura"] + v(0, 0, -A.pelvis[2] * .8), tuple(r * 1.1 for r in A.pelvis), m)
        sube = a["cintura"][2] - (A.pelvis_u + A.pelvis[2] * .8)
        hasta = {"cadera": A.cadera_u * .9, "medio_muslo": A.cadera_u * .62, "rodilla": A.cadera_u * .45}[p["largo"]]
        j = max(1, int(p["jirones"]))
        jirones = lambda d, t: ~((t > .72) & ((np.floor(np.arctan2(d[..., 1], d[..., 0]) * j / np.pi) % 2) == 0))
        esc.faldon(a["cintura"], v(-.3 * s, 0, hasta + sube), A.pelvis[1] * 1.08, A.pelvis[1] * 1.3, m,
                   conservar=lambda d: np.ones(d.shape[:-1], bool), recorte=jirones)
        if not p["sin_mangas"]:
            for k, s_ in enumerate(("derecho", "izquierdo")):
                entrar(esc, ctx, spec, 1 + k)
                hom, codo = a[f"hombro_{s_}"], a[f"codo_{s_}"]
                esc.capsula(hom, hom + (codo - hom) * .5, A.r_brazo + .25 * s, m)


@registrar
class Cinturon(Componente):
    tipo = "cinturon"
    anclas_validas = ("cintura",)
    material_defecto = "cuero"
    params_defecto = {"hebilla": None}
    params_material = ("hebilla",)

    def dibujar(self, esc, ctx, spec):
        A, a = ctx.anat, ctx.a
        entrar(esc, ctx, spec)
        esc.elipsoide(a["cintura"], (A.pelvis[0] * 1.22, A.pelvis[1] * 1.22, A.pelvis[2] * 1.2), spec["material"],
                      conservar=lambda d: np.abs(d[..., 2]) < .3)
        if spec["parametros"]["hebilla"]:
            esc.detalle(a["cintura"] + v(A.pelvis[0] * 1.25, 0, 0), ctx.paleta[spec["parametros"]["hebilla"]][2])
```

- [ ] **Step 5: Completar los `por_que` en `personajes/fichas/clast.yaml`** (el validador los exige)

Agregar `por_que` a los componentes que no lo tienen:
- `pierna_robotica`: `por_que: "prótesis industriales: lo mecánico domina de la cintura para abajo"`
- `placa_sien`: `por_que: "implante del mismo lado del daño"`
- `cables_nuca`: `por_que: "conexión del visor: se ven de espaldas y cuentan que es cyborg"`
- `remera_larga_rota`: ya tiene; `cinturon`: `por_que: "sostiene la remera y marca la cintura"`
- `ojos`: `por_que: "solo el ojo izquierdo es humano; el derecho está bajo el visor"`

- [ ] **Step 6: Correr los tests de esta tarea y todos los anteriores**

Run: `.venv/bin/python -m pytest -q`
Expected: todos pasan (`test_componentes_clast.py`: 7 passed).

- [ ] **Step 7: Commit**

```bash
git add sprites_lib/componentes/robot.py sprites_lib/componentes/ropa.py personajes/fichas/clast.yaml tests/test_componentes_clast.py
git commit -m "Componentes robóticos y de ropa; ficha de Clast completa"
```

---

### Task 8: Tests de consistencia del personaje

**Files:**
- Create: `sprites_lib/tests_personaje.py`, `tests/test_tests_personaje.py`

**Interfaces:**
- Consumes: `armado.render_todo/Cuadro`, `cuerpo.SEGMENTOS/PADRE`, `escala.celda`, `estilos.ESTILOS`, `paleta.paleta_estilo/hex_rgb`, `render3d._oscurecer`, `comparar_estilo.metricas/comparar`, `ficha.cargar` (import diferido).
- Produces: `Resultado(regla, ok, detalle="", evidencia=[], omitido=False)`; `mascara(cuadro, comp_id)`; `ancla_visible(cuadro, ancla, tol=None)`; `t_visibilidad, t_ausentes, t_lineas_guia, t_paleta, t_tamano, t_recorte, t_cara, t_simetria, t_distinto, t_estilo`; `correr_tests(ficha, estilo, todo, carpeta) -> list[Resultado]`; `informe_md(ficha, estilo, resultados) -> str`.

- [ ] **Step 1: Escribir los tests que fallan** — `tests/test_tests_personaje.py`

```python
import numpy as np
import pytest
from PIL import Image

import sprites_lib.componentes as comps
from sprites_lib import tests_personaje as tp
from sprites_lib.armado import render_todo
from sprites_lib.ficha import cargar
from sprites_lib.render3d import v


@pytest.fixture(scope="module")
def mago():
    return cargar("mago")


@pytest.fixture(scope="module")
def todo_mago(mago):
    return render_todo(mago, "stardew")


def test_sano_tamano_recorte_paleta(mago, todo_mago):
    for r in (tp.t_tamano(mago, "stardew", todo_mago), tp.t_recorte(todo_mago),
              tp.t_paleta(mago, "stardew", todo_mago)):
        assert r.ok, (r.regla, r.evidencia)


def test_detecta_pulsera_que_desaparece_en_una_direccion(mago, monkeypatch):
    orig = comps.REGISTRO["pulsera"].dibujar
    monkeypatch.setattr(comps.REGISTRO["pulsera"], "dibujar",
                        lambda esc, ctx, spec: None if ctx.mira == "E" else orig(esc, ctx, spec))
    r = tp.t_visibilidad(mago, render_todo(mago, "stardew"))
    assert not r.ok and any("pulsera@muneca_derecha" in e and "/E/" in e for e in r.evidencia)


def test_detecta_ojos_corridos_2px(mago, monkeypatch):
    orig = comps.REGISTRO["ojos"].dibujar

    def corridos(esc, ctx, spec):
        if ctx.mira == "S":
            ctx.a = dict(ctx.a, ojo_izquierdo=ctx.a["ojo_izquierdo"] + v(0, 0, 2.2),
                         ojo_derecho=ctx.a["ojo_derecho"] + v(0, 0, 2.2), cara=ctx.a["cara"] + v(0, 0, 2.2))
        orig(esc, ctx, spec)

    monkeypatch.setattr(comps.REGISTRO["ojos"], "dibujar", corridos)
    r = tp.t_lineas_guia(mago, render_todo(mago, "stardew"))
    assert not r.ok and any("ojos@cara" in e for e in r.evidencia)


def test_detecta_recorte(todo_mago):
    c = todo_mago[("quieto", "S")][0]
    a = np.array(c.img); a[0, 8] = (255, 0, 0, 255)
    roto = {("quieto", "S"): [type(c)(**{**c.__dict__, "img": Image.fromarray(a, "RGBA")})]}
    assert not tp.t_recorte(roto).ok


def test_detecta_tamano_incorrecto(mago, monkeypatch):
    import sprites_lib.armado as armado
    orig = armado.anatomia
    monkeypatch.setattr(armado, "anatomia", lambda e, c="adulto", x="normal": orig(e, "grande", x))
    r = tp.t_tamano(mago, "stardew", render_todo(mago, "stardew", poses=("neutra",)))
    assert not r.ok


def test_detecta_color_fuera_de_paleta(mago, todo_mago):
    c = todo_mago[("quieto", "S")][0]
    a = np.array(c.img); ys, xs = np.nonzero(a[..., 3]); a[ys[0], xs[0]] = (1, 254, 3, 255)
    roto = {("quieto", "S"): [type(c)(**{**c.__dict__, "img": Image.fromarray(a, "RGBA")})]}
    r = tp.t_paleta(mago, "stardew", roto)
    assert not r.ok and "(1, 254, 3)" in r.detalle


def test_cara_sin_ojos_falla(mago, monkeypatch):
    monkeypatch.setattr(comps.REGISTRO["ojos"], "dibujar", lambda esc, ctx, spec: None)
    assert not tp.t_cara(mago, "stardew", render_todo(mago, "stardew", poses=("quieto",))).ok


def test_distinto_del_elenco(mago):
    assert tp.t_distinto(mago).ok
    parecido = dict(mago, reglas_globales=[{"distinto_de": ["mago"]}])
    assert not tp.t_distinto(parecido).ok             # contra sí mismo: todo igual


def test_informe(mago, todo_mago, tmp_path):
    res = tp.correr_tests(mago, "stardew", todo_mago, str(tmp_path))
    md = tp.informe_md(mago, "stardew", res)
    assert md.startswith("# Informe de consistencia") and "| Regla | Estado | Detalle |" in md
    assert {r.regla for r in res} >= {"visibilidad de componentes", "líneas guía", "paleta", "tamaño y pivote",
                                     "recorte", "cara visible", "simetría", "distinto del elenco",
                                     "estilo vs referencia", "partes ausentes"}
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/bin/python -m pytest tests/test_tests_personaje.py -q`
Expected: FAIL con `ImportError: cannot import name 'tests_personaje'`.

- [ ] **Step 3: Crear `sprites_lib/tests_personaje.py`**

```python
"""Tests de consistencia de un personaje sobre todos sus cuadros renderizados (todas las poses y direcciones).
Cada test devuelve un Resultado con la evidencia exacta (pose/dirección/cuadro) para poder corregir."""
import contextlib
import io
import os
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

from .cuerpo import PADRE, SEGMENTOS
from .escala import alto_objetivo_px, celda
from .estilos import ESTILOS
from .paleta import hex_rgb, paleta_estilo
from .render3d import _oscurecer

CONTORNO = (16, 10, 24)
GUIAS = {"cara", "ojo_derecho", "ojo_izquierdo", "frente", "cintura", "sien_derecha", "sien_izquierda"}
FRENTE = {"stardew": "S", "volumen": "S", "lateral": None}


@dataclass
class Resultado:
    regla: str
    ok: bool
    detalle: str = ""
    evidencia: list = field(default_factory=list)
    omitido: bool = False


def _cuadros(todo):
    for frs in todo.values():
        yield from frs


def _specs(todo):
    return next(_cuadros(todo)).specs


def mascara(cuadro, comp_id):
    n = cuadro.buf["comp_nombres"]
    if comp_id not in n:
        return np.zeros(cuadro.buf["comp"].shape, bool)
    return cuadro.buf["comp"] == n.index(comp_id)


def ancla_visible(cuadro, ancla, tol=None):
    """Un ancla está a la vista si el píxel donde se proyecta muestra una superficie cercana a ella
    (y no algo que la tapa por delante, como el torso)."""
    nombre = SEGMENTOS[ancla][1] if ancla in SEGMENTOS else ancla
    x, y, d = cuadro.anclas_px[nombre]
    ix, iy = int(round(x)), int(round(y))
    sol = cuadro.buf["solido"]
    if not (0 <= iy < sol.shape[0] and 0 <= ix < sol.shape[1]) or not sol[iy, ix]:
        return False
    tol = 3.0 * cuadro.escala if tol is None else tol
    return cuadro.buf["depth"][iy, ix] - d <= tol


def _exceptuado(ficha, regla, tipo, mira):
    return any(ex.get("regla") == regla and ex.get("componente") == tipo and mira in (ex.get("direcciones") or [])
               for ex in ficha.get("excepciones") or [])


def _res(regla, fallas, ok_txt):
    return Resultado(regla, not fallas, f"{len(fallas)} casos" if fallas else ok_txt, fallas[:25])


def t_visibilidad(ficha, todo):
    fallas = []
    for s in _specs(todo):
        reglas = set(s["reglas"])
        if not reglas & {"visible_si_ancla_visible", "siempre_visible"}:
            continue
        for c in _cuadros(todo):
            if any(_exceptuado(ficha, r, s["tipo"], c.mira) for r in reglas):
                continue
            if mascara(c, s["id"]).any():
                continue
            if "siempre_visible" in reglas or ancla_visible(c, s["ancla"]):
                fallas.append(f'{s["id"]}: invisible en {c.pose}/{c.mira}/{c.indice} con el ancla a la vista')
    return _res("visibilidad de componentes", fallas, "todos visibles cuando su ancla se ve")


def _dist_segmento(xs, ys, x0, y0, x1, y1):
    px, py = xs - x0, ys - y0
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    t = np.clip((px * dx + py * dy) / L2, 0, 1) if L2 > 1e-9 else np.zeros_like(px, float)
    return np.hypot(px - t * dx, py - t * dy)


def t_ausentes(ficha, todo):
    fallas = []
    for s in _specs(todo):
        for r in s["reglas"]:
            if not r.startswith("ausente_mas_alla_de_"):
                continue
            ancla = r[len("ausente_mas_alla_de_"):]
            padre = PADRE[ancla]
            for c in _cuadros(todo):
                ys, xs = np.nonzero(mascara(c, s["id"]))
                if not len(xs):
                    continue
                (x0, y0, _), (x1, y1, _) = c.anclas_px[padre], c.anclas_px[ancla]
                dist = _dist_segmento(xs.astype(float), ys.astype(float), x0, y0, x1, y1)
                lim = 2.6 * c.escala + 1.5
                if dist.max() > lim:
                    fallas.append(f'{s["id"]}: {int((dist > lim).sum())} px más allá de {ancla} en '
                                  f'{c.pose}/{c.mira}/{c.indice}')
    return _res("partes ausentes", fallas, "nada dibujado donde falta una parte")


def t_lineas_guia(ficha, todo, tol=1.5):
    fallas = []
    for s in _specs(todo):
        if s["ancla"] not in GUIAS:
            continue
        por = {}
        for c in _cuadros(todo):
            ys = np.nonzero(mascara(c, s["id"]))[0]
            if len(ys):
                por.setdefault((c.pose, c.indice), {})[c.mira] = float(ys.mean())
        for (pose, i), alturas in por.items():
            if len(alturas) > 1 and max(alturas.values()) - min(alturas.values()) > tol:
                fallas.append(f'{s["id"]}: altura distinta entre direcciones en {pose}/{i}: '
                              + ", ".join(f"{k} {y:.1f}" for k, y in alturas.items()))
    return _res("líneas guía", fallas, "rasgos a la misma altura en todas las direcciones")


def colores_permitidos(ficha, estilo):
    est = ESTILOS[estilo]
    ok = {CONTORNO}
    for tonos in paleta_estilo(ficha["paleta"], est).values():
        ok |= set(tonos)
        ok.add(_oscurecer(tonos[0], .8))
        ok.add(_oscurecer(tonos[0], est["render"].get("oscurecer", .55)))
    return ok


def t_paleta(ficha, estilo, todo):
    base = colores_permitidos(ficha, estilo)
    extra = set()
    for c in _cuadros(todo):
        a = np.array(c.img)
        cols = {tuple(int(x) for x in px) for px in a[a[..., 3] > 0][:, :3]}
        extra |= cols - base - c.buf["colores_detalle"]
    return Resultado("paleta", not extra, f"colores fuera de paleta: {sorted(extra)[:5]}" if extra
                     else "todos los colores salen de la paleta del personaje")


def t_tamano(ficha, estilo, todo):
    cel = celda(estilo, ficha["cuerpo"].get("clase_altura", "adulto"))
    fallas = []
    for c in _cuadros(todo):
        if c.img.size != (cel["cw"], cel["ch"]):
            fallas.append(f"{c.pose}/{c.mira}: celda {c.img.size} en vez de {(cel['cw'], cel['ch'])}")
            continue
        if c.bob != 0:
            continue
        alto = cel["gy"] - c.anclas_px["coronilla"][1]
        objetivo = alto_objetivo_px(estilo, ficha["cuerpo"].get("clase_altura", "adulto"))
        if abs(alto - objetivo) > 1:
            fallas.append(f"{c.pose}/{c.mira}/{c.indice}: mide {alto:.1f} px y su clase mide {objetivo}")
        filas = np.nonzero((np.array(c.img)[..., 3] > 0).any(1))[0]
        if len(filas) and not (cel["gy"] - 1 <= filas.max() <= cel["gy"] + 2):
            fallas.append(f"{c.pose}/{c.mira}/{c.indice}: los pies terminan en la fila {filas.max()}, pivote {cel['gy']}")
    return _res("tamaño y pivote", fallas, "mide lo que dice su clase y apoya en el pivote")


def t_recorte(todo):
    fallas = []
    for c in _cuadros(todo):
        op = np.array(c.img)[..., 3] > 0
        if op[0].any() or op[:, 0].any() or op[:, -1].any():
            fallas.append(f"{c.pose}/{c.mira}/{c.indice}: toca el borde de la celda")
    return _res("recorte", fallas, "nada toca los bordes superior ni laterales")


def _regla_global(ficha, nombre):
    for r in ficha.get("reglas_globales") or []:
        if isinstance(r, dict) and nombre in r:
            return r[nombre]
    return None


def t_cara(ficha, estilo, todo):
    dirs = [d for d in (_regla_global(ficha, "cara_visible_en") or []) if d in ESTILOS[estilo]["direcciones"]]
    if not dirs:
        return Resultado("cara visible", True, "sin direcciones que pedir en este estilo: omitido", omitido=True)
    ids = [s["id"] for s in _specs(todo) if s["tipo"] in ("ojos", "visor")]
    fallas = [f"{c.pose}/{c.mira}/{c.indice}: no se ven ojos ni visor" for c in _cuadros(todo)
              if c.mira in dirs and not any(mascara(c, i).any() for i in ids)]
    return _res("cara visible", fallas, f"se lee la cara en {', '.join(dirs)}")


def t_simetria(ficha, estilo, todo):
    frente = FRENTE.get(estilo)
    if not frente:
        return Resultado("simetría", True, "vista sin frente: omitido", omitido=True)
    fallas = []
    grupos = {}
    for s in _specs(todo):
        if "simetrico" in s["reglas"]:
            grupos.setdefault(s["tipo"], []).append(s["id"])
    for tipo, ids in grupos.items():
        for c in todo.get(("quieto", frente), []):
            faltan = [i for i in ids if not mascara(c, i).any()]
            if faltan:
                fallas.append(f"{tipo}: de frente no se ve {', '.join(faltan)} (cuadro {c.indice})")
    return _res("simetría", fallas, "los componentes simétricos se ven de los dos lados")


def t_distinto(ficha):
    otros = _regla_global(ficha, "distinto_de") or []
    if not otros:
        return Resultado("distinto del elenco", True, "sin comparación pedida: omitido", omitido=True)
    from .ficha import cargar
    fallas = []
    mis_emi = [hex_rgb(m["base"]) for m in ficha["paleta"].values() if m.get("emisivo")]
    mis = [hex_rgb(m["base"]) for m in ficha["paleta"].values()]
    for nombre in otros:
        try:
            o = cargar(nombre, validar_=False)
        except FileNotFoundError:
            fallas.append(f"no existe la ficha {nombre!r} para comparar")
            continue
        sus_emi = [hex_rgb(m["base"]) for m in o["paleta"].values() if m.get("emisivo")]
        suyos = [hex_rgb(m["base"]) for m in o["paleta"].values()]
        dist = lambda p, q: float(np.linalg.norm(np.subtract(p, q)))
        if mis_emi and sus_emi and min(dist(p, q) for p in mis_emi for q in sus_emi) < 60:
            fallas.append(f"el color identitario se parece demasiado al de {nombre}")
        parecidos = sum(1 for p in mis if min(dist(p, q) for q in suyos) < 30)
        if parecidos > len(mis) / 2:
            fallas.append(f"{parecidos} de {len(mis)} colores casi iguales a los de {nombre}")
    return _res("distinto del elenco", fallas, f"se distingue de {', '.join(otros)}")


def t_estilo(ficha, estilo, todo, carpeta):
    ref = ESTILOS[estilo].get("referencia")
    if not ref or not os.path.exists(ref["ruta"]):
        return Resultado("estilo vs referencia", True, "sin referencia local: omitido", omitido=True)
    from .comparar_estilo import comparar, metricas
    frames = [c.img for c in _cuadros(todo) if c.pose == "quieto"]
    cw, ch = frames[0].size
    tira = Image.new("RGBA", (cw * len(frames), ch), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        tira.paste(fr, (i * cw, 0))
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "_estilo.png")
    tira.save(ruta)
    r, _ = metricas(ref["ruta"], ref["celda"], ref.get("recorte"))
    m, _ = metricas(ruta, (cw, ch))
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        fallas = comparar(r, m)
    return Resultado("estilo vs referencia", not fallas, salida.getvalue().strip(),
                     [f"{k}: referencia {a:.2f}, propio {b:.2f}" for k, a, b in fallas])


def correr_tests(ficha, estilo, todo, carpeta):
    return [
        t_visibilidad(ficha, todo), t_ausentes(ficha, todo), t_lineas_guia(ficha, todo),
        t_paleta(ficha, estilo, todo), t_tamano(ficha, estilo, todo), t_recorte(todo),
        t_cara(ficha, estilo, todo), t_simetria(ficha, estilo, todo), t_distinto(ficha),
        t_estilo(ficha, estilo, todo, carpeta),
    ]


def informe_md(ficha, estilo, resultados):
    ok = sum(1 for r in resultados if r.ok and not r.omitido)
    mal = sum(1 for r in resultados if not r.ok)
    om = sum(1 for r in resultados if r.omitido)
    L = [f"# Informe de consistencia — {ficha['identidad']['nombre']} ({estilo})", "",
         f"Resultado: **{'APROBADO' if not mal else 'CON FALLAS'}** — {ok} ok, {mal} fallas, {om} omitidos", "",
         "| Regla | Estado | Detalle |", "|---|---|---|"]
    for r in resultados:
        estado = "omitido" if r.omitido else ("✓" if r.ok else "✗")
        primera = r.detalle.splitlines()[0] if r.detalle else ""
        L.append(f"| {r.regla} | {estado} | {primera.replace('|', '/')} |")
    for r in resultados:
        if r.evidencia:
            L += ["", f"## {r.regla}", *[f"- {e}" for e in r.evidencia]]
    return "\n".join(L) + "\n"
```

- [ ] **Step 4: Correr los tests**

Run: `.venv/bin/python -m pytest tests/test_tests_personaje.py -q`
Expected: `9 passed`. Si `test_sano_tamano_recorte_paleta` falla en paleta, revisar que el color sobrante venga de un detalle registrado (los detalles pintados quedan en `buf["colores_detalle"]`); si falla en recorte, bajar el ancho de las rastas (`rl * 1.02`) o el radio de las cápsulas.

- [ ] **Step 5: Commit**

```bash
git add sprites_lib/tests_personaje.py tests/test_tests_personaje.py
git commit -m "Tests de consistencia: visibilidad, ausentes, líneas guía, paleta, tamaño, recorte, cara, simetría, elenco y estilo"
```

---

### Task 9: Hoja de modelo, fotos de control y CLI

**Files:**
- Create: `sprites_lib/hoja_modelo.py`, `sprites_lib/fotos_control.py`, `personajes/generar.py`, `tests/test_generar.py`

**Interfaces:**
- Consumes: `armado.render_todo`, `ficha.cargar/FichaInvalida`, `tests_personaje.correr_tests/informe_md/Resultado`, `exportar.exportar_direcciones`, `poses.fps`, `paleta.paleta_estilo`, `escala.celda`.
- Produces: `hoja_modelo.hoja(ficha, estilo, todo, resultados, ruta) -> ruta`; `fotos_control.DIR`, `fotos_control.guardar(nombre, estilo, todo) -> carpeta`, `fotos_control.comparar(nombre, estilo, todo, carpeta_dif) -> Resultado`; `personajes.generar.main(argv) -> int` con subcomandos `validar|hoja|tests|aprobar <nombre> [--estilo stardew|volumen|lateral|todos|a,b]`.

- [ ] **Step 1: Escribir los tests que fallan** — `tests/test_generar.py`

```python
import os

import numpy as np
from PIL import Image

from personajes import generar
from sprites_lib import fotos_control
from sprites_lib.armado import render_todo
from sprites_lib.ficha import cargar
from sprites_lib.tests_personaje import Resultado


def test_validar_ok(capsys):
    assert generar.main(["validar", "mago"]) == 0
    assert "válida" in capsys.readouterr().out


def test_ficha_inexistente_codigo_2_sin_traceback(capsys):
    assert generar.main(["validar", "nadie"]) == 2
    err = capsys.readouterr().err
    assert "no existe la ficha" in err and "Traceback" not in err


def test_yaml_roto_codigo_2(tmp_path, capsys):
    ruta = tmp_path / "rota.yaml"
    ruta.write_text("identidad: [", encoding="utf-8")
    assert generar.main(["validar", str(ruta)]) == 2
    assert "YAML mal formado" in capsys.readouterr().err


def test_hoja_genera_archivos(tmp_path, monkeypatch):
    monkeypatch.setattr(generar, "SALIDA", str(tmp_path))
    codigo = generar.main(["hoja", "mago", "--estilo", "stardew"])
    base = tmp_path / "mago" / "stardew"
    assert codigo in (0, 1)
    for f in ("hoja_modelo.png", "informe.md", "quieto.png", "quieto.json"):
        assert (base / f).exists(), f


def test_aprobar_se_niega_si_fallan_tests(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(generar, "SALIDA", str(tmp_path))
    monkeypatch.setattr(fotos_control, "DIR", str(tmp_path / "aprobados"))
    monkeypatch.setattr(generar, "correr_tests", lambda *a: [Resultado("x", False, "roto")])
    assert generar.main(["aprobar", "mago", "--estilo", "stardew"]) == 1
    assert not (tmp_path / "aprobados").exists()


def test_fotos_de_control_detectan_cambios(tmp_path, monkeypatch):
    monkeypatch.setattr(fotos_control, "DIR", str(tmp_path / "aprobados"))
    f = cargar("mago")
    todo = render_todo(f, "stardew", poses=("neutra",))
    assert fotos_control.comparar("mago", "stardew", todo, str(tmp_path / "dif")).omitido
    fotos_control.guardar("mago", "stardew", todo)
    assert fotos_control.comparar("mago", "stardew", todo, str(tmp_path / "dif")).ok
    c = todo[("neutra", "S")][0]
    a = np.array(c.img); a[5, 5] = (255, 0, 0, 255); c.img = Image.fromarray(a, "RGBA")
    r = fotos_control.comparar("mago", "stardew", todo, str(tmp_path / "dif"))
    assert not r.ok and "neutra_S_0.png" in r.evidencia[0]
    assert os.path.exists(tmp_path / "dif" / "neutra_S_0.png")
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/bin/python -m pytest tests/test_generar.py -q`
Expected: FAIL con `ImportError: cannot import name 'generar' from 'personajes'`.

- [ ] **Step 3: Crear `sprites_lib/fotos_control.py`**

```python
"""Fotos de control: las poses aprobadas por el usuario quedan congeladas (versionadas en git). Si un cambio
del motor o de un componente altera aunque sea un píxel, el test lo reporta con una imagen antes/después."""
import os

import numpy as np
from PIL import Image

from .tests_personaje import Resultado

DIR = os.path.join("personajes", "aprobados")


def carpeta(nombre, estilo):
    return os.path.join(DIR, nombre, estilo)


def _archivo(c):
    return f"{c.pose}_{c.mira}_{c.indice}.png"


def guardar(nombre, estilo, todo):
    out = carpeta(nombre, estilo)
    os.makedirs(out, exist_ok=True)
    for frs in todo.values():
        for c in frs:
            c.img.save(os.path.join(out, _archivo(c)))
    return out


def _diferencia(antes, ahora, ruta, zoom=6):
    h, w = antes.shape[:2]
    m = np.any(antes != ahora, axis=2)
    marca = np.zeros_like(ahora); marca[m] = (255, 40, 40, 255)
    hoja = Image.new("RGBA", (w * 3 * zoom + 8, h * zoom), (60, 58, 80, 255))
    for i, arr in enumerate((antes, ahora, marca)):
        im = Image.fromarray(arr, "RGBA").resize((w * zoom, h * zoom), Image.NEAREST)
        hoja.paste(im, (i * (w * zoom + 4), 0), im)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    hoja.save(ruta)


def comparar(nombre, estilo, todo, carpeta_dif):
    base = carpeta(nombre, estilo)
    if not os.path.isdir(base):
        return Resultado("fotos de control", True, "todavía no hay poses aprobadas: omitido", omitido=True)
    fallas = []
    for frs in todo.values():
        for c in frs:
            f = os.path.join(base, _archivo(c))
            if not os.path.exists(f):
                fallas.append(f"{_archivo(c)}: no estaba aprobado")
                continue
            antes, ahora = np.array(Image.open(f).convert("RGBA")), np.array(c.img)
            if antes.shape != ahora.shape:
                fallas.append(f"{_archivo(c)}: cambió el tamaño {antes.shape[:2]} → {ahora.shape[:2]}")
            elif (antes != ahora).any():
                n = int(np.any(antes != ahora, axis=2).sum())
                _diferencia(antes, ahora, os.path.join(carpeta_dif, _archivo(c)))
                fallas.append(f"{_archivo(c)}: {n} píxeles distintos (ver {os.path.join(carpeta_dif, _archivo(c))})")
    return Resultado("fotos de control", not fallas, f"{len(fallas)} cuadros cambiaron" if fallas
                     else "idéntico a lo aprobado", fallas[:25])
```

- [ ] **Step 4: Crear `sprites_lib/hoja_modelo.py`**

```python
"""Hoja de modelo: todas las direcciones alineadas por pose, con líneas guía (coronilla, ojos, hombros, cintura,
suelo), muestras de paleta, componentes con su porqué y el resultado de los tests. Es lo que el usuario aprueba."""
import textwrap

from PIL import Image, ImageDraw, ImageFont

from .estilos import ESTILOS
from .paleta import paleta_estilo

ZOOM = {"stardew": 8, "lateral": 6, "volumen": 4}
FONDO = (60, 58, 80)
COLORES_GUIA = {"coronilla": (255, 120, 120), "ojos": (120, 220, 255), "hombros": (255, 220, 90),
                "cintura": (160, 255, 140), "suelo": (200, 200, 200)}


def _texto(d, xy, txt, col=(230, 230, 240), ancho=58, font=None):
    x, y = xy
    for linea in textwrap.wrap(str(txt), ancho) or [""]:
        d.text((x, y), linea, fill=col, font=font)
        y += 14
    return y


def hoja(ficha, estilo, todo, resultados, ruta):
    est = ESTILOS[estilo]
    dirs = est["direcciones"]
    Z = ZOOM.get(estilo, 5)
    poses = [p for p in ("neutra", "quieto") if (p, dirs[0]) in todo]
    cw, ch = todo[(poses[0], dirs[0])][0].img.size
    colw, filah, panel = cw * Z + 16, ch * Z + 34, 440
    W = colw * len(dirs) + panel
    H = max(filah * len(poses) + 20, 620)
    im = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(im)
    font = ImageFont.load_default()
    for r, pose in enumerate(poses):
        y0 = 22 + r * filah
        d.text((6, y0 - 18), f"pose: {pose}", fill=(255, 220, 90), font=font)
        c = todo[(pose, dirs[0])][0]
        guias = {"coronilla": c.anclas_px["coronilla"][1],
                 "ojos": (c.anclas_px["ojo_derecho"][1] + c.anclas_px["ojo_izquierdo"][1]) / 2,
                 "hombros": c.anclas_px["hombro_derecho"][1], "cintura": c.anclas_px["cintura"][1],
                 "suelo": c.anclas_px["suelo"][1]}
        for nombre, gy in guias.items():
            yy = y0 + int(gy * Z)
            d.line([(0, yy), (colw * len(dirs), yy)], fill=COLORES_GUIA[nombre], width=1)
            d.text((colw * len(dirs) - 64, yy - 12), nombre, fill=COLORES_GUIA[nombre], font=font)
        for i, mira in enumerate(dirs):
            fr = todo[(pose, mira)][0].img.resize((cw * Z, ch * Z), Image.NEAREST)
            im.paste(fr, (i * colw + 8, y0), fr)
            d.text((i * colw + 8, y0 + ch * Z + 2), mira, fill=(230, 230, 240), font=font)
    x = colw * len(dirs) + 14
    idt = ficha["identidad"]
    y = _texto(d, (x, 10), f"{idt['nombre']} — estilo {estilo}", (255, 220, 90), font=font)
    y = _texto(d, (x, y + 4), f"Silueta clave: {idt['silueta_clave']}", font=font)
    y = _texto(d, (x, y + 4), idt["concepto"], (200, 200, 215), font=font)
    y = _texto(d, (x, y + 8), "Paleta", (255, 220, 90), font=font)
    for nombre, tonos in paleta_estilo(ficha["paleta"], est).items():
        if nombre.endswith("_b") or nombre not in ficha["paleta"]:
            continue
        for k, t in enumerate(tonos):
            d.rectangle([x + k * 14, y, x + k * 14 + 12, y + 12], fill=t)
        y = _texto(d, (x + 48, y), f"{nombre}: {ficha['paleta'][nombre].get('por_que', '')}", ancho=52, font=font)
    y = _texto(d, (x, y + 8), "Componentes", (255, 220, 90), font=font)
    for comp in ficha["componentes"]:
        y = _texto(d, (x, y), f"- {comp['tipo']}: {comp.get('por_que', '')}", ancho=62, font=font)
    y = _texto(d, (x, y + 8), "Tests", (255, 220, 90), font=font)
    for r in resultados:
        estado = "omitido" if r.omitido else ("OK" if r.ok else "FALLA")
        col = (170, 170, 180) if r.omitido else ((140, 240, 140) if r.ok else (255, 120, 120))
        y = _texto(d, (x, y), f"[{estado}] {r.regla}", col, font=font)
    im.save(ruta)
    return ruta
```

- [ ] **Step 5: Crear `personajes/generar.py`**

```python
"""CLI de personajes desde fichas.

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
from sprites_lib.armado import render_todo
from sprites_lib.escala import celda
from sprites_lib.estilos import ESTILOS
from sprites_lib.exportar import exportar_direcciones
from sprites_lib.ficha import FichaInvalida, cargar
from sprites_lib.hoja_modelo import hoja
from sprites_lib.poses import fps
from sprites_lib.tests_personaje import correr_tests, informe_md

SALIDA = "salida"


def _estilos(arg):
    return list(ESTILOS) if arg == "todos" else arg.split(",")


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
    for n in ("validar", "hoja", "tests", "aprobar"):
        p = sub.add_parser(n)
        p.add_argument("nombre")
        p.add_argument("--estilo", default="todos")
    a = ap.parse_args(argv)
    try:
        return {"validar": cmd_validar, "hoja": cmd_hoja, "tests": cmd_tests, "aprobar": cmd_aprobar}[a.cmd](a)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except FichaInvalida as e:
        print(e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Correr todos los tests**

Run: `.venv/bin/python -m pytest -q`
Expected: todos pasan (`test_generar.py`: 6 passed).

- [ ] **Step 7: Commit**

```bash
git add sprites_lib/hoja_modelo.py sprites_lib/fotos_control.py personajes/generar.py tests/test_generar.py
git commit -m "Hoja de modelo, fotos de control y CLI de personajes"
```

---

### Task 10: Integración — el mago y Clast pasan en los tres estilos

**Files:**
- Modify (solo si los diagnósticos lo piden): `sprites_lib/componentes/*.py`, `sprites_lib/estilos.py` (proporciones), `personajes/fichas/*.yaml`
- Create: `personajes/aprobados/<nombre>/<estilo>/*.png` (solo después del OK del usuario)

**Interfaces:**
- Consumes: la CLI de la Tarea 9.
- Produces: hojas de modelo aprobadas y fotos de control versionadas.

- [ ] **Step 1: Generar las hojas del mago**

Run: `.venv/bin/python -m personajes.generar hoja mago --estilo todos`
Expected: tres `hoja → salida/mago/<estilo>/hoja_modelo.png` y el resumen por estilo.

- [ ] **Step 2: Autoanálisis antes de mostrar** (protocolo de la skill `sprite-estilo`)

Para cada estilo: leer `salida/mago/<estilo>/informe.md` y abrir `hoja_modelo.png` con Read. Responder por escrito el checklist: silueta (formas cuadradas vs. esferas), detalle dibujado, tamaño/proporción, cara de frente **y** de perfil, contorno, recorte, sombreado, manos legibles. Comparar además con la versión vieja:
`.venv/bin/python -m sprites_lib.lado_a_lado salida/_cmp_mago.png salida/mago_stardew/quieto/quieto.png:0,0,16,32 salida/mago/stardew/quieto.png:0,0,16,32`

- [ ] **Step 3: Corregir las fallas por la causa, no el síntoma**

Por cada ✗ del informe o problema del checklist: ubicar el componente o proporción responsable, corregirlo, volver al Step 1. Criterio de salida: **ningún ✗** en los tres estilos (los "omitido" están permitidos solo para estilo sin referencia y fotos de control). Si `estilo vs referencia` falla en `huerfanos` (poco micro-detalle), agregar textura con variantes `_b` en el componente de mayor superficie (túnica, pelo) antes de tocar tolerancias. Nunca relajar una tolerancia de `comparar_estilo` sin volver a calibrarla con el control Abigail vs Wizard.

- [ ] **Step 4: Lo mismo para Clast**

Run: `.venv/bin/python -m personajes.generar hoja clast --estilo todos`
Repetir Steps 2–3. Verificar a ojo, además: el muñón y el visor se leen mirando al E; mirando al W se ve "el humano"; los cables de la nuca se ven de espaldas; el verde solo en detalles.

- [ ] **Step 5: Lateral contra Mega Man X**

Confirmar en `salida/<nombre>/lateral/informe.md` que `estilo vs referencia` da ✓. Si falla, ajustar primero `ESTILOS["lateral"]["render"]` y `proporciones` (no los componentes), regenerar y volver a medir.

- [ ] **Step 6: Suite completa verde**

Run: `.venv/bin/python -m pytest -q`
Expected: todos pasan.

- [ ] **Step 7: Mostrar al usuario y pedir la aprobación 2**

Run: `xdg-open salida/clast/stardew/hoja_modelo.png` (y las demás hojas que el usuario quiera ver).
Presentar: qué se corrigió en cada vuelta, estado de los tests por estilo y personaje. **No aprobar sin su OK.**

- [ ] **Step 8: Congelar lo aprobado** (solo con el OK)

Run: `.venv/bin/python -m personajes.generar aprobar mago --estilo todos && .venv/bin/python -m personajes.generar aprobar clast --estilo todos`
Expected: `aprobado → personajes/aprobados/...` por estilo.

- [ ] **Step 9: Commit**

```bash
git add personajes/aprobados sprites_lib personajes/fichas
git commit -m "Mago y Clast aprobados en stardew, volumen y lateral (fotos de control)"
```

---

### Task 11: Skill `sprite-personaje` y documentación

**Files:**
- Create: `.claude/skills/sprite-personaje/SKILL.md`
- Modify: `CLAUDE.md`, `CRITERIOS_ANIMACION.md`

**Interfaces:**
- Consumes: CLI y fichas de las tareas anteriores.
- Produces: la skill que usa el flujo completo.

- [ ] **Step 1: Crear `.claude/skills/sprite-personaje/SKILL.md`**

```markdown
---
name: sprite-personaje
description: Crear un personaje nuevo del juego de punta a punta y de forma consistente — entrevista de requisitos, ficha YAML con el porqué de cada decisión, hoja de modelo (poses neutra y quieto en todas las direcciones), tests automáticos de consistencia y fotos de control. Usar siempre que el usuario describa un personaje ("quiero un robot con...", "haceme una bruja que..."), pida un personaje nuevo, quiera cambiar uno existente, o hable de fichas, hoja de modelo o consistencia de personajes, aunque no diga "skill".
---

# Personaje nuevo: entrevista → ficha → hoja de modelo → tests → aprobación

Leer antes `CRITERIOS_ANIMACION.md` y el diseño `docs/superpowers/specs/2026-09-26-fichas-personaje-design.md`
(sección 3.9). Fichas de ejemplo: `personajes/fichas/mago.yaml`, `personajes/fichas/clast.yaml`.

## 0. Entrevista (antes de escribir nada)
Reflejar lo que el usuario ya dijo y preguntar solo lo que falta, con `AskUserQuestion` (opciones cortas, una
recomendada). Temas fijos, en este orden: identidad y rol · silueta clave · cuerpo (clase de altura, complexión,
piel, cabello) · ropa y accesorios con su porqué · colores con significado (uno identitario) · vistas/estilos y
direcciones · referencias.

Objetar con conocimiento del kit (esto es lo que agrega valor):
- **Escala**: en stardew la cara mide ~6 px y el ancho 16 px → accesorios de ≥2 px, ~3 accesorios legibles.
- **Oclusión**: qué se tapa de perfil o de espaldas (declarar `excepciones` por oclusión, con motivo).
- **Elenco**: comparar paleta y silueta con las fichas existentes; el color identitario tiene que distinguirse.
- **Componentes que no existen**: listarlos como trabajo nuevo antes de prometer el resultado.
Cuando la decisión es visual (silueta, paleta), generar miniaturas rápidas y mostrarlas.

## 1. Ficha
Escribir `personajes/fichas/<nombre>.yaml` (formato de `mago.yaml`): `identidad`, `cuerpo`
(`sustituciones`/`ausentes` si hace falta), `paleta` con `por_que`, `componentes` con `ancla`, `material`,
`parametros`, `por_que` y `reglas`, `reglas_globales`, `excepciones`, `decisiones` (pregunta, respuesta y motivo de la
entrevista) y `creditos`. Validar:
`.venv/bin/python -m personajes.generar validar <nombre>` → corregir hasta que diga "válida".
Mostrar un resumen legible y pedir la **aprobación 1**.

## 2. Componentes nuevos (si la ficha los pide)
Cada uno en `sprites_lib/componentes/<tema>.py` con `@registrar`, `anclas_validas`, `params_defecto`,
`params_material`, `material_defecto` y `dibujar()` usando `entrar()` antes de cada pieza. Aplicar las
lecciones de `CRITERIOS_ANIMACION.md` en el código (pieza propia para lo que tiene que leerse separado,
tamaño mínimo en px, nacer fuera del volumen que lo tapa). Test en `tests/` que verifique que se ve.

## 3. Hoja de modelo + tests
`.venv/bin/python -m personajes.generar hoja <nombre> --estilo todos` → leer cada `informe.md` y mirar cada
`hoja_modelo.png` con Read (checklist de `sprite-estilo`, paso 5). Corregir la causa de cada ✗ y repetir;
**no mostrar nada con ✗**.

## 4. Aprobación 2 y fotos de control
Abrir la hoja con `xdg-open`, explicar decisiones y correcciones, pedir el OK. Con el OK:
`.venv/bin/python -m personajes.generar aprobar <nombre> --estilo todos` y commitear `personajes/aprobados/`.
Si más adelante un cambio altera una pose aprobada, `hoja` lo reporta con imágenes antes/después en
`salida/<nombre>/<estilo>/diferencias/`: mostrárselas al usuario antes de volver a aprobar.

## 5. Anotar
Lecciones nuevas → `CRITERIOS_ANIMACION.md`.
```

- [ ] **Step 2: Actualizar `CLAUDE.md`** — en la tabla "Kit de sprites", fila Skills agregar `sprite-personaje`; fila Librería agregar `escala`, `paleta`, `cuerpo`, `poses`, `componentes/`, `armado`, `ficha`, `tests_personaje`, `hoja_modelo`, `fotos_control`; reemplazar la fila Personajes por:

```markdown
| Personajes | fichas en `personajes/fichas/*.yaml` → `personajes/generar.py` (validar/hoja/tests/aprobar); aprobados en `personajes/aprobados/` (versionado). `personajes/mago_*.py` = versión anterior sin ficha |
```

y agregar debajo de "Un sprite = ...": `Personaje nuevo → skill sprite-personaje (entrevista → ficha → hoja → tests → aprobación).`

- [ ] **Step 3: Anotar en `CRITERIOS_ANIMACION.md`** una sección "Fichas y consistencia (fase 1)" con: por qué la ficha es la única fuente de verdad, cómo se detecta un accesorio oculto por pose vs. olvidado (ancla visible por profundidad), por qué las líneas guía miden píxeles reales y no anclas, y cualquier corrección hecha en la Tarea 10 (qué falló y por qué).

- [ ] **Step 4: Probar la entrevista con una descripción problemática** (criterio de éxito del diseño)

Despachar un subagente (modelo estándar) con acceso a la skill y esta descripción: *"una bruja en estilo stardew con
anillo, collar, aros, pulsera en cada muñeca, broche y tobillera"*, pidiéndole que haga solo la entrevista (sin
generar sprites) y devuelva las preguntas y objeciones. Pasa si detecta que en 16 px de ancho no entran ~7
accesorios de 1 px legibles y propone priorizar, fusionar o agrandar. Si no lo detecta, reforzar el paso 0 de la
skill y repetir.

- [ ] **Step 5: Verificación final**

Run: `.venv/bin/python -m pytest -q && .venv/bin/python -m personajes.generar tests mago && .venv/bin/python -m personajes.generar tests clast`
Expected: todos los tests pasan; los dos personajes `OK` en los tres estilos (fotos de control idénticas).

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/sprite-personaje CLAUDE.md CRITERIOS_ANIMACION.md
git commit -m "Skill sprite-personaje y documentación de fichas"
```
