# F.A.R.O.L. — dados

Pipeline de dados do F.A.R.O.L. (NASA Space Apps): junta topografia, térmico e geologia de uma área de
2 km × 2 km em Jezero, Marte, numa tabela única por célula de 20 m (`mapa_risco`).

## Bases de dados usadas
- **Mars Trek** — MRO HiRISE, Jezero DEM, Controlled (1 m): https://trek.nasa.gov/mars/
- **USGS-NASA Planetary Geologic Mapping Program** — *Geologic Map of Jezero Crater and the Nili Planum Region, Mars* (SIM 3464), database: https://doi.org/10.3133/sim3464
  - inclui o mapa geológico (`Nili.gdb`), o mosaico THEMIS IR noite/dia e DTMs CTX

## Estrutura
```
farol/
├── config.py              # AOI, caminhos, projeções (mude só aqui)
├── etl/                   # Extract + Transform em Python (raster/vetor)
│   ├── inventario.py      # BRONZE: catálogo de metadados dos rasters (sem ler pixels)
│   ├── recorte_hirise.py  # recorta o DEM grande só na AOI
│   ├── grade.py           # grade mestre de 10.000 células (cell_id)
│   ├── topografia.py      # elevação, declive, rugosidade
│   ├── termico.py         # THEMIS noite/dia, amplitude, índice de firmeza
│   └── geologia.py        # unidade geológica, material escuro, distâncias
├── elt/                   # Load + Transform em SQL (DuckDB)
│   ├── carregar.py
│   └── sql/{mapa_risco.sql, resumo.sql}
├── docs/dicionario_dados.md
└── data/
    ├── raw/               # arquivos originais (não vão pro GitHub)
    └── processed/         # saídas
```

## Como rodar
1. `python -m venv .venv` e ative o ambiente
2. `pip install -r requirements.txt`
3. Descompacte o zip do SIM 3464 em `data/raw/` (pasta `sim3464_JezeroNili_FINAL`)
4. Na raiz do projeto, em ordem:
```
python -m etl.grade
python -m etl.topografia
python -m etl.termico
python -m etl.geologia
python -m elt.carregar
```

Para trocar o DEM CTX (20 m) pelo HiRISE (1 m): coloque o `.tif` em `data/raw/` e mude `DEM_ATIVO` em `config.py`.

## Orquestração (recomendado)
```
python run_pipeline.py                      # roda tudo em ordem, para no primeiro erro
python run_pipeline.py --desde etl.termico  # recomeça de uma etapa
```
Se o HiRISE estiver em `data/raw/`, a primeira etapa recorta só a AOI (~20 MB) e a topografia passa a usá-lo automaticamente.

## Resultados
- `data/processed/mapa_risco.csv` — todas as camadas por célula
- `data/processed/decisao.csv` — classe (verde / amarelo_declive / amarelo_armadilha / vermelho) + motivo
- `relatorios/perguntas.md` — respostas às perguntas de decisão (SQL em `elt/sql/perguntas.sql`)
- `relatorios/dashboard.html` — **dashboard interativo** (clique duplo para abrir no navegador)
- `docs/consultas_dbeaver.sql` — 11 consultas prontas para explorar o `data/farol.duckdb` no DBeaver
- `relatorios/mapa_decisao.png` — declive, firmeza, material escuro e decisão lado a lado

Limites de decisão (hipóteses do time) ficam em `config.py`: `DECLIVE_ATENCAO_GRAUS`, `FIRMEZA_SOLTO`, `DIST_CRATERA_ATENCAO_M`.

## Dados brutos (não vão para o GitHub)
Coloque em `data/raw/` antes de rodar:

| Arquivo | Onde baixar |
|---|---|
| `JEZ_hirise_soc_006_DTM_..._1m_...blend40.tif` (1,8 GB) | Mars Trek → busca "Jezero" → *MRO HiRISE, Jezero DEM, Controlled* → Download. O pipeline recorta sozinho para `hirise_aoi.tif`. |
| `JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif` | Mars Trek → *MRO CTX, Jezero DEM, Controlled* |
| `JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0.tif` | Mars Trek → *MRO CTX, Jezero Mosaic, Controlled* |
| pasta `sim3464_JezeroNili_FINAL/` | https://pubs.usgs.gov/sim/3464/sim3464_database.zip (descompactar) |
| `m20_waypoints_aoi.csv`, `m20_traverse_aoi.csv` | já incluídos (recorte da rota oficial NASA MMGIS) |
