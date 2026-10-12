"""One figure with the open sources of the state of Pará on the 5 km grid of `sources.toml`.

    python figure_sources.py [cube.tif] [--bdc bdc_ndvi.tif] [--year 2024] [--out ../../docs/figures/para_sources.png]
                             [--state-zip FILE.zip] [--title "Pará: ..."]

(a) MapBiomas: the level-1 class that covers most of each cell (`l1_class`: Forest, Herbaceous and shrubby
vegetation, Farming, Non vegetated area, Water). (b) PRODES: the class that covers most of the cell (`prodes_class`:
Forest, Deforested up to the year, Other, Water). (c) Brazil Data Cube: MODIS NDVI, only when --bdc gives the cube of
bdc_ndvi.toml. Cells outside the state are masked with the IBGE boundary (territorial mesh 2025), downloaded once into the
DisSCube cache and checked against its SHA-256; --state-zip gives a local copy instead.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from rasterio.features import rasterize

HERE = Path(__file__).resolve().parent
LEVEL1 = {1: ("Forest", "#1f6b2e"), 2: ("Herbaceous and shrubby vegetation", "#c9d86b"), 3: ("Farming", "#f2c14e"),
          4: ("Non vegetated area", "#b0524a"), 5: ("Water", "#2b6cb0")}
PRODES = {1: ("Forest", LEVEL1[1][1]), 2: ("Deforested up to the year", "#f0d800"),   # same green as MapBiomas forest
          3: ("Other (non-forest vegetation)", "#c9c9c9"),
          4: ("Water (hydrography)", LEVEL1[5][1])}     # class 4 needs `water = 4` in [source.codes] of sources.toml; clouds are no data


def band(ds, name):
    names = [d or f"band{i + 1}" for i, d in enumerate(ds.descriptions)]
    if name not in names:                     # variables with a time axis carry the year: name_<year>
        cand = [n for n in names if n.startswith(name + "_")]
        if len(cand) != 1:
            return None
        name = cand[0]
    a = ds.read(names.index(name) + 1).astype("float64")
    if ds.nodata is not None and not np.isnan(ds.nodata):
        a[a == ds.nodata] = np.nan
    return a


STATE_URL = ("https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/"
             "municipio_2025/UFs/PA/PA_UF_2025.zip")
STATE_SHA256 = "f01247e31debb8a11bada4d22cdfaf621cacc7a0f80f9248cc4865719bad622c"


def state_boundary(local=None):
    """The IBGE boundary of Pará: a local file, or the download kept in the DisSCube cache (verified by hash)."""
    if local:
        return local
    import os

    import pooch
    root = os.environ.get("DISSCUBE_CACHE_DIR") or os.environ.get("DISSCUBE_CACHE")
    cache = Path(root) / "raw" if root else Path(pooch.os_cache("disscube")) / "raw"
    return pooch.retrieve(STATE_URL, known_hash=f"sha256:{STATE_SHA256}", fname="PA_UF_2025.zip", path=cache)


def load(path, name, state_zip):
    import geopandas as gpd
    with rasterio.open(path) as ds:
        g = gpd.read_file(f"zip://{state_zip}").to_crs(ds.crs)
        inside = rasterize(g.geometry, out_shape=ds.shape, transform=ds.transform, fill=0, default_value=1,
                           all_touched=True).astype(bool)
        arr = band(ds, name)
        ext = (ds.bounds.left / 1e3, ds.bounds.right / 1e3, ds.bounds.bottom / 1e3, ds.bounds.top / 1e3)
    return arr, inside, ext


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cube", nargs="?", default=str(HERE / "data" / "sources.tif"))
    ap.add_argument("--bdc", default=None, help="GeoTIFF of bdc_ndvi.toml (adds the NDVI panel)")
    ap.add_argument("--year", default="2024")
    ap.add_argument("--out", default=str(HERE.parent.parent / "docs" / "figures" / "para_sources.png"))
    ap.add_argument("--state-zip", default=None, help="a local copy of the state boundary (IBGE shapefile in a zip); default: download it")
    ap.add_argument("--title", default=None, help="title above the panels (none by default: the caption of the article says it)")
    a = ap.parse_args()
    a.state_zip = state_boundary(a.state_zip)

    l1, inside, ext = load(a.cube, f"l1_class_{a.year}", a.state_zip)
    pr, _, _ = load(a.cube, f"prodes_class_{a.year}", a.state_zip)
    if l1 is None:
        raise SystemExit(f"no band l1_class_{a.year} in {a.cube}")
    nd = load(a.bdc, "ndvi_mean", a.state_zip)[0] if a.bdc else None

    n = 2 + (nd is not None)
    aspect = (ext[3] - ext[2]) / (ext[1] - ext[0])             # map height / width, so the panels fit the state
    pw = 5.4
    fig, axes = plt.subplots(1, n, figsize=(pw * n, pw * aspect + 1.3), constrained_layout=True)
    axes = np.atleast_1d(axes)
    for ax in axes:
        ax.set_xticks([]); ax.set_yticks([]); ax.set_facecolor("white")

    cmap = ListedColormap([c for _, c in LEVEL1.values()])
    axes[0].imshow(np.where(inside, l1, np.nan), extent=ext, cmap=cmap, norm=BoundaryNorm(np.arange(0.5, 6.5), cmap.N),
                   interpolation="nearest")
    axes[0].set_title(f"(a) MapBiomas land use, {a.year}", fontsize=11, loc="left")
    axes[0].legend(handles=[Patch(color=c, label=nm) for nm, c in LEVEL1.values()], loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, fontsize=8,
                   title="MapBiomas level 1 (class covering most of the cell)", title_fontsize=8, frameon=False)

    pcmap = ListedColormap([c for _, c in PRODES.values()])
    axes[1].imshow(np.where(inside, pr, np.nan), extent=ext, cmap=pcmap, norm=BoundaryNorm(np.arange(0.5, 5.5), pcmap.N),
                   interpolation="nearest")
    axes[1].set_title(f"(b) PRODES, {a.year}", fontsize=11, loc="left")
    axes[1].legend(handles=[Patch(color=c, label=nm) for nm, c in PRODES.values()], loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, fontsize=8,
                   title="PRODES (class covering most of the cell)", title_fontsize=8, frameon=False)

    if nd is not None:
        im = axes[2].imshow(np.where(inside, nd, np.nan), extent=ext, cmap="YlGn", vmin=0, vmax=1, interpolation="nearest")
        fig.colorbar(im, ax=axes[2], shrink=0.6, label="NDVI (mean of the dry-season composite)")
        axes[2].set_title("(c) Brazil Data Cube, MODIS NDVI, dry season 2020", fontsize=11, loc="left")

    # scale bar: about a quarter of the width, rounded to 1, 2 or 5 x 10^k km (the extent is in km, in the grid CRS)
    width, height = ext[1] - ext[0], ext[3] - ext[2]
    raw = width / 4
    mag = 10 ** np.floor(np.log10(raw))
    km = next(m * mag for m in (5, 2, 1) if m * mag <= raw)
    x0, y0 = ext[0] + 0.04 * width, ext[2] + 0.05 * height
    axes[0].plot([x0, x0 + km], [y0, y0], color="black", lw=2, solid_capstyle="butt")
    axes[0].text(x0 + km / 2, y0 + 0.012 * height, f"{km:g} km", ha="center", va="bottom", fontsize=8)
    for ax in axes:
        ax.set_xlim(ext[0], ext[1])
        ax.set_ylim(ext[2], ext[3])
    if a.title:
        fig.suptitle(a.title, fontsize=12)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=300, bbox_inches="tight")
    share = {LEVEL1[k][0]: float(np.mean(l1[inside & ~np.isnan(l1)] == k)) for k in LEVEL1}
    print("figure:", a.out, "| share of the cells by class:", {k: round(v, 3) for k, v in share.items()})


if __name__ == "__main__":
    main()
