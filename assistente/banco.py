"""
Camadas 2, 3 e 4 de segurança: executar o SQL de forma protegida.

- Camada 2: o arquivo do banco é aberto em modo somente leitura (mode=ro).
- Camada 3: um "authorizer" do SQLite aprova cada operação que o comando tenta
  fazer e NEGA tudo o que não for leitura.
- Camada 4: limite de tempo (timeout) e limite de linhas retornadas.
"""

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "dados" / "delivery.db"

# Operações que o authorizer libera: ler tabelas, usar funções e CTEs.
_OPERACOES_PERMITIDAS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    getattr(sqlite3, "SQLITE_RECURSIVE", 33),  # WITH RECURSIVE
}


class ErroExecucao(RuntimeError):
    """Erro ao executar o SQL no banco (sintaxe, coluna inexistente, timeout...)."""


@dataclass
class ResultadoConsulta:
    tabela: pd.DataFrame
    truncado: bool        # True se havia mais linhas que o limite
    tempo_ms: float


def _authorizer(acao, arg1, arg2, nome_banco, gatilho):
    return sqlite3.SQLITE_OK if acao in _OPERACOES_PERMITIDAS else sqlite3.SQLITE_DENY


def conectar_somente_leitura(caminho: Path = CAMINHO_PADRAO) -> sqlite3.Connection:
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(
            f"Banco não encontrado em {caminho}. Rode primeiro: python dados/gerar_dados.py"
        )
    con = sqlite3.connect(f"file:{caminho.as_posix()}?mode=ro", uri=True, check_same_thread=False)
    con.execute("PRAGMA query_only = ON")  # antes de ligar o authorizer (que bloqueia PRAGMA)
    con.set_authorizer(_authorizer)
    return con


def executar_consulta(
    sql: str,
    caminho: Path = CAMINHO_PADRAO,
    limite_linhas: int = 500,
    timeout_s: float = 5.0,
) -> ResultadoConsulta:
    """Executa um SELECT já validado e devolve o resultado como DataFrame."""
    con = conectar_somente_leitura(caminho)
    inicio = time.perf_counter()

    def _checar_tempo():
        # Chamado pelo SQLite a cada N instruções internas; retornar 1 interrompe a consulta.
        return 1 if time.perf_counter() - inicio > timeout_s else 0

    con.set_progress_handler(_checar_tempo, 10_000)
    try:
        cursor = con.execute(sql)
        colunas = [c[0] for c in cursor.description] if cursor.description else []
        linhas = cursor.fetchmany(limite_linhas + 1)  # +1 para saber se passou do limite
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e).lower():
            raise ErroExecucao(f"A consulta passou do limite de {timeout_s:.0f}s e foi interrompida.") from e
        raise ErroExecucao(str(e)) from e
    except sqlite3.DatabaseError as e:
        raise ErroExecucao(str(e)) from e
    finally:
        con.close()

    truncado = len(linhas) > limite_linhas
    tabela = pd.DataFrame(linhas[:limite_linhas], columns=colunas)
    return ResultadoConsulta(tabela, truncado, (time.perf_counter() - inicio) * 1000)
