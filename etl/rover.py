"""
ETL da rota real do Perseverance (MMGIS da NASA, mars.nasa.gov/mmgis-maps/M20)

Entrada (já recortadas na AOI):
  data/raw/m20_waypoints_aoi.csv  -> paradas: site, drive, sol, lat, lon, elevação
  data/raw/m20_traverse_aoi.csv   -> pontos da trilha percorrida (sol, trecho, lon, lat)

Saída: data/processed/rover.csv, uma linha por célula:
  - rover_passou   : a trilha real passou pela célula
  - n_paradas      : quantas paradas (waypoints) caem na célula
  - site_drive     : a primeira parada da célula, chave para ligar as FOTOS (raw images têm site/drive)
  - sol_min        : primeiro sol em que o rover esteve na célula

Rodar da raiz:  python -m etl.rover
"""

import numpy as np
import pandas as pd
from pyproj import Transformer

import config
from etl.comum import checar_tabela, ler_grade


def para_celula(lat, lon, grade):
    t = Transformer.from_crs(config.CRS_LATLON, config.CRS_GRADE, always_xy=True)
    x, y = t.transform(np.asarray(lon), np.asarray(lat))
    tam = config.TAMANHO_CELULA_M
    x0 = grade["x_m"].min() - tam / 2
    y0 = grade["y_m"].max() + tam / 2
    linha = np.floor((y0 - y) / tam).astype(int)
    coluna = np.floor((x - x0) / tam).astype(int)
    n = grade["linha"].max() + 1
    valido = (linha >= 0) & (linha < n) & (coluna >= 0) & (coluna < n)
    ids = np.where(valido, [f"r{l:03d}_c{c:03d}" for l, c in zip(linha, coluna)], None)
    return ids


def main():
    grade = ler_grade()
    trilha = pd.read_csv(config.DATA_RAW / "m20_traverse_aoi.csv")
    paradas = pd.read_csv(config.DATA_RAW / "m20_waypoints_aoi.csv")

    trilha["cell_id"] = para_celula(trilha["lat"], trilha["lon"], grade)
    paradas["cell_id"] = para_celula(paradas["lat"], paradas["lon"], grade)
    paradas["site_drive"] = paradas["site"].astype(str) + "_" + paradas["drive"].astype(str)

    por_trilha = trilha.dropna(subset=["cell_id"]).groupby("cell_id").agg(sol_trilha=("sol", "min"))
    por_parada = (paradas.dropna(subset=["cell_id"]).sort_values("sol").groupby("cell_id")
                  .agg(n_paradas=("sol", "size"), site_drive=("site_drive", "first"), sol_parada=("sol", "min")))

    tabela = grade[["cell_id"]].merge(por_trilha, on="cell_id", how="left").merge(por_parada, on="cell_id", how="left")
    tabela["rover_passou"] = tabela["sol_trilha"].notna() | tabela["sol_parada"].notna()
    tabela["sol_min"] = tabela[["sol_trilha", "sol_parada"]].min(axis=1)
    tabela["n_paradas"] = tabela["n_paradas"].fillna(0).astype(int)
    tabela = tabela[["cell_id", "rover_passou", "n_paradas", "site_drive", "sol_min"]]

    checar_tabela(tabela, "rover")
    print(f"Células por onde o rover passou: {tabela['rover_passou'].sum()} | com parada: {(tabela['n_paradas'] > 0).sum()}")
    tabela.to_csv(config.DATA_PROCESSED / "rover.csv", index=False)


if __name__ == "__main__":
    main()
