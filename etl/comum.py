"""
Funções usadas por todos os ETLs: ler a grade mestre e checar integridade.
"""

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

import config


def ler_grade():
    return pd.read_csv(config.GRADE_CSV)


def amostrar_raster(caminho, grade, nodata=None):
    """
    Lê o valor do raster no CENTRO de cada célula (vizinho mais próximo).
    Não reprojeta nem interpola o dado: só converte a coordenada da célula
    para a projeção do arquivo. Fora da cobertura ou sem dado -> NaN.
    """
    with rasterio.open(caminho) as fonte:
        para_fonte = Transformer.from_crs(config.CRS_GRADE, fonte.crs, always_xy=True)
        xs, ys = para_fonte.transform(grade["x_m"].to_numpy(), grade["y_m"].to_numpy())
        linhas, colunas = rasterio.transform.rowcol(fonte.transform, xs, ys)
        linhas, colunas = np.asarray(linhas), np.asarray(colunas)

        dentro = (linhas >= 0) & (linhas < fonte.height) & (colunas >= 0) & (colunas < fonte.width)
        banda = fonte.read(1)
        valores = np.full(len(grade), np.nan)
        valores[dentro] = banda[linhas[dentro], colunas[dentro]]

        nodata = fonte.nodata if nodata is None else nodata
        if nodata is not None:
            valores[np.isclose(valores, nodata)] = np.nan
    return valores


def checar_tabela(tabela, nome, faixas=None):
    """Checagens que toda tabela de célula precisa passar antes de ser salva."""
    grade = ler_grade()
    print(f"\n--- Checagem: {nome} ---")
    assert len(tabela) == len(grade), f"{nome}: {len(tabela)} linhas, esperado {len(grade)}"
    assert tabela["cell_id"].is_unique, f"{nome}: cell_id duplicado"
    assert set(tabela["cell_id"]) == set(grade["cell_id"]), f"{nome}: cell_id diferente da grade"
    print(f"Linhas: {len(tabela)} | cell_id únicos e iguais à grade: OK")

    for coluna in tabela.columns.drop("cell_id"):
        nulos = tabela[coluna].isna().sum()
        if nulos:
            print(f"  {coluna}: {nulos} nulos")

    for coluna, (minimo, maximo) in (faixas or {}).items():
        valores = tabela[coluna].dropna()
        assert valores.between(minimo, maximo).all(), f"{nome}: {coluna} fora de [{minimo}, {maximo}]"
        print(f"  {coluna}: {valores.min():.2f} a {valores.max():.2f} (faixa esperada {minimo}–{maximo}) OK")
