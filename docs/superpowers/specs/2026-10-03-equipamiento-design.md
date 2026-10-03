# Diseño: equipamiento (guantes, armas, gorros, armaduras)

Fecha: 2026-10-03 · Estado: **pendiente de aprobación**

## Decisión del usuario (2026-10-03)

1. **Gorros**: van **anclados** (sobre el pelo), no sustituyen la cabeza.
2. **Skins de ítems**: **simples** — misma forma con otro color, o una forma levemente distinta
   (p. ej. espada roja, antorcha). No entra el sistema cilíndrico de Fase 2 de `docs/OBJETOS.md`.
3. **Organización**: cada cosa en su **archivo separado**.

## Principio rector

Todo el equipo es **datos** sobre el **registro de componentes** que ya existe en
`sprites_lib/componentes/`. El motor no cambia: renderiza una ficha. Agregar un ítem nuevo
nunca toca el motor.

## Mecanismo existente (no reinventar)

- `componentes/` + `registrar`: cada pieza sabe dibujarse en su ancla.
- `objeto` (`componentes/objetos.py`): espada/hacha/antorcha/escudo/bastón, enganchado a la
  mano. Sigue la animación gratis (la mano es un ancla que ya mueven todos los ciclos).
- `armado.expandir`: base + componentes, en orden = capas (ropa → armadura → accesorios).
- `ficha.validar`: valida tipo/ancla/params.

## Estructura de archivos (separados)

| Archivo | Qué vive acá |
|---|---|
| `sprites_lib/componentes/equipo.py` | componentes nuevos: `guante`, `sombrero`, `armadura` |
| `sprites_lib/skins_item.py` | skins simples de ítems (color + forma), reutiliza `skins.material` |
| `motor/equipo.py` | catálogo `ITEMS` + `Equipo` + `ficha_con_equipo` |
| `motor/renderer.py` | `set_equipo([...])` (reconstruye ficha, limpia caché) |
| `tests/test_equipo.py` | tests del equipamiento |

## Modelo de datos

Catálogo (`motor/equipo.py`):
```python
ITEMS = {
    "guante_cuero":   {"tipo": "guante",   "ancla": "mano_derecha", "material": "cuero"},
    "espada":         {"tipo": "objeto",   "ancla": "mano_derecha", "parametros": {"forma": "espada"}},
    "espada_roja":    {"tipo": "objeto",   "ancla": "mano_derecha",
                       "parametros": {"forma": "espada"}, "skin": "items/espada_roja.png"},
    "antorcha":       {"tipo": "objeto",   "ancla": "mano_derecha", "parametros": {"forma": "antorcha"}},
    "sombrero":       {"tipo": "sombrero", "ancla": "coronilla",    "material": "cuero"},
    "armadura_malla": {"tipo": "armadura", "ancla": "torso",        "material": "metal"},
}
```

`Equipo` = lista ordenada de nombres de ítem (el orden = capas). `ficha_con_equipo(ficha_base, items)`
mergea los componentes en la ficha base y devuelve la ficha lista para `armado.render_cuadro`.

## Skins simples de ítems

`sprites_lib/skins_item.py`: un ítem con `skin` apunta a un PNG chico (reutiliza `skins.material`
para el nombre de color). El componente correspondiente lo pinta con ese material. Si no hay
`skin`, usa `material` (color plano de la paleta). Nada de coordenadas cilíndricas.

## Componentes nuevos

- `guante` · ancla `mano_derecha`/`mano_izquierda` · pinta la mano (material o skin).
- `sombrero` · ancla `coronilla` · se dibuja sobre el pelo, sin tapar la cara.
- `armadura` · ancla `torso` · sobre la ropa.

Reutilizar al máximo: `objeto` ya cubre las 5 armas; `brazo_skin`/`torso_skin` ya pintan con skin.

## Motor

`renderer.set_equipo(["espada", "sombrero"])` → reconstruye la ficha → limpia la caché.
Mismo patrón que `set_arma`/`set_dano`. Teclas en `main` para equipar/desequipar.

## Animaciones: reutilización total

Todo ítem se ancla a una ancla que ya mueven los ciclos. Blandir una espada = reusar `golpear`.
Cero trabajo por animación.

## Regla de escalabilidad (el contrato)

1. Ítem con dibujo existente → **1 entrada en `ITEMS`**. Sin código.
2. Ítem con dibujo nuevo → **1 componente registrado** + 1 entrada en `ITEMS`.
3. El motor **nunca** cambia.

## Verificación

- Test: armar una ficha con equipo y renderizar (todas las direcciones).
- Test: un ítem nuevo agregado al catálogo funciona sin tocar el motor.
- `pytest` en verde; `motor.debug` muestra un personaje equipado.

## Fuera de alcance (esta fase)

- Sistema cilíndrico de skins de objetos (Fase 2 de `docs/OBJETOS.md`).
- Puente referencias → ciclos (Fase 3).
- Skins de cuerpo completas por ítem (solo color + forma simple).
