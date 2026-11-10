"""
Gera um banco SQLite com dados FICTÍCIOS de uma plataforma de delivery.

Por que dados fictícios?
- Não exigem conta no Kaggle nem download.
- Não têm problema de licença ou de privacidade.
- São reproduzíveis: a semente (SEED) faz o script gerar sempre os mesmos dados,
  então as perguntas de avaliação têm sempre a mesma resposta correta.

Os dados têm padrões "escondidos" de propósito (horário de pico atrasa mais,
bicicleta em distâncias longas atrasa mais, atraso derruba a nota da avaliação),
para que as perguntas de análise tenham respostas interessantes.

Uso:
    python dados/gerar_dados.py
"""

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
CAMINHO_BANCO = Path(__file__).parent / "delivery.db"

N_CLIENTES = 1500
N_RESTAURANTES = 60
N_ENTREGADORES = 120
N_PEDIDOS = 12000
INICIO = datetime(2025, 1, 1)
FIM = datetime(2025, 12, 31, 23, 59)

CIDADES = {  # cidade: peso (participação no volume de pedidos)
    "São Paulo": 35,
    "Porto Alegre": 20,
    "Osasco": 10,
    "Curitiba": 15,
    "Belo Horizonte": 12,
    "Recife": 8,
}

PRIMEIROS_NOMES = [
    "Ana", "Bruno", "Carla", "Diego", "Eduarda", "Felipe", "Gabriela", "Henrique",
    "Isabela", "João", "Karina", "Lucas", "Mariana", "Nicolas", "Olívia", "Pedro",
    "Rafaela", "Samuel", "Tainá", "Vitor", "Yasmin", "Leonardo", "Beatriz", "Mateus",
    "Larissa", "Gustavo", "Camila", "Rodrigo", "Juliana", "Thiago",
]
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa", "Rodrigues",
    "Almeida", "Nascimento", "Carvalho", "Gomes", "Martins", "Rocha", "Ribeiro",
    "Fernandes", "Barbosa", "Dias", "Moreira", "Teixeira",
]

# categoria: lista de (produto, preço mínimo, preço máximo)
CARDAPIO = {
    "Pizza": [("Pizza Margherita", 45, 60), ("Pizza Calabresa", 45, 62), ("Pizza Quatro Queijos", 52, 70), ("Refrigerante 2L", 10, 14)],
    "Japonesa": [("Combinado 20 peças", 55, 80), ("Temaki Salmão", 25, 35), ("Yakisoba", 35, 48), ("Missoshiru", 10, 15)],
    "Hambúrguer": [("Hambúrguer Clássico", 28, 38), ("Hambúrguer Duplo", 36, 48), ("Batata Frita", 15, 22), ("Milkshake", 18, 25)],
    "Brasileira": [("Prato Feito", 22, 32), ("Feijoada", 38, 50), ("Parmegiana", 40, 55), ("Suco Natural", 9, 13)],
    "Saudável": [("Salada Completa", 28, 38), ("Bowl de Frango", 32, 42), ("Wrap Integral", 24, 32), ("Suco Detox", 12, 16)],
    "Doces": [("Bolo de Pote", 14, 20), ("Açaí 500ml", 22, 30), ("Brigadeiros (6 un.)", 18, 24), ("Torta Fatia", 15, 22)],
    "Mexicana": [("Burrito", 32, 42), ("Tacos (3 un.)", 30, 40), ("Nachos", 28, 36), ("Guacamole", 15, 20)],
}
PREFIXOS_RESTAURANTE = ["Casa", "Cantinho", "Empório", "Point", "Sabor", "Ponto", "Recanto", "Estação"]
SUFIXOS_RESTAURANTE = ["do Chef", "da Vila", "Central", "Express", "da Esquina", "Gourmet", "Prime", "da Praça"]

VEICULOS = {"moto": 60, "bicicleta": 25, "carro": 15}
VELOCIDADE_MIN_POR_KM = {"moto": 2.5, "bicicleta": 4.0, "carro": 3.2}
FORMAS_PAGAMENTO = {"cartao_credito": 45, "pix": 35, "cartao_debito": 15, "dinheiro": 5}


def escolher_ponderado(rng, opcoes: dict):
    return rng.choices(list(opcoes), weights=list(opcoes.values()), k=1)[0]


def nome_pessoa(rng):
    return f"{rng.choice(PRIMEIROS_NOMES)} {rng.choice(SOBRENOMES)}"


def fmt(dt: datetime | None):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


def data_aleatoria(rng, inicio: datetime, fim: datetime) -> datetime:
    segundos = int((fim - inicio).total_seconds())
    return inicio + timedelta(seconds=rng.randint(0, segundos))


def hora_do_pedido(rng) -> int:
    # Picos no almoço (11h-13h) e no jantar (18h-21h)
    pesos = {h: 1 for h in range(8, 24)}
    for h in (11, 12, 13):
        pesos[h] = 6
    for h in (18, 19, 20, 21):
        pesos[h] = 8
    return escolher_ponderado(rng, pesos)


def criar_tabelas(con: sqlite3.Connection):
    con.executescript(
        """
        DROP TABLE IF EXISTS avaliacoes;
        DROP TABLE IF EXISTS itens_pedido;
        DROP TABLE IF EXISTS pedidos;
        DROP TABLE IF EXISTS entregadores;
        DROP TABLE IF EXISTS restaurantes;
        DROP TABLE IF EXISTS clientes;

        CREATE TABLE clientes (
            id             INTEGER PRIMARY KEY,
            nome           TEXT NOT NULL,
            cidade         TEXT NOT NULL,
            data_cadastro  TEXT NOT NULL
        );

        CREATE TABLE restaurantes (
            id             INTEGER PRIMARY KEY,
            nome           TEXT NOT NULL,
            categoria      TEXT NOT NULL,
            cidade         TEXT NOT NULL,
            data_cadastro  TEXT NOT NULL
        );

        CREATE TABLE entregadores (
            id             INTEGER PRIMARY KEY,
            nome           TEXT NOT NULL,
            veiculo        TEXT NOT NULL CHECK (veiculo IN ('moto', 'bicicleta', 'carro')),
            cidade         TEXT NOT NULL
        );

        CREATE TABLE pedidos (
            id                INTEGER PRIMARY KEY,
            cliente_id        INTEGER NOT NULL REFERENCES clientes(id),
            restaurante_id    INTEGER NOT NULL REFERENCES restaurantes(id),
            entregador_id     INTEGER REFERENCES entregadores(id),
            data_pedido       TEXT NOT NULL,
            previsao_entrega  TEXT NOT NULL,
            data_entrega      TEXT,
            status            TEXT NOT NULL CHECK (status IN ('entregue', 'cancelado')),
            distancia_km      REAL NOT NULL,
            valor_itens       REAL NOT NULL,
            taxa_entrega      REAL NOT NULL,
            valor_total       REAL NOT NULL,
            forma_pagamento   TEXT NOT NULL
        );

        CREATE TABLE itens_pedido (
            id               INTEGER PRIMARY KEY,
            pedido_id        INTEGER NOT NULL REFERENCES pedidos(id),
            produto          TEXT NOT NULL,
            quantidade       INTEGER NOT NULL CHECK (quantidade > 0),
            preco_unitario   REAL NOT NULL
        );

        CREATE TABLE avaliacoes (
            pedido_id        INTEGER PRIMARY KEY REFERENCES pedidos(id),
            nota             INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5),
            data_avaliacao   TEXT NOT NULL
        );

        -- Índices nas colunas mais usadas em filtros e junções
        CREATE INDEX idx_pedidos_data        ON pedidos(data_pedido);
        CREATE INDEX idx_pedidos_cliente     ON pedidos(cliente_id);
        CREATE INDEX idx_pedidos_restaurante ON pedidos(restaurante_id);
        CREATE INDEX idx_pedidos_entregador  ON pedidos(entregador_id);
        CREATE INDEX idx_pedidos_status      ON pedidos(status);
        CREATE INDEX idx_itens_pedido        ON itens_pedido(pedido_id);
        """
    )


def gerar(caminho: Path = CAMINHO_BANCO):
    rng = random.Random(SEED)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if caminho.exists():
        caminho.unlink()
    con = sqlite3.connect(caminho)
    criar_tabelas(con)

    # --- Clientes ---
    clientes = []
    for i in range(1, N_CLIENTES + 1):
        cidade = escolher_ponderado(rng, CIDADES)
        cadastro = data_aleatoria(rng, datetime(2023, 1, 1), datetime(2025, 6, 30))
        clientes.append((i, nome_pessoa(rng), cidade, fmt(cadastro)[:10]))
    con.executemany("INSERT INTO clientes VALUES (?, ?, ?, ?)", clientes)

    # --- Restaurantes (garante pelo menos um de cada categoria por cidade grande) ---
    restaurantes = []
    nomes_usados = set()
    categorias = list(CARDAPIO)
    for i in range(1, N_RESTAURANTES + 1):
        cidade = list(CIDADES)[(i - 1) % len(CIDADES)]
        categoria = categorias[(i - 1) % len(categorias)]
        while True:
            nome = f"{rng.choice(PREFIXOS_RESTAURANTE)} {rng.choice(SUFIXOS_RESTAURANTE)}"
            nome = f"{nome} ({categoria})"
            if nome not in nomes_usados:
                nomes_usados.add(nome)
                break
        cadastro = data_aleatoria(rng, datetime(2022, 1, 1), datetime(2024, 12, 31))
        restaurantes.append((i, nome, categoria, cidade, fmt(cadastro)[:10]))
    con.executemany("INSERT INTO restaurantes VALUES (?, ?, ?, ?, ?)", restaurantes)

    # --- Entregadores ---
    entregadores = []
    for i in range(1, N_ENTREGADORES + 1):
        cidade = list(CIDADES)[(i - 1) % len(CIDADES)]
        entregadores.append((i, nome_pessoa(rng), escolher_ponderado(rng, VEICULOS), cidade))
    con.executemany("INSERT INTO entregadores VALUES (?, ?, ?, ?)", entregadores)

    rest_por_cidade, entreg_por_cidade = {}, {}
    for r in restaurantes:
        rest_por_cidade.setdefault(r[3], []).append(r)
    for e in entregadores:
        entreg_por_cidade.setdefault(e[3], []).append(e)

    # --- Pedidos, itens e avaliações ---
    pedidos, itens, avaliacoes = [], [], []
    item_id = 1
    for pid in range(1, N_PEDIDOS + 1):
        cliente = rng.choice(clientes)
        cidade = cliente[2]
        restaurante = rng.choice(rest_por_cidade[cidade])
        entregador = rng.choice(entreg_por_cidade[cidade])
        veiculo = entregador[2]

        dia = data_aleatoria(rng, INICIO, FIM).replace(hour=0, minute=0, second=0)
        data_pedido = dia.replace(hour=hora_do_pedido(rng), minute=rng.randint(0, 59), second=rng.randint(0, 59))

        distancia = round(rng.triangular(0.5, 10.0, 2.5), 1)
        previsao_min = 30 + distancia * 3.4
        previsao = data_pedido + timedelta(minutes=round(previsao_min))

        # Tempo real = preparo + deslocamento + ruído (+ atraso no horário de pico)
        preparo = rng.uniform(10, 28)
        deslocamento = distancia * VELOCIDADE_MIN_POR_KM[veiculo]
        if veiculo == "bicicleta" and distancia > 5:
            deslocamento *= 1.35
        pico = 18 <= data_pedido.hour <= 21
        extra_pico = rng.uniform(0, 14) if pico else 0
        real_min = preparo + deslocamento + extra_pico + rng.gauss(0, 4)
        real_min = max(real_min, 12)

        cancelado = rng.random() < (0.07 if pico else 0.04)
        status = "cancelado" if cancelado else "entregue"
        data_entrega = None if cancelado else data_pedido + timedelta(minutes=round(real_min))

        # Itens do pedido
        cardapio = CARDAPIO[restaurante[2]]
        valor_itens = 0.0
        for produto, pmin, pmax in rng.sample(cardapio, k=rng.randint(1, 3)):
            qtd = rng.choices([1, 2, 3], weights=[70, 22, 8])[0]
            preco = round(rng.uniform(pmin, pmax), 2)
            itens.append((item_id, pid, produto, qtd, preco))
            item_id += 1
            valor_itens += qtd * preco
        valor_itens = round(valor_itens, 2)

        taxa = round(3.99 + distancia * 0.9, 2)
        if valor_itens >= 100:  # frete grátis para pedidos de R$ 100 ou mais
            taxa = 0.0
        valor_total = round(valor_itens + taxa, 2)

        pedidos.append((
            pid, cliente[0], restaurante[0], None if cancelado and rng.random() < 0.5 else entregador[0],
            fmt(data_pedido), fmt(previsao), fmt(data_entrega), status, distancia,
            valor_itens, taxa, valor_total, escolher_ponderado(rng, FORMAS_PAGAMENTO),
        ))

        # Avaliação: ~70% dos pedidos entregues; atraso derruba a nota
        if not cancelado and rng.random() < 0.70:
            atraso_min = (data_entrega - previsao).total_seconds() / 60
            if atraso_min <= 0:
                pesos = [2, 3, 8, 30, 57]
            elif atraso_min <= 15:
                pesos = [6, 10, 25, 35, 24]
            else:
                pesos = [25, 25, 25, 15, 10]
            nota = rng.choices([1, 2, 3, 4, 5], weights=pesos)[0]
            data_av = data_entrega + timedelta(hours=rng.randint(1, 48))
            avaliacoes.append((pid, nota, fmt(data_av)))

    con.executemany("INSERT INTO pedidos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", pedidos)
    con.executemany("INSERT INTO itens_pedido VALUES (?, ?, ?, ?, ?)", itens)
    con.executemany("INSERT INTO avaliacoes VALUES (?, ?, ?)", avaliacoes)
    con.commit()
    con.close()
    return {
        "clientes": len(clientes), "restaurantes": len(restaurantes),
        "entregadores": len(entregadores), "pedidos": len(pedidos),
        "itens_pedido": len(itens), "avaliacoes": len(avaliacoes),
    }


if __name__ == "__main__":
    contagens = gerar()
    print(f"Banco criado em: {CAMINHO_BANCO}")
    for tabela, n in contagens.items():
        print(f"  {tabela:<14} {n:>6} linhas")
