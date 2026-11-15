"""
ETL geológico — Nili.gdb (SIM 3464, USGS-NASA Planetary Geologic Mapping Program)

Camadas usadas:
  GeoUnits_v1      -> unidade geológica de cada célula
  SurfaceFeatures  -> a célula cai em "dark-colored mantling material" ou "ridged"?
  LocationFeatures -> distância até a cratera pequena mais próxima
  LinearFeatures   -> distância até a borda de cratera ("crest of crater rim") mais próxima
  LandingEllipse   -> a célula está dentro da elipse de pouso?

Integridade:
  - geometrias inválidas são corrigidas com make_valid (e contadas)
  - erro de digitação da fonte "Crater riim unit" é padronizado (e registrado)
  - o cruzamento usa o CENTRO da célula; GeoUnits_v1 não tem polígonos sobrepostos,
    então cada célula recebe exatamente 1 unidade

Rodar da raiz:  python -m etl.geologia
"""

import geopandas as gpd
import numpy as np

import config
from etl.comum import checar_tabela, ler_grade

CORRECOES_NOME = {"Crater riim unit": "Crater rim unit"}


def ler_camada(nome):
    camada = gpd.read_file(config.GDB, layer=nome).to_crs(config.CRS_GRADE)
    invalidas = (~camada.is_valid).sum()
    if invalidas:
        camada["geometry"] = camada.make_valid()
        print(f"{nome}: {invalidas} geometria(s) inválida(s) corrigida(s)")
    return camada


def main():
    grade = ler_grade()
    centros = gpd.GeoDataFrame(
        grade[["cell_id"]], geometry=gpd.points_from_xy(grade["x_m"], grade["y_m"]), crs=config.CRS_GRADE)

    # Unidade geológica
    unidades = ler_camada("GeoUnits_v1")[["symbol", "name", "geometry"]]
    unidades["name"] = unidades["name"].replace(CORRECOES_NOME)
    tabela = gpd.sjoin(centros, unidades, how="left", predicate="within").drop(columns="index_right")
    tabela = tabela.rename(columns={"symbol": "unidade_simbolo", "name": "unidade_nome"})

    # Feições de superfície (marca cada tipo como verdadeiro/falso)
    superficie = ler_camada("SurfaceFeatures")
    for tipo, coluna in [("dark-colored mantling material", "material_escuro"), ("ridged", "terreno_ridged")]:
        dentro = gpd.sjoin(centros, superficie[superficie["TYPE"] == tipo][["geometry"]], predicate="within")
        tabela[coluna] = tabela["cell_id"].isin(dentro["cell_id"])

    # Distâncias (metros) até feições pontuais e lineares
    crateras = ler_camada("LocationFeatures")
    tabela["dist_cratera_pequena_m"] = centros.geometry.distance(crateras.union_all()).round(1).values
    bordas = ler_camada("LinearFeatures")
    bordas = bordas[bordas["TYPE"] == "crest of crater rim"]
    tabela["dist_borda_cratera_m"] = centros.geometry.distance(bordas.union_all()).round(1).values

    # Dentro da elipse de pouso?
    elipse = ler_camada("LandingEllipse").union_all()
    tabela["dentro_elipse_pouso"] = centros.geometry.within(elipse).values

    tabela = tabela.drop(columns="geometry")
    tabela = tabela.drop_duplicates("cell_id")  # proteção extra; não deve remover nada

    checar_tabela(tabela, "geologia", faixas={"dist_cratera_pequena_m": (0, 1e6)})
    print("Unidades na AOI:\n" + tabela["unidade_nome"].value_counts(dropna=False).to_string())
    tabela.to_csv(config.GEOLOGIA_CSV, index=False)
    print(f"Salvo em {config.GEOLOGIA_CSV}")


if __name__ == "__main__":
    main()
