"""
ETL de topografia — DEM ativo em config.DEM_ATIVO
  hoje : DTM CTX 20 m (SIM 3464)
  depois: DEM HiRISE 1 m (Mars Trek)

EXTRACT   : lê só a janela da AOI (com margem) do DEM
TRANSFORM : calcula declive e rugosidade na resolução ORIGINAL do DEM;
            depois liga cada pixel à célula da grade mestre:
              - DEM fino (pixel < 5 m): agrega os pixels de cada célula (média e máximo)
              - DEM grosso (CTX): lê o pixel no centro da célula
LOAD      : data/processed/topografia.csv

Rodar da raiz:  python -m etl.topografia
"""

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.windows import from_bounds
from scipy.ndimage import uniform_filter

import config
from etl.comum import checar_tabela, ler_grade

MARGEM_M = 100  # lê um pouco além da AOI para o declive da borda não sair errado


# ---------------- EXTRACT ----------------
def ler_janela(grade):
    with rasterio.open(config.DEM_ATIVO) as dem:
        para_dem = Transformer.from_crs(config.CRS_GRADE, dem.crs, always_xy=True)
        xs, ys = para_dem.transform(grade["x_m"].to_numpy(), grade["y_m"].to_numpy())
        janela = from_bounds(xs.min() - MARGEM_M, ys.min() - MARGEM_M,
                             xs.max() + MARGEM_M, ys.max() + MARGEM_M, dem.transform)
        janela = janela.round_offsets().round_lengths()
        elevacao = dem.read(1, window=janela, masked=True).astype("float64").filled(np.nan)
        return elevacao, dem.window_transform(janela), dem.res, dem.crs


# ---------------- TRANSFORM ----------------
def fator_leste_oeste(crs):
    # Em projeção equiretangular (eqc), 1 m no eixo X só é 1 m real no equador.
    # Em Jezero (~18,4°N) a distância real é ~0,95 m.
    return np.cos(np.radians(config.CENTRO_LAT)) if "eqc" in crs.to_proj4() else 1.0


def calcular_declive(elevacao, res, crs):
    dx = res[0] * fator_leste_oeste(crs)
    dz_dy, dz_dx = np.gradient(elevacao, res[1], dx)
    return np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))


def calcular_rugosidade(elevacao):
    # desvio-padrão da elevação numa janela 3x3 pixels
    media = uniform_filter(elevacao, size=3, mode="nearest")
    media_q = uniform_filter(elevacao ** 2, size=3, mode="nearest")
    return np.sqrt(np.clip(media_q - media ** 2, 0, None))


def pixels_para_celulas(camadas, transform, crs_dem, grade):
    """Agrega pixels finos por célula (média e máximo)."""
    n_lin, n_col = next(iter(camadas.values())).shape
    linhas, colunas = np.indices((n_lin, n_col))
    xs, ys = rasterio.transform.xy(transform, linhas.ravel(), colunas.ravel())
    para_grade = Transformer.from_crs(crs_dem, config.CRS_GRADE, always_xy=True)
    gx, gy = para_grade.transform(np.asarray(xs), np.asarray(ys))

    x_oeste = grade["x_m"].min() - config.TAMANHO_CELULA_M / 2
    y_norte = grade["y_m"].max() + config.TAMANHO_CELULA_M / 2
    lin = np.floor((y_norte - gy) / config.TAMANHO_CELULA_M).astype(int)
    col = np.floor((gx - x_oeste) / config.TAMANHO_CELULA_M).astype(int)

    df = pd.DataFrame({nome: m.ravel() for nome, m in camadas.items()})
    df["linha"], df["coluna"] = lin, col
    agg = df.groupby(["linha", "coluna"]).agg(
        elevacao_m=("elevacao", "mean"),
        declive_medio_graus=("declive", "mean"),
        declive_max_graus=("declive", "max"),
        rugosidade_m=("rugosidade", "mean"),
        n_pixels=("elevacao", "count"),
    ).reset_index()
    return grade[["cell_id", "linha", "coluna"]].merge(agg, on=["linha", "coluna"], how="left")


def amostrar_centros(camadas, transform, crs_dem, grade):
    """Lê o pixel no centro de cada célula (DEM com pixel do tamanho da célula)."""
    para_dem = Transformer.from_crs(config.CRS_GRADE, crs_dem, always_xy=True)
    xs, ys = para_dem.transform(grade["x_m"].to_numpy(), grade["y_m"].to_numpy())
    lin, col = rasterio.transform.rowcol(transform, xs, ys)
    lin, col = np.asarray(lin), np.asarray(col)
    saida = grade[["cell_id"]].copy()
    saida["elevacao_m"] = camadas["elevacao"][lin, col]
    saida["declive_medio_graus"] = camadas["declive"][lin, col]
    saida["declive_max_graus"] = np.nan  # CTX: 1 pixel por célula, não existe "máximo dentro da célula"
    saida["rugosidade_m"] = camadas["rugosidade"][lin, col]
    saida["n_pixels"] = 1
    return saida


# ---------------- LOAD ----------------
def main():
    grade = ler_grade()
    elevacao, transform, res, crs = ler_janela(grade)
    print(f"DEM ativo: {config.DEM_ATIVO.name} | pixel {res[0]:.1f} m | janela {elevacao.shape}")

    camadas = {
        "elevacao": elevacao,
        "declive": calcular_declive(elevacao, res, crs),
        "rugosidade": calcular_rugosidade(elevacao),
    }

    if res[0] < 5:
        tabela = pixels_para_celulas(camadas, transform, crs, grade)
    else:
        tabela = amostrar_centros(camadas, transform, crs, grade)

    tabela = tabela[["cell_id", "elevacao_m", "declive_medio_graus", "declive_max_graus",
                     "rugosidade_m", "n_pixels"]].round(3)
    tabela["fonte_dem"] = config.DEM_ATIVO.name

    checar_tabela(tabela, "topografia", faixas={
        "elevacao_m": (-4000, 0),
        "declive_medio_graus": (0, 90),
        "rugosidade_m": (0, 100),
    })
    tabela.to_csv(config.TOPOGRAFIA_CSV, index=False)
    print(f"Salvo em {config.TOPOGRAFIA_CSV}")


if __name__ == "__main__":
    main()
