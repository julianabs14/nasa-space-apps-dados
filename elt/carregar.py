"""
ELT — carrega as tabelas processadas no DuckDB e roda os SQLs.

  LOAD      : cada CSV de data/processed/ vira uma tabela (sem alterar nada)
  TRANSFORM : mapa_risco.sql (junta por cell_id) -> decisao.sql (classifica)
  CHECK     : nenhuma célula perdida ou duplicada
  REPORT    : perguntas.sql -> relatorios/perguntas.md

Rodar da raiz:  python -m elt.carregar
"""

from pathlib import Path

import duckdb

import config

TABELAS = {
    "grade": config.GRADE_CSV,
    "topografia": config.TOPOGRAFIA_CSV,
    "termico": config.TERMICO_CSV,
    "geologia": config.GEOLOGIA_CSV,
    "optico": config.DATA_PROCESSED / config.OPTICO_CSV_NOME,
    "rover": config.DATA_PROCESSED / "rover.csv",
}
PASTA_SQL = Path(__file__).parent / "sql"
LIMITES = {nome: getattr(config, nome)
           for nome in ("DECLIVE_ATENCAO_GRAUS", "FIRMEZA_SOLTO", "DIST_CRATERA_ATENCAO_M", "DECLIVE_MAX_ALERTA_GRAUS")}


def ler_sql(nome):
    texto = (PASTA_SQL / nome).read_text(encoding="utf-8")
    for chave, valor in LIMITES.items():
        texto = texto.replace("{" + chave + "}", str(valor))
    return texto


def checar(con, tabela, esperado):
    total, unicos = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT cell_id) FROM {tabela}").fetchone()
    assert total == unicos == esperado, f"{tabela}: {total} linhas, {unicos} únicas, esperado {esperado}"
    print(f"{tabela}: {total} células, nenhuma perdida ou duplicada")


def responder_perguntas(con):
    blocos = [b.strip() for b in ler_sql("perguntas.sql").split("-- @") if b.strip()]
    linhas = ["# Perguntas de decisão — AOI Jezero\n",
              f"Limites: declive ≥ {config.DECLIVE_ATENCAO_GRAUS}° = íngreme; "
              f"firmeza < {config.FIRMEZA_SOLTO} = solo solto; "
              f"cratera a < {config.DIST_CRATERA_ATENCAO_M} m = atenção.\n"]
    for bloco in blocos:
        titulo, _, sql = bloco.partition("\n")
        if not sql.strip().upper().startswith("SELECT"):
            continue  # cabeçalho/comentário, não é pergunta
        resultado = con.execute(sql).df()
        linhas += [f"## {titulo.strip()}\n", resultado.to_markdown(index=False), ""]
        print(f"\n{titulo.strip()}\n{resultado.to_string(index=False)}")
    config.RELATORIOS.mkdir(exist_ok=True)
    (config.RELATORIOS / "perguntas.md").write_text("\n".join(linhas), encoding="utf-8")


def main():
    con = duckdb.connect(str(config.BANCO))

    for nome, caminho in TABELAS.items():
        con.execute(f"CREATE OR REPLACE TABLE {nome} AS SELECT * FROM read_csv_auto('{caminho}')")
    esperado = con.execute("SELECT COUNT(*) FROM grade").fetchone()[0]

    con.execute(ler_sql("mapa_risco.sql"))
    checar(con, "mapa_risco", esperado)
    con.execute(ler_sql("decisao.sql"))
    checar(con, "decisao", esperado)

    for tabela in ("mapa_risco", "decisao"):
        con.execute(f"COPY {tabela} TO '{config.DATA_PROCESSED / (tabela + '.csv')}' (HEADER)")

    responder_perguntas(con)
    con.close()


if __name__ == "__main__":
    main()
