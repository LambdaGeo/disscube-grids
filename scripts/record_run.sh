#!/usr/bin/env bash
# Run one pipeline of one case and keep its record in the case folder.
#
#   scripts/record_run.sh <case> [<pipeline>]       e.g.  scripts/record_run.sh ilha_maranhao bdc_mapbiomas
#
# It checks that the installed DisSCube is the release pinned in requirements.txt (not an editable install), runs
# `cases/<case>/run.sh run <pipeline>` under `/usr/bin/time -v`, and writes next to the case:
#   run_<pipeline>.log   the output of the run, the `time -v` summary and a summary of every band of the GeoTIFF
#   run_<pipeline>.json  the run record of DisSCube (pipeline, sources, derived variables, SHA-256, DisSCube version)
#   env.txt              CPU, memory and the versions of the main libraries
# Absolute paths of this repository in the log are replaced by <repo>. Needs: GNU time (/usr/bin/time), python with rasterio.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE="${1:?usage: scripts/record_run.sh <case> [<pipeline>]}"; DIR="$ROOT/cases/$CASE"
[ -d "$DIR" ] || { echo "no such case: $CASE" >&2; exit 2; }
P="${2:-$(ls "$DIR"/*.toml | head -1 | xargs -n1 basename | sed 's/\.toml$//')}"
[ -f "$DIR/$P.toml" ] || { echo "no such pipeline: cases/$CASE/$P.toml" >&2; exit 2; }
command -v /usr/bin/time >/dev/null || { echo "GNU time not found (apt install time)" >&2; exit 2; }

PIN="$(sed -n 's/^disscube==\([0-9][0-9.]*\).*/\1/p' "$ROOT/requirements.txt" | head -1)"
HAVE="$(python - <<'PY'
from importlib.metadata import version, distribution
import json
d = distribution("disscube")
direct = d.read_text("direct_url.json")
editable = bool(direct and json.loads(direct).get("dir_info", {}).get("editable"))
print(version("disscube") + (" editable" if editable else ""))
PY
)"
if [ "$HAVE" != "$PIN" ]; then
  echo "DisSCube installed: $HAVE; requirements.txt pins: $PIN." >&2
  echo "Run: pip uninstall -y disscube && pip install -r requirements.txt" >&2
  exit 3
fi

LOG="$DIR/run_$P.log"; TMP="$(mktemp)"
echo "== $CASE / $P, DisSCube $HAVE, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
set +e
( cd "$DIR" && /usr/bin/time -v bash ./run.sh run "$P" ) 2>&1 | tee "$TMP"
status=${PIPESTATUS[0]}
set -e

{
  cat "$TMP"
  echo
  echo "== band summary of the exported GeoTIFF (cells with data, mean, min, max; values as stored)"
  TIF="$(ls "$DIR"/data/"$P".tif "$DIR"/data/"$P"_*.tif 2>/dev/null | head -1 || true)"
  [ -n "$TIF" ] && python - "$TIF" <<'PY'
import sys, numpy as np, rasterio
with rasterio.open(sys.argv[1]) as s:
    print(f"{s.width} x {s.height} cells, {s.count} bands, {s.crs}")
    for i, name in enumerate(s.descriptions, 1):
        a = s.read(i, masked=True).astype("float64"); a = np.ma.masked_invalid(a)
        v = a.compressed()
        print(f"{name or 'band'+str(i)}\tcells {v.size}\tmean {v.mean():.4g}\tmin {v.min():.4g}\tmax {v.max():.4g}" if v.size else f"{name}\tno data")
PY
} 2>&1 | sed "s#$ROOT#<repo>#g" > "$LOG"
rm -f "$TMP"

[ -f "$DIR/data/$P/run.json" ] && sed "s#$ROOT#<repo>#g" "$DIR/data/$P/run.json" > "$DIR/run_$P.json"
{
  lscpu | grep -m1 "Model name" || true
  free -h | head -2
  python -m pip freeze 2>/dev/null | grep -i -E "^(disscube|numpy|rasterio|rioxarray|xarray|zarr|pystac|geopandas|shapely|matplotlib)" || true
  python --version
} > "$DIR/env.txt"

echo
echo "== record in cases/$CASE: run_$P.log, run_$P.json, env.txt"
grep -E "Elapsed|Maximum resident" "$LOG" | sed 's/^\s*//'
[ -f "$DIR/run_$P.json" ] && python - "$DIR/run_$P.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1])); print("disscube", r.get("disscube"), "|", r.get("started"), "->", r.get("finished"))
PY
exit "$status"
