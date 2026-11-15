"""
Gera docs/FAROL_fontes_de_dados.pdf: links, dados usados e por que foram usados.
Rodar da raiz:  python docs/gerar_pdf_fontes.py
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

FONTES = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", FONTES + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", FONTES + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVI", FONTES + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DVI", boldItalic="DVB")

SAIDA = Path(__file__).parent / "FAROL_fontes_de_dados.pdf"

AZUL = colors.HexColor("#184f95")
CINZA = colors.HexColor("#52514e")
LINHA = colors.HexColor("#d9d8d3")
FUNDO = colors.HexColor("#f1f0ec")
VERDE = colors.HexColor("#0a7a0a")
LARANJA = colors.HexColor("#b4511f")
VERMELHO = colors.HexColor("#a32d2d")

titulo = ParagraphStyle("t", fontName="DVB", fontSize=20, leading=25, textColor=colors.black, spaceAfter=4)
subt = ParagraphStyle("s", fontName="DV", fontSize=10, leading=14, textColor=CINZA, spaceAfter=14)
h1 = ParagraphStyle("h1", fontName="DVB", fontSize=14, leading=18, textColor=AZUL, spaceBefore=14, spaceAfter=6)
h2 = ParagraphStyle("h2", fontName="DVB", fontSize=11, leading=14, spaceBefore=10, spaceAfter=4)
corpo = ParagraphStyle("c", fontName="DV", fontSize=9.5, leading=13.5, alignment=TA_LEFT, spaceAfter=6)
cel = ParagraphStyle("cel", fontName="DV", fontSize=8, leading=10.5)
celb = ParagraphStyle("celb", parent=cel, fontName="DVB")
cab = ParagraphStyle("cab", parent=cel, fontName="DVB", textColor=colors.white)
link = ParagraphStyle("lk", parent=cel, textColor=AZUL)


def P(t, s=cel):
    return Paragraph(t, s)


def L(url, texto=None):
    return f'<link href="{url}" color="#184f95"><u>{texto or url}</u></link>'


def tabela(linhas, larguras, cabecalho=True):
    dados = [[c if not isinstance(c, str) else P(c) for c in l] for l in linhas]
    if cabecalho:
        dados[0] = [P(c, cab) for c in linhas[0]]
    t = Table(dados, colWidths=larguras, repeatRows=1 if cabecalho else 0)
    estilo = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINHA),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if cabecalho:
        estilo += [("BACKGROUND", (0, 0), (-1, 0), AZUL)]
        estilo += [("BACKGROUND", (0, i), (-1, i), FUNDO) for i in range(2, len(linhas), 2)]
    t.setStyle(TableStyle(estilo))
    return t


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.5)
    canvas.setFillColor(CINZA)
    canvas.drawString(18 * mm, 10 * mm, "F.A.R.O.L. · NASA Space Apps · Fontes de dados")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Página {doc.page}")
    canvas.restoreState()


W = A4[0] - 36 * mm
s = []

# ---------------- Capa / resumo ----------------
s += [
    Paragraph("F.A.R.O.L. — Fontes de dados", titulo),
    Paragraph("Field Astronaut Route &amp; Optimized Locator · Cratera Jezero, Marte · NASA Space Apps", subt),
    Paragraph("Para que serve este documento", h1),
    Paragraph(
        "Lista as <b>bases de dados indicadas pelo desafio</b>, o que encontramos em cada uma, "
        "<b>quais dados usamos, por que usamos</b> e o que ficou de fora (com o motivo). "
        "Todos os links levam à fonte oficial.", corpo),
    Paragraph(
        "<b>Área de estudo (AOI):</b> quadrado de 2 km × 2 km centrado em lat 18,4447 / lon 77,4508, "
        "no ponto de pouso do Perseverance, dentro da elipse de pouso da missão Mars 2020. "
        "A área foi dividida em <b>10.000 células de 20 m</b>; cada fonte é lida no centro de cada célula "
        "e tudo é cruzado pela chave <b>cell_id</b>.", corpo),
    Paragraph("Resumo em uma tabela", h1),
    tabela([
        ["Pergunta do projeto", "Tipo de dado", "Fonte usada", "Base do desafio"],
        ["Dá para passar sem cair?", "Topográfico", "DEM HiRISE 1 m (principal) + DEM CTX 20 m (validação)", "Mars Trek"],
        ["O chão aguenta o peso?", "Térmico", "THEMIS infravermelho noite e dia (100 m)", "USGS (SIM 3464)"],
        ["Por que o chão é assim?", "Geológico", "Mapa geológico Nili.gdb (unidades, material escuro, crateras)", "USGS (SIM 3464)"],
        ["O que se vê de cima?", "Óptico", "Mosaico CTX 6 m", "Mars Trek"],
        ["O mapa bate com a realidade?", "Rota real", "Paradas e trilha do Perseverance (NASA MMGIS)", "Perseverance"],
        ["O ambiente vai mudar?", "Atmosférico", "Nenhuma das bases do desafio tem este dado para Jezero", "—"],
    ], [38 * mm, 24 * mm, 82 * mm, W - 144 * mm]),
]

# ---------------- As 5 bases ----------------
s += [PageBreak(), Paragraph("As 5 bases indicadas pelo desafio", h1)]
s.append(tabela([
    ["Base", "Link", "Decisão", "Motivo"],
    ["<b>JPL Mars Trek</b>", L("https://trek.nasa.gov/mars/"), f'<font color="{VERDE.hexval()}"><b>USADA</b></font>',
     "Tem os modelos de terreno (DEM) e imagens de Jezero com download, e a busca por “jezero” retorna 15 produtos."],
    ["<b>USGS-NASA Planetary Geologic Mapping</b> (Interactive Maps: Mars)",
     L("https://astrogeology-usgs.hub.arcgis.com/pages/interactive-maps-mars", "astrogeology-usgs.hub.arcgis.com/…/interactive-maps-mars"),
     f'<font color="{VERDE.hexval()}"><b>USADA</b></font>',
     "Busca por “Jezero” retorna o mapa geológico SIM 3464, cujo database traz geologia, THEMIS e DTMs."],
    ["<b>Mars Perseverance Raw Images</b>", L("https://mars.nasa.gov/mars2020/multimedia/raw-images/", "mars.nasa.gov/mars2020/multimedia/raw-images"),
     f'<font color="{VERDE.hexval()}"><b>USADA</b></font>',
     "1.055.868 imagens com metadados (sol, câmera, site/drive). A rota oficial do rover, do mesmo site, liga as fotos ao mapa."],
    ["<b>Curiosity’s Proposed Path up Mount Sharp</b>",
     L("https://science.nasa.gov/resource/curiositys-proposed-path-up-mount-sharp/", "science.nasa.gov/resource/curiositys-proposed-path-up-mount-sharp"),
     f'<font color="{VERMELHO.hexval()}"><b>NÃO USADA</b></font>',
     "Só oferece um GIF (1041 × 586), sem dados, de outra cratera (Gale). Serve apenas como inspiração visual."],
    ["<b>NASA Worldview</b>", L("https://worldview.earthdata.nasa.gov/"), f'<font color="{VERMELHO.hexval()}"><b>NÃO USADA</b></font>',
     "1.346 camadas, todas da Terra (projeções ártica, antártica e geográfica). Nenhuma de Marte."],
], [42 * mm, 52 * mm, 20 * mm, W - 114 * mm]))

# ---------------- Dados usados ----------------
s += [PageBreak(), Paragraph("Dados que usamos, de onde vieram e por quê", h1)]

itens = [
    ("1. Topografia principal — MRO HiRISE, Jezero DEM, Controlled",
     [["Base", "Mars Trek → busca “jezero” → <i>MRO HiRISE, Jezero DEM, Controlled</i> → Download"],
      ["Link", L("https://trek.nasa.gov/mars/")],
      ["Arquivo", "JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif (1,84 GB), recortado para hirise_aoi.tif (9,5 MB)"],
      ["O que é", "Modelo de elevação de <b>1 m por pixel</b>, feito por estéreo da câmera HiRISE (sonda MRO). Feito pela USGS para o pouso autônomo do Perseverance (Terrain Relative Navigation)."],
      ["O que extraímos", "Altitude, <b>declive médio</b>, <b>declive máximo</b> (pior trecho de 1 m dentro da célula) e rugosidade."],
      ["Por que usamos", "É o dado mais detalhado de Jezero: enxerga degraus e pedras que dados de 20 m não veem. Revelou <b>220 “degraus escondidos”</b> e 6× mais células perigosas que o CTX."]]),
    ("2. Topografia de validação — MRO CTX, Jezero DEM, Controlled",
     [["Base", "Mars Trek → <i>MRO CTX, Jezero DEM, Controlled</i>"],
      ["Arquivo", "JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif (9,7 MB)"],
      ["O que é", "Modelo de elevação de 20 m (câmera CTX, sonda MRO), da mesma série do HiRISE."],
      ["Por que usamos", "Reserva enquanto o HiRISE baixava e <b>controle de qualidade</b>: diferença média de −1,9 m em relação ao HiRISE (as fontes concordam)."]]),
    ("3. Térmico — THEMIS infravermelho noite e dia (Mars Odyssey)",
     [["Base", "USGS SIM 3464 → database → Rasters/USGS_THEMIS_IR_controlled_mosaic_oct2018"],
      ["Link", L("https://pubs.usgs.gov/publication/sim3464") + " · download: " + L("https://pubs.usgs.gov/sim/3464/sim3464_database.zip", "sim3464_database.zip")],
      ["Arquivos", "nili_THEMIS_NightIR_Controlled_oct2018.tif e nili_THEMIS_DayIR_Controlled_oct2018.tif (100 m)"],
      ["O que é", "Brilho infravermelho reescalado (0–255) de noite e de dia. <b>Não é temperatura</b>."],
      ["O que extraímos", "Amplitude dia − noite e um <b>índice de firmeza do solo</b> (0 = mais solto, 1 = mais firme, relativo à área)."],
      ["Por que usamos", "Rocha firme varia pouco de temperatura; poeira e areia soltas esquentam e esfriam muito. É o único dado que mostra o <b>solo solto</b> — o perigo que a câmera não vê."]]),
    ("4. Geologia — mapa geológico Nili.gdb (USGS SIM 3464)",
     [["Base", "USGS SIM 3464 → database → Geodatabase/Nili.gdb"],
      ["Link", L("https://pubs.usgs.gov/publication/sim3464")],
      ["Camadas usadas", "GeoUnits_v1 (unidades), SurfaceFeatures (material escuro de cobertura), LocationFeatures (crateras pequenas), LinearFeatures (bordas de cratera), LandingEllipse (elipse de pouso)"],
      ["O que extraímos", "Unidade geológica de cada célula (<i>Jezero floor</i> / <i>Lower etched</i>), se cai em material escuro, distância até cratera pequena, se está na elipse de pouso."],
      ["Por que usamos", "Segunda opinião, feita por geólogos: <b>54% das células de possível solo solto</b> também caem em material escuro de cobertura (contra 6% das células seguras). Não é totalmente independente do térmico (os autores consultaram o THEMIS noturno) e o mapa pode estar deslocado 100–200 m."]]),
    ("5. Óptico — MRO CTX, Jezero Mosaic, Controlled",
     [["Base", "Mars Trek → <i>MRO CTX, Jezero Mosaic, Controlled</i>"],
      ["Arquivo", "JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0.tif (36 MB, 6 m, tons de cinza)"],
      ["O que extraímos", "Brilho médio de cada célula; fundo visual dos mapas e do dashboard."],
      ["Por que usamos", "Para provar que <b>a câmera quase não enxerga o solo solto</b>: o brilho cai só de 131 para 126 nas armadilhas, enquanto a firmeza cai de 0,68 para 0,15."]]),
    ("6. Rota real do Perseverance — NASA MMGIS",
     [["Base", "Site oficial da missão Mars 2020 (mesmo domínio das Raw Images)"],
      ["Links", L("https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_waypoints.json", "M20_waypoints.json") + " (708 paradas) · " +
       L("https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_traverse.json", "M20_traverse.json") + " (trilha)"],
      ["Arquivos", "m20_waypoints_aoi.csv (108 paradas na área) e m20_traverse_aoi.csv (4.603 pontos), já no repositório"],
      ["O que extraímos", "Por quais células o rover passou, onde parou, o sol e a chave <b>site_drive</b>."],
      ["Por que usamos", "<b>Comparação com a realidade</b>: só 5 das 271 células da rota (1,8%) são íngremes, então a NASA evitou declives como o mapa faria. Mas 101 células da rota (37%) estão marcadas como possível solo solto e o rover passou por elas: esse alerta é para checar, não proibição. E o site_drive liga as 1,05 milhão de fotos ao mapa."]]),
    ("7. Imagens do rover — Mars Perseverance Raw Images (próxima fase)",
     [["Link", L("https://mars.nasa.gov/mars2020/multimedia/raw-images/") + " · API: " +
       L("https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020&feedtype=json&ver=1.2&num=100&page=0&order=sol+desc", "rss/api (JSON)")],
      ["O que tem", "1.055.868 imagens; campos imageid, sol, camera.instrument, site, drive, image_files, date_taken_utc."],
      ["Por que vamos usar", "É a vista do chão (como a câmera do capacete). Pelo volume, é o módulo que justifica PySpark (bronze → prata → ouro)."]]),
]
for titulo_item, linhas in itens:
    s.append(KeepTogether([Paragraph(titulo_item, h2),
                           tabela([[f"<b>{a}</b>", b] for a, b in linhas], [32 * mm, W - 32 * mm], cabecalho=False)]))

# ---------------- Descartados ----------------
s += [PageBreak(), Paragraph("O que encontramos e decidimos NÃO usar", h1),
      Paragraph("Tão importante quanto escolher dados é justificar o que fica de fora.", corpo)]
s.append(tabela([
    ["Dado", "Onde estava", "Motivo"],
    ["MRO HiRISE, DEM e Mosaic Columbia Hills", "Mars Trek", "Outra cratera (Gusev), não cobre Jezero."],
    ["MRO HiRISE, DEM e Mosaic Jezero NE Syrtis Midway", "Mars Trek", "10 GB e 25 GB, região maior; o HiRISE Jezero já cobre a área."],
    ["MRO HiRISE, Jezero Mosaic, Controlled (25 cm)", "Mars Trek", "9,8 GB. Fica para a fase de HUD/demo, recortado só na área."],
    ["MRO CTX, Jezero Mosaic, Preliminary", "Mars Trek", "Versão preliminar do mosaico controlado que usamos."],
    ["Mars 2020 Candidate Landing Site", "Mars Trek", "Locais candidatos de 2017; já temos a elipse final no SIM 3464."],
    ["MGS TES Thermal Inertia, TES Dust, MOLA (global)", "Mars Trek", "Resolução de quilômetros: um pixel cobre a área inteira."],
    ["DTM CTX B18 e ortoimagem B17", "SIM 3464", "Não cobrem a área de estudo."],
    ["DEM e hillshade HRSC (75 m)", "SIM 3464", "Grossos demais para células de 20 m; hillshade é imagem derivada."],
    ["DTM CTX J03 do SIM 3464", "SIM 3464", "Usado só como checagem (Trek − SIM = −5,1 m em média)."],
    ["GeoContacts, Figures, anotações, T_*", "SIM 3464 (Nili.gdb)", "Limites repetidos, figuras e controle interno do mapa."],
    ["MEDA (estação meteorológica do Perseverance)", "Fora das bases do desafio", "Decisão do time: fora desta fase."],
    ["Dado atmosférico", "—", "Nenhuma das 5 bases tem para Jezero. Limitação declarada."],
], [62 * mm, 36 * mm, W - 98 * mm]))

s += [Paragraph("Integridade do cruzamento", h1),
      Paragraph(
          "• Uma <b>grade mestre</b> de 10.000 células com cell_id fixo; cada fonte é lida no centro da célula, "
          "sem reprojetar nem interpolar o dado original.<br/>"
          "• Valores sem dado viram nulo (nunca 0); THEMIS 0 é tratado como sem cobertura.<br/>"
          "• Cada ETL confere 10.000 linhas, cell_id único e faixas de valores; o JOIN no DuckDB confere que nada se perdeu ou duplicou.<br/>"
          "• Correções registradas: 3 geometrias inválidas corrigidas e o erro de digitação “Crater riim unit” padronizado.", corpo),
      Paragraph("Créditos", h1),
      Paragraph("NASA/JPL-Caltech (Mars Trek, MRO, Mars 2020) · University of Arizona (HiRISE) · MSSS (CTX) · "
                "Arizona State University (THEMIS) · USGS Astrogeology Science Center — Sun, V.Z. &amp; Stack, K.M. (2020), "
                "<i>Geologic Map of Jezero Crater and the Nili Planum Region, Mars</i>, USGS SIM 3464, "
                + L("https://doi.org/10.3133/sim3464", "doi.org/10.3133/sim3464") + ".", corpo)]

doc = SimpleDocTemplate(str(SAIDA), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=16 * mm, bottomMargin=18 * mm,
                        title="F.A.R.O.L. — Fontes de dados", author="Time F.A.R.O.L.")
doc.build(s, onFirstPage=rodape, onLaterPages=rodape)
print(f"PDF salvo em {SAIDA}")
