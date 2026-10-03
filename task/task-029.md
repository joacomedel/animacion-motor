# task-029 — `test_referencia_compara_especimen`: métrica `huerfanos` fuera de tolerancia

**Estado:** pendiente
**Origen:** verificación del merge de integración (PR #14/#15, 2026-10-03). Falla preexistente detectada al correr la suite sobre `motor-3d-tiempo-real`.

## Contexto

`tests/test_proceso_estilo.py::test_referencia_compara_especimen` falla comparando el espécimen contra la
referencia de Stardew (`referencias/stardew/abigail.png`):

```
Resultado(regla='estilo vs referencia', ok=False,
  detalle='...: 1 métricas bloqueantes fuera de tolerancia',
  evidencia=['huerfanos: referencia 0.39, espécimen 0.23'])
```

Es **preexistente**: se reprodujo idéntico en un worktree limpio de `origin` (`63cc137`), con las
referencias enlazadas. No lo introdujo el trabajo de escala/pies (PR #15).

`huerfanos` mide la fracción de píxeles "huérfanos" (aislados / sin vecino del mismo tono, según
`comparar_estilo`). La referencia trae 0.39 y el espécimen 0.23, fuera de la tolerancia configurada para
`stardew` (`ESTILOS["stardew"]["referencia"]`).

## Criterio de aceptación

- Decidir si el problema es del **espécimen** (el render de `stardew` deja menos píxeles huérfanos de los
  que corresponden) o de la **tolerancia/referencia** (el umbral de `huerfanos` no aplica a este caso).
- Que el test pase de forma legítima (no subir el umbral "para que dé verde" sin justificar qué métrica se
  relaja y por qué).
- Documentar la causa en `CRITERIOS_ANIMACION.md` si el ajuste toca el look del estilo.

## Relaciona

- task-017 (paleta fija por estilo), ya que cambia los colores del espécimen y puede afectar `huerfanos`.
- `sprites_lib/comparar_plantilla.py` / `proceso_estilo.check_referencia`.
