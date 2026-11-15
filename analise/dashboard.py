"""
Dashboard HTML (um arquivo só, funciona offline) a partir do DuckDB.
Saída: relatorios/dashboard.html

Rodar da raiz:  python -m analise.dashboard
"""

import base64
import io
import json

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyproj import Transformer

import config
from analise.mapa_optico import imagem_aoi

MODELO = config.RAIZ / "analise" / "dashboard_modelo.html"
SAIDA = config.RELATORIOS / "dashboard.html"


def dados_celulas():
    con = duckdb.connect(str(config.BANCO), read_only=True)
    df = con.sql("""
        SELECT g.linha, g.coluna, m.*
        FROM grade g JOIN mapa_risco m USING (cell_id)
        ORDER BY g.linha, g.coluna
    """).df()
    con.close()
    unidades = sorted(df["unidade_nome"].dropna().unique().tolist())

    def col(nome, casas):
        return [None if pd.isna(v) else round(float(v), casas) for v in df[nome]]

    return {
        "n": int(df["linha"].max() + 1),
        "tam_celula_m": config.TAMANHO_CELULA_M,
        "lat": col("lat", 5), "lon": col("lon", 5),
        "elev": col("elevacao_m", 1),
        "dm": col("declive_medio_graus", 3), "dx": col("declive_max_graus", 2),
        "fi": col("indice_firmeza", 3), "amp": col("amplitude_dia_noite", 0),
        "br": col("brilho_ctx", 0),
        "me": df["material_escuro"].fillna(False).astype(int).tolist(),
        "rv": df["rover_passou"].fillna(False).astype(int).tolist(),
        "sol": col("sol_min", 0),
        "un": [unidades.index(u) if isinstance(u, str) else -1 for u in df["unidade_nome"]],
        "unidades": unidades,
        "dc": col("dist_cratera_pequena_m", 0),
        "fonte_dem": str(df["fonte_dem"].iloc[0]),
        "limites": {"declive": config.DECLIVE_ATENCAO_GRAUS, "firmeza": config.FIRMEZA_SOLTO,
                    "degrau": config.DECLIVE_MAX_ALERTA_GRAUS},
    }


def imagem_base64(grade):
    img = imagem_aoi(grade)
    buf = io.BytesIO()
    plt.imsave(buf, img, cmap="gray", format="png")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def rota_km(grade):
    trilha = pd.read_csv(config.DATA_RAW / "m20_traverse_aoi.csv")
    t = Transformer.from_crs(config.CRS_LATLON, config.CRS_GRADE, always_xy=True)
    x, y = t.transform(trilha["lon"].to_numpy(), trilha["lat"].to_numpy())
    x0 = grade["x_m"].min() - config.TAMANHO_CELULA_M / 2
    y0 = grade["y_m"].min() - config.TAMANHO_CELULA_M / 2
    pts = np.round(np.c_[(x - x0) / 1000, (y - y0) / 1000], 3)
    # quebra a linha quando há salto (> 60 m) entre pontos consecutivos
    saltos = np.r_[False, np.hypot(*np.diff(pts, axis=0).T) > 0.06]
    trechos, atual = [], []
    for p, salto in zip(pts.tolist(), saltos):
        if salto and atual:
            trechos.append(atual)
            atual = []
        if not atual or p != atual[-1]:
            atual.append(p)
    trechos.append(atual)
    return trechos


def main():
    grade = pd.read_csv(config.GRADE_CSV)
    dados = dados_celulas()
    dados["imagem"] = imagem_base64(grade)
    dados["rota"] = rota_km(grade)
    dados["lado_km"] = 2 * config.RAIO_M / 1000

    html = MODELO.read_text(encoding="utf-8").replace(
        "/*__DADOS__*/null", json.dumps(dados, separators=(",", ":")))
    config.RELATORIOS.mkdir(exist_ok=True)
    SAIDA.write_text(html, encoding="utf-8")
    print(f"Dashboard salvo em {SAIDA} ({SAIDA.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
