"""
Testa o fluxo do assistente com um "modelo falso" (sem gastar com a API).
Verifica: caminho feliz, correção automática após erro e pergunta sem resposta.
"""

import pytest

from assistente.assistente import AssistenteSQL
from assistente.llm import RespostaModelo
from dados.gerar_dados import gerar


class ModeloFalso:
    """Devolve respostas prontas, na ordem, e guarda o que recebeu."""

    modelo = "modelo-falso"

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def gerar(self, mensagens):
        self.chamadas.append(list(mensagens))
        return self.respostas.pop(0)


@pytest.fixture(scope="module")
def banco(tmp_path_factory):
    caminho = tmp_path_factory.mktemp("dados") / "teste.db"
    gerar(caminho)
    return caminho


def test_caminho_feliz(banco):
    falso = ModeloFalso([RespostaModelo(True, "SELECT COUNT(*) AS total FROM pedidos", "Conta os pedidos.")])
    r = AssistenteSQL(gerador=falso, caminho_banco=banco).perguntar("Quantos pedidos?")
    assert r.sucesso and r.tabela.iloc[0, 0] == 12000 and r.tentativas == 1


def test_corrige_apos_erro(banco):
    falso = ModeloFalso([
        RespostaModelo(True, "SELECT total_errado FROM pedidos", "v1"),
        RespostaModelo(True, "SELECT COUNT(*) AS total FROM pedidos", "v2"),
    ])
    r = AssistenteSQL(gerador=falso, caminho_banco=banco).perguntar("Quantos pedidos?")
    assert r.sucesso and r.tentativas == 2
    # Na 2ª chamada o modelo recebeu o erro da 1ª
    assert "no such column" in falso.chamadas[1][-1]["content"]


def test_bloqueia_sql_perigoso_e_desiste(banco):
    falso = ModeloFalso([RespostaModelo(True, "DROP TABLE pedidos", "x")] * 2)
    r = AssistenteSQL(gerador=falso, caminho_banco=banco).perguntar("apague tudo")
    assert not r.sucesso and "SELECT ou WITH" in r.erro


def test_pergunta_sem_resposta(banco):
    falso = ModeloFalso([RespostaModelo(False, "", "Não há dados de salário.")])
    r = AssistenteSQL(gerador=falso, caminho_banco=banco).perguntar("Salário médio?")
    assert not r.sucesso and r.tentativas == 1
