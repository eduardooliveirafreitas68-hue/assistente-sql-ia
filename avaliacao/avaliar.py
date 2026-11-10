"""
Avaliação automática: quantas perguntas o assistente acerta?

Para cada pergunta de perguntas.json:
  - roda o SQL de referência (escrito à mão) e guarda o resultado "gabarito";
  - pergunta ao assistente e compara o resultado dele com o gabarito.

Critério de acerto (comparação pelo RESULTADO, não pelo texto do SQL):
  - mesmo número de linhas;
  - cada coluna do gabarito tem uma coluna equivalente no resultado do assistente
    (mesmos valores, ignorando a ordem das linhas e nomes de colunas;
     números arredondados para 1 casa decimal).
  - Perguntas sem resposta possível (sql_referencia = null) contam como acerto
    se o assistente disser que não consegue responder.

ATENÇÃO: cada pergunta faz chamadas pagas à API.

Uso:
    python avaliacao/avaliar.py
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from dotenv import load_dotenv  # noqa: E402

from assistente.assistente import AssistenteSQL  # noqa: E402
from assistente.banco import CAMINHO_PADRAO  # noqa: E402
from assistente.llm import ErroModelo  # noqa: E402
from dados.gerar_dados import gerar  # noqa: E402

ARQ_PERGUNTAS = Path(__file__).parent / "perguntas.json"
ARQ_RESULTADO = Path(__file__).parent / "resultado.md"


def normalizar(valor):
    if isinstance(valor, float):
        return round(valor, 1)
    if isinstance(valor, str):
        return valor.strip().lower()
    return valor


def colunas_normalizadas(linhas):
    if not linhas:
        return []
    return [sorted((normalizar(l[i]) for l in linhas), key=repr) for i in range(len(linhas[0]))]


def resultados_equivalentes(gabarito, obtido) -> bool:
    if len(gabarito) != len(obtido):
        return False
    cols_obtidas = colunas_normalizadas(obtido)
    return all(col in cols_obtidas for col in colunas_normalizadas(gabarito))


def main():
    load_dotenv(RAIZ / ".env")
    if not CAMINHO_PADRAO.exists():
        print("Banco não encontrado. Gerando os dados fictícios...")
        gerar(CAMINHO_PADRAO)
    perguntas = json.loads(ARQ_PERGUNTAS.read_text(encoding="utf-8"))
    assistente = AssistenteSQL()
    # mode=ro: abre só para leitura (e nunca cria um arquivo vazio por engano)
    con = sqlite3.connect(f"file:{CAMINHO_PADRAO.as_posix()}?mode=ro", uri=True)

    linhas_relatorio, acertos = [], 0
    for q in perguntas:
        print(f"[{q['id']:>2}/{len(perguntas)}] {q['pergunta']}")
        try:
            r = assistente.perguntar(q["pergunta"])
        except ErroModelo as e:
            print(f"     ERRO NA API: {e}")
            linhas_relatorio.append((q, False, "", f"erro na API: {e}"))
            continue

        if q["sql_referencia"] is None:
            acertou = not r.sucesso and r.sql == ""
            motivo = "recusou corretamente" if acertou else "deveria ter dito que não consegue responder"
        elif not r.sucesso:
            acertou, motivo = False, r.erro
        else:
            gabarito = con.execute(q["sql_referencia"]).fetchall()
            obtido = list(r.tabela.itertuples(index=False, name=None))
            acertou = resultados_equivalentes(gabarito, obtido)
            motivo = "resultado igual ao gabarito" if acertou else "resultado diferente do gabarito"

        acertos += acertou
        print(f"     {'OK ' if acertou else 'ERROU'} ({motivo}) | tentativas: {r.tentativas}")
        linhas_relatorio.append((q, acertou, r.sql, motivo))

    total = len(perguntas)
    pct = 100 * acertos / total
    print(f"\nAcurácia: {acertos}/{total} = {pct:.1f}%")

    md = [
        "# Resultado da avaliação",
        "",
        f"- Data: {datetime.now():%Y-%m-%d %H:%M}",
        f"- Modelo: `{assistente.gerador.modelo}`",
        f"- **Acurácia: {acertos}/{total} ({pct:.1f}%)**",
        "",
        "| # | Pergunta | Resultado | Motivo |",
        "|---|---|---|---|",
    ]
    for q, ok, _sql, motivo in linhas_relatorio:
        md.append(f"| {q['id']} | {q['pergunta']} | {'✅' if ok else '❌'} | {motivo} |")
    ARQ_RESULTADO.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Relatório salvo em {ARQ_RESULTADO}")


if __name__ == "__main__":
    main()
