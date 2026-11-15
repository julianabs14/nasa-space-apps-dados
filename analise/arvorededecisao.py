import heapq
import re
import duckdb
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text


class MotorCamadaJev:
    def __init__(self, caminho_db="data/farol.duckdb"):
        # 1. Carrega o terreno REAL de Jezero direto do banco do pipeline F.A.R.O.L.
        self.con = duckdb.connect(caminho_db, read_only=True)
        df = self.con.execute("""
            SELECT cell_id, declive_medio_graus AS declividade, indice_firmeza AS firmeza, classe
            FROM decisao
            WHERE classe <> 'sem_dado'
              AND declive_medio_graus IS NOT NULL
              AND indice_firmeza IS NOT NULL
        """).df()

        self.features = ["declividade", "firmeza"]
        X = df[self.features]
        y = df["classe"]  # verde, amarelo_armadilha, amarelo_declive, vermelho

        # 2. Treina a Árvore de Decisão (profundidade 4 para manter regras claras)
        self.modelo_jev = DecisionTreeClassifier(max_depth=4, random_state=42)
        self.modelo_jev.fit(X, y)

        # 3. Exibe as regras aprendidas pela árvore ao inicializar
        print("=== REGRAS APRENDIDAS PELA ÁRVORE (CAMADA JEV) ===")
        print(export_text(self.modelo_jev, feature_names=self.features))

        # 4. Mapeia células de risco do banco para o roteador A* e inicia controle Human-in-the-Loop
        self.celulas_bloqueadas_db = set(
            self.con.execute("""
                SELECT cell_id FROM decisao
                WHERE classe IN ('vermelho', 'amarelo_armadilha', 'sem_dado')
            """).df()["cell_id"].tolist()
        )
        self.status_decisao = "NOMINAL"   # NOMINAL | PENDENTE | ACEITA | RECUSADA
        self.sugestao_atual = None
        self.historico_log = []

    def _explicar_caminho_arvore(self, entrada_df):
        """Extrai o caminho exato dos nós percorridos na árvore para exibir no Painel do Rover."""
        arvore = self.modelo_jev.tree_
        caminho = self.modelo_jev.decision_path(entrada_df).indices
        regras = []
        for no in caminho[:-1]:
            feat = self.features[arvore.feature[no]]
            limiar = round(float(arvore.threshold[no]), 2)
            valor = round(float(entrada_df[feat].values[0]), 2)
            op = "<=" if valor <= limiar else ">"
            regras.append(f"{feat} ({valor}) {op} {limiar}")
        return " E ".join(regras)

    # --------------------------------------------------------------------------
    # ROTEAMENTO A* COMPATÍVEL COM O PADRÃO 'r050_c050' DO F.A.R.O.L.
    # --------------------------------------------------------------------------
    @staticmethod
    def _parse_cell_id(cell_id):
        m = re.match(r"^r(\d+)_c(\d+)$", cell_id)
        if not m:
            raise ValueError(f"Formato de cell_id inválido: {cell_id}")
        return int(m.group(1)), int(m.group(2))

    @staticmethod
    def _format_cell_id(r, c):
        return f"r{r:03d}_c{c:03d}"

    def calcular_desvio_a_star(self, cell_origem, cell_destino, max_r=100, max_c=100):
        """Calcula rota alternativa desviando das células 'vermelho' e 'amarelo_armadilha'."""
        inicio = self._parse_cell_id(cell_origem)
        fim = self._parse_cell_id(cell_destino)

        fila = [(0, inicio)]
        veio_de = {inicio: None}
        custo_ate = {inicio: 0}

        while fila:
            _, atual = heapq.heappop(fila)
            if atual == fim:
                break

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = atual[0] + dr, atual[1] + dc
                if 0 <= nr < max_r and 0 <= nc < max_c:
                    viz_id = self._format_cell_id(nr, nc)
                    if viz_id in self.celulas_bloqueadas_db and (nr, nc) != fim:
                        continue
                    novo_custo = custo_ate[atual] + 1
                    if (nr, nc) not in custo_ate or novo_custo < custo_ate[(nr, nc)]:
                        custo_ate[(nr, nc)] = novo_custo
                        heuristica = abs(fim[0] - nr) + abs(fim[1] - nc)
                        heapq.heappush(fila, (novo_custo + heuristica, (nr, nc)))
                        veio_de[(nr, nc)] = atual

        if fim not in veio_de:
            return [], 0

        caminho = []
        curr = fim
        while curr is not None:
            caminho.append(self._format_cell_id(*curr))
            curr = veio_de[curr]
        caminho.reverse()
        distancia_m = (len(caminho) - 1) * 20  # cada célula tem 20m
        return caminho, distancia_m

    # --------------------------------------------------------------------------
    # AVALIAÇÃO EM TEMPO REAL (PAINEL DO ROVER + VISOR DO CAPACETE)
    # --------------------------------------------------------------------------
    def avaliar_situacao(self, cell_id, d_pressao, o2, mineral, cell_destino=None):
        celula = self.con.execute("""
            SELECT declive_medio_graus AS declividade, indice_firmeza AS firmeza, motivo
            FROM decisao WHERE cell_id = ?
        """, [cell_id]).df()

        if celula.empty:
            return {"erro": f"célula {cell_id} não existe no banco"}
        if celula[self.features].isna().any().any():
            return {"erro": f"célula {cell_id} marcada como 'sem_dado' no banco"}

        # 1. Classificação do terreno pela Árvore de Decisão
        entrada_terreno = celula[self.features]
        terreno = self.modelo_jev.predict(entrada_terreno)[0]
        confianca = round(float(self.modelo_jev.predict_proba(entrada_terreno).max() * 100), 1)
        regra_arvore = self._explicar_caminho_arvore(entrada_terreno)
        motivo_banco = celula["motivo"].iloc[0]

        # 2. Fusão com sensores em tempo real + guardrails de segurança
        if d_pressao < -10:
            classe = 3
        elif terreno in ("amarelo_armadilha", "vermelho"):
            classe = 2
        elif terreno == "amarelo_declive" and o2 > 1.2:
            classe = 1
        elif mineral == 1 and terreno == "verde":
            classe = 4
        else:
            classe = 0

        # 3. Se for desvio (classe 2) e houver destino, calcula rota alternativa A*
        rota_alt, dist_alt_m = ([], 0)
        if classe == 2 and cell_destino:
            rota_alt, dist_alt_m = self.calcular_desvio_a_star(cell_id, cell_destino)

        sugestoes = {
            0: ("ROTA LIVRE", "Manter trajeto e velocidade nominal.", "ROTA LIVRE", "VERDE"),
            1: ("REDUZIR RITMO", "Consumo de O2 elevado para o aclive. Reduzir velocidade em 20%?", "O2 ALTO: REDUZIR RITMO 20%", "AMBAR"),
            2: ("DESVIO SUGERIDO", f"Solo possivelmente solto à frente ({terreno}). Rota alternativa: {dist_alt_m}m.", "SOLO INSTAVEL: DESVIO SUGERIDO", "AMBAR"),
            3: ("PARADA E ABRIGO", "Queda brusca de pressão (Dust Devil). Parar e ancorar imediatamente?", "DUST DEVIL: PARAR E ANCORAR", "VERMELHO"),
            4: ("ALVO CIENTÍFICO", "Assinatura mineral detectada na margem. Pausar 3 min para coleta?", "ALVO MINERAL: PARAR 3 MIN?", "AZUL"),
        }
        titulo, msg_rover, msg_hud, cor = sugestoes[classe]

        # Se tudo está normal e não há pendência
        if classe == 0 and self.status_decisao != "PENDENTE":
            self.status_decisao = "NOMINAL"
            return {
                "cell_id": cell_id,
                "status": self.status_decisao,
                "terreno": terreno,
                "classe": classe,
                "rover": {
                    "titulo": titulo,
                    "mensagem": msg_rover,
                    "confianca_terreno": confianca,
                    "regra_arvore": regra_arvore,
                    "motivo_banco": motivo_banco,
                    "rota_alternativa": None,
                },
                "capacete": {
                    "hud": msg_hud,
                    "cor": cor,
                    "pedir_confirmacao": False,
                },
            }

        # Caso contrário, abre sugestão Human-in-the-Loop aguardando resposta
        self.status_decisao = "PENDENTE"
        self.sugestao_atual = {
            "cell_id": cell_id,
            "terreno": terreno,
            "classe": classe,
            "titulo": titulo,
            "confianca_terreno": confianca,
            "regra_arvore": regra_arvore,
            "motivo_banco": motivo_banco,
            "rota_alternativa": rota_alt if rota_alt else None,
        }

        return {
            "cell_id": cell_id,
            "status": self.status_decisao,
            "terreno": terreno,
            "classe": classe,
            "rover": {
                "titulo": titulo,
                "mensagem": msg_rover,
                "confianca_terreno": confianca,
                "regra_arvore": regra_arvore,
                "motivo_banco": motivo_banco,
                "rota_alternativa": rota_alt if rota_alt else None,
            },
            "capacete": {
                "hud": f"{msg_hud} [ACEITAR / RECUSAR]",
                "cor": cor,
                "pedir_confirmacao": True,
            },
        }

    def confirmar_decisao(self, resposta):
        """Registra a escolha do astronauta (ACEITAR ou RECUSAR) no log da missão."""
        if self.status_decisao != "PENDENTE":
            return {"aviso": "Nenhuma sugestão pendente."}

        aceita = resposta.strip().upper() in ("ACEITAR", "OK", "SIM", "TRUE")
        self.status_decisao = "ACEITA" if aceita else "RECUSADA"
        registro = {**self.sugestao_atual, "decisao_humana": self.status_decisao}
        self.historico_log.append(registro)
        return registro

    def fechar(self):
        self.con.close()


# ==============================================================================
# TESTES COM AS CÉLULAS REAIS DO BANCO farol.duckdb
# ==============================================================================
if __name__ == "__main__":
    jev = MotorCamadaJev("data/farol.duckdb")

    # 1. Célula verde, tudo normal
    print("\n1. NORMAL:", jev.avaliar_situacao("r050_c050", d_pressao=0.5, o2=0.9, mineral=0))

    # 2. Armadilha real no banco (calcula desvio A* até r095_c040 e aguarda confirmação)
    print("\n2. ARMADILHA:", jev.avaliar_situacao("r092_c034", d_pressao=0.0, o2=0.9, mineral=0, cell_destino="r095_c040"))
    print("   -> ASTRONAUTA RESPONDE:", jev.confirmar_decisao("ACEITAR"))

    # 3. Redemoinho de poeira (regra fixa de segurança d_pressao < -10)
    print("\n3. DUST DEVIL:", jev.avaliar_situacao("r050_c050", d_pressao=-14.5, o2=1.4, mineral=0))
    print("   -> ASTRONAUTA RESPONDE:", jev.confirmar_decisao("ACEITAR"))

    # 4. Mineral em terreno seguro
    print("\n4. MINERAL:", jev.avaliar_situacao("r050_c050", d_pressao=0.3, o2=0.9, mineral=1))
    print("   -> ASTRONAUTA RESPONDE:", jev.confirmar_decisao("RECUSAR"))

    # 5. Aclive + O2 alto
    print("\n5. ACLIVE + O2:", jev.avaliar_situacao("r006_c018", d_pressao=0.0, o2=1.6, mineral=0))
    print("   -> ASTRONAUTA RESPONDE:", jev.confirmar_decisao("ACEITAR"))

    jev.fechar()