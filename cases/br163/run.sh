#!/usr/bin/env bash
# ./run.sh [validate|run|plot|all] [prodes|bdc_mapbiomas]      (default: all prodes)
# `plot` is the quick look of `disscube plot` (needs matplotlib): one panel per band -> images/<pipeline>.png
# `run` fetches the sources (network), derives the variables and exports one GeoTIFF.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; P="${2:-prodes}"
case "${1:-all}" in
  validate) disscube validate "$HERE/$P.toml" ;;
  run)      disscube validate "$HERE/$P.toml"
            mkdir -p "$HERE/data"
            disscube run "$HERE/$P.toml" --workspace "$HERE/data/$P" --output "$HERE/data/$P.tif" ;;
  plot)     mkdir -p "$HERE/images"
            disscube plot "$HERE/data/$P.tif" -o "$HERE/images/$P.png" --crop ;;
  all)      "$0" run "$P"; "$0" plot "$P" ;;
esac
