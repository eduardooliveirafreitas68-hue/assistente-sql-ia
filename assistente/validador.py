"""
Camada 1 de segurança: valida o TEXTO do SQL antes de executar.

Regras:
- precisa começar com SELECT ou WITH (consulta de leitura);
- só pode haver UM comando (nada de "SELECT ...; DROP TABLE ...");
- não pode ter comentários (eles podem esconder comandos);
- não pode conter palavras de escrita ou de administração do banco.

Importante: esta checagem por texto NÃO é a única proteção. O banco também é
aberto em modo somente leitura e com um "authorizer" (veja banco.py). A ideia é
defesa em camadas: se uma camada falhar, a outra segura.
"""

import re

PALAVRAS_PROIBIDAS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "ATTACH", "DETACH",
    "PRAGMA", "VACUUM", "REINDEX", "TRUNCATE", "GRANT", "REVOKE", "MERGE", "UPSERT",
]
# Obs.: REPLACE ficou fora da lista porque replace() também é uma função de texto
# do SQLite (usada em SELECT). Um "REPLACE INTO" seria bloqueado pelo authorizer.

_PADRAO_PROIBIDAS = re.compile(r"\b(" + "|".join(PALAVRAS_PROIBIDAS) + r")\b", re.IGNORECASE)


class SQLInvalido(ValueError):
    """Erro levantado quando o SQL gerado não passa na validação."""


def _remover_textos_entre_aspas(sql: str) -> str:
    """Troca o conteúdo de 'strings' por vazio, para não confundir as checagens.
    Ex.: WHERE produto = 'Drop de chocolate' não deve ser confundido com DROP."""
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def validar_sql(sql: str) -> str:
    """Retorna o SQL limpo se for seguro; senão levanta SQLInvalido com o motivo."""
    if not sql or not sql.strip():
        raise SQLInvalido("O SQL está vazio.")

    limpo = sql.strip()
    # Um único ponto e vírgula no final é aceitável; removemos.
    if limpo.endswith(";"):
        limpo = limpo[:-1].rstrip()

    sem_strings = _remover_textos_entre_aspas(limpo)

    if ";" in sem_strings:
        raise SQLInvalido("Só é permitido um comando SQL por vez.")
    if "--" in sem_strings or "/*" in sem_strings:
        raise SQLInvalido("Comentários não são permitidos no SQL.")
    if not re.match(r"^\s*(SELECT|WITH)\b", sem_strings, re.IGNORECASE):
        raise SQLInvalido("Só são permitidas consultas que começam com SELECT ou WITH.")

    proibida = _PADRAO_PROIBIDAS.search(sem_strings)
    if proibida:
        raise SQLInvalido(f"Comando não permitido encontrado: {proibida.group(1).upper()}.")

    return limpo
