-- Resumo por unidade geológica: o que cada tipo de terreno tem de topografia e térmico.
SELECT
    unidade_nome,
    COUNT(*)                                  AS celulas,
    ROUND(AVG(elevacao_m), 1)                 AS elevacao_media_m,
    ROUND(AVG(declive_medio_graus), 2)        AS declive_medio,
    ROUND(MAX(declive_medio_graus), 2)        AS declive_maximo,
    ROUND(AVG(rugosidade_m), 2)               AS rugosidade_media_m,
    ROUND(AVG(ir_noite), 1)                   AS ir_noite_medio,
    ROUND(AVG(amplitude_dia_noite), 1)        AS amplitude_media,
    ROUND(AVG(indice_firmeza), 2)             AS firmeza_media,
    SUM(CASE WHEN material_escuro THEN 1 ELSE 0 END) AS celulas_material_escuro
FROM mapa_risco
GROUP BY unidade_nome
ORDER BY celulas DESC;
