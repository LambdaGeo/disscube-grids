"""Figure of the Ilha do Maranhão grid (300 m): Brazil Data Cube indices and MapBiomas land use.

    python figure_sources.py [--cube data/bdc_mapbiomas.tif] [--out ../docs/ilha_maranhao_sources.png]

Top row: Landsat NDVI and MNDWI from the Brazil Data Cube (dry season 2020), the MapBiomas land use of 2020
and the PRODES deforested share of 2024. Bottom row: urban and mangrove share in 2020 and the change in urban
share from 2000 to 2020. Bands that are missing from the file are drawn as an empty panel. The PRODES panel is
a record of the test: the island lies at the edge of the PRODES domain and the south-west block is an artefact
(see the README), so it is not a land-cover reference for the island.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
CLASSES = {3: ("Forest", "#1f6b2e"), 5: ("Mangrove", "#0d8f7a"), 6: ("Flooded forest", "#3c8d5a"),
           11: ("Wetland", "#6bc2c9"), 12: ("Grassland", "#c9d86b"), 15: ("Pasture", "#f2c14e"),
           21: ("Mosaic of uses", "#e0a45f"), 23: ("Beach, dune", "#f4e3a1"), 24: ("Urban area", "#c0392b"),
           25: ("Other non-vegetated", "#b0b0b0"), 33: ("River, lake", "#2b6cb0")}


def band(path, name):
    """Band called `name`, or the only one called `name_<time>` (variables with a time axis carry the year)."""
    with rasterio.open(path) as ds:
        names = [d or f"band{i + 1}" for i, d in enumerate(ds.descriptions)]
        if name not in names:
            cand = [n for n in names if n.startswith(name + "_")]
            if len(cand) != 1:
                return None, None
            name = cand[0]
        a = ds.read(names.index(name) + 1).astype("float64")
        if ds.nodata is not None and not np.isnan(ds.nodata):
            a[a == ds.nodata] = np.nan
        ext = (ds.bounds.left / 1e3, ds.bounds.right / 1e3, ds.bounds.bottom / 1e3, ds.bounds.top / 1e3)
    return a, ext


def panel(ax, a, ext, title, cmap, vmin, vmax, label):
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(title, fontsize=10, loc="left")
    if a is None:
        ax.set_facecolor("#f1f1f1")
        ax.text(0.5, 0.5, "band not in the file", ha="center", va="center", fontsize=9, color="#555",
                transform=ax.transAxes)
        return
    cm = plt.get_cmap(cmap).copy(); cm.set_bad("#d9d9d9")
    im = ax.imshow(np.ma.masked_invalid(a), extent=ext, cmap=cm, vmin=vmin, vmax=vmax)
    cb = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02); cb.set_label(label, fontsize=8)
    cb.ax.tick_params(labelsize=8)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cube", default=str(HERE / "data/bdc_mapbiomas.tif"))
    p.add_argument("--out", default=str(HERE.parent / "docs/ilha_maranhao_sources.png"))
    a = p.parse_args()

    ndvi, ext = band(a.cube, "ndvi_mean")
    mndwi, e2 = band(a.cube, "mndwi_mean")
    lu, e3 = band(a.cube, "landuse_2020")
    u20, _ = band(a.cube, "urban_pct_2020")
    u00, _ = band(a.cube, "urban_pct_2000")
    m20, _ = band(a.cube, "mangrove_pct_2020")
    ext = ext or e2 or e3

    fig, axs = plt.subplots(2, 4, figsize=(14.5, 7.8))
    panel(axs[0][0], ndvi, ext, "(a) BDC: NDVI, dry season 2020", "YlGn", 0, 1, "NDVI")
    panel(axs[0][1], mndwi, ext, "(b) BDC: MNDWI, dry season 2020", "Blues", -1, 1, "MNDWI")
    ax = axs[0][2]; ax.set_xticks([]); ax.set_yticks([]); ax.set_title("(c) MapBiomas: land use, 2020", fontsize=10, loc="left")
    if lu is None:
        ax.set_facecolor("#f1f1f1")
    else:
        present = [c for c in CLASSES if np.any(lu == c)]
        idx = np.full(lu.shape, np.nan)
        for i, c in enumerate(present):
            idx[lu == c] = i
        cm = ListedColormap([CLASSES[c][1] for c in present]); cm.set_bad("#d9d9d9")
        ax.imshow(np.ma.masked_invalid(idx), extent=ext, cmap=cm, vmin=-0.5, vmax=len(present) - 0.5,
                  interpolation="nearest")
        fig.legend(handles=[Patch(color=CLASSES[c][1], label=CLASSES[c][0]) for c in present], loc="lower center",
                   ncol=min(len(present), 8), fontsize=8, frameon=False)
    pdef, pe = band(a.cube, "prodes_deforested_pct_2024")
    panel(axs[0][3], pdef, pe or ext, "(d) PRODES: deforested, 2024 *", "OrRd", 0, 1, "share of the cell")
    axs[1][3].axis("off")
    axs[1][3].text(0, 0.95, "* edge of the PRODES domain:\nthe south-west block is an\nartefact, see the README.",
                   fontsize=8, va="top", color="#444", transform=axs[1][3].transAxes)
    panel(axs[1][0], u20, ext, "(e) MapBiomas: urban share, 2020", "Reds", 0, 1, "share of the cell")
    panel(axs[1][1], m20, ext, "(f) MapBiomas: mangrove share, 2020", "BuGn", 0, 1, "share of the cell")
    panel(axs[1][2], None if u20 is None or u00 is None else u20 - u00, ext,
          "(g) MapBiomas: urban change 2000-20", "RdBu_r", -1, 1, "difference")
    fig.suptitle("Ilha do Maranhão (São Luís): the same 300 m grid from open sources", fontsize=11)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=200)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
