#!/usr/bin/env bash
# Renderiza las animaciones de todas las skins disponibles, saltando las que ya están hechas.
#
# Uso:
#   ./render_skins.sh                        # caminar_lpc, estilo stardew; salta las ya generadas
#   ./render_skins.sh --forzar               # regenera todo aunque exista
#   ./render_skins.sh --listar               # muestra qué haría, sin renderizar
#   ./render_skins.sh --anim quieto          # otra animación (o caminar_lpc,quieto,saltar)
#   ./render_skins.sh --anim todas           # las 6: neutra,quieto,caminar_lpc,saltar,agachar,golpear
#   ./render_skins.sh --estilo stardew8      # otro estilo
#   ./render_skins.sh --entrega              # exporta a output/ con PNG por cuadro (entrega del juego)
#   ./render_skins.sh --skins vampira,mago   # solo esas skins
#   ./render_skins.sh --pintar               # además corre skins/<nombre>.py antes de renderizar
#
# Determinístico e idempotente: si la salida existe y es más nueva que el PNG de la skin, la saltea.
# Construir una skin nueva (el .py que la pinta) es lo único que necesita al LLM; esto solo la aplica.
# Layout de salida: <raíz>/<personaje>/<estilo>/<anim>/<anim>{_todas.gif,_DIR.gif,.png,.json}
#   con <raíz> = salida/ (o output/ con --entrega) y <estilo> = stardew (4 dir) o stardew8 (8 dir).
set -euo pipefail
cd "$(dirname "$0")"

PY=.venv/bin/python
ANIMS=caminar_lpc
ESTILO=stardew
FORZAR=0
LISTAR=0
ENTREGA=0
PINTAR=0
SOLO=""

while [ $# -gt 0 ]; do
  case "$1" in
    --forzar|-f) FORZAR=1 ;;
    --listar|-n) LISTAR=1 ;;
    --entrega)   ENTREGA=1 ;;
    --pintar)    PINTAR=1 ;;
    --anim)      ANIMS="$2"; shift ;;
    --estilo)    ESTILO="$2"; shift ;;
    --skins)     SOLO="$2"; shift ;;
    -h|--help)   sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "opción desconocida: $1" >&2; exit 2 ;;
  esac
  shift
done

if [ ! -x "$PY" ]; then
  echo "no encuentro $PY; corré esto desde la raíz del repo" >&2
  exit 2
fi

[ "$ANIMS" = "todas" ] && ANIMS="neutra,quieto,caminar_lpc,saltar,agachar,golpear"
IFS=',' read -r -a LISTA_ANIMS <<< "$ANIMS"

en_solo() { [ -z "$SOLO" ] || [[ ",$SOLO," == *",$1,"* ]]; }

shopt -s nullglob
SKINS=(skins/*.png)
total=0; hechas=0; saltadas=0; fallaron=0

for png in "${SKINS[@]}"; do
  nombre=$(basename "$png" .png)
  case "$nombre" in zonas|guia) continue ;; esac   # plantillas de depuración, no personajes
  en_solo "$nombre" || continue

  if [ "$PINTAR" = 1 ] && [ -f "skins/$nombre.py" ]; then
    if [ "$LISTAR" = 1 ]; then
      echo "p $nombre (skins/$nombre.py)"
    else
      echo "p $nombre (skins/$nombre.py)"
      "$PY" "skins/$nombre.py" || { echo "  ¡falló skins/$nombre.py!" >&2; fallaron=$((fallaron+1)); continue; }
    fi
  fi

  for anim in "${LISTA_ANIMS[@]}"; do
    total=$((total+1))
    if [ "$ENTREGA" = 1 ]; then
      marca="output/$nombre/$ESTILO/$anim/$anim.png"
    else
      marca="salida/$nombre/$ESTILO/$anim/$anim.png"
    fi

    if [ "$FORZAR" = 0 ] && [ -f "$marca" ] && [ "$marca" -nt "$png" ]; then
      saltadas=$((saltadas+1))
      [ "$LISTAR" = 1 ] && echo "= $nombre/$anim (ya está)"
      continue
    fi

    if [ "$LISTAR" = 1 ]; then
      echo "? $nombre/$anim (falta o quedó vieja)"
      continue
    fi

    echo "+ $nombre/$anim"
    if [ "$ENTREGA" = 1 ]; then
      "$PY" -m sprites_lib.skins juego "$png" --anim "$anim" --estilo "$ESTILO" --output
    else
      "$PY" -m sprites_lib.skins juego "$png" --anim "$anim" --estilo "$ESTILO"
    fi
    hechas=$((hechas+1))
  done
done

echo
echo "resumen: $hechas renderizadas, $saltadas salteadas, $total en total, $fallaron fallaron"
