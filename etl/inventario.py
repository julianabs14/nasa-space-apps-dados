"""
Inventário (catálogo) dos rasters em data/raw/ — camada BRONZE.

Ideia de engenharia de dados: antes de processar GBs, extrair só os METADADOS
e um perfil leve de cada arquivo, para decidir o que vale a pena usar.

Para cada .tif encontrado:
  - metadados (não lê os pixels): tamanho, resolução, projeção, tipo, nodata, área coberta
  - cobertura da AOI: a AOI está dentro? quantos pixels e MB custa ler só ela?
  - perfil leve: estatísticas lidas de uma versão reduzida (overview), não do arquivo inteiro
  - papel: topografia (DEM) ou imagem/térmico

Saída: data/processed/inventario.csv  (+ tabela no DuckDB via elt.carregar)

Rodar da raiz:  python -m etl.inventario
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling

import config

TAMANHO_PERFIL = 512  # lado da versão reduzida usada para estatísticas


def papel(arquivo, dtype):
    nome = arquivo.name.lower()
    if "dtm" in nome or "dem" in nome or "da4" in nome or "hirise_aoi" in nome:
        return "topografia"
    if "themis" in nome:
        return "termico"
    if "hillshade" in nome:
        return "derivado_topografia"
    return "imagem" if dtype == "uint8" else "outro"


def cobertura_aoi(fonte):
    """Quantos pixels e MB custa ler só a AOI deste arquivo, e se a AOI está coberta."""
    para_fonte = Transformer.from_crs(config.CRS_LATLON, fonte.crs, always_xy=True)
    x, y = para_fonte.transform(config.CENTRO_LON, config.CENTRO_LAT)
    l, r = config.RAIO_M, config.RAIO_M
    b = fonte.bounds
    dentro = b.left <= x - l and x + l <= b.right and b.bottom <= y - r and y + r <= b.top
    fator = np.cos(np.radians(config.CENTRO_LAT)) if "eqc" in fonte.crs.to_proj4() else 1.0
    px_x = 2 * l / (fonte.res[0] * fator)
    px_y = 2 * r / fonte.res[1]
    pixels = px_x * px_y
    mb = pixels * np.dtype(fonte.dtypes[0]).itemsize / 1e6
    return dentro, int(pixels), round(mb, 2)


def perfil(fonte):
    reduzido = fonte.read(1, out_shape=(TAMANHO_PERFIL, TAMANHO_PERFIL),
                          resampling=Resampling.nearest, masked=True).astype("float64")
    if fonte.nodata is None and fonte.dtypes[0] == "uint8":
        reduzido = np.ma.masked_equal(reduzido, 0)
    validos = reduzido.compressed()
    pct_valido = 100 * validos.size / reduzido.size
    if validos.size == 0:
        return pct_valido, None, None, None
    return pct_valido, validos.min(), np.median(validos), validos.max()


def main():
    arquivos = sorted(
        Path(pasta) / nome
        for pasta, _, nomes in os.walk(config.DATA_RAW, followlinks=True)
        for nome in nomes
        if nome.endswith(".tif") and not nome.startswith("._")
    )
    if not arquivos:
        raise SystemExit(f"Nenhum .tif encontrado em {config.DATA_RAW}")
    linhas = []
    for arquivo in arquivos:
        with rasterio.open(arquivo) as fonte:
            dentro, px_aoi, mb_aoi = cobertura_aoi(fonte)
            pct_valido, vmin, vmed, vmax = perfil(fonte)
            tamanho_mb = arquivo.stat().st_size / 1e6
            linhas.append({
                "arquivo": arquivo.name,
                "papel": papel(arquivo, fonte.dtypes[0]),
                "tamanho_disco_mb": round(tamanho_mb, 1),
                "largura_px": fonte.width,
                "altura_px": fonte.height,
                "resolucao_m": round(fonte.res[0], 2),
                "tipo": fonte.dtypes[0],
                "nodata": fonte.nodata,
                "projecao": fonte.crs.to_proj4().split(" +")[0].replace("+proj=", ""),
                "aoi_coberta": dentro,
                "pixels_aoi": px_aoi,
                "mb_para_ler_aoi": mb_aoi,
                "pct_pixels_validos": round(pct_valido, 1),
                "valor_min": vmin, "valor_mediana": vmed, "valor_max": vmax,
                "caminho": str(arquivo.relative_to(config.DATA_RAW)),
            })

    inventario = pd.DataFrame(linhas).sort_values(["papel", "resolucao_m"])
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    inventario.to_csv(config.DATA_PROCESSED / "inventario.csv", index=False)

    colunas = ["arquivo", "papel", "tamanho_disco_mb", "resolucao_m", "aoi_coberta",
               "mb_para_ler_aoi", "valor_min", "valor_mediana", "valor_max"]
    print(inventario[colunas].to_string(index=False))
    total = inventario["tamanho_disco_mb"].sum()
    aoi = inventario.loc[inventario["aoi_coberta"], "mb_para_ler_aoi"].sum()
    print(f"\nTotal em disco: {total:,.0f} MB | lido de fato para a AOI: {aoi:,.1f} MB "
          f"({100 * aoi / total:.1f}%)")


if __name__ == "__main__":
    main()
