"""
Lê o dicionário de dados (descrição de cada coluna) direto do dados/esquema.md.
Assim existe uma única fonte da verdade: o mesmo texto que o modelo lê
é o que aparece no app e na planilha.
"""

import re
from pathlib import Path

import pandas as pd

CAMINHO_ESQUEMA = Path(__file__).resolve().parent.parent / "dados" / "esquema.md"


def carregar_dicionario(caminho: Path = CAMINHO_ESQUEMA) -> pd.DataFrame:
    linhas, tabela_atual = [], None
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        titulo = re.match(r"^###\s+(\w+)", linha)
        if titulo:
            tabela_atual = titulo.group(1)
            continue
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if tabela_atual and linha.startswith("|") and len(celulas) == 3:
            if celulas[0] in ("coluna", "") or set(celulas[0]) <= {"-"}:
                continue  # cabeçalho ou linha separadora
            linhas.append({"tabela": tabela_atual, "coluna": celulas[0],
                           "tipo": celulas[1], "descricao": celulas[2]})
    return pd.DataFrame(linhas)
