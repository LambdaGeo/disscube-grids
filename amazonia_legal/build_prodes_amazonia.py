#!/usr/bin/env python3
"""PRODES over the whole Legal Amazon on a 5.28 km grid, one 105.6 km tile at a time, and the map.

DisSCube 0.5.0 reads the whole window of a source into memory, and the PRODES raster of the Legal Amazon has
9.7 billion pixels, so one `disscube run` over the region does not fit. This script writes prodes_tile.toml for
each tile (only the bbox changes), runs DisSCube, and joins the tiles in one GeoTIFF with the same bands the
TOML would give (prodes_deforested_pct_<year>, prodes_forest_pct_<year>). Then it draws the map.

    python build_prodes_amazonia.py --workdir data --jobs 2          # about 7 s per tile; ~800 tiles
    python build_prodes_amazonia.py --workdir data --resume          # continue an interrupted run
    python build_prodes_amazonia.py --workdir data --tiles "10,12;11,12"   # a few tiles, to try
    python build_prodes_amazonia.py --workdir data --figure-only     # map from data/amazonia_prodes_5k.tif

The first run downloads the PRODES edition (about 130 MB) from TerraBrasilis into the DisSCube cache.
"""
from __future__ import annotations

import argparse, concurrent.futures as cf, json, pathlib, re, shutil, subprocess, sys, time

import numpy as np
import rasterio
from rasterio.transform import from_origin

HERE = pathlib.Path(__file__).resolve().parent
TILE_M, RES = 105600.0, 5280.0
PER = round(TILE_M / RES)                      # 20 cells per side
CRS = "EPSG:10857"
# Legal Amazon (PRODES domain), WGS84 envelope; tiles with no data come out empty and are dropped from the map
LON0, LON1, LAT0, LAT1 = -74.0, -43.9, -18.1, 5.4


def extent():
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    xs, ys = [], []
    for lon in np.linspace(LON0, LON1, 25):
        for lat in np.linspace(LAT0, LAT1, 25):
            x, y = t.transform(lon, lat); xs.append(x); ys.append(y)
    x0 = np.floor(min(xs) / TILE_M) * TILE_M; y1 = np.ceil(max(ys) / TILE_M) * TILE_M
    x1 = np.ceil(max(xs) / TILE_M) * TILE_M;  y0 = np.floor(min(ys) / TILE_M) * TILE_M
    return x0, y0, x1, y1


def tile_toml(template: str, bbox) -> str:
    return re.sub(r"bbox = \[.*?\]", "bbox = [" + ", ".join(repr(float(v)) for v in bbox) + "]", template, count=1)


def figure(tif: pathlib.Path, png: pathlib.Path, year: str) -> None:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with rasterio.open(tif) as s:
        names = list(s.descriptions); tr = s.transform
        d = s.read(names.index(f"prodes_deforested_pct_{year}") + 1)
        f = s.read(names.index(f"prodes_forest_pct_{year}") + 1)
    ext = [tr.c, tr.c + tr.a * d.shape[1], tr.f + tr.e * d.shape[0], tr.f]
    fig, ax = plt.subplots(1, 2, figsize=(11, 5.2), constrained_layout=True)
    for a, arr, title, cmap in ((ax[0], f, f"(a) forest, {year}", "Greens"), (ax[1], d, f"(b) accumulated deforestation, {year}", "OrRd")):
        im = a.imshow(np.where(arr > 0, arr * 100, np.nan) if False else arr * 100, extent=ext, cmap=cmap, vmin=0, vmax=100)
        a.set_title(title, fontsize=10); a.set_xticks([]); a.set_yticks([])
        fig.colorbar(im, ax=a, shrink=0.7, label="share of the cell (%)")
    fig.suptitle("PRODES (TerraBrasilis) aggregated by DisSCube on a 5.28 km grid, Legal Amazon", fontsize=11)
    fig.savefig(png, dpi=300); print("figure:", png)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", type=pathlib.Path, default=HERE / "data")
    ap.add_argument("--toml", type=pathlib.Path, default=HERE / "prodes_tile.toml")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--tiles", default=None, help='"col,row;col,row" (row counted from the top)')
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--figure-only", action="store_true")
    ap.add_argument("--year", default="2024")
    a = ap.parse_args()
    out_tif, png = a.workdir / "amazonia_prodes_5k.tif", HERE.parent / "docs" / "amazonia_prodes.png"
    if a.figure_only:
        png.parent.mkdir(exist_ok=True); figure(out_tif, png, a.year); return

    x0, y0, x1, y1 = extent()
    ncol, nrow = int(round((x1 - x0) / TILE_M)), int(round((y1 - y0) / TILE_M))
    ids = [(c, r) for r in range(nrow) for c in range(ncol)]
    if a.tiles:
        want = {tuple(int(v) for v in t.split(",")) for t in a.tiles.split(";")}
        ids = [t for t in ids if t in want]
    template = a.toml.read_text(encoding="utf-8")
    a.workdir.mkdir(parents=True, exist_ok=True)
    print(f"{len(ids)} tiles ({ncol} x {nrow} in the envelope)", flush=True)

    def run(tid):
        c, r = tid; wd = a.workdir / f"tile_{c}_{r}"; tif = wd / "tile.tif"
        if a.resume and tif.exists():
            return tid, 0.0, ""
        if wd.exists(): shutil.rmtree(wd)
        wd.mkdir()
        bbox = (x0 + c * TILE_M, y1 - (r + 1) * TILE_M, x0 + (c + 1) * TILE_M, y1 - r * TILE_M)
        (wd / "tile.toml").write_text(tile_toml(template, bbox), encoding="utf-8")
        t0 = time.perf_counter()
        p = subprocess.run(["disscube", "run", str(wd / "tile.toml"), "--workspace", str(wd / "ws"), "--output", str(tif)],
                           capture_output=True, text=True)
        err = (p.stdout + p.stderr)[-800:] if p.returncode else ""
        shutil.rmtree(wd / "ws", ignore_errors=True)
        return tid, time.perf_counter() - t0, err

    names, arr, report, failed = None, None, [], []
    H, W = nrow * PER, ncol * PER
    t_all = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        for n, (tid, dt, err) in enumerate(ex.map(run, ids), 1):
            c, r = tid
            if err:
                failed.append(tid); print(f"tile {c},{r} failed:\n{err}", file=sys.stderr); continue
            with rasterio.open(a.workdir / f"tile_{c}_{r}" / "tile.tif") as t:
                if names is None:
                    names = list(t.descriptions); arr = np.full((len(names), H, W), np.nan, "float32")
                arr[:, r * PER:(r + 1) * PER, c * PER:(c + 1) * PER] = t.read()
            report.append({"tile": [c, r], "seconds": round(dt, 1)})
            if n % 20 == 0 or n == len(ids):
                print(f"[{n}/{len(ids)}] {time.perf_counter() - t_all:.0f} s", flush=True)
    if arr is None:
        sys.exit("no tile finished")
    prof = dict(driver="GTiff", height=H, width=W, count=len(names), dtype="float32", crs=CRS,
                transform=from_origin(x0, y1, RES, RES), compress="deflate", nodata=float("nan"))
    with rasterio.open(out_tif, "w", **prof) as d:
        d.write(arr); d.descriptions = tuple(names)
    (a.workdir / "build_report.json").write_text(json.dumps(
        {"toml": str(a.toml), "tiles": len(ids), "failed": failed, "wall_seconds": round(time.perf_counter() - t_all, 1),
         "bands": names, "per_tile": report}, indent=2), encoding="utf-8")
    print("wrote", out_tif, "| failed tiles:", failed or "none")
    png.parent.mkdir(exist_ok=True); figure(out_tif, png, a.year)


if __name__ == "__main__":
    main()
