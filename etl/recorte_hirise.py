"""
Recorte do DEM HiRISE (Mars Trek, ~1,8 GB) para só a AOI (~20 MB).

Por quê: o arquivo cobre ~21 x 21 km; usamos 2 x 2 km. Ler só uma janela
evita carregar o arquivo inteiro e gera um arquivo pequeno para o time.
O original fica intacto em data/raw/.

Rodar da raiz:  python -m etl.recorte_hirise
"""

import rasterio
from pyproj import Transformer
from rasterio.windows import from_bounds

import config

MARGEM_M = 200


def main():
    if config.DEM_HIRISE_AOI.exists():
        print(f"Recorte já existe em {config.DEM_HIRISE_AOI} — pulando (apague o arquivo para refazer).")
        return
    if not config.DEM_HIRISE.exists():
        print(f"HiRISE não encontrado em {config.DEM_HIRISE} — pulando (o pipeline usa o CTX).")
        return

    with rasterio.open(config.DEM_HIRISE) as dem:
        para_dem = Transformer.from_crs(config.CRS_LATLON, dem.crs, always_xy=True)
        x, y = para_dem.transform(config.CENTRO_LON, config.CENTRO_LAT)
        r = config.RAIO_M + MARGEM_M
        janela = from_bounds(x - r, y - r, x + r, y + r, dem.transform).round_offsets().round_lengths()

        perfil = dem.profile | {
            "width": int(janela.width), "height": int(janela.height),
            "transform": dem.window_transform(janela), "compress": "lzw",
        }
        with rasterio.open(config.DEM_HIRISE_AOI, "w", **perfil) as saida:
            saida.write(dem.read(1, window=janela), 1)

    print(f"Recorte salvo: {config.DEM_HIRISE_AOI} ({perfil['width']} x {perfil['height']} pixels)")


if __name__ == "__main__":
    main()
