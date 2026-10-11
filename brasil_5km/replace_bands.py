#!/usr/bin/env python3
"""Put the land-use bands of a DisSCube output into a cell space, keeping its drivers and its mask.

    python replace_bands.py --base data/raw_cellspace_bdc_5k.tif --bands data/mapbiomas_5k.tif \
        --out data/raw_cellspace_bdc_5k_mapbiomas.tif

--bands is the GeoTIFF of `disscube run mapbiomas.toml` (bands <class>_<year>); every band of --base whose name is
<class> gets the values of <class>_<year>. Both rasters must be on the same grid.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np
import rasterio


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, type=pathlib.Path)
    ap.add_argument("--bands", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    a = ap.parse_args()
    with rasterio.open(a.base) as s:
        profile, names, data, tr, shape = s.profile, list(s.descriptions), s.read().astype("float32"), s.transform, s.shape
    with rasterio.open(a.bands) as s:
        if s.shape != shape or not np.allclose(tuple(s.transform)[:6], tuple(tr)[:6]):
            sys.exit("the two rasters are not on the same grid")
        new = {(d or "").rsplit("_", 1)[0]: s.read(i + 1) for i, d in enumerate(s.descriptions)}
    done = []
    for i, n in enumerate(names):
        if n in new:
            data[i] = new[n]
            done.append(n)
    if not done:
        sys.exit(f"no band of {a.bands.name} matches a band of {a.base.name}")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    profile.update(count=data.shape[0], dtype="float32")
    with rasterio.open(a.out, "w", **profile) as d:
        d.write(data)
        d.descriptions = tuple(names)
    print("replaced:", ", ".join(done))


if __name__ == "__main__":
    main()
