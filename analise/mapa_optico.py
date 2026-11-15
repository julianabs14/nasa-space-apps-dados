"""
Imagem CTX 6 m da AOI lado a lado com a decisão sobreposta.
Saída: relatorios/mapa_optico.png

Rodar da raiz:  python -m analise.mapa_optico
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from pyproj import Transformer

import config

PASSO_M = 6  # amostra a imagem a cada 6 m (resolução nativa)


def imagem_aoi(grade):
    """Reamostra a ortoimagem numa malha de 6 m alinhada à grade mestre (vizinho mais próximo)."""
    meia = config.RAIO_M
    cx = grade["x_m"].mean()
    cy = grade["y_m"].mean()
    eixo = np.arange(-meia + PASSO_M / 2, meia, PASSO_M)
    xx, yy = np.meshgrid(cx + eixo, cy - eixo)
    with rasterio.open(config.ORTO_CTX) as img:
        t = Transformer.from_crs(config.CRS_GRADE, img.crs, always_xy=True)
        ix, iy = t.transform(xx.ravel(), yy.ravel())
        l, c = rasterio.transform.rowcol(img.transform, ix, iy)
        l, c = np.asarray(l), np.asarray(c)
        l0, c0 = l.min(), c.min()
        bloco = img.read(1, window=((l0, l.max() + 1), (c0, c.max() + 1)))
    return bloco[l - l0, c - c0].reshape(xx.shape)


def main():
    grade = pd.read_csv(config.GRADE_CSV)
    dec = grade[["cell_id", "linha", "coluna"]].merge(
        pd.read_csv(config.DATA_PROCESSED / "decisao.csv"), on="cell_id")
    n = dec["linha"].max() + 1
    mapa = {"amarelo_armadilha": 1, "amarelo_declive": 2, "vermelho": 3}
    sobre = np.full((n, n), np.nan)
    sobre[dec["linha"], dec["coluna"]] = dec["classe"].map(mapa)

    img = imagem_aoi(grade)
    lado = 2 * config.RAIO_M / 1000
    ext = [0, lado, 0, lado]
    cores = ListedColormap(["#e8873a", "#e8c547", "#c8352e"])

    fig, eixos = plt.subplots(1, 2, figsize=(14, 7.4), constrained_layout=True)
    eixos[0].imshow(img, cmap="gray", extent=ext)
    eixos[0].set_title("O que a câmera vê — CTX 6 m (Mars Trek)")
    eixos[1].imshow(img, cmap="gray", extent=ext)
    eixos[1].imshow(sobre, cmap=cores, vmin=0.5, vmax=3.5, alpha=0.45, extent=ext, interpolation="nearest")
    eixos[1].set_title("O que os dados revelam — decisão sobreposta")
    eixos[1].legend(handles=[Patch(color="#e8873a", label="Atenção: plano, possível solo solto"),
                            Patch(color="#e8c547", label="Atenção: declive"),
                            Patch(color="#c8352e", label="Evitar")],
                    loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=3, frameon=False)
    trilha = pd.read_csv(config.DATA_RAW / "m20_traverse_aoi.csv")
    t = Transformer.from_crs(config.CRS_LATLON, config.CRS_GRADE, always_xy=True)
    tx, ty = t.transform(trilha["lon"].to_numpy(), trilha["lat"].to_numpy())
    x0 = grade["x_m"].min() - config.TAMANHO_CELULA_M / 2
    y0 = grade["y_m"].min() - config.TAMANHO_CELULA_M / 2
    for e in eixos:
        e.plot((tx - x0) / 1000, (ty - y0) / 1000, ".", color="#2b8cff", markersize=1.2,
            label="Rota real do Perseverance")
    eixos[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.07), frameon=False, markerscale=8)
    for e in eixos:
        e.set_xlabel("km (oeste → leste)")
        e.set_ylabel("km (sul → norte)")
    fig.suptitle("F.A.R.O.L. — Jezero, AOI 2 × 2 km", fontsize=13)
    saida = config.RELATORIOS / "mapa_optico.png"
    fig.savefig(saida, dpi=120)
    print(f"Mapa salvo em {saida}")


if __name__ == "__main__":
    main()
