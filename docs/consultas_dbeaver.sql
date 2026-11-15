-- =====================================================================
-- F.A.R.O.L. — Consultas para explorar o farol.duckdb no DBeaver
-- Conexão: DuckDB → arquivo  ...\farol\data\farol.duckdb
-- Rode uma consulta por vez: cursor dentro dela + Ctrl+Enter
-- (feche o DBeaver antes de rodar o run_pipeline.py)
-- =====================================================================

-- 1. Que tabelas existem e quantas linhas cada uma tem?
SELECT table_name, estimated_size AS linhas
FROM duckdb_tables()
ORDER BY table_name;

-- 2. Quais colunas tem a tabela final?
DESCRIBE mapa_risco;

-- 3. Uma olhada geral: 20 células quaisquer
SELECT * FROM mapa_risco LIMIT 20;

-- 4. Quanto da área cai em cada classe? (km² = células × 400 m²)
SELECT classe,
      COUNT(*)                                             AS celulas,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)   AS pct_area,
       ROUND(COUNT(*) * 400 / 1e6, 2)                       AS km2
FROM decisao
GROUP BY classe
ORDER BY celulas DESC;

-- 5. Perfil de cada classe: o que distingue uma da outra?
SELECT d.classe,
      ROUND(AVG(m.declive_medio_graus), 1) AS declive_medio,
      ROUND(AVG(m.declive_max_graus), 1)   AS declive_max_medio,
      ROUND(AVG(m.indice_firmeza), 2)      AS firmeza_media,
      ROUND(AVG(m.amplitude_dia_noite), 1) AS amplitude_media,
      ROUND(AVG(m.brilho_ctx), 0)          AS brilho_medio
FROM decisao d JOIN mapa_risco m USING (cell_id)
GROUP BY d.classe
ORDER BY firmeza_media DESC;

-- 6. Armadilhas confirmadas por DUAS fontes independentes
--    (térmico diz "solto" E o mapa geológico diz "material escuro")
SELECT cell_id, lat, lon,
      ROUND(declive_medio_graus, 1) AS declive,
      ROUND(indice_firmeza, 2)      AS firmeza,
      unidade_nome
FROM mapa_risco
WHERE indice_firmeza < 0.35 AND material_escuro
ORDER BY indice_firmeza
LIMIT 30;

-- 7. Degraus escondidos: célula plana na média, mas com trecho íngreme (só HiRISE vê)
SELECT cell_id, lat, lon,
      ROUND(declive_medio_graus, 1) AS declive_medio,
      ROUND(declive_max_graus, 1)   AS pior_trecho,
      rover_passou
FROM mapa_risco
WHERE declive_max_graus >= 20 AND declive_medio_graus < 10
ORDER BY declive_max_graus DESC
LIMIT 30;

-- 8. Por onde o Perseverance andou: em que classe estava cada parada?
SELECT m.sol_min AS sol, m.site_drive, m.cell_id, d.classe, d.motivo
FROM mapa_risco m JOIN decisao d USING (cell_id)
WHERE m.n_paradas > 0
ORDER BY m.sol_min;

-- 9. Comparação entre unidades geológicas
SELECT unidade_nome,
      COUNT(*)                                                         AS celulas,
       ROUND(100.0 * AVG(CASE WHEN material_escuro THEN 1 ELSE 0 END), 1) AS pct_material_escuro,
      ROUND(AVG(indice_firmeza), 2)                                    AS firmeza_media,
      ROUND(AVG(declive_medio_graus), 1)                               AS declive_medio
FROM mapa_risco
GROUP BY unidade_nome;

-- 10. Qualidade dos dados: as duas topografias CTX concordam?
SELECT ROUND(AVG(dif_alt_ctx_sim_m), 2)    AS diferenca_media_m,
      ROUND(STDDEV(dif_alt_ctx_sim_m), 2) AS desvio_m,
      ROUND(MIN(dif_alt_ctx_sim_m), 2)    AS minima_m,
      ROUND(MAX(dif_alt_ctx_sim_m), 2)    AS maxima_m,
      COUNT(*) FILTER (WHERE elevacao_m IS NULL) AS celulas_sem_altitude
FROM mapa_risco;

-- 11. E se o limite de declive fosse 8° em vez de 10°? (simulação sem mudar o pipeline)
SELECT CASE
        WHEN declive_medio_graus >= 8 AND indice_firmeza < 0.35 THEN 'vermelho'
        WHEN indice_firmeza < 0.35                             THEN 'amarelo_armadilha'
        WHEN declive_medio_graus >= 8                          THEN 'amarelo_declive'
        ELSE 'verde'
      END AS classe_simulada,
      COUNT(*) AS celulas
FROM mapa_risco
GROUP BY 1
ORDER BY 2 DESC;
