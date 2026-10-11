#!/usr/bin/env bash
# ./run.sh [validate|run|plot|all] [bdc_mapbiomas]      (default: all bdc_mapbiomas)
# `run` fetches the sources (network), derives the variables and exports one GeoTIFF.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; P="${2:-bdc_mapbiomas}"
case "${1:-all}" in
  validate) disscube validate "$HERE/$P.toml" ;;
  run)      disscube validate "$HERE/$P.toml"
            mkdir -p "$HERE/data"
            disscube run "$HERE/$P.toml" --workspace "$HERE/data/$P" --output "$HERE/data/$P.tif" ;;
  plot)     python "$HERE/../common/plot_cube.py" "$HERE/data/$P.tif" "$HERE/images/$P" ;;
  all)      "$0" run "$P"; "$0" plot "$P" ;;
esac
