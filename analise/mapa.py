"""
Mapas da AOI a partir de data/processed/decisao.csv e mapa_risco.csv.
Saída: relatorios/mapa_decisao.png (4 painéis: declive, firmeza, geologia, decisão)

Rodar da raiz:  python -m analise.mapa
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

import config

CLASSES = ["verde", "amarelo_declive", "amarelo_armadilha", "vermelho", "sem_dado"]
CORES = ["#2e9e5b", "#e8c547", "#e8873a", "#c8352e", "#9a9a9a"]
NOMES = ["Seguro", "Atenção: declive", "Armadilha: plano mas solto", "Evitar", "Sem dado"]


def para_matriz(tabela, coluna):
    n = tabela["linha"].max() + 1
    matriz = np.full((n, n), np.nan)
    matriz[tabela["linha"], tabela["coluna"]] = tabela[coluna]
    return matriz


def main():
    grade = pd.read_csv(config.GRADE_CSV)[["cell_id", "linha", "coluna"]]
    risco = grade.merge(pd.read_csv(config.DATA_PROCESSED / "mapa_risco.csv"), on="cell_id")
    decisao = grade.merge(pd.read_csv(config.DATA_PROCESSED / "decisao.csv"), on="cell_id")
    decisao["classe_num"] = decisao["classe"].map({c: i for i, c in enumerate(CLASSES)})
    risco["escuro_num"] = risco["material_escuro"].astype(float)

    lado_km = 2 * config.RAIO_M / 1000
    extensao = [0, lado_km, 0, lado_km]
    fig, eixos = plt.subplots(1, 4, figsize=(20, 6.6), constrained_layout=True)

    paineis = [
        ("Declive (°) — topografia", para_matriz(risco, "declive_medio_graus"), "viridis", None),
        ("Índice de firmeza (0–1) — THEMIS", para_matriz(risco, "indice_firmeza"), "RdYlGn", (0, 1)),
        ("Material escuro — mapa geológico", para_matriz(risco, "escuro_num"),
        ListedColormap(["#e9e4da", "#3b3b3b"]), (0, 1)),
    ]
    for eixo, (titulo, matriz, cmap, limites) in zip(eixos[:3], paineis):
        img = eixo.imshow(matriz, cmap=cmap, extent=extensao,
                        vmin=limites[0] if limites else None, vmax=limites[1] if limites else None)
        eixo.set_title(titulo, fontsize=11)
        if titulo.startswith(("Declive", "Índice")):
            fig.colorbar(img, ax=eixo, shrink=0.8)

    eixos[3].imshow(para_matriz(decisao, "classe_num"), cmap=ListedColormap(CORES),
                    vmin=-0.5, vmax=len(CLASSES) - 0.5, extent=extensao, interpolation="nearest")
    eixos[3].set_title("Decisão (declive × firmeza)", fontsize=11, fontweight="bold")
    contagem = decisao["classe"].value_counts()
    eixos[3].legend(
        handles=[Patch(color=c, label=f"{n} ({contagem.get(k, 0)})")
                for k, c, n in zip(CLASSES, CORES, NOMES) if contagem.get(k, 0)],
        loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=1, fontsize=9, frameon=False)

    for eixo in eixos:
        eixo.set_xlabel("km (oeste → leste)")
        eixo.set_ylabel("km (sul → norte)")

    fonte = risco["fonte_dem"].iloc[0]
    fig.suptitle(f"F.A.R.O.L. — Jezero, AOI 2 × 2 km, células de {config.TAMANHO_CELULA_M} m   |   DEM: {fonte}",
                fontsize=13)
    config.RELATORIOS.mkdir(exist_ok=True)
    saida = config.RELATORIOS / "mapa_decisao.png"
    fig.savefig(saida, dpi=130)
    print(f"Mapa salvo em {saida}")


if __name__ == "__main__":
    main()
