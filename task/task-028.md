# task-028 — La herramienta `edit` reformatea el Python entero al guardar (diffs inflados)

**Estado:** pendiente
**Origen:** trabajo de task-019 con subagentes (2026-10-03).

## Contexto

Al aplicar una corrección mínima con la herramienta `edit` sobre `sprites_lib/render3d.py`, el archivo
se reformateó **completo** al guardar: pasó de 348 líneas (estilo compacto del repo) a 526 líneas
(`def faldon(` multilínea, una sentencia por línea, etc.). El diff de un cambio de 11 líneas se infló a
~330 líneas. El subagente que hizo task-019 reportó el mismo síntoma ("el formatter del repo reformateó").

- No hay `pyproject.toml`/`ruff.toml`/`setup.cfg` en el repo, ni binario de formateador en `.venv/bin`.
- El repo **no** está en estilo autopep8: usa sentencias compactas (`a = ...; b = ...`), que el formateador parte.
- Workaround usado: hacer las ediciones mínimas **por shell** (`git checkout` + script Python / heredoc),
  que no dispara el formateador. Así el diff quedó en 8 inserciones / 3 borrados.

## Criterio de aceptación

- Entender qué formateador dispara OpenCode al escribir archivos y si se puede desactivar por proyecto
  (o fijar uno que respete el estilo actual del repo).
- Documentar en `AGENTS.md` la forma segura de editar Python sin inflar diffs (o el flag de config).

## Notas

- Afecta a todos los subagentes que editen `.py` con la herramienta `edit`.
