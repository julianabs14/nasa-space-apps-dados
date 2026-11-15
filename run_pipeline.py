"""
Orquestrador do F.A.R.O.L. — roda todas as etapas em ordem, para no primeiro erro.

    python run_pipeline.py              # tudo
    python run_pipeline.py --desde etl.termico   # recomeça de uma etapa

Cada etapa roda em um processo separado (python -m ...), então o config.py é relido
a cada etapa (ex.: depois do recorte HiRISE, a topografia já usa o novo DEM).
"""

import argparse
import subprocess
import sys
import time

ETAPAS = [
    ("etl.inventario",     "Bronze: inventário de metadados de todos os rasters"),
    ("etl.recorte_hirise", "Recorta o DEM HiRISE para a AOI (pula se não houver HiRISE)"),
    ("etl.grade",          "Cria a grade mestre de células (cell_id)"),
    ("etl.topografia",     "Elevação, declive, rugosidade"),
    ("etl.termico",        "THEMIS noite/dia, amplitude, índice de firmeza"),
    ("etl.geologia",       "Unidade geológica, material escuro, distâncias"),
    ("etl.optico",         "Brilho CTX 6 m + validação de altitude CTX Trek x SIM"),
    ("etl.rover",          "Rota real do Perseverance por célula (ponte para as fotos)"),
    ("elt.carregar",       "DuckDB: mapa_risco + decisao + perguntas"),
    ("analise.mapa",       "Mapa visual da decisão"),
    ("analise.mapa_optico", "Imagem CTX com a decisão sobreposta"),
    ("analise.dashboard",  "Dashboard HTML interativo (abre no navegador)"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--desde", help="nome da etapa para recomeçar (ex.: etl.termico)")
    args = parser.parse_args()

    nomes = [nome for nome, _ in ETAPAS]
    inicio = nomes.index(args.desde) if args.desde else 0

    total = time.perf_counter()
    for nome, descricao in ETAPAS[inicio:]:
        print(f"\n{'=' * 70}\n▶ {nome}: {descricao}\n{'=' * 70}")
        t0 = time.perf_counter()
        resultado = subprocess.run([sys.executable, "-W", "ignore", "-m", nome])
        if resultado.returncode != 0:
            print(f"\n✖ Falhou em {nome}. Corrija e rode: python run_pipeline.py --desde {nome}")
            sys.exit(resultado.returncode)
        print(f"✔ {nome} ({time.perf_counter() - t0:.1f} s)")

    print(f"\nPipeline completo em {time.perf_counter() - total:.1f} s")
    print("Resultados: relatorios/dashboard.html | relatorios/perguntas.md | data/farol.duckdb")


if __name__ == "__main__":
    main()
