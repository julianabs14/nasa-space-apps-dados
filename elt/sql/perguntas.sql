-- Perguntas de decisão sobre a AOI. Cada bloco separado por "-- @" é uma pergunta.

-- @ 1. Quanto da área cai em cada classe?
SELECT classe,
       COUNT(*) AS celulas,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_area,
       ROUND(COUNT(*) * 400 / 1e6, 2) AS km2
FROM decisao GROUP BY classe ORDER BY celulas DESC;

-- @ 2. Armadilhas escondidas: planas, mas com solo solto. Onde a geologia confirma?
SELECT material_escuro AS confirmado_pelo_mapa_geologico,
       COUNT(*) AS celulas,
       ROUND(AVG(indice_firmeza), 2) AS firmeza_media,
       ROUND(AVG(declive_medio_graus), 1) AS declive_medio
FROM decisao WHERE classe = 'amarelo_armadilha'
GROUP BY 1 ORDER BY 1 DESC;

-- @ 3. Risco por unidade geológica
SELECT unidade_nome,
       COUNT(*) AS celulas,
       ROUND(100.0 * AVG(CASE WHEN classe = 'verde' THEN 1 ELSE 0 END), 1) AS pct_verde,
       ROUND(100.0 * AVG(CASE WHEN classe LIKE 'amarelo%' THEN 1 ELSE 0 END), 1) AS pct_amarelo,
       ROUND(100.0 * AVG(CASE WHEN classe = 'vermelho' THEN 1 ELSE 0 END), 1) AS pct_vermelho
FROM decisao GROUP BY 1 ORDER BY 1;

-- @ 4. As 5 células mais críticas (para checar no QGIS / fotos)
SELECT cell_id, lat, lon, classe, motivo
FROM decisao
WHERE classe IN ('vermelho', 'amarelo_armadilha', 'amarelo_declive')
ORDER BY (classe = 'vermelho') DESC, indice_firmeza ASC, declive_medio_graus DESC
LIMIT 5;

-- @ 5. A câmera (CTX 6 m) enxerga as armadilhas? Brilho médio por classe
SELECT d.classe, COUNT(*) AS celulas, ROUND(AVG(m.brilho_ctx), 1) AS brilho_medio,
       ROUND(AVG(m.indice_firmeza), 2) AS firmeza_media
FROM decisao d JOIN mapa_risco m USING (cell_id)
GROUP BY d.classe ORDER BY celulas DESC;

-- @ 6. Validação com a realidade: por onde o Perseverance andou, o que nosso mapa dizia?
SELECT d.classe,
       COUNT(*) AS celulas_na_rota,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_da_rota,
       ROUND(AVG(m.declive_medio_graus), 1) AS declive_medio,
       ROUND(AVG(m.indice_firmeza), 2) AS firmeza_media
FROM decisao d JOIN mapa_risco m USING (cell_id)
WHERE m.rover_passou
GROUP BY d.classe ORDER BY celulas_na_rota DESC;

-- @ 7. Degraus escondidos (só o HiRISE de 1 m enxerga): plano na média, íngreme em algum trecho
SELECT d.classe, COUNT(*) AS celulas_com_degrau,
       ROUND(AVG(m.declive_medio_graus), 1) AS declive_medio, ROUND(MAX(m.declive_max_graus), 1) AS pior_trecho
FROM decisao d JOIN mapa_risco m USING (cell_id)
WHERE d.degrau_escondido
GROUP BY d.classe ORDER BY celulas_com_degrau DESC;
