"""
ETL térmico — THEMIS IR controlado (SIM 3464), noite e dia, 100 m/pixel

O que os números SÃO: brilho infravermelho reescalado para 0–255 (não é temperatura).
O que fazemos com eles:
  - ir_noite, ir_dia : valor bruto lido no centro de cada célula (0 vira NaN)
  - amplitude_dia_noite = ir_dia - ir_noite
      solo solto/poeira: esquenta muito de dia e esfria muito à noite -> amplitude ALTA
      rocha/solo firme : varia pouco                                 -> amplitude BAIXA
  - indice_firmeza (0 a 1, RELATIVO à AOI):
      média de (noite normalizada) e (1 - amplitude normalizada)
      é uma HIPÓTESE do time, documentada no dicionário de dados

Rodar da raiz:  python -m etl.termico
"""

import numpy as np

import config
from etl.comum import amostrar_raster, checar_tabela, ler_grade


def normalizar(valores):
    """0 = menor valor da AOI, 1 = maior (usa percentis 5–95 para ignorar extremos)."""
    baixo, alto = np.nanpercentile(valores, [5, 95])
    return np.clip((valores - baixo) / (alto - baixo), 0, 1)


def main():
    grade = ler_grade()
    tabela = grade[["cell_id"]].copy()

    # EXTRACT
    tabela["ir_noite"] = amostrar_raster(config.THEMIS_NOITE, grade, nodata=config.THEMIS_SEM_DADO)
    tabela["ir_dia"] = amostrar_raster(config.THEMIS_DIA, grade, nodata=config.THEMIS_SEM_DADO)

    # TRANSFORM
    tabela["amplitude_dia_noite"] = tabela["ir_dia"] - tabela["ir_noite"]
    tabela["indice_firmeza"] = np.round(
        (normalizar(tabela["ir_noite"]) + (1 - normalizar(tabela["amplitude_dia_noite"]))) / 2, 3)

    # quantas células compartilham o mesmo pixel THEMIS (esperado ~25, pois 100 m / 20 m)
    pixels_distintos = tabela[["ir_noite", "ir_dia"]].drop_duplicates().shape[0]
    print(f"Combinações noite/dia distintas na AOI: {pixels_distintos}")

    # LOAD
    checar_tabela(tabela, "termico", faixas={
        "ir_noite": (1, 255), "ir_dia": (1, 255), "indice_firmeza": (0, 1)})
    tabela.to_csv(config.TERMICO_CSV, index=False)
    print(f"Salvo em {config.TERMICO_CSV}")


if __name__ == "__main__":
    main()
