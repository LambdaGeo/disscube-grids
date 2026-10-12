#!/usr/bin/env bash
# ./run.sh [validate|run|bands|all]      (default: run)
#   validate  checks mapbiomas.toml
#   run       builds the 5.28 km grid with MapBiomas (network, whole Brazil; hours) -> data/mapbiomas_5k.tif
#   bands     puts the land-use bands into the base cell space of the main run
#             (needs data/raw_cellspace_bdc_5k.tif from open-lucc-workflow and scripts/ of that repository on PATH or in ./scripts)
#   all       run, then bands
# Leave it running: nohup /usr/bin/time -v ./run.sh run > run.log 2>&1 &
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HERE/data"
case "${1:-run}" in
  validate) disscube validate "$HERE/mapbiomas.toml" ;;
  run)      disscube validate "$HERE/mapbiomas.toml"
            disscube run "$HERE/mapbiomas.toml" --workspace "$HERE/data/mapbiomas" --output "$HERE/data/mapbiomas_5k.tif" ;;
  bands)    python "$HERE/replace_bands.py" --base "$HERE/data/raw_cellspace_bdc_5k.tif" \
              --bands "$HERE/data/mapbiomas_5k.tif" --out "$HERE/data/raw_cellspace_bdc_5k_mapbiomas.tif" ;;
  all)      "$0" run; "$0" bands ;;
esac
