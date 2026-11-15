# Perguntas de decisão — AOI Jezero

Limites: declive ≥ 10° = íngreme; firmeza < 0.35 = solo solto; cratera a < 30 m = atenção.

## 1. Quanto da área cai em cada classe?

| classe            |   celulas |   pct_area |   km2 |
|:------------------|----------:|-----------:|------:|
| verde             |      7370 |       73.7 |  2.95 |
| amarelo_armadilha |      2323 |       23.2 |  0.93 |
| amarelo_declive   |       200 |        2   |  0.08 |
| vermelho          |       107 |        1.1 |  0.04 |

## 2. Planas, mas com possível solo solto: onde o mapa geológico também mostra material escuro?

| com_material_escuro_no_mapa   |   celulas |   firmeza_media |   declive_medio |
|:------------------------------|----------:|----------------:|----------------:|
| True                          |      1249 |             0.1 |             2.8 |
| False                         |      1074 |             0.2 |             4   |

## 3. Risco por unidade geológica

| unidade_nome      |   celulas |   pct_verde |   pct_amarelo |   pct_vermelho |
|:------------------|----------:|------------:|--------------:|---------------:|
| Jezero floor unit |      5044 |        66.2 |          31.9 |            1.9 |
| Lower etched unit |      4956 |        81.3 |          18.5 |            0.2 |

## 4. As 5 células mais críticas (para checar no QGIS / fotos)

| cell_id   |     lat |     lon | classe   | motivo                                                                                                |
|:----------|--------:|--------:|:---------|:------------------------------------------------------------------------------------------------------|
| r020_c090 | 18.4547 | 77.4652 | vermelho | declive 18.0°; solo possivelmente solto (firmeza 0.06); material escuro de cobertura (mapa geológico) |
| r020_c089 | 18.4547 | 77.4648 | vermelho | declive 17.2°; solo possivelmente solto (firmeza 0.06); material escuro de cobertura (mapa geológico) |
| r020_c091 | 18.4547 | 77.4656 | vermelho | declive 17.1°; solo possivelmente solto (firmeza 0.06); material escuro de cobertura (mapa geológico) |
| r021_c091 | 18.4543 | 77.4656 | vermelho | declive 14.3°; solo possivelmente solto (firmeza 0.06); material escuro de cobertura (mapa geológico) |
| r020_c088 | 18.4547 | 77.4645 | vermelho | declive 13.3°; solo possivelmente solto (firmeza 0.06); material escuro de cobertura (mapa geológico) |

## 5. A câmera (CTX 6 m) enxerga as armadilhas? Brilho médio por classe

| classe            |   celulas |   brilho_medio |   firmeza_media |
|:------------------|----------:|---------------:|----------------:|
| verde             |      7370 |          130.8 |            0.68 |
| amarelo_armadilha |      2323 |          126.4 |            0.15 |
| amarelo_declive   |       200 |          123.6 |            0.6  |
| vermelho          |       107 |          128.8 |            0.21 |

## 6. Comparação com a rota real: por onde o Perseverance andou, o que nosso mapa dizia?

| classe            |   celulas_na_rota |   pct_da_rota |   declive_medio |   firmeza_media |
|:------------------|------------------:|--------------:|----------------:|----------------:|
| verde             |               165 |          60.9 |             3.2 |            0.56 |
| amarelo_armadilha |               101 |          37.3 |             3.3 |            0.21 |
| amarelo_declive   |                 3 |           1.1 |            11.9 |            0.52 |
| vermelho          |                 2 |           0.7 |            10.3 |            0.27 |

## 7. Degraus escondidos (só o HiRISE de 1 m enxerga): plano na média, íngreme em algum trecho

| classe            |   celulas_com_degrau |   declive_medio |   pior_trecho |
|:------------------|---------------------:|----------------:|--------------:|
| verde             |                  187 |             7.6 |          35.2 |
| amarelo_armadilha |                   33 |             7.2 |          28.3 |
