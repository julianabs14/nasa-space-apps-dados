-- mapa_risco: uma linha por célula de 20 m, com todas as camadas lado a lado.
-- Só junta e renomeia. Nenhuma regra de risco aqui (isso vem na etapa da LLM/cérebro).
-- LEFT JOIN a partir da grade: célula sem dado numa fonte fica com NULL, nunca some.

CREATE OR REPLACE TABLE mapa_risco AS
SELECT
    g.cell_id,
    g.lat,
    g.lon,

    -- Topografia (DEM ativo: ver coluna fonte_dem)
    t.elevacao_m,
    t.declive_medio_graus,
    t.declive_max_graus,
    t.rugosidade_m,
    t.fonte_dem,

    -- Térmico (THEMIS, 100 m, valores relativos 0-255)
    th.ir_noite,
    th.ir_dia,
    th.amplitude_dia_noite,
    th.indice_firmeza,

    -- Geologia (SIM 3464)
    geo.unidade_simbolo,
    geo.unidade_nome,
    geo.material_escuro,
    geo.terreno_ridged,
    geo.dist_cratera_pequena_m,
    geo.dist_borda_cratera_m,
    geo.dentro_elipse_pouso,

    -- Óptico e validação (CTX ortho 6 m, Mars Trek)
    op.brilho_ctx,
    op.dif_alt_ctx_sim_m,

    -- Rota real do Perseverance (MMGIS NASA)
    rv.rover_passou,
    rv.n_paradas,
    rv.site_drive,
    rv.sol_min

FROM grade AS g
LEFT JOIN topografia AS t   USING (cell_id)
LEFT JOIN termico    AS th  USING (cell_id)
LEFT JOIN geologia   AS geo USING (cell_id)
LEFT JOIN optico     AS op  USING (cell_id)
LEFT JOIN rover      AS rv  USING (cell_id)
ORDER BY g.cell_id;
