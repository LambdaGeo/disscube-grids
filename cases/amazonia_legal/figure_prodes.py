#!/usr/bin/env python3
"""Map of the PRODES forest and accumulated deforestation shares on the Legal Amazon grid.

    python figure_prodes.py data/prodes.tif [--year 2024] [--out ../../docs/figures/amazonia_prodes.png]

Reads the GeoTIFF that `disscube run prodes.toml --output data/prodes.tif` writes (bands
prodes_forest_pct_<year> and prodes_deforested_pct_<year>).
"""
from __future__ import annotations

import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import rasterio

HERE = pathlib.Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tif", type=pathlib.Path)
    ap.add_argument("--year", default="2024")
    ap.add_argument("--out", type=pathlib.Path, default=HERE.parent.parent / "docs" / "figures" / "amazonia_prodes.png")
    a = ap.parse_args()
    with rasterio.open(a.tif) as s:
        names, tr = list(s.descriptions), s.transform
        forest = s.read(names.index(f"prodes_forest_pct_{a.year}") + 1)
        defor = s.read(names.index(f"prodes_deforested_pct_{a.year}") + 1)
        res = abs(tr.a)
    ext = [tr.c, tr.c + tr.a * forest.shape[1], tr.f + tr.e * forest.shape[0], tr.f]
    fig, ax = plt.subplots(1, 2, figsize=(11, 5.2), constrained_layout=True)
    for axis, arr, title, cmap in ((ax[0], forest, f"(a) forest, {a.year}", "Greens"),
                                   (ax[1], defor, f"(b) accumulated deforestation, {a.year}", "OrRd")):
        im = axis.imshow(arr * 100, extent=ext, cmap=cmap, vmin=0, vmax=100)
        axis.set_title(title, fontsize=10)
        axis.set_xticks([])
        axis.set_yticks([])
        fig.colorbar(im, ax=axis, shrink=0.7, label="share of the cell (%)")
    fig.suptitle(f"PRODES (TerraBrasilis) aggregated by DisSCube on a {res / 1000:g} km grid, Legal Amazon", fontsize=11)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=300)
    print("figure:", a.out)


if __name__ == "__main__":
    main()
