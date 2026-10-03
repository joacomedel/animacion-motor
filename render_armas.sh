#!/usr/bin/env bash
# Renderiza las animaciones de todas las skins CON UN ARMA en la mano (la skin no cambia: el arma es una capa aparte).
#
# Uso:
#   ./render_armas.sh                         # espada, estilo stardew, todas las animaciones; salta las ya hechas
#   ./render_armas.sh --arma hacha            # otra arma (espada,hacha,antorcha,escudo,baston)
#   ./render_armas.sh --anim golpear          # una animación (o caminar_lpc,quieto,saltar)
#   ./render_armas.sh --anim todas            # las 6: neutra,quieto,caminar_lpc,saltar,agachar,golpear
#   ./render_armas.sh --estilo stardew8       # 8 direcciones
#   ./render_armas.sh --entrega               # exporta a output/ con PNG por cuadro
#   ./render_armas.sh --skins vampira,mago    # solo esas skins
#   ./render_armas.sh --forzar                # regenera aunque exista
#   ./render_armas.sh --listar                # muestra qué haría
#
# Layout: <raíz>/<personaje>/<estilo>/<anim>_<arma>/<anim>_<arma>{,_todas.gif,_DIR.gif,.png,.json}
# (el personaje conserva su nombre; el arma es una variante de animación, ver docs/ESTRUCTURA_SALIDAS.md)
set -euo pipefail
cd "$(dirname "$0")"

PY=.venv/bin/python
ANIMS=todas
ESTILO=stardew
ARMA=espada
FORZAR=0
LISTAR=0
ENTREGA=0
SOLO=""

while [ $# -gt 0 ]; do
  case "$1" in
    --forzar|-f) FORZAR=1 ;;
    --listar|-n) LISTAR=1 ;;
    --entrega)   ENTREGA=1 ;;
    --anim)      ANIMS="$2"; shift ;;
    --estilo)    ESTILO="$2"; shift ;;
    --arma)      ARMA="$2"; shift ;;
    --skins)     SOLO="$2"; shift ;;
    -h|--help)   sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "opción desconocida: $1" >&2; exit 2 ;;
  esac
  shift
done

[ -x "$PY" ] || { echo "no encuentro $PY; corré esto desde la raíz del repo" >&2; exit 2; }
[ "$ANIMS" = "todas" ] && ANIMS="neutra,quieto,caminar_lpc,saltar,agachar,golpear"
IFS=',' read -r -a LISTA_ANIMS <<< "$ANIMS"

en_solo() { [ -z "$SOLO" ] || [[ ",$SOLO," == *",$1,"* ]]; }

shopt -s nullglob
SKINS=(skins/*.png)
total=0; hechas=0; saltadas=0; fallaron=0

for png in "${SKINS[@]}"; do
  nombre=$(basename "$png" .png)
  case "$nombre" in zonas|guia) continue ;; esac
  en_solo "$nombre" || continue

  for anim in "${LISTA_ANIMS[@]}"; do
    total=$((total+1))
    vdir="${anim}_${ARMA}"
    if [ "$ENTREGA" = 1 ]; then
      marca="output/${nombre}/$ESTILO/$vdir/$vdir.png"
    else
      marca="salida/${nombre}/$ESTILO/$vdir/$vdir.png"
    fi
    if [ "$FORZAR" = 0 ] && [ -f "$marca" ] && [ "$marca" -nt "$png" ]; then
      saltadas=$((saltadas+1)); [ "$LISTAR" = 1 ] && echo "= $nombre/$ARMA/$anim (ya está)"; continue
    fi
    if [ "$LISTAR" = 1 ]; then echo "? $nombre/$ARMA/$anim (falta o quedó vieja)"; continue; fi
    echo "+ $nombre/$ARMA/$anim"
    if [ "$ENTREGA" = 1 ]; then
      "$PY" -m sprites_lib.skins arma "$png" --arma "$ARMA" --anim "$anim" --estilo "$ESTILO" --output
    else
      "$PY" -m sprites_lib.skins arma "$png" --arma "$ARMA" --anim "$anim" --estilo "$ESTILO"
    fi
    hechas=$((hechas+1))
  done
done

echo
echo "resumen: $hechas renderizadas, $saltadas salteadas, $total en total, $fallaron fallaron"
