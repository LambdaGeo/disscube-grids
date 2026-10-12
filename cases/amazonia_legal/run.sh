#!/usr/bin/env bash
# ./run.sh [validate|run|plot|all]      (default: all)
# `plot` is the quick look of `disscube plot` (needs matplotlib): forest and accumulated deforestation, 2024.
# `run` fetches PRODES (network, about 130 MB the first time), derives the variables and exports one GeoTIFF.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "${1:-all}" in
  validate) disscube validate "$HERE/prodes.toml" ;;
  run)      disscube validate "$HERE/prodes.toml"
            mkdir -p "$HERE/data"
            disscube run -v "$HERE/prodes.toml" --workspace "$HERE/data/prodes" --output "$HERE/data/prodes.tif" ;;
  plot)     disscube plot "$HERE/data/prodes.tif" -o "$HERE/../../docs/figures/amazonia_prodes.png" \
              --year 2024 --cols 2 --shared-colorbar --crop --dpi 300 ;;
  all)      "$0" run; "$0" plot ;;
esac
