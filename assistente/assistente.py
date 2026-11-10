"""
O "maestro" do projeto: junta modelo + validação + execução.

Fluxo de uma pergunta:
  1. envia a pergunta ao modelo e recebe {pode_responder, sql, explicacao}
  2. valida o SQL (validador.py)
  3. executa em modo somente leitura (banco.py)
  4. se a validação ou a execução falhar, devolve o erro ao modelo e tenta de novo
     (no máximo MAX_TENTATIVAS vezes no total)
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .banco import CAMINHO_PADRAO, ErroExecucao, executar_consulta
from .llm import GeradorSQL
from .validador import SQLInvalido, validar_sql

MAX_TENTATIVAS = 2  # 1 tentativa normal + 1 correção


@dataclass
class Resposta:
    pergunta: str
    sucesso: bool
    sql: str = ""
    explicacao: str = ""
    tabela: pd.DataFrame | None = None
    truncado: bool = False
    erro: str = ""
    tentativas: int = 0
    historico_erros: list[str] = field(default_factory=list)


class AssistenteSQL:
    def __init__(self, gerador: GeradorSQL | None = None, caminho_banco: Path = CAMINHO_PADRAO,
                 limite_linhas: int = 500):
        self.gerador = gerador or GeradorSQL()
        self.caminho_banco = caminho_banco
        self.limite_linhas = limite_linhas

    def perguntar(self, pergunta: str) -> Resposta:
        resposta = Resposta(pergunta=pergunta, sucesso=False)
        mensagens = [{"role": "user", "content": pergunta}]

        for tentativa in range(1, MAX_TENTATIVAS + 1):
            resposta.tentativas = tentativa
            gerado = self.gerador.gerar(mensagens)
            resposta.sql, resposta.explicacao = gerado.sql, gerado.explicacao

            if not gerado.pode_responder:
                resposta.erro = "Não é possível responder com os dados disponíveis."
                return resposta

            try:
                sql_seguro = validar_sql(gerado.sql)
                resultado = executar_consulta(sql_seguro, self.caminho_banco, self.limite_linhas)
            except (SQLInvalido, ErroExecucao) as e:
                resposta.erro = str(e)
                resposta.historico_erros.append(f"Tentativa {tentativa}: {e}")
                # Devolve ao modelo a própria resposta + o erro, para ele corrigir.
                mensagens += [
                    {"role": "assistant", "content": json.dumps(
                        {"pode_responder": gerado.pode_responder, "sql": gerado.sql,
                         "explicacao": gerado.explicacao}, ensure_ascii=False)},
                    {"role": "user", "content": (
                        f"O SQL acima falhou com este erro: {e}\n"
                        "Corrija a consulta seguindo as regras e responda no mesmo formato.")},
                ]
                continue

            resposta.sql = sql_seguro
            resposta.tabela = resultado.tabela
            resposta.truncado = resultado.truncado
            resposta.sucesso = True
            resposta.erro = ""
            return resposta

        return resposta
