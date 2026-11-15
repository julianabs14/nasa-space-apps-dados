"""
Grade mestre — a "régua" que todas as bases usam.

Cria 100 x 100 células de 20 m em volta do centro da AOI, numa projeção em metros reais.
Cada célula ganha um cell_id fixo (r000_c000 = canto noroeste).
Nenhum dado de fonte é usado aqui: a grade não depende de qual DEM está ativo.

Rodar da raiz do projeto:  python -m etl.grade
"""

import numpy as np
import pandas as pd
from pyproj import Transformer

import config


def main():
    para_grade = Transformer.from_crs(config.CRS_LATLON, config.CRS_GRADE, always_xy=True)
    cx, cy = para_grade.transform(config.CENTRO_LON, config.CENTRO_LAT)

    n = int(2 * config.RAIO_M / config.TAMANHO_CELULA_M)
    tam = config.TAMANHO_CELULA_M
    x_oeste, y_norte = cx - config.RAIO_M, cy + config.RAIO_M

    linhas, colunas = np.indices((n, n))
    x = x_oeste + (colunas.ravel() + 0.5) * tam
    y = y_norte - (linhas.ravel() + 0.5) * tam

    para_latlon = Transformer.from_crs(config.CRS_GRADE, config.CRS_LATLON, always_xy=True)
    lon, lat = para_latlon.transform(x, y)

    grade = pd.DataFrame({
        "cell_id": [f"r{l:03d}_c{c:03d}" for l, c in zip(linhas.ravel(), colunas.ravel())],
        "linha": linhas.ravel(),
        "coluna": colunas.ravel(),
        "x_m": np.round(x, 2),
        "y_m": np.round(y, 2),
        "lat": np.round(lat, 6),
        "lon": np.round(lon, 6),
    })

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    grade.to_csv(config.GRADE_CSV, index=False)
    print(f"Grade: {n} x {n} = {len(grade)} células de {tam} m")
    print(f"Lat {grade.lat.min():.5f}–{grade.lat.max():.5f} | Lon {grade.lon.min():.5f}–{grade.lon.max():.5f}")
    print(f"Salvo em {config.GRADE_CSV}")


if __name__ == "__main__":
    main()
