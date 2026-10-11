"""Figure of the three open sources on the same 500 m grid (BR-163, Pará).

    python figure_sources.py [--bdc data/bdc_mapbiomas.tif] [--mapbiomas data/bdc_mapbiomas.tif]
                             [--prodes data/prodes.tif] [--out ../docs/br163_sources.png]

Top row: Landsat NDVI from the Brazil Data Cube (dry season 2020), the forest share from MapBiomas
and from PRODES at the end of 2024. Bottom row: pasture (MapBiomas) and deforested share (PRODES) in
2024, and the difference between the two forest shares. The BDC panel is left empty when the file
has no `ndvi_mean` band (run the pipeline `bdc_mapbiomas.toml` for it). Illustration only: the three
sources use different definitions of forest, so the maps are not expected to agree cell by cell.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio

HERE = Path(__file__).resolve().parent


def band(path, name):
    with rasterio.open(path) as ds:
        names = [d or f"band{i + 1}" for i, d in enumerate(ds.descriptions)]
        if name not in names:                      # variables without a year are exported as <name>_<time>
            names_t = [n for n in names if n.startswith(name + "_")]
            if len(names_t) != 1:
                return None, None
            name = names_t[0]
        a = ds.read(names.index(name) + 1).astype("float64")
        if ds.nodata is not None and not np.isnan(ds.nodata):
            a[a == ds.nodata] = np.nan
        ext = (ds.bounds.left / 1e3, ds.bounds.right / 1e3, ds.bounds.bottom / 1e3, ds.bounds.top / 1e3)
    return a, ext


def panel(ax, a, ext, title, cmap, vmin, vmax, label):
    cm = plt.get_cmap(cmap).copy(); cm.set_bad("#d9d9d9")
    if a is None:
        ax.text(0.5, 0.5, "not run\n(bdc_mapbiomas.toml)", ha="center", va="center", fontsize=9,
                color="#555", transform=ax.transAxes)
        ax.set_facecolor("#f1f1f1")
        ax.set_xticks([]); ax.set_yticks([]); ax.set_title(title, fontsize=10, loc="left")
        return
    im = ax.imshow(np.ma.masked_invalid(a), extent=ext, cmap=cm, vmin=vmin, vmax=vmax)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(title, fontsize=10, loc="left")
    cb = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02); cb.set_label(label, fontsize=8)
    cb.ax.tick_params(labelsize=8)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bdc", default=str(HERE / "data/bdc_mapbiomas.tif"))
    p.add_argument("--mapbiomas", default=str(HERE / "data/bdc_mapbiomas.tif"))
    p.add_argument("--prodes", default=str(HERE / "data/prodes.tif"))
    p.add_argument("--out", default=str(HERE.parent / "docs/br163_sources.png"))
    a = p.parse_args()

    ndvi = ndvi_ext = None
    if Path(a.bdc).exists():
        ndvi, ndvi_ext = band(a.bdc, "ndvi_mean")
    mbf, ext = band(a.mapbiomas, "forest_pct_2024")
    mbp, _ = band(a.mapbiomas, "pasture_pct_2024")
    pf, pext = band(a.prodes, "forest_pct_2024")
    pd_, _ = band(a.prodes, "deforested_pct_2024")
    ext = ext or pext

    fig, axs = plt.subplots(2, 3, figsize=(11, 7.4))
    panel(axs[0][0], ndvi, ndvi_ext or ext, "(a) Brazil Data Cube: NDVI, dry season 2020", "YlGn", 0, 1, "NDVI")
    panel(axs[0][1], mbf, ext, "(b) MapBiomas: forest share, 2024", "Greens", 0, 1, "share of the cell")
    panel(axs[0][2], pf, ext, "(c) PRODES: forest share, end of 2024", "Greens", 0, 1, "share of the cell")
    panel(axs[1][0], mbp, ext, "(d) MapBiomas: pasture share, 2024", "YlOrBr", 0, 1, "share of the cell")
    panel(axs[1][1], pd_, ext, "(e) PRODES: deforested share, 2024", "OrRd", 0, 1, "share of the cell")
    if mbf is not None and pf is not None:
        diff = mbf - pf
        panel(axs[1][2], diff, ext, "(f) forest share: MapBiomas minus PRODES", "RdBu", -1, 1, "difference")
        ok = np.isfinite(diff)
        print(f"cells with both: {ok.sum()}; mean difference {np.nanmean(diff):+.3f}; "
              f"|diff| < 0.1 in {np.mean(np.abs(diff[ok]) < 0.1) * 100:.1f}% of the cells")
    fig.suptitle("The same 500 m grid built from three open sources (BR-163, Mojuí dos Campos, Pará)", fontsize=11)
    fig.tight_layout()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=200)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
