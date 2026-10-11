#!/usr/bin/env bash
# ./run.sh [validate|run|plot|all] [sources|bdc_ndvi]      (default: all sources)
# `run` fetches the sources (network), derives the variables and exports one GeoTIFF.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; P="${2:-sources}"
case "${1:-all}" in
  validate) disscube validate "$HERE/$P.toml" ;;
  run)      disscube validate "$HERE/$P.toml"
            mkdir -p "$HERE/data"
            disscube run "$HERE/$P.toml" --workspace "$HERE/data/$P" --output "$HERE/data/$P.tif" ;;
  plot)     BDC=(); [ -f "$HERE/data/bdc_ndvi.tif" ] && BDC=(--bdc "$HERE/data/bdc_ndvi.tif")     # third panel when it was run
            python "$HERE/figure_sources.py" "$HERE/data/$P.tif" ${BDC[@]+"${BDC[@]}"} ;;
  all)      "$0" run "$P"; "$0" plot "$P" ;;
esac
