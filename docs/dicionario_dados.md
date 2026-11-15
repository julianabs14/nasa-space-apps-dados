# Dicionário de dados — `mapa_risco`

Uma linha por célula de **20 m × 20 m** numa área de **2 km × 2 km** em Jezero, Marte
(centro: lat 18.4447, lon 77.4508, dentro da elipse de pouso do Perseverance). Total: **10.000 células**.

Regra geral: célula sem dado numa fonte fica **nula (NULL)**. Nenhum valor é inventado nem preenchido com 0.

## Fontes

| Fonte | Arquivo | Base oficial do desafio | Resolução | Projeção original |
|---|---|---|---|---|
| DTM CTX (provisório) | `J03_045994_1986_J03_046060_1986_20m_DTM.tif` | USGS-NASA Planetary Geologic Mapping Program (SIM 3464) | 20,2 m | Equiretangular, meridiano 180° |
| DEM HiRISE (definitivo, em download) | `JEZ_hirise_soc_006_DTM_..._1m_...tif` | Mars Trek | 1 m | Equiretangular, meridiano 0° |
| THEMIS IR noite/dia | `nili_THEMIS_{Night,Day}IR_Controlled_oct2018.tif` | SIM 3464 | 100 m | Transversa de Mercator 77,5°E |
| Mapa geológico | `Nili.gdb` | SIM 3464 | vetorial | Transversa de Mercator 77,5°E |

**Grade mestre:** Transversa de Mercator 77,5°E (metros reais). Para cada fonte, o **centro da célula** é convertido
para a projeção da fonte e o valor é lido ali. Os dados originais não são reprojetados nem interpolados.

## Colunas

### Identificação (`etl/grade.py`)
| Coluna | Unidade | Descrição |
|---|---|---|
| `cell_id` | – | Chave da célula. `r000_c000` = canto noroeste. Não muda quando o DEM é trocado. |
| `lat`, `lon` | graus | Centro da célula (Marte esférico, R = 3.396.190 m) |

### Topografia (`etl/topografia.py`)
| Coluna | Unidade | Descrição |
|---|---|---|
| `elevacao_m` | m | Altitude em relação ao geoide de Marte ("nível do mar"). Negativa em Jezero. |
| `declive_medio_graus` | ° | Inclinação do terreno. Com CTX: valor do pixel no centro. Com HiRISE: média dos ~400 pixels da célula. |
| `declive_max_graus` | ° | Maior inclinação dentro da célula. **Só existe com HiRISE** (com CTX fica nulo: 1 pixel por célula). |
| `rugosidade_m` | m | Desvio-padrão da elevação numa janela 3×3 pixels. Com CTX (20 m) acompanha o declive quase 1:1; com HiRISE (1 m) mostra irregularidade fina. |
| `fonte_dem` | – | Nome do arquivo DEM usado, para rastreabilidade. |

### Térmico (`etl/termico.py`)
| Coluna | Unidade | Descrição |
|---|---|---|
| `ir_noite` | 0–255 | Brilho infravermelho noturno THEMIS. **Não é temperatura**: valor reescalado. Maior = mais quente à noite. 0 na fonte = sem dado → NULL. |
| `ir_dia` | 0–255 | Mesmo, de dia. |
| `amplitude_dia_noite` | 0–255 | `ir_dia − ir_noite`. Alta = varia muito entre dia e noite (típico de poeira/areia solta). |
| `indice_firmeza` | 0–1 | **Hipótese do time**, relativa à AOI: média de `ir_noite` normalizado e `1 − amplitude` normalizada (percentis 5–95). 1 = mais firme da AOI. |

Observação: o THEMIS tem 100 m/pixel, então ~25 células vizinhas compartilham o mesmo valor térmico.

### Geologia (`etl/geologia.py`)
| Coluna | Unidade | Descrição |
|---|---|---|
| `unidade_simbolo` | – | Símbolo da unidade geológica (ex.: `Njf`, `Nle`) |
| `unidade_nome` | – | Nome da unidade (ex.: "Jezero floor unit") |
| `material_escuro` | sim/não | Centro da célula dentro de "dark-colored mantling material" |
| `terreno_ridged` | sim/não | Centro da célula dentro de terreno "ridged" |
| `dist_cratera_pequena_m` | m | Distância até a cratera pequena mapeada mais próxima |
| `dist_borda_cratera_m` | m | Distância até a crista de borda de cratera mapeada mais próxima |
| `dentro_elipse_pouso` | sim/não | Centro dentro da elipse de pouso do Mars 2020 |

## Correções aplicadas na fonte (registradas)
- `GeoUnits_v1`: 2 geometrias inválidas corrigidas com `make_valid`.
- `SurfaceFeatures`: 1 geometria inválida corrigida com `make_valid`.
- `GeoUnits_v1`: nome "Crater riim unit" padronizado para "Crater rim unit" (erro de digitação da fonte; não ocorre na AOI).

## Limitações conhecidas
- Térmico é relativo (0–255), não temperatura nem inércia térmica calibrada.
- `indice_firmeza` é um índice proposto pelo time, não um produto da NASA.
- Material escuro (mapa geológico) e THEMIS podem não ser totalmente independentes: os autores do mapa tinham o THEMIS entre as bases usadas no mapeamento.
- Dado atmosférico: sem fonte nesta fase.
- THEMIS tem 100 m por pixel: a AOI inteira tem 400 pixels térmicos e só 384 combinações dia/noite. A firmeza muda em blocos de 5 × 5 células.
- `indice_firmeza` é normalizado pelos percentis 5–95 da própria AOI, então é relativo: uma parte da área sempre sai "solta". `ir_noite` e a amplitude têm correlação de −0,97 (quase a mesma informação).
- O mapa geológico SIM 3464 foi desenhado sobre mosaico semicontrolado e pode ter deslocamento de 100–200 m (metadados USGS). Perto de fronteiras, unidade e material escuro podem estar na célula errada.
- A rota do rover passou por 101 células `amarelo_armadilha` (37% da rota): a classe é um alerta para checar o chão, não uma proibição.
- `dentro_elipse_pouso` é verdadeiro e `terreno_ridged` é falso em todas as 10.000 células: não servem para decidir nesta AOI.

## Tabela `decisao` (`elt/sql/decisao.sql`)
| Coluna | Descrição |
|---|---|
| `classe` | `verde` (plano e firme), `amarelo_declive` (íngreme e firme), `amarelo_armadilha` (plano, possível solo solto: checar antes de pisar), `vermelho` (íngreme e solto), `sem_dado` |
| `perto_cratera` | célula a menos de `DIST_CRATERA_ATENCAO_M` de uma cratera pequena mapeada |
| `motivo` | texto com os fatores que levaram à classe (base do contexto da LLM na próxima fase) |

Limites usados (config.py, hipóteses do time): íngreme = declive ≥ 10°; solto = indice_firmeza < 0,35; perto de cratera = < 30 m.
