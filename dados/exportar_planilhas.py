"""
Exporta o banco para uma planilha Excel, com uma aba por tabela,
para explorar os dados antes de fazer perguntas ao assistente.

Uso:
    python dados/exportar_planilhas.py

Gera: dados/delivery_ficticio.xlsx
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from assistente.dicionario import carregar_dicionario  # noqa: E402
from dados.gerar_dados import CAMINHO_BANCO, gerar  # noqa: E402

TABELAS = ["pedidos", "itens_pedido", "clientes", "restaurantes", "entregadores", "avaliacoes"]
ARQUIVO_SAIDA = RAIZ / "dados" / "delivery_ficticio.xlsx"

LEIA_ME = [
    ("Sobre", "Dados FICTÍCIOS de uma plataforma de delivery, pedidos de 01/01/2025 a 31/12/2025."),
    ("Origem", "Gerados pelo script dados/gerar_dados.py (sempre os mesmos dados). Nenhuma pessoa ou empresa é real."),
    ("Abas", "Uma aba por tabela do banco + a aba 'dicionario' com o significado de cada coluna."),
    ("Ligações", "pedidos.cliente_id → clientes.id | pedidos.restaurante_id → restaurantes.id | "
                 "pedidos.entregador_id → entregadores.id | itens_pedido.pedido_id → pedidos.id | "
                 "avaliacoes.pedido_id → pedidos.id"),
    ("Pedido atrasado", "status = 'entregue' e data_entrega maior que previsao_entrega."),
    ("Como usar", "Explore as abas, anote o que achar interessante e pergunte ao assistente em português."),
]


def exportar(caminho_saida: Path = ARQUIVO_SAIDA, caminho_banco: Path = CAMINHO_BANCO) -> Path:
    if not caminho_banco.exists():
        gerar(caminho_banco)
    con = sqlite3.connect(f"file:{caminho_banco.as_posix()}?mode=ro", uri=True)
    with pd.ExcelWriter(caminho_saida, engine="openpyxl") as planilha:
        pd.DataFrame(LEIA_ME, columns=["tópico", "informação"]).to_excel(planilha, sheet_name="leia_me", index=False)
        carregar_dicionario().to_excel(planilha, sheet_name="dicionario", index=False)
        for tabela in TABELAS:
            pd.read_sql_query(f"SELECT * FROM {tabela}", con).to_excel(planilha, sheet_name=tabela, index=False)
        # Ajusta a largura das colunas e congela a linha do cabeçalho
        for aba in planilha.book.worksheets:
            aba.freeze_panes = "A2"
            for coluna in aba.columns:
                maior = max(len(str(c.value)) if c.value is not None else 0 for c in coluna[:200])
                aba.column_dimensions[coluna[0].column_letter].width = min(max(maior + 2, 10), 70)
    con.close()
    return caminho_saida


if __name__ == "__main__":
    print(f"Planilha criada em: {exportar()}")
