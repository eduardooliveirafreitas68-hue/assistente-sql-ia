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
    python avaliacao/avaliar.py            # todas as perguntas
    python avaliacao/avaliar.py --ids 9 10 # só algumas (mais barato)
"""

import argparse
import json
import os
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


def tabela_md(linhas, limite=5) -> str:
    """Mostra as primeiras linhas de um resultado como texto, para o relatório."""
    if not linhas:
        return "(vazio)"
    texto = "\n".join(str(l) for l in linhas[:limite])
    return texto + (f"\n... ({len(linhas)} linhas no total)" if len(linhas) > limite else "")


def main():
    parser = argparse.ArgumentParser(description="Avalia o assistente com as perguntas de referência.")
    parser.add_argument("--ids", type=int, nargs="+",
                        help="roda só estas perguntas (ex.: --ids 9 10). Mais barato para investigar erros.")
    args = parser.parse_args()

    load_dotenv(RAIZ / ".env")
    if not os.getenv("ANTHROPIC_API_KEY", "").strip() or "coloque-sua-chave" in os.getenv("ANTHROPIC_API_KEY", ""):
        sys.exit(
            "ERRO: chave da API não encontrada.\n"
            f"Crie o arquivo {RAIZ / '.env'} (copie o .env.example) com a linha:\n"
            "ANTHROPIC_API_KEY=sk-ant-...sua-chave..."
        )
    if not CAMINHO_PADRAO.exists():
        print("Banco não encontrado. Gerando os dados fictícios...")
        gerar(CAMINHO_PADRAO)
    perguntas = json.loads(ARQ_PERGUNTAS.read_text(encoding="utf-8"))
    if args.ids:
        perguntas = [q for q in perguntas if q["id"] in set(args.ids)]
    arq_resultado = ARQ_RESULTADO if not args.ids else ARQ_RESULTADO.with_name("resultado_parcial.md")

    assistente = AssistenteSQL()
    # mode=ro: abre só para leitura (e nunca cria um arquivo vazio por engano)
    con = sqlite3.connect(f"file:{CAMINHO_PADRAO.as_posix()}?mode=ro", uri=True)

    detalhes, acertos = [], 0
    for n, q in enumerate(perguntas, start=1):
        print(f"[{n:>2}/{len(perguntas)}] (#{q['id']}) {q['pergunta']}")
        gabarito = con.execute(q["sql_referencia"]).fetchall() if q["sql_referencia"] else None
        try:
            r = assistente.perguntar(q["pergunta"])
        except ErroModelo as e:
            print(f"     ERRO NA API: {e}")
            detalhes.append({"q": q, "ok": False, "motivo": f"erro na API: {e}", "sql": "", "obtido": None,
                             "gabarito": gabarito, "explicacao": ""})
            continue

        obtido = list(r.tabela.itertuples(index=False, name=None)) if r.sucesso else None
        if q["sql_referencia"] is None:
            acertou = not r.sucesso and r.sql == ""
            motivo = "recusou corretamente" if acertou else "deveria ter dito que não consegue responder"
        elif not r.sucesso:
            acertou, motivo = False, r.erro
        else:
            acertou = resultados_equivalentes(gabarito, obtido)
            motivo = "resultado igual ao gabarito" if acertou else "resultado diferente do gabarito"

        acertos += acertou
        print(f"     {'OK ' if acertou else 'ERROU'} ({motivo}) | tentativas: {r.tentativas}")
        if not acertou:
            print(f"     SQL da IA: {r.sql}")
            print(f"     Resultado da IA: {tabela_md(obtido, 3) if obtido else '-'}")
            print(f"     Gabarito: {tabela_md(gabarito, 3) if gabarito else '-'}")
        detalhes.append({"q": q, "ok": acertou, "motivo": motivo, "sql": r.sql, "obtido": obtido,
                         "gabarito": gabarito, "explicacao": r.explicacao})

    total = len(perguntas)
    pct = 100 * acertos / total if total else 0
    print(f"\nAcurácia: {acertos}/{total} = {pct:.1f}%")

    md = [
        "# Resultado da avaliação" + (" (parcial)" if args.ids else ""),
        "",
        f"- Data: {datetime.now():%Y-%m-%d %H:%M}",
        f"- Modelo: `{assistente.gerador.modelo}`",
        f"- **Acurácia: {acertos}/{total} ({pct:.1f}%)**",
        "",
        "| # | Pergunta | Resultado | Motivo |",
        "|---|---|---|---|",
    ]
    for d in detalhes:
        md.append(f"| {d['q']['id']} | {d['q']['pergunta']} | {'✅' if d['ok'] else '❌'} | {d['motivo']} |")
    md += ["", "## Detalhes", ""]
    for d in detalhes:
        md += [
            f"### #{d['q']['id']} {'✅' if d['ok'] else '❌'} {d['q']['pergunta']}",
            "",
            f"**Explicação da IA:** {d['explicacao'] or '-'}",
            "",
            "**SQL da IA:**", "```sql", d["sql"] or "(nenhum)", "```",
            "**Resultado da IA:**", "```", tabela_md(d["obtido"]) if d["obtido"] else "-", "```",
            "**SQL de referência:**", "```sql", d["q"]["sql_referencia"] or "(sem resposta possível)", "```",
            "**Gabarito:**", "```", tabela_md(d["gabarito"]) if d["gabarito"] else "-", "```",
            "",
        ]
    arq_resultado.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Relatório salvo em {arq_resultado}")


if __name__ == "__main__":
    main()
