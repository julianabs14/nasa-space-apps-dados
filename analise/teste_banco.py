"""Teste do banco farol.duckdb: o banco está de pé e os dados estão íntegros?

Rodar (com o DBeaver desconectado ou fechado):
    python -m analise.teste_banco

Parte 1 - saúde do banco (abre, tabelas, contagens, chaves, nulos, faixas, regra).
Parte 2 - o banco alimentando a árvore de decisão (mesma ideia do código da equipe,
        mas com dados REAIS de Jezero em vez de um CSV inventado).
Parte 3 - consulta "em tempo real" de uma célula, como o capacete faria.
"""
import time
import duckdb
import pandas as pd

from config import BANCO, DECLIVE_ATENCAO_GRAUS, FIRMEZA_SOLTO

TABELAS = ["grade", "topografia", "termico", "geologia", "optico", "rover", "mapa_risco", "decisao"]
CLASSES = {"verde", "amarelo_armadilha", "amarelo_declive", "vermelho", "sem_dado"}
falhas = 0


def checar(ok, msg):
    global falhas
    print(("  ✔ " if ok else "  ✘ ") + msg)
    if not ok:
        falhas += 1


def um(con, sql):
    return con.execute(sql).fetchone()[0]


def parte1(con):
    print("\n[1] Saúde do banco")
    existentes = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    faltando = [t for t in TABELAS if t not in existentes]
    checar(not faltando, f"8 tabelas presentes {'' if not faltando else '- faltam: ' + str(faltando)}")

    for t in TABELAS:
        if t in existentes:
            n, d = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT cell_id) FROM {t}").fetchone()
            checar(n == 10_000 and d == 10_000, f"{t:11s} {n:>6} linhas, {d:>6} cell_id únicos")

    orfas = um(con, """SELECT COUNT(*) FROM decisao d
                    LEFT JOIN grade g USING (cell_id) WHERE g.cell_id IS NULL""")
    checar(orfas == 0, f"nenhuma célula órfã na decisao (sem par na grade): {orfas}")

    nulos = con.execute("""SELECT COUNT(*) FILTER (WHERE declive_medio_graus IS NULL),
                            COUNT(*) FILTER (WHERE indice_firmeza IS NULL)
                        FROM decisao""").fetchone()
    checar(nulos == (0, 0), f"sem nulos em declive/firmeza: declive={nulos[0]} firmeza={nulos[1]}")

    fora = um(con, """SELECT COUNT(*) FROM decisao
                      WHERE declive_medio_graus NOT BETWEEN 0 AND 90
                        OR indice_firmeza NOT BETWEEN 0 AND 1""")
    checar(fora == 0, f"valores dentro das faixas físicas (declive 0-90°, firmeza 0-1): {fora} fora")

    classes = {r[0] for r in con.execute("SELECT DISTINCT classe FROM decisao").fetchall()}
    checar(classes <= CLASSES, f"classes válidas: {sorted(classes)}")

    # a regra do SQL bate se recalculada aqui fora?
    df = con.execute("SELECT declive_medio_graus d, indice_firmeza f, classe FROM decisao").df()
    ing, sol = df.d >= DECLIVE_ATENCAO_GRAUS, df.f < FIRMEZA_SOLTO
    esperado = pd.Series("verde", index=df.index)
    esperado[~ing & sol] = "amarelo_armadilha"
    esperado[ing & ~sol] = "amarelo_declive"
    esperado[ing & sol] = "vermelho"
    div = int((esperado != df.classe).sum())
    checar(div == 0, f"classe recalculada em Python == classe do SQL: {div} divergências")

    print("\n  Distribuição:")
    print(con.execute("""SELECT classe, COUNT(*) celulas, ROUND(100.0*COUNT(*)/10000,1) pct
                        FROM decisao GROUP BY 1 ORDER BY 2 DESC""").df().to_string(index=False))


def parte2(con):
    print("\n[2] Árvore de decisão treinada com dados reais do banco")
    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
        from sklearn.model_selection import train_test_split
    except ImportError:
        print("  (pulado: pip install scikit-learn)")
        return None
    df = con.execute("""SELECT declive_medio_graus AS declividade, indice_firmeza AS firmeza, classe
                        FROM decisao WHERE classe <> 'sem_dado'""").df()
    X, y = df[["declividade", "firmeza"]], df["classe"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    arvore = DecisionTreeClassifier(max_depth=4, random_state=42).fit(Xtr, ytr)
    acc = (arvore.predict(Xte) == yte).mean()
    print(export_text(arvore, feature_names=list(X.columns)))
    checar(acc > 0.99, f"árvore reproduz a regra do banco: acurácia {acc:.1%} em células nunca vistas")
    print(f"  (limites no config.py: declive {DECLIVE_ATENCAO_GRAUS}°, firmeza {FIRMEZA_SOLTO} "
          f"- a árvore deve ter achado valores próximos)")
    return arvore


def parte3(con):
    print("\n[3] Consulta em tempo real de uma célula (como o capacete faria)")
    sql = """SELECT cell_id, classe, ROUND(declive_medio_graus,1) declive, ROUND(indice_firmeza,2) firmeza, motivo
             FROM decisao WHERE cell_id = ?"""
    for cel in ["r050_c050", "r092_c034"]:
        t0 = time.perf_counter()
        linha = con.execute(sql, [cel]).df()
        ms = (time.perf_counter() - t0) * 1000
        checar(len(linha) == 1, f"{cel} encontrada em {ms:.1f} ms")
        if len(linha):
            print("     " + linha.iloc[0].to_dict().__repr__())


if __name__ == "__main__":
    print(f"Banco: {BANCO}")
    if not BANCO.exists():
        raise SystemExit("✘ farol.duckdb não existe - rode python run_pipeline.py primeiro")
    try:
        con = duckdb.connect(str(BANCO), read_only=True)
    except duckdb.IOException as e:
        raise SystemExit(f"✘ banco travado (DBeaver conectado?): {e}")
    parte1(con)
    parte2(con)
    parte3(con)
    con.close()
    print("\n" + ("✔ BANCO OK - todos os testes passaram" if falhas == 0 else f"✘ {falhas} teste(s) falharam"))
