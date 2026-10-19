# Data sources, licences and how to cite them

This repository holds **no third-party data**: only pipeline files (TOML), scripts, run records and a few figures.
The data are fetched from the provider when a case runs, and each run records the catalogue and edition it
used (`run.json`, `*.provenance.json`). The licences below are those the providers state; they were read on
13 Oct 2026. Items marked `[A CONFIRMAR]` were not confirmed from the provider's own page.

| Source | Used in | Licence stated by the provider | Credit requested |
|---|---|---|---|
| **MapBiomas**, collection 11 | `ilha_maranhao`, `br163`, `para`, `brasil_5km` | CC BY 4.0 ([brasil.mapbiomas.org](https://brasil.mapbiomas.org/en/wp-json/wp/v2/pages/779)) | "MapBiomas – Collection 11 of the Annual Series of Land Use and Land Cover Maps of Brazil", with access date and link |
| **PRODES** (INPE), Legal Amazon edition `prodes_amazonia_legal_2025_v20260408` | `amazonia_legal`, `br163`, `ilha_maranhao`, `para` | CC BY-SA 4.0 (TerraBrasilis [licence page](https://www.terrabrasilis.dpi.inpe.br/?p=1216); INPE catalogue record of PRODES Cerrado; checked for the Legal Amazon on the TerraBrasilis page of the programme) | Assis, L. F. F. G. et al. (2019), TerraBrasilis, *ISPRS Int. J. Geo-Inf.* 8, 513, doi:10.3390/ijgi8110513; and the "Como citar" of the PRODES page |
| **MODIS MOD13Q1 v061** (NASA), as the BDC COG collection `mod13q1-6.1` | `para` (`bdc_ndvi.toml`) | "proprietary" in the STAC; it links to the NASA LAADS Data Use and Citation Policy: no restriction on use or redistribution, acknowledgement and citation requested | Didan, K. (2021). MOD13Q1 MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061. NASA EOSDIS Land Processes DAAC. doi:10.5067/MODIS/MOD13Q1.061 `[A CONFIRMAR o DOI]`; plus a note that it was read through the Brazil Data Cube (INPE) |
| **Brazil Data Cube**, Landsat (`LANDSAT-16D-1`) | `ilha_maranhao`, `br163` (`bdc_mapbiomas.toml`; run on 14 Oct 2026, only numbers derived from it are published, no figure) | CC BY-NC 3.0 Unported, no adaptations ([BDC page](https://data.inpe.br/bdc/?p=9167)) | Ferreira, K. R. et al. (2020), *Remote Sensing* 12(24), 4033, "Earth Observation Data Cubes for Brazil: Requirements, Methodology and Products", doi:10.3390/rs12244033 |
| **IBGE**, municipal seats (`GEOFT_CIDADE_2016`, BC250 2016), through the ANA metadata catalogue | `para` (`seats.toml`) | The ANA record says "access is free"; no IBGE licence or terms of use found `[A CONFIRMAR]` | "Fonte: IBGE, Bases cartográficas contínuas, BC250, 2016, via catálogo de metadados da ANA" |
| **IBGE**, country outline (`BR_Pais_2025`, `malhas_territoriais`) | figures and masks | No licence stated on the mesh documentation (the "Leia-me" only says the mesh is not official); IBGE products under its own terms of use (for BC250: copyright IBGE, no sale, credit required) `[A CONFIRMAR para a malha]` | "Fonte: IBGE, Malhas territoriais, edição 2025" |

The Brazil Data Cube **grid** (Albers mesh and the tile size) is used as a reference; no BDC data is stored.

## Figures

The images in `docs/figures/` are maps made from the data above. The code that draws them is MIT; the
images are adaptations of the data and follow the licence of their most restrictive source:

- `brasil_mapbiomas.png`: MapBiomas, CC BY 4.0.
- `amazonia_prodes.png`: PRODES, CC BY-SA 4.0 (credit INPE / PRODES; share alike).
- `ilha_maranhao_mapbiomas.png`: MapBiomas, CC BY 4.0.
- `br163_prodes.png`: PRODES, CC BY-SA 4.0 (credit INPE / PRODES; share alike).
- `para_sources.png`: MapBiomas, PRODES, MODIS NDVI and, when drawn with `--seats`, the distance to the municipal seats (IBGE, licence not confirmed, see the table), so CC BY-SA 4.0 for the first three; a figure with the fourth panel keeps the credit to IBGE and the ANA catalogue.

Reuse of a figure must keep the credit to the providers. A figure that shows only Landsat from the BDC would
fall under CC BY-NC 3.0 without adaptations; none is included.
