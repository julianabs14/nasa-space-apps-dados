"""
ETL óptico — MRO CTX, Jezero Mosaic, Controlled (Mars Trek, 6 m, tons de cinza 0–255)

O que extrai por célula de 20 m:
  - brilho_ctx: brilho médio dos pixels de 6 m dentro da célula (0 = sem dado -> NaN)
  - dif_alt_ctx_sim_m: diferença de altitude entre o DTM CTX do Trek e o do SIM 3464
    (checagem de qualidade da topografia: duas fontes independentes do mesmo terreno)

Rodar da raiz:  python -m etl.optico
"""

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.windows import Window

import config
from etl.comum import amostrar_raster, checar_tabela, ler_grade

JANELA_PX = 3  # 3 x 3 pixels de 6 m ~ 18 m, cabe dentro da célula de 20 m


def brilho_medio(caminho, grade):
    with rasterio.open(caminho) as img:
        para_img = Transformer.from_crs(config.CRS_GRADE, img.crs, always_xy=True)
        xs, ys = para_img.transform(grade["x_m"].to_numpy(), grade["y_m"].to_numpy())
        linhas, colunas = rasterio.transform.rowcol(img.transform, xs, ys)
        l0, c0 = min(linhas) - 2, min(colunas) - 2
        bloco = img.read(1, window=Window(c0, l0, max(colunas) - c0 + 3, max(linhas) - l0 + 3)).astype(float)
        bloco[bloco == (img.nodata or 0)] = np.nan
    meio = JANELA_PX // 2
    return np.array([
        np.nanmean(bloco[l - l0 - meio:l - l0 + meio + 1, c - c0 - meio:c - c0 + meio + 1])
        for l, c in zip(linhas, colunas)
    ])


def main():
    grade = ler_grade()
    tabela = grade[["cell_id"]].copy()
    tabela["brilho_ctx"] = np.round(brilho_medio(config.ORTO_CTX, grade), 1)

    alt_trek = amostrar_raster(config.DEM_CTX, grade)
    alt_sim = amostrar_raster(config.DEM_CTX_SIM3464, grade)
    tabela["dif_alt_ctx_sim_m"] = np.round(alt_trek - alt_sim, 2)

    checar_tabela(tabela, "optico", faixas={"brilho_ctx": (1, 255), "dif_alt_ctx_sim_m": (-50, 50)})
    d = tabela["dif_alt_ctx_sim_m"]
    print(f"Validação topografia (Trek - SIM): média {d.mean():.2f} m, desvio {d.std():.2f} m")
    tabela.to_csv(config.DATA_PROCESSED / config.OPTICO_CSV_NOME, index=False)
    print(f"Salvo em {config.DATA_PROCESSED / config.OPTICO_CSV_NOME}")


if __name__ == "__main__":
    main()
