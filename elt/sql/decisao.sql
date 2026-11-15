-- decisao: classifica cada célula cruzando "dá para passar?" (declive) e "o chão aguenta?" (firmeza).
-- Os limites vêm do config.py (substituídos no lugar dos marcadores {…} por elt/carregar.py).
--
--                 | solo firme        | solo solto
--   plano         | verde             | amarelo_armadilha  (parece seguro; checar antes de pisar)
--   íngreme       | amarelo_declive   | vermelho

CREATE OR REPLACE TABLE decisao AS
WITH base AS (
    SELECT
        *,
        declive_medio_graus >= {DECLIVE_ATENCAO_GRAUS} AS ingreme,
        indice_firmeza      <  {FIRMEZA_SOLTO}         AS solto,
        dist_cratera_pequena_m < {DIST_CRATERA_ATENCAO_M} AS perto_cratera,
        COALESCE(declive_max_graus >= {DECLIVE_MAX_ALERTA_GRAUS} AND declive_medio_graus < {DECLIVE_ATENCAO_GRAUS}, FALSE) AS degrau_escondido
    FROM mapa_risco
)
SELECT
    cell_id, lat, lon,
    declive_medio_graus, declive_max_graus, indice_firmeza, unidade_nome, material_escuro, dist_cratera_pequena_m,
    CASE
        WHEN declive_medio_graus IS NULL OR indice_firmeza IS NULL THEN 'sem_dado'
        WHEN ingreme AND solto       THEN 'vermelho'
        WHEN NOT ingreme AND solto   THEN 'amarelo_armadilha'
        WHEN ingreme AND NOT solto   THEN 'amarelo_declive'
        ELSE 'verde'
    END AS classe,
    perto_cratera,
    degrau_escondido,
    -- motivo legível (vai virar contexto da LLM na próxima fase)
    CONCAT_WS('; ',
        CASE WHEN ingreme THEN 'declive ' || ROUND(declive_medio_graus, 1) || '°' END,
        CASE WHEN solto THEN 'solo possivelmente solto (firmeza ' || ROUND(indice_firmeza, 2) || ')' END,
        CASE WHEN material_escuro THEN 'material escuro de cobertura (mapa geológico)' END,
        CASE WHEN degrau_escondido THEN 'degrau escondido: trecho de ' || ROUND(declive_max_graus) || '° dentro da célula' END,
        CASE WHEN perto_cratera THEN 'cratera pequena a ' || ROUND(dist_cratera_pequena_m) || ' m' END
    ) AS motivo
FROM base;
