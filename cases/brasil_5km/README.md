# Test with another land-use source: MapBiomas (grid only, not part of the main result)

> **Status in this repository.** The 5.28 km grid and the seven land-use shares are one TOML here, `mapbiomas.toml`. The drivers and the
> mask of the input raster still come from the open-lucc-workflow pipeline (`data/raw_cellspace_bdc_5k.tif`); `replace_bands.py` puts the
> land-use bands of the DisSCube output into it. The whole country ran on 12 Oct 2026 (see "The whole country").

The main runs of the [open-lucc-workflow](https://github.com/LambdaGeo/open-lucc-workflow) use the land-cover layer of the LuccME-BR database (NetCDF, pixels of about
100 km²). At 5.28 km the land-use bands therefore carry no information finer than that source. This test builds the
5.28 km grid with MapBiomas (collection 11, 30 m, CC-BY-4.0, year 2000, the year of the main layer) instead,
to exercise the ingestion of another open source at national scale and to measure its cost. **It generates the
grid only. The model is not run on it and no result of the open-lucc-workflow depends on it.**

## Why it needs a DisSCube that reads by blocks

MapBiomas at 30 m over Brazil is 22.6 billion pixels (154,470 × 146,501; about 90 GB as float32). DisSCube 0.5.0 reads the whole window of a
source into memory, so it does not fit; the first version of this test ran DisSCube tile by tile from a script. With DisSCube 0.6.0 ([DisSModel/disscube](https://github.com/DisSModel/disscube)) one `disscube run` reads, aligns and aggregates by strips of grid rows, and the script is gone. The grid is the BDC_SM mesh in
tiles of 105.6 km (45 × 52 = 2,340 tiles of 20 × 20 cells, 900 × 1,040 cells).

## Steps

```bash
pip install -r requirements.txt            # DisSCube 0.6.0
disscube validate mapbiomas.toml
disscube run mapbiomas.toml --workspace data/mapbiomas --output data/mapbiomas_5k.tif     # network
# a quick try on two tiles of Pará: bbox = [5280000.0, 10771200.0, 5491200.0, 10876800.0] in a copy of the file
# then, with the input raster of the main run:
python replace_bands.py --base data/raw_cellspace_bdc_5k.tif --bands data/mapbiomas_5k.tif \
    --out data/raw_cellspace_bdc_5k_mapbiomas.tif
python scripts/complete_cellspace.py data/raw_cellspace_bdc_5k_mapbiomas.tif data/cellspace_bdc_5k_mapbiomas.tif
python scripts/check_cellspace.py data/cellspace_bdc_5k_mapbiomas.tif
```

`disscube run` writes `data/mapbiomas/run.json` (sources, derived variables, hashes). Each of the seven classes is one derivation, and
each one reads and aligns the source again: the whole country took 1 h 43 min 55 s (seven passes over 22.6 billion pixels, see below).

## Choices that are ours

- The correspondence between MapBiomas codes and the seven classes is declared in
  `mapbiomas.toml` (`class_code` lists; `crosswalk.toml` has the same lists). It is not the one of LuccME-BR, and the legend of
  collection 11 must be checked ([TO CONFIRM] in the file).
- `others` lists every other code of the legend (10, 14, 22–27, 29–33, 49, 50, 75, 91), so the seven shares add to 1; code 0 (not
  observed) is nodata, and a cell with no observed pixel is left empty and removed by `complete_cellspace.py`, as in the main input raster.
- The drivers and the mask are those of the base input raster.

## Pilot on the published files (author's machine, 10 Oct 2026)

Two tiles in Pará (25,10 and 26,10; 400 cells of the mask each): 29.1 s and 31.8 s per tile, peak memory 521 MB
(process tree), windows of 3551 x 3553 pixels, no pixel without data, shares summing to 1 in all 800 cells. The
process used about 54% of one CPU, so the time is dominated by the network. Sequentially, 865 tiles at this rate
would take about 7 hours; `--jobs` runs tiles at the same time.

## What was tested here

On the two tiles of the pilot (25,10 and 26,10, real MapBiomas 2000) the single TOML and the tile script agree: same cells, same empty
cells, shares add to 1 in all 800 cells, largest difference 0.24 % of a cell (the edge of the strips and tiles). The TOML took 11 s for the
two tiles, the script 44 s; `replace_bands.py` on a base input raster gives the same file as the script. Not yet done here: the class codes against the legend of collection 11 and the comparison of class areas with the NetCDF layer (the whole country is below).

## The whole country (12 Oct 2026)

`./run.sh run` with DisSCube at commit `f2feb95` (the code that became 0.6.0), on one CPU core (Intel Core i7-7700T, 15 GiB of RAM): 1 h 43 min 55 s, peak memory 3.9 GB,
seven passes over the source, one per class. Window 154,470 × 146,501 pixels (22,630,009,470), grid `brasil_5km` of 900 × 1,040 cells. Hashes: pipeline `2cf54bc8…380fdc`,
source `lulc_2000.tif` `ad6f0a6a…c2ad2f`, output `mapbiomas_5k.tif` `3d7ef2f6…92ff72` (the full values are in `data/mapbiomas/run.json`). `./run.sh plot` draws four of the seven classes
(`docs/figures/brasil_mapbiomas.png`). The class codes against the legend of collection 11 and the comparison of class areas with the NetCDF layer are still not done.
