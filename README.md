# disscube-grids

How to build gridded variables ("cellular spaces") from open data with
[DisSCube](https://github.com/DisSModel/disscube): one study area per folder, one TOML file per
grid, a few lines of shell to run it, and the maps it produces.

The point is the **grid construction**: each pipeline file states the grid (snapped to the
[Brazil Data Cube](https://brazil-data-cube.github.io/) Albers mesh), the sources and how each
variable is derived. There is no case-specific code; the only shared script is
`common/plot_cube.py`, which draws the maps.

| Area | Pipeline | Sources | Grid | Status |
|---|---|---|---|---|
| `ilha_maranhao/` | `bdc_mapbiomas.toml` | BDC Landsat indices (STAC), MapBiomas, PRODES | 300 m, 58 × 59 cells | MapBiomas half **ran here** (10 Oct 2026, DisSCube 0.5.0); BDC half not run (STAC unreachable from the build machine) |
| `br163/` | `prodes.toml` | PRODES (Legal Amazon) | 500 m, 94 × 86 cells | **ran here** (10 Oct 2026, DisSCube 0.5.0) |
| `br163/` | `bdc_mapbiomas.toml` | BDC Landsat NDVI (STAC), MapBiomas | same | MapBiomas half **ran here** (11 Oct 2026, DisSCube 0.5.0); BDC half: to run (needs access to the BDC STAC service) |
| `brasil_5km/` | `build_mapbiomas_cellspace.py` | MapBiomas (collection 11, 30 m) | 5.28 km, 900 × 1,040 cells | in progress; needs a tile loop |

## First results (Ilha do Maranhão, 10 Oct 2026)

MapBiomas (collection 11) on the 300 m BDC-snapped grid: 3,083 of 3,422 cells have data; urban share
41.4 % (2000) → 47.5 % (2020), forest 22.8 % → 19.4 %, mangrove 4.1 % → 4.5 %, the same figures
as the earlier run in `disscube-recipes`. It takes about 6 s after the download.
![MapBiomas on the island](docs/ilha_maranhao_mapbiomas.png)

`ilha_maranhao/figure_sources.py` draws the island with the BDC indices (NDVI and MNDWI, when `bdc_mapbiomas.toml` has been
run) and the MapBiomas land use, urban and mangrove shares and the urban change from 2000 to 2020
(`python figure_sources.py` in `ilha_maranhao/`; the PRODES maps are left out, see below).

PRODES (edition `prodes_amazonia_legal_2025_v20260408`) returns data in 2,897 of the 3,422 cells,
so the island is inside its domain. **It is not a good demonstration**: the south-west shows a
straight-edged block that is entirely "deforested" in every year, which looks like an artefact of
the PRODES domain edge (the island lies at the limit of the Legal Amazon) and not like land cover.
The PRODES source is kept in `bdc_mapbiomas.toml` (variables prefixed `prodes_`) as the record of this test, so the island is
built from three sources in one file; PRODES is shown as a useful map on `br163/` instead.
![PRODES on the island](docs/ilha_maranhao_prodes.png)

PRODES on the BR-163 near Mojuí dos Campos (500 m grid, 94 × 86 cells, 7,997 of 8,084 cells with data,
about 5 s after the download): deforested share 18.1 % (2008) → 20.1 % (2016) → 20.5 % (2024); forest
81.6 % → 79.5 % → 79.2 %. The maps show the fishbone pattern of the road's side roads.
![PRODES on the BR-163](docs/br163_prodes.png)

### Three sources on one grid (BR-163)

`br163/bdc_mapbiomas.toml` uses the same area and 500 m grid as `br163/prodes.toml` (the LuccME Lab15 cellular
space), so that the Brazil Data Cube (Landsat NDVI, dry season 2020), MapBiomas (collection 11) and PRODES can be read
cell by cell. `br163/figure_sources.py` draws them together (forest share from MapBiomas and from PRODES, pasture and
deforested share, and the difference between the two forest shares). It is an illustration of how the same declarative
file starts from different open sources, not a validation: the sources define forest differently and are not expected to
agree cell by cell. The BDC panel stays empty until `bdc_mapbiomas.toml` has been run.
![The three sources on the BR-163](docs/br163_sources.png)

Two things found while running, both in DisSCube 0.5.0: `disscube export` as a separate command
looks the grid up by its name (`ilha_do_maranhao`) while the cube stores `ilha_do_maranhao/300m`, and
fails; `run --output` exports correctly, which is what `run.sh` uses. And the process ends with an
`Error in sys.excepthook` message after the work is done (output is complete).

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ilha_maranhao && ./run.sh all            # validate, run (network), export GeoTIFF, plot
cd ../br163 && ./run.sh run prodes && ./run.sh run bdc_mapbiomas && python figure_sources.py   # three sources on one grid
./run.sh validate bdc_mapbiomas             # any step, any pipeline of the folder
```

Maps are written to `<area>/images/<pipeline>/` (git-ignored; the ones shown in this README are
copied to `docs/`).

## What each area tests

- **Sources with different geometry on one grid:** BDC composites (raster, STAC), MapBiomas
  (30 m classes), PRODES (Legal Amazon only, years from 2007).
- **Cost:** `brasil_5km` is the large case. DisSCube 0.5.0 reads the whole window of a MapBiomas
  source into memory, which does not fit over Brazil at 30 m, so the script runs the same pipeline
  tile by tile (BDC_SM tiles of 105.6 km, 20 × 20 cells of 5.28 km). Moving this into DisSCube would
  leave only TOML here.

## Notes

- Data are fetched from the providers when a case runs; the repository holds text and a few images.
  Check each provider's terms before reusing the data.
- BDC and PRODES results depend on the catalog contents and on the PRODES edition when the case is
  run; each run records them in `run.json` and in `*.provenance.json`.
- Code and configuration: MIT.
