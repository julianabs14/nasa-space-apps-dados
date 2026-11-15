"""
Configuração central do F.A.R.O.L. — todos os scripts leem daqui.
Mudou a área, um arquivo ou um limite? Muda só aqui.
"""

from pathlib import Path

# ---------------------------------------------------------------
# Pastas
# ---------------------------------------------------------------
RAIZ = Path(__file__).parent
DATA_RAW = RAIZ / "data" / "raw"
DATA_PROCESSED = RAIZ / "data" / "processed"
BANCO = RAIZ / "data" / "farol.duckdb"

SIM3464 = DATA_RAW / "sim3464_JezeroNili_FINAL"   # zip do mapa geológico, descompactado

# ---------------------------------------------------------------
# Fontes
# ---------------------------------------------------------------
# Topografia: enquanto o HiRISE (Mars Trek, 1 m) baixa, usamos o DTM CTX (20 m) do SIM 3464.
# Quando o HiRISE chegar, basta trocar DEM_ATIVO para DEM_HIRISE. Os cell_id não mudam.
DEM_CTX = DATA_RAW / "JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif"   # Mars Trek
DEM_CTX_SIM3464 = SIM3464 / "Rasters/USGS_CTX_Stereo_DTMs/J03_045994_1986_J03_046060_1986_20m_DTM.tif"  # só validação
DEM_HIRISE = DATA_RAW / "JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif"
DEM_HIRISE_AOI = DATA_RAW / "hirise_aoi.tif"   # recorte pequeno (~20 MB) feito por etl/recorte_hirise.py

# Escolha automática: usa o recorte HiRISE se existir; senão, o CTX.
DEM_ATIVO = DEM_HIRISE_AOI if DEM_HIRISE_AOI.exists() else DEM_CTX

THEMIS_NOITE = SIM3464 / "Rasters/USGS_THEMIS_IR_controlled_mosaic_oct2018/nili_THEMIS_NightIR_Controlled_oct2018.tif"
THEMIS_DIA = SIM3464 / "Rasters/USGS_THEMIS_IR_controlled_mosaic_oct2018/nili_THEMIS_DayIR_Controlled_oct2018.tif"
THEMIS_SEM_DADO = 0   # o arquivo não declara nodata; pelo histograma, 0 = sem cobertura

GDB = SIM3464 / "Geodatabase/Nili.gdb"

ORTO_CTX = DATA_RAW / "JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0.tif"  # Mars Trek, 6 m
OPTICO_CSV_NOME = "optico.csv"

# ---------------------------------------------------------------
# Área de interesse (AOI) e grade mestre
# Centro perto do ponto de pouso do Perseverance, dentro da LandingEllipse do SIM 3464
# ---------------------------------------------------------------
CENTRO_LAT = 18.4447
CENTRO_LON = 77.4508
RAIO_M = 1000            # quadrado de 2 km x 2 km
TAMANHO_CELULA_M = 20    # 100 x 100 = 10.000 células

# ---------------------------------------------------------------
# Projeções (Marte como esfera, raio usado pela USGS)
# ---------------------------------------------------------------
RAIO_MARTE_M = 3_396_190
CRS_LATLON = f"+proj=longlat +R={RAIO_MARTE_M} +no_defs"
# A grade mestre fica em metros reais na mesma projeção do mapa geológico e do THEMIS
# (Transversa de Mercator centrada em 77,5°E): distorção desprezível em 2 km.
CRS_GRADE = f"+proj=tmerc +lat_0=0 +lon_0=77.5 +k=1 +x_0=0 +y_0=0 +R={RAIO_MARTE_M} +units=m +no_defs"

# ---------------------------------------------------------------
# Limites de decisão — HIPÓTESES do time (ajustáveis e justificadas no pitch)
# ---------------------------------------------------------------
DECLIVE_ATENCAO_GRAUS = 10   # a partir daqui o terreno conta como "íngreme"
FIRMEZA_SOLTO = 0.35         # indice_firmeza abaixo disso conta como "solo solto"
DIST_CRATERA_ATENCAO_M = 30  # célula muito perto de cratera pequena
DECLIVE_MAX_ALERTA_GRAUS = 20  # só com HiRISE: degrau/pedra escondido dentro de célula plana na média

# ---------------------------------------------------------------
# Saídas
# ---------------------------------------------------------------
RELATORIOS = RAIZ / "relatorios"
GRADE_CSV = DATA_PROCESSED / "grade.csv"
TOPOGRAFIA_CSV = DATA_PROCESSED / "topografia.csv"
TERMICO_CSV = DATA_PROCESSED / "termico.csv"
GEOLOGIA_CSV = DATA_PROCESSED / "geologia.csv"
