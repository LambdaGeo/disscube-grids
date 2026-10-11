"""Plot every band of a DisSCube GeoTIFF export as a PNG (the only script the cases share).

    python plot_cube.py cube.tif out_dir

One image per band, named after the band description, plus a contact sheet (all.png).
Fractions (0-1) use a sequential scale; other bands use the data range. NaN is drawn grey.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio


def main(tif, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    with rasterio.open(tif) as ds:
        names = [d or f"band{i+1}" for i, d in enumerate(ds.descriptions)]
        data = ds.read().astype("float64")
        if ds.nodata is not None and not np.isnan(ds.nodata):
            data[data == ds.nodata] = np.nan
        ext = (ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top)
    cmap = plt.get_cmap("viridis").copy(); cmap.set_bad("#d9d9d9")
    n = len(names); cols = min(4, n); rows = -(-n // cols)
    sheet, axs = plt.subplots(rows, cols, figsize=(3.2 * cols, 3.0 * rows), squeeze=False)
    for i, name in enumerate(names):
        a = data[i]
        if not np.isfinite(a).any():
            continue
        lo, hi = np.nanmin(a), np.nanmax(a)
        for ax, size in ((axs[i // cols][i % cols], None), (None, (5, 4.5))):
            if ax is None:
                fig, ax = plt.subplots(figsize=size)
            im = ax.imshow(np.ma.masked_invalid(a), extent=ext, cmap=cmap, vmin=lo, vmax=hi)
            ax.set_title(f"{name}  [{lo:.3g}, {hi:.3g}]", fontsize=8); ax.set_xticks([]); ax.set_yticks([])
            if size:
                fig.colorbar(im, ax=ax, shrink=0.8); fig.tight_layout()
                fig.savefig(out / f"{name}.png", dpi=150); plt.close(fig)
    for j in range(n, rows * cols):
        axs[j // cols][j % cols].axis("off")
    sheet.tight_layout(); sheet.savefig(out / "all.png", dpi=130)
    print(f"{n} bands -> {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
