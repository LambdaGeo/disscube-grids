#!/usr/bin/env bash
# ./run.sh [validate|run|plot|all]      (default: all)
# `run` fetches PRODES (network, about 130 MB the first time), derives the variables and exports one GeoTIFF.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "${1:-all}" in
  validate) disscube validate "$HERE/prodes.toml" ;;
  run)      disscube validate "$HERE/prodes.toml"
            mkdir -p "$HERE/data"
            disscube run "$HERE/prodes.toml" --workspace "$HERE/data/prodes" --output "$HERE/data/prodes.tif" ;;
  plot)     python "$HERE/figure_prodes.py" "$HERE/data/prodes.tif" ;;
  all)      "$0" run; "$0" plot ;;
esac
