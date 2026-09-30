# Procesos del kit (estilo, animación, skin) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tres procesos ejecutables con gates deterministas (estilo → animación → skin) que permitan iterar solo hasta VERDE y producir personajes completos al por mayor sobre animaciones congeladas.

**Architecture:** Se agrega una capa fina de orquestación sobre el kit actual: `estado.py` (hash de fuente + `estado.json` para deriva), `gates.py` (motor de veredicto VERDE/ROJO + checks universales), `proporciones.py` (contrato numérico del muñeco) y tres CLIs (`proceso_estilo`, `proceso_anim`, `proceso_skin`) que orquestan lo existente (`zonas`, `pulido`, `comparar_estilo`, `comparar_plantilla`, `fotos_control`, `skins`). Cada artefacto congelado = fuente + métricas + control + test; aprobar es la única acción humana.

**Tech Stack:** Python 3.11 (`.venv`), numpy, Pillow, PyYAML, pytest.

**Spec:** `docs/superpowers/specs/2026-09-29-procesos-estilo-animacion-skin-design.md`

## Global Constraints

- Correr todo desde la raíz del repo con `.venv/bin/python ...`. Tests: `.venv/bin/python -m pytest` (por defecto saltea los `lento`); al cerrar la rama, `-m ""`.
- Español en identificadores, docstrings y mensajes; nombres de anclas sin tildes (`muneca_derecha`).
- No romper los flujos actuales: `personajes/generar`, `skins demo|juego`, `zonas`, `pulido`. Cambios de firma siempre con parámetro por defecto.
- Todo módulo nuevo se agrega a `MODULOS` en `sprites_lib/mapa.py` y se regenera `MAPA.md` con `.venv/bin/python -m sprites_lib.mapa` (lo exige `tests/test_mapa.py`).
- Artefactos congelados en `aprobados/<proceso>/...` (versionado en git); salidas de trabajo en `salida/` (ignorada).
- El único paso humano es `aprobar`; requiere gate VERDE o `--excepcion "motivo"` (el motivo queda en `estado.json`).
- Commits por tarea, mensajes en español descriptivos (estilo del repo: "Procesos: ...").

## Review Focus

1. **Nombre de animación/estilo con caracteres de ruta** (`../`, espacios, mayúsculas): debe rechazarse con error claro antes de tocar `aprobados/`.
2. **`aprobar` con gate ROJO**: no debe escribir ningún archivo (ni parciales); `estado.json` se escribe último, como marca de congelado.
3. **Cambio de motor sin cambio de fuente** (editar `render3d.py` tras aprobar): el pixel diff contra los cuadros de control debe reportarlo; si faltan cuadros de control, el gate lo dice, no crashea.
4. **Estilos sin referencia o en `VERIFICACION`** (`lpc`, `fry8`): los checks de referencia quedan `omitido`, nunca ROJO por falta de datos.
5. **Lote con 0 animaciones aprobadas o con una animación que falla**: informe claro y exit code definido, sin stacktrace ni salida a medias silenciosa.

---

### Task 1: Estado y deriva (`estado.py`)

**Files:**
- Create: `sprites_lib/estado.py`
- Create: `tests/test_estado.py`
- Modify: `sprites_lib/mapa.py` (agregar `"estado"` a `MODULOS`), luego regenerar `sprites_lib/MAPA.md`

**Interfaces:**
- Consumes: nada (módulo base).
- Produces: `canonico(obj) -> str`, `hash_obj(obj) -> str`, `hash_archivo(ruta) -> str`, `escribir(carpeta, artefacto, fuentes, metricas, nota=None) -> str`, `leer(carpeta) -> dict | None`, `deriva(estado_dict, fuentes) -> list[str]`, `listar(raiz) -> list[dict]`.

- [ ] **Step 1: Write the failing test** — `tests/test_estado.py`

```python
import os
from sprites_lib import estado


def test_hash_obj_estable_y_sensible():
    assert estado.hash_obj({"a": [1, 2], "b": "x"}) == estado.hash_obj({"b": "x", "a": [1, 2]})
    assert estado.hash_obj({"a": 1}) != estado.hash_obj({"a": 2})


def test_deriva_detecta_cambio():
    est = {"fuentes": {"ciclo": "sha256:aaa", "perfil": "sha256:bbb"}}
    assert estado.deriva(est, {"ciclo": "sha256:aaa", "perfil": "sha256:bbb"}) == []
    assert estado.deriva(est, {"ciclo": "sha256:nuevo", "perfil": "sha256:bbb"}) == ["ciclo"]


def test_escribir_y_leer_ida_vuelta(tmp_path):
    carpeta = str(tmp_path / "art")
    estado.escribir(carpeta, "anim/saltar/stardew", {"ciclo": "sha256:abc"}, "metricas.json")
    e = estado.leer(carpeta)
    assert e["artefacto"] == "anim/saltar/stardew"
    assert e["fuentes"]["ciclo"] == "sha256:abc"
    assert e["aprobado_por"] == "usuario" and e["fecha"]
    assert estado.leer(str(tmp_path / "no_existe")) is None


def test_listar_encuentra_artefactos(tmp_path):
    a = tmp_path / "aprobados" / "animaciones" / "quieto" / "stardew"
    estado.escribir(str(a), "anim/quieto/stardew", {"ciclo": "sha256:x"}, "metricas.json")
    encontrados = estado.listar(str(tmp_path / "aprobados" / "animaciones"))
    assert [(x["nombre"], x["estilo"]) for x in encontrados] == [("quieto", "stardew")]
    assert os.path.exists(encontrados[0]["carpeta"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_estado.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'sprites_lib.estado'`

- [ ] **Step 3: Implement `sprites_lib/estado.py`**

Docstring del módulo: "Estado de artefactos aprobados: hash de la fuente, fecha y detección de deriva."
- `canonico(obj)`: `json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))`.
- `hash_obj(obj)`: `"sha256:" + hashlib.sha256(canonico(obj).encode()).hexdigest()`.
- `hash_archivo(ruta)`: idem sobre los bytes del archivo (si no existe, `"sha256:falta"`).
- `escribir(carpeta, artefacto, fuentes, metricas, nota=None)`: crea la carpeta, escribe `estado.json` con `{"artefacto", "fuentes", "metricas", "fecha" (ISO), "aprobado_por": "usuario", "nota"}`; devuelve la ruta del JSON.
- `leer(carpeta)`: carga `estado.json` o `None`.
- `deriva(estado_dict, fuentes)`: claves de `fuentes` cuyo hash difiere del guardado (las que falten en el actual también cuentan).
- `listar(raiz)`: recorre `raiz/<nombre>/<estilo>/estado.json` (o `raiz/<nombre>/estado.json` para skins) y devuelve `[{"nombre", "estilo", "carpeta", "estado"}]` ordenado.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_estado.py -q`
Expected: 4 passed

- [ ] **Step 5: Registrar módulo y regenerar MAPA**

Agregar `"estado"` a `MODULOS` en `sprites_lib/mapa.py`; correr `.venv/bin/python -m sprites_lib.mapa` y `.venv/bin/python -m pytest tests/test_mapa.py -q` → passed.

- [ ] **Step 6: Commit**

```bash
git add sprites_lib/estado.py tests/test_estado.py sprites_lib/mapa.py sprites_lib/MAPA.md
git commit -m "Procesos: estado de artefactos aprobados con hash de fuente y detección de deriva"
```

---

### Task 2: Motor de gates (`gates.py`)

**Files:**
- Create: `sprites_lib/gates.py`
- Create: `tests/test_gates.py`, `tests/test_determinismo.py`, `tests/test_deriva.py`
- Modify: `sprites_lib/mapa.py`, `sprites_lib/MAPA.md`

**Interfaces:**
- Consumes: `tests_personaje.Resultado` (regla, ok, detalle, evidencia, omitido), `armado.FICHA_MINIMA` + `render_cuadro`, `estado.deriva`, `estilos.ESTILOS`.
- Produces: `Resultado` (re-exportado de `tests_personaje`), `Veredicto` (dataclass: `verde: bool`, `checks: list[Resultado]`), `correr(checks) -> Veredicto`, `informe(v) -> str`, `guardar(v, ruta) -> str`, `check_determinismo(estilo, pose="quieto", mira=None, veces=2) -> Resultado`, `check_deriva(estado_dict, fuentes, regla="deriva") -> Resultado`.

- [ ] **Step 1: Write the failing tests** — `tests/test_gates.py`

```python
from sprites_lib import gates
from sprites_lib.tests_personaje import Resultado


def test_veredicto_verde_solo_si_todos_ok():
    v = gates.correr([lambda: Resultado("a", True), lambda: Resultado("b", True)])
    assert v.verde and "VERDE" in gates.informe(v)
    v = gates.correr([lambda: Resultado("a", True), lambda: Resultado("b", False, "falló")])
    assert not v.verde and "ROJO" in gates.informe(v)


def test_excepcion_es_rojo_con_detalle():
    def boom():
        raise ValueError("explosión")
    v = gates.correr([boom])
    assert not v.verde and "explosión" in v.checks[0].detalle


def test_guardar_json(tmp_path):
    v = gates.correr([lambda: Resultado("a", True)])
    ruta = gates.guardar(v, str(tmp_path / "g.json"))
    assert "VERDE" in open(ruta).read()
```

`tests/test_determinismo.py`:

```python
from sprites_lib import gates
from sprites_lib.estilos import ACTIVOS


def test_determinismo_por_estilo_activo():
    for estilo in ACTIVOS:
        r = gates.check_determinismo(estilo)
        assert r.ok, r.detalle
```

`tests/test_deriva.py`:

```python
from sprites_lib import gates


def test_deriva_rojo_si_cambio_la_fuente():
    estado_dict = {"fuentes": {"ciclo": "sha256:viejo"}}
    r = gates.check_deriva(estado_dict, {"ciclo": "sha256:nuevo"})
    assert not r.ok and "ciclo" in r.detalle


def test_deriva_omitida_si_no_hay_estado():
    r = gates.check_deriva(None, {"ciclo": "sha256:x"})
    assert r.ok and r.omitido
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_gates.py tests/test_determinismo.py tests/test_deriva.py -q`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implement `sprites_lib/gates.py`**

Docstring: "Motor de gates: corre checks y arma un veredicto VERDE/ROJO con evidencia para el agente."
- `correr(checks)`: ejecuta cada callable; excepción → `Resultado(regla=nombre_del_callable, ok=False, detalle=f"excepción: {e}")`. `verde = all(r.ok or r.omitido)`.
- `informe(v)`: primera línea `VERDE (n/m)` o `ROJO (k fallan)`; luego una línea por check fallido con `detalle` y hasta 5 `evidencia`.
- `guardar(v, ruta)`: JSON `{"verde", "checks": [vars(r)]}`.
- `check_determinismo(estilo, pose="quieto", mira=None, veces=2)`: renderiza `FICHA_MINIMA` `veces` veces por (pose, mira) con `mira` por defecto la primera dirección del estilo; compara `img.tobytes()` entre corridas; ok si todos coinciden.
- `check_deriva(estado_dict, fuentes, regla="deriva")`: sin `estado_dict` → `Resultado(regla, ok=True, omitido=True, detalle="sin aprobación previa")`; con cambios → `ok=False`, detalle con las claves cambiadas.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_gates.py tests/test_determinismo.py tests/test_deriva.py -q`
Expected: passed (determinismo tarda unos segundos: renderiza)

- [ ] **Step 5: Registrar módulo y regenerar MAPA**

Agregar `"gates"` a `MODULOS`; `.venv/bin/python -m sprites_lib.mapa`; `pytest tests/test_mapa.py -q` → passed.

- [ ] **Step 6: Commit**

```bash
git add sprites_lib/gates.py tests/test_gates.py tests/test_determinismo.py tests/test_deriva.py sprites_lib/mapa.py sprites_lib/MAPA.md
git commit -m "Procesos: motor de gates con veredicto VERDE/ROJO, determinismo y deriva"
```

---

### Task 3: Contrato numérico del muñeco (`proporciones.py` + esqueleto)

**Files:**
- Create: `sprites_lib/proporciones.py`
- Create: `tests/test_proporciones.py`, `tests/test_esqueleto.py`
- Modify: `sprites_lib/mapa.py`, `sprites_lib/MAPA.md`

**Interfaces:**
- Consumes: `armado.FICHA_MINIMA`, `armado.render_cuadro`, `armado.pivote`, `tests_personaje.mascara`, `escala.alto_objetivo_px`, `estilos.ESTILOS` + `ACTIVOS` + `VERIFICACION`, `cuerpo.anatomia` + `posar`, `poses.POSES` + `cuadros`, `ciclos.pose`.
- Produces: `TOL_PX`, `TOL_REL`, `medir(estilo, clase="adulto") -> dict`, `comparar(estilo, clase="adulto") -> Resultado`. Claves de `medir`: `alto_px`, `cabeza_px`, `piernas_px`, `cabezas`, `piernas_frac`, `ancho_px`, `ancho_cabeza_px`, `por_direccion` `{dir: {...}}`.

- [ ] **Step 1: Write the failing tests** — `tests/test_proporciones.py`

```python
import pytest
from sprites_lib import proporciones
from sprites_lib.estilos import ESTILOS


@pytest.mark.parametrize("estilo", sorted(ESTILOS))
def test_proporciones_dentro_de_tolerancia(estilo):
    r = proporciones.comparar(estilo)
    assert r.ok, r.detalle


def test_alto_igual_entre_direcciones():
    m = proporciones.medir("stardew")
    altos = [v["alto_px"] for v in m["por_direccion"].values()]
    assert max(altos) - min(altos) <= 2
```

`tests/test_esqueleto.py`:

```python
import numpy as np
import pytest
from sprites_lib.cuerpo import anatomia, posar
from sprites_lib.escala import CLASES
from sprites_lib.estilos import ESTILOS
from sprites_lib.poses import POSES, cuadros

CAM = np.array([0.0, 0.0, 1.0])


@pytest.mark.parametrize("estilo", sorted(ESTILOS))
@pytest.mark.parametrize("clase", sorted(CLASES))
def test_huesos_y_piso(estilo, clase):
    a = anatomia(estilo, clase)
    assert abs(a.muslo - a.canilla) / a.muslo <= .02
    assert a.hombro_u > a.cadera_u
    ratio = (a.muslo + a.canilla) / (a.cadera_u - a.r_pie)
    assert .95 <= ratio <= 1.10


@pytest.mark.parametrize("estilo", ["stardew", "lateral"])
@pytest.mark.parametrize("anim", sorted(POSES))
def test_cadera_sobre_tobillo_en_todas_las_poses(estilo, anim):
    a = anatomia(estilo)
    for ps in cuadros(anim):
        pos = posar(a, ps, CAM)
        for lado in ("derecha", "izquierda"):
            assert pos[f"cadera_{lado}"][2] > pos[f"tobillo_{lado}"][2]


@pytest.mark.parametrize("estilo", ["stardew", "lateral"])
def test_brazos_no_se_estiran(estilo):
    a = anatomia(estilo)
    for anim in ("caminar_lpc", "golpear"):
        for ps in cuadros(anim):
            pos = posar(a, ps, CAM)
            for m in ("derecho", "izquierdo"):
                largo = np.linalg.norm(pos[f"codo_{m}"] - pos[f"hombro_{m}"])
                assert largo <= a.brazo + .01
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_proporciones.py tests/test_esqueleto.py -q`
Expected: `ModuleNotFoundError` (proporciones) y, tras crearlo, posibles fallas reales de tolerancia/pose a corregir

- [ ] **Step 3: Implement `sprites_lib/proporciones.py`**

Docstring: "Contrato numérico del muñeco por estilo: mide el render real y lo compara con el perfil."
- `medir(estilo, clase="adulto")`: por cada dirección del estilo, renderiza `FICHA_MINIMA` en pose `neutra`; con `tests_personaje.mascara` obtiene máscaras de `cabeza_humana@cabeza`, `pierna_humana@pierna_derecha/izquierda` y de todo lo opaco; calcula:
  `alto_px = pivote_y - top_opaco`, `cabeza_px` (alto de la máscara de cabeza), `piernas_px` (alto del bbox de las dos piernas), `cabezas = alto_px / cabeza_px`, `piernas_frac = piernas_px / alto_px`, `ancho_px` (ancho del bbox opaco), `ancho_cabeza_px`; devuelve el resumen de la primera dirección más `por_direccion`.
- `comparar(estilo, clase="adulto")`: espera `alto = escala.alto_objetivo_px`, `cabezas ≈ 1 / proporciones.cabeza_frac`, `piernas_frac ≈ proporciones.piernas_frac`, `ancho_cabeza_px ≈ 2·cabeza_ancho·uz + 2`; compara con `TOL_PX = 2` y `TOL_REL = .10`; además exige que `alto_px` varíe ≤ 2 px entre direcciones. Devuelve `Resultado` con el detalle de cada desvío.
- **Calibrar una vez**: correr `medir` sobre los 6 estilos y fijar `TOL_PX`/`TOL_REL` para que los estilos existentes pasen con margen (si un estilo legítimo queda fuera por más del doble de la tolerancia, es un hallazgo: anotarlo en `CRITERIOS_ANIMACION.md`, no ensanchar más).

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_proporciones.py tests/test_esqueleto.py -q`
Expected: passed (si una pose real falla la aserción de cadera/tobillo, corregir la pose o documentar el caso límite en `CRITERIOS_ANIMACION.md`; no relajar la aserción sin evidencia)

- [ ] **Step 5: Registrar módulo y regenerar MAPA**

Agregar `"proporciones"` a `MODULOS`; regenerar; `pytest tests/test_mapa.py -q` → passed.

- [ ] **Step 6: Commit**

```bash
git add sprites_lib/proporciones.py tests/test_proporciones.py tests/test_esqueleto.py sprites_lib/mapa.py sprites_lib/MAPA.md
git commit -m "Procesos: contrato numérico del muñeco (proporciones y esqueleto)"
```

---

### Task 4: Proceso de estilo (`proceso_estilo.py`)

**Files:**
- Create: `sprites_lib/proceso_estilo.py`
- Create: `tests/test_proceso_estilo.py`
- Modify (solo si hace falta): `sprites_lib/comparar_estilo.py` — exponer las métricas bloqueantes de forma estructurada sin cambiar la salida del CLI
- Modify: `sprites_lib/mapa.py`, `sprites_lib/MAPA.md`

**Interfaces:**
- Consumes: `estado.hash_obj/leer/escribir`, `gates.correr/informe/guardar/check_determinismo/check_deriva`, `proporciones.comparar`, `comparar_estilo.metricas/comparar`, `estilos.ESTILOS`, `escala.TAMANOS`, `lado_a_lado.lado_a_lado`.
- Produces: `main(argv=None) -> int`; `correr_gate(estilo) -> Veredicto`, `check_referencia(estilo) -> Resultado`; subcomandos `medir <estilo>`, `validar <estilo>`, `aprobar <estilo> [--excepcion MOTIVO]`. Congela en `aprobados/estilos/<estilo>/` (`control.png`, `metricas.json`, `estado.json`) y crea `docs/estilos/<estilo>.md` si no existe. Exit codes: 0 VERDE, 1 ROJO, 2 error de uso/desconocido.

- [ ] **Step 1: Write the failing tests** — `tests/test_proceso_estilo.py`

```python
import json
import os
from sprites_lib import proceso_estilo


def test_validar_verde_y_rojo(capsys):
    assert proceso_estilo.main(["validar", "stardew"]) == 0
    assert "VERDE" in capsys.readouterr().out


def test_aprobar_congela_y_deriva(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_estilo.main(["aprobar", "stardew"]) == 0
    carpeta = tmp_path / "aprobados" / "estilos" / "stardew"
    assert (carpeta / "estado.json").exists() and (carpeta / "control.png").exists()
    e = json.loads((carpeta / "estado.json").read_text())
    assert e["fuentes"]["perfil"].startswith("sha256:")
    assert os.path.exists(tmp_path / "docs" / "estilos" / "stardew.md")


def test_aprobar_rojo_no_escribe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from sprites_lib import gates
    monkeypatch.setattr(proceso_estilo, "correr_gate",
                        lambda estilo: gates.correr([lambda: gates.Resultado("test", False, "forzado")]))
    assert proceso_estilo.main(["aprobar", "stardew"]) == 1
    assert not (tmp_path / "aprobados").exists()


def test_estilo_desconocido_da_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_estilo.main(["validar", "no_existe"]) == 2


def test_sin_referencia_calibrada_omite():
    r = proceso_estilo.check_referencia("lpc")
    assert r.ok and r.omitido
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_proceso_estilo.py -q`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implement `sprites_lib/proceso_estilo.py`**

Docstring con uso (patrón del repo, ver `skins.py`).
- `correr_gate(estilo) -> Veredicto` con checks: `proporciones.comparar(estilo)`, `gates.check_determinismo(estilo)`, `check_referencia(estilo)`, `check_deriva(estado.leer("aprobados/estilos/<estilo>"), fuentes_actuales(estilo))`.
- `fuentes_actuales(estilo)`: `{"perfil": hash_obj(ESTILOS[estilo]), "escala": hash_obj(TAMANOS[estilo])}`.
- `check_referencia(estilo)`: sin `referencia` o sin `calibrada` → `Resultado(..., omitido=True)`; si hay, corre `comparar_estilo` sobre el render del muñeco y exige que ninguna métrica bloqueante falle (leer `comparar_estilo.py`; si la distinción bloqueante/informativa no está accesible, refactor mínimo para exponerla manteniendo el print del CLI).
- `medir`: imprime las métricas de referencia (si hay) y `proporciones.medir(estilo)`; no escribe nada.
- `validar`: imprime `gates.informe`.
- `aprobar`: corre el gate; si ROJO y sin `--excepcion` → 1 sin escribir nada. Si VERDE (o con excepción): `aprobados/estilos/<estilo>/control.png` (comparativa `lado_a_lado` referencia vs nuestro), `metricas.json` (métricas del gate + referencias), `estado.json` **último** (fuentes, `nota` si hubo excepción), y `docs/estilos/<estilo>.md` con un esqueleto (medidas, reglas del perfil, placeholders de trampas) solo si no existe.
- `main`: valida el nombre del estilo contra `ESTILOS` (error 2 con mensaje claro y `raise SystemExit` capturado, sin traceback).

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_proceso_estilo.py -q`
Expected: passed

- [ ] **Step 5: Registrar módulo, regenerar MAPA y probar a mano**

Agregar `"proceso_estilo"` a `MODULOS`; regenerar; probar: `.venv/bin/python -m sprites_lib.proceso_estilo validar stardew` → termina en VERDE/ROJO con informe legible.

- [ ] **Step 6: Commit**

```bash
git add sprites_lib/proceso_estilo.py tests/test_proceso_estilo.py sprites_lib/mapa.py sprites_lib/MAPA.md
git commit -m "Procesos: proceso de estilo con validación y congelado (aprobados + doc)"
```

---

### Task 5: Proceso de animación — smoke

**Files:**
- Create: `sprites_lib/proceso_anim.py`, `tests/test_proceso_anim.py`
- Modify: `sprites_lib/gates.py` (checks universales de zonas y pulido), `sprites_lib/mapa.py`, `sprites_lib/MAPA.md`

**Interfaces:**
- Consumes: `zonas.analizar/marcar_falsas`, `pulido.analizar/resumen`, `skins.ficha`, `armado.render_cuadro`, `poses.POSES`.
- Produces: `gates.check_zonas(anim, estilo, ficha=None, dirs=None) -> Resultado`, `gates.check_pulido(anim, estilo, ficha=None, dirs=None) -> Resultado`; `proceso_anim.main(argv)` con `smoke <anim> --estilo X [--dir D] [--skin RUTA]` (por defecto `skins/zonas.png`). Exit 0/1/2.

- [ ] **Step 1: Write the failing test** — `tests/test_proceso_anim.py`

```python
from sprites_lib import proceso_anim


def test_smoke_quieto_verde(capsys):
    assert proceso_anim.main(["smoke", "quieto", "--estilo", "stardew", "--skin", "skins/mago.png"]) == 0
    assert "VERDE" in capsys.readouterr().out


def test_anim_desconocida_da_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["smoke", "no_existe", "--estilo", "stardew"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_proceso_anim.py -q`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implement `gates.check_zonas` y `gates.check_pulido`**

- `check_zonas`: `res = zonas.analizar(anim=anim, estilo=estilo, ficha=ficha, dirs=dirs)`; `zonas.marcar_falsas({}, res)`; cuenta `por_revisar = [a for a in res["alertas"] if a["sev"] >= 2 and a["fp"] is None]` (ajustar las claves exactas leyendo `sprites_lib/zonas.py` y su informe); `Resultado(regla=f"zonas {anim}/{estilo}", ok=not por_revisar, detalle=f"{len(por_revisar)} por revisar", evidencia=textos)`.
- `check_pulido`: `pul = pulido.analizar(anim=anim, estilo=estilo, ficha=ficha, dirs=dirs)`; usar `pulido.resumen`/estructura para contar hallazgos **MAL** (leer `pulido.py`); `ok = 0 MAL`, detalle con los REVISAR listados.

- [ ] **Step 4: Implement `sprites_lib/proceso_anim.py` (solo `smoke`)**

Docstring con uso. `smoke <anim> --estilo X [--dir D] [--skin RUTA]`:
- valida anim ∈ `POSES` y estilo ∈ `ESTILOS` (si no, mensaje claro + 2);
- ficha = `skins.ficha(ruta)` (default `skins/zonas.png`);
- dirs = `[D]` si se pasó, si no la primera dirección del estilo;
- gate con `check_zonas` + `check_pulido`; imprime `gates.informe`; 0 si VERDE, 1 si ROJO.

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_proceso_anim.py -q`
Expected: passed

- [ ] **Step 6: Registrar módulos, regenerar MAPA, probar el default y commit**

Probar a mano el default de skin de zonas: `.venv/bin/python -m sprites_lib.proceso_anim smoke quieto --estilo stardew` y anotar el resultado (si aparece algo ROJO, mirarlo: los umbrales no se bajan sin evidencia).

```bash
.venv/bin/python -m sprites_lib.mapa
git add sprites_lib/proceso_anim.py sprites_lib/gates.py tests/test_proceso_anim.py sprites_lib/mapa.py sprites_lib/MAPA.md
git commit -m "Procesos: smoke de animación con skin de zonas (zonas + pulido como gate)"
```

---

### Task 6: Proceso de animación — validar, aprobar y export

**Files:**
- Modify: `sprites_lib/proceso_anim.py`, `sprites_lib/fotos_control.py` (parámetro `raiz` con default), `tests/test_proceso_anim.py`

**Interfaces:**
- Consumes: `comparar_plantilla.medir/resumen`, `fotos_control.guardar/comparar`, `exportar.exportar_direcciones`, `armado.pivote`, `poses.fps/loop/offset_y`, `estado.*`.
- Produces: `validar <anim> --estilo X [--skin RUTA]` (todas las direcciones + plantilla + control + deriva) y `aprobar <anim> --estilo X [--skin RUTA] [--excepcion MOTIVO]`, que congela `aprobados/animaciones/<anim>/<estilo>/` (cuadros de control, `metricas.json`, `estado.json`) y exporta `salida/animaciones/<anim>/<estilo>/`.

- [ ] **Step 1: Write the failing tests** (agregar a `tests/test_proceso_anim.py`)

```python
def test_aprobar_congela_y_exporta(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["aprobar", "quieto", "--estilo", "stardew"]) == 0
    carpeta = tmp_path / "aprobados" / "animaciones" / "quieto" / "stardew"
    assert (carpeta / "estado.json").exists()
    assert list(carpeta.glob("*.png")), "faltan cuadros de control"
    assert (tmp_path / "salida" / "animaciones" / "quieto" / "stardew" / "quieto.png").exists()


def test_validar_con_control_ok(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["aprobar", "quieto", "--estilo", "stardew"]) == 0
    assert proceso_anim.main(["validar", "quieto", "--estilo", "stardew"]) == 0


def test_validar_sin_control_ok(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["validar", "quieto", "--estilo", "stardew"]) == 0


def test_nombre_invalido_rechazado(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_anim.main(["aprobar", "../afuera", "--estilo", "stardew"]) == 2
    assert not (tmp_path.parent / "afuera").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_proceso_anim.py -q`
Expected: FAIL (subcomandos no existen)

- [ ] **Step 3: Refactor mínimo de `fotos_control.py`**

`carpeta(nombre, estilo, raiz=DIR)`, `guardar(nombre, estilo, todo, raiz=DIR)`, `comparar(nombre, estilo, todo, carpeta_dif, raiz=DIR)`: mismos defaults (`personajes/aprobados`), para que `personajes/generar.py` no cambie. En animaciones se usa `raiz="aprobados/animaciones"`.

- [ ] **Step 4: Implementar `validar` y `aprobar` en `proceso_anim.py`**

- `REFERENCIAS = {"caminar_lpc": "lpc"}`: si la anim tiene referencia, correr `comparar_plantilla.medir(estilo=ref, pose=anim, mira="E")` y exigir error medio de huesos ≤ 2 px (el resto del resumen es informativo); si no, check `omitido`.
- `validar`: renderiza todas las direcciones (skin de zonas o `--skin`), gate = smoke completo + `check_determinismo` (pose=anim) + `check_deriva` + plantilla; si hay cuadros de control, agrega `fotos_control.comparar(anim, estilo, todo, dif_dir, raiz="aprobados/animaciones")`.
- `aprobar`: gate primero; si VERDE (o `--excepcion`), escribe cuadros de control con `fotos_control.guardar(anim, estilo, todo, raiz="aprobados/animaciones")`, `metricas.json` (alertas por dirección, pulido, fps/loop) y `estado.json` **último** con `fuentes={"ciclo": hash_obj(POSES[anim])}`; exporta `salida/animaciones/<anim>/<estilo>/` con `exportar_direcciones` (pivote `armado.pivote(estilo, pose=anim)`, `extra` con `offset_y` si existe).
- Saneado: `nombre` debe matchear `^[a-z0-9_]+$` (anims) y `^[a-z0-9_]+$` (estilos); si no → mensaje + 2.

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_proceso_anim.py -q`
Expected: passed

- [ ] **Step 6: Probarlo a mano y commit**

```bash
.venv/bin/python -m sprites_lib.proceso_anim validar caminar_lpc --estilo stardew
git add sprites_lib/proceso_anim.py sprites_lib/fotos_control.py tests/test_proceso_anim.py
git commit -m "Procesos: validar y aprobar animaciones (control visual, deriva y export fuente)"
```

---

### Task 7: Proceso de skin — smoke

**Files:**
- Create: `sprites_lib/proceso_skin.py`, `tests/test_proceso_skin.py`
- Modify: `sprites_lib/mapa.py`, `sprites_lib/MAPA.md`

**Interfaces:**
- Consumes: `skins.cargar/ficha`, `gates.check_zonas/check_pulido/check_determinismo/correr/informe`, `estado.hash_archivo`.
- Produces: `main(argv)` con `smoke <nombre> [--anim quieto] [--estilo stardew]`; exit 0/1/2.

- [ ] **Step 1: Write the failing test** — `tests/test_proceso_skin.py`

```python
from sprites_lib import proceso_skin


def test_smoke_skin_existente(capsys):
    assert proceso_skin.main(["smoke", "mago"]) == 0
    assert "VERDE" in capsys.readouterr().out


def test_skin_inexistente_da_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_skin.main(["smoke", "no_existe"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_proceso_skin.py -q`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implement `sprites_lib/proceso_skin.py` (solo `smoke`)**

Docstring con uso. `smoke <nombre>`:
- ruta = `skins/<nombre>.png`; si no existe → mensaje claro + 2;
- chequeo de dimensión y carga con `skins.cargar` (32×32) como `Resultado`;
- gate = ese check + `check_zonas(anim, estilo, ficha=skins.ficha(ruta))` + `check_pulido(...)` + `check_determinismo` sobre la ficha de la skin;
- imprime `gates.informe`; 0/1.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_proceso_skin.py -q`
Expected: passed

- [ ] **Step 5: Registrar módulo, regenerar MAPA y commit**

```bash
.venv/bin/python -m sprites_lib.mapa
git add sprites_lib/proceso_skin.py tests/test_proceso_skin.py sprites_lib/mapa.py sprites_lib/MAPA.md
git commit -m "Procesos: smoke de skin sobre quieto (zonas, pulido y determinismo)"
```

---

### Task 8: Proceso de skin — aprobar y lote

**Files:**
- Modify: `sprites_lib/proceso_skin.py`, `tests/test_proceso_skin.py`

**Interfaces:**
- Consumes: `estado.listar/escribir/hash_archivo`, `skins.salida_juego`, `exportar.exportar_direcciones`, `gates.*`.
- Produces: `aprobar <nombre> [--estilo stardew]` → `aprobados/skins/<nombre>/` (`smoke.gif`, `metricas.json`, `estado.json`); `lote <nombre> [--estilo stardew] [--raiz output]` → exporta todas las animaciones aprobadas y escribe `salida/zonas/lote_<nombre>.md` con el informe por animación. Exit 0 todas verdes, 1 si alguna falla o no hay animaciones aprobadas, 2 error de uso.

- [ ] **Step 1: Write the failing tests** (agregar a `tests/test_proceso_skin.py`)

```python
import json


def test_aprobar_congela(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert proceso_skin.main(["aprobar", "mago"]) == 0
    carpeta = tmp_path / "aprobados" / "skins" / "mago"
    assert (carpeta / "estado.json").exists() and (carpeta / "smoke.gif").exists()
    e = json.loads((carpeta / "estado.json").read_text())
    assert e["fuentes"]["skin"].startswith("sha256:")


def test_lote_sin_aprobadas_avisa_y_da_1(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert proceso_skin.main(["lote", "mago"]) == 1
    assert "no hay animaciones aprobadas" in capsys.readouterr().out.lower()


def test_lote_exporta(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from sprites_lib import estado
    a = tmp_path / "aprobados" / "animaciones" / "quieto" / "stardew"
    estado.escribir(str(a), "anim/quieto/stardew", {"ciclo": "sha256:x"}, "metricas.json")
    assert proceso_skin.main(["lote", "mago", "--raiz", str(tmp_path / "output")]) == 0
    assert (tmp_path / "output" / "mago" / "quieto" / "quieto.png").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_proceso_skin.py -q`
Expected: FAIL (subcomandos no existen)

- [ ] **Step 3: Implementar `aprobar` y `lote`**

- `aprobar`: gate de `smoke` primero; si VERDE (o `--excepcion`), renderiza `quieto` todas las direcciones con la skin y exporta a `aprobados/skins/<nombre>/` (hoja + `smoke.gif` con `exportar_direcciones`), `metricas.json` (resultado del gate) y `estado.json` **último** con `fuentes={"skin": hash_archivo(png)}` (+ `{"pintar": hash_archivo(script)}` si existe `skins/pintar_<nombre>.py`).
- `lote`: `estado.listar("aprobados/animaciones")` filtrando por estilo; si vacío → imprime "no hay animaciones aprobadas para <estilo>" y 1. Por cada (anim, estilo): gate por animación (`check_zonas` + `check_pulido` + `check_deriva` contra la fuente del ciclo) y export con `skins.salida_juego(ruta, anim, estilo, raiz=raiz, cuadros=True)`; junta todo en el informe `.md`; exit 1 si alguna animación falla, 0 si todas verdes.
- El lote nunca corta a la mitad por una animación fallida: continúa, la lista en el informe.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_proceso_skin.py -q`
Expected: passed

- [ ] **Step 5: Commit**

```bash
git add sprites_lib/proceso_skin.py tests/test_proceso_skin.py
git commit -m "Procesos: aprobar skin y lote sobre animaciones aprobadas (salida del juego)"
```

---

### Task 9: Documentación, integración y cierre

**Files:**
- Create: `docs/procesos/estilo.md`, `docs/procesos/animacion.md`, `docs/procesos/skin.md`
- Modify: `CLAUDE.md` (sección "Procesos"), `CRITERIOS_ANIMACION.md` (nota breve con los comandos nuevos)
- Modify: `sprites_lib/MAPA.md` (regenerado final)

- [ ] **Step 1: Escribir los tres docs de proceso**

Cada doc: cuándo usarlo, pasos con el comando exacto, qué congela, qué gate corre, y el flujo de iteración autónoma (tope 3 vueltas propias antes de consultar). Español, corto (una pantalla cada uno). Referenciar `docs/superpowers/specs/2026-09-29-procesos-estilo-animacion-skin-design.md` como diseño.

- [ ] **Step 2: Actualizar `CLAUDE.md`**

Agregar en el kit de sprites: "Procesos: `python -m sprites_lib.proceso_estilo|proceso_anim|proceso_skin` (pasos y gates en `docs/procesos/`); aprobar es el único paso humano; artefactos congelados en `aprobados/`."

- [ ] **Step 3: Demostración de punta a punta (pegar salidas en el mensaje de cierre)**

```bash
.venv/bin/python -m sprites_lib.proceso_estilo validar stardew
.venv/bin/python -m sprites_lib.proceso_anim smoke saltar --estilo stardew
.venv/bin/python -m sprites_lib.proceso_skin smoke clast
```

- [ ] **Step 4: Suite completa y MAPA**

Run: `.venv/bin/python -m pytest -m "" -q` → todo verde (los lentos incluidos).
Run: `.venv/bin/python -m sprites_lib.mapa` y `git status --short` (sin cambios pendientes en MAPA).

- [ ] **Step 5: Commit**

```bash
git add docs/procesos CLAUDE.md CRITERIOS_ANIMACION.md sprites_lib/MAPA.md
git commit -m "Procesos: documentación, integración y cierre (docs/procesos + CLAUDE.md)"
```

---

## Acceptance final (del spec)

- Los tres comandos corren de punta a punta sobre artefactos reales (Task 9, Step 3).
- Un gate ROJO nunca congela; `aprobar` escribe `estado.json` al final (Tasks 4, 6, 8 con sus tests).
- Editar la fuente de un artefacto congelado da ROJO por deriva o por pixel diff (Tasks 2, 6; `tests/test_deriva.py`).
- `pytest` completo verde con `-m ""` (Task 9, Step 4).
- Flujos actuales intactos: `personajes/generar`, `skins demo|juego`, `zonas`, `pulido` (suite existente en verde).
