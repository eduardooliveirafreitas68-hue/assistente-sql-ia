"""
Conversa com o modelo de linguagem (Claude, via API da Anthropic).

O modelo recebe: as regras (prompt de sistema) + o esquema do banco + a pergunta.
E devolve um JSON com formato garantido (structured outputs):
    {"pode_responder": bool, "sql": str, "explicacao": str}
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

import anthropic

CAMINHO_ESQUEMA = Path(__file__).resolve().parent.parent / "dados" / "esquema.md"
MODELO_PADRAO = "claude-opus-5-5"

REGRAS = """Você é um assistente que converte perguntas em português em consultas SQL para SQLite.

Regras obrigatórias:
1. Use SOMENTE as tabelas e colunas descritas no esquema abaixo. Nunca invente colunas.
2. Gere apenas UMA consulta de leitura, começando com SELECT ou WITH.
   Nunca gere INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA ou qualquer comando de escrita.
3. Não use comentários (-- ou /* */) e não termine com ponto e vírgula.
4. Se a pergunta pedir uma lista de registros, inclua LIMIT 100 (a não ser que o usuário peça outro número).
5. Dê nomes claros em português às colunas calculadas (ex.: AS taxa_atraso_pct).
   Arredonde percentuais e valores em reais com ROUND(..., 2).
6. Siga as convenções do esquema (ex.: a definição de pedido atrasado).
7. Se a pergunta não puder ser respondida com estes dados (ex.: pede algo que não existe
   no banco, ou não é uma pergunta sobre os dados), responda com pode_responder = false,
   sql = "" e explique o motivo em explicacao.
8. Em explicacao, escreva 1 a 3 frases curtas, em português simples, dizendo o que a consulta faz
   e qualquer suposição que você fez (ex.: "considerei apenas pedidos entregues").
"""

FORMATO_RESPOSTA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "pode_responder": {"type": "boolean"},
            "sql": {"type": "string"},
            "explicacao": {"type": "string"},
        },
        "required": ["pode_responder", "sql", "explicacao"],
        "additionalProperties": False,
    },
}


@dataclass
class RespostaModelo:
    pode_responder: bool
    sql: str
    explicacao: str
    tokens_entrada: int = 0
    tokens_saida: int = 0


class ErroModelo(RuntimeError):
    """Erro ao falar com a API do modelo."""


def montar_prompt_sistema() -> str:
    esquema = CAMINHO_ESQUEMA.read_text(encoding="utf-8")
    return f"{REGRAS}\n\n<esquema>\n{esquema}\n</esquema>"


class GeradorSQL:
    def __init__(self, modelo: str | None = None, cliente: anthropic.Anthropic | None = None):
        self.modelo = modelo or os.getenv("MODELO_CLAUDE", MODELO_PADRAO)
        # Sem api_key explícita: o SDK lê ANTHROPIC_API_KEY do ambiente (.env).
        self.cliente = cliente or anthropic.Anthropic()
        self.prompt_sistema = montar_prompt_sistema()

    def gerar(self, mensagens: list[dict]) -> RespostaModelo:
        """mensagens = histórico no formato da API: [{"role": "user", "content": "..."} ...]"""
        try:
            resposta = self.cliente.beta.messages.create(
                model=self.modelo,
                max_tokens=16000,
                system=self.prompt_sistema,
                messages=mensagens,
                output_config={"format": FORMATO_RESPOSTA, "effort": "medium"},
                # Se o modelo principal recusar, a API tenta automaticamente um modelo reserva.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                # Guarda o prompt de sistema (regras + esquema) em cache: perguntas seguintes ficam mais baratas.
                cache_control={"type": "ephemeral"},
            )
        except anthropic.AuthenticationError as e:
            raise ErroModelo("Chave da API inválida. Confira ANTHROPIC_API_KEY no arquivo .env.") from e
        except anthropic.RateLimitError as e:
            raise ErroModelo("Limite de uso da API atingido. Espere um pouco e tente de novo.") from e
        except anthropic.APIStatusError as e:
            raise ErroModelo(f"Erro da API ({e.status_code}): {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise ErroModelo("Sem conexão com a API. Verifique sua internet.") from e

        if resposta.stop_reason == "refusal":
            raise ErroModelo("O modelo recusou esta pergunta.")
        if resposta.stop_reason == "max_tokens":
            raise ErroModelo("A resposta do modelo foi cortada (max_tokens).")

        texto = next((b.text for b in resposta.content if b.type == "text"), None)
        if texto is None:
            raise ErroModelo("O modelo não retornou texto.")
        dados = json.loads(texto)
        return RespostaModelo(
            pode_responder=bool(dados["pode_responder"]),
            sql=dados["sql"].strip(),
            explicacao=dados["explicacao"].strip(),
            tokens_entrada=resposta.usage.input_tokens,
            tokens_saida=resposta.usage.output_tokens,
        )
