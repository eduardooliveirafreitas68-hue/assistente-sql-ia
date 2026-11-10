"""
Testes das camadas de segurança. Não usam a API (são gratuitos).

Uso:
    python -m pytest
"""

import sqlite3

import pytest

from assistente.banco import ErroExecucao, conectar_somente_leitura, executar_consulta
from assistente.validador import SQLInvalido, validar_sql
from dados.gerar_dados import gerar


@pytest.fixture(scope="session")
def banco(tmp_path_factory):
    caminho = tmp_path_factory.mktemp("dados") / "teste.db"
    gerar(caminho)
    return caminho


# ---------- Camada 1: validação do texto ----------

@pytest.mark.parametrize("sql", [
    "SELECT COUNT(*) FROM pedidos",
    "select * from pedidos limit 5;",
    "WITH x AS (SELECT 1 AS a) SELECT a FROM x",
    "SELECT replace(nome, 'a', 'b') FROM clientes",
    "SELECT * FROM itens_pedido WHERE produto = 'Drop; de chocolate -- teste'",
])
def test_aceita_consultas_de_leitura(sql):
    assert validar_sql(sql)


@pytest.mark.parametrize("sql", [
    "",
    "DROP TABLE pedidos",
    "DELETE FROM pedidos",
    "UPDATE pedidos SET status = 'entregue'",
    "INSERT INTO clientes VALUES (1, 'x', 'y', 'z')",
    "SELECT 1; DROP TABLE pedidos",
    "SELECT * FROM pedidos -- comentario",
    "SELECT * FROM pedidos /* oi */",
    "PRAGMA table_info(pedidos)",
    "ATTACH DATABASE 'x.db' AS x",
    "WITH x AS (SELECT 1) DELETE FROM pedidos",
])
def test_bloqueia_comandos_perigosos(sql):
    with pytest.raises(SQLInvalido):
        validar_sql(sql)


# ---------- Camadas 2 e 3: conexão somente leitura + authorizer ----------

def test_conexao_nao_permite_escrita_mesmo_sem_validador(banco):
    con = conectar_somente_leitura(banco)
    with pytest.raises(sqlite3.DatabaseError):
        con.execute("DELETE FROM pedidos")
    with pytest.raises(sqlite3.DatabaseError):
        con.execute("CREATE TABLE hack (x)")
    con.close()


def test_executa_consulta_e_limita_linhas(banco):
    r = executar_consulta("SELECT id FROM pedidos", caminho=banco, limite_linhas=10)
    assert len(r.tabela) == 10
    assert r.truncado is True


def test_erro_de_sql_vira_erro_execucao(banco):
    with pytest.raises(ErroExecucao):
        executar_consulta("SELECT coluna_que_nao_existe FROM pedidos", caminho=banco)


# ---------- Camada 4: timeout ----------

def test_timeout_interrompe_consulta_lenta(banco):
    sql_lento = "SELECT COUNT(*) FROM itens_pedido a, itens_pedido b"
    with pytest.raises(ErroExecucao, match="limite"):
        executar_consulta(sql_lento, caminho=banco, timeout_s=0.5)


# ---------- Dicionário de dados ----------

def test_dicionario_cobre_todas_as_colunas_do_banco(banco):
    from assistente.dicionario import carregar_dicionario
    dic = carregar_dicionario()
    con = sqlite3.connect(banco)
    tabelas = [t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    colunas_banco = {(t, c[1]) for t in tabelas for c in con.execute(f"PRAGMA table_info({t})")}
    con.close()
    assert colunas_banco == set(zip(dic["tabela"], dic["coluna"]))
