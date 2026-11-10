"""
Interface web do assistente (Streamlit).

Uso:
    streamlit run app.py
"""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from assistente.assistente import AssistenteSQL
from assistente.banco import CAMINHO_PADRAO
from assistente.llm import CAMINHO_ESQUEMA, ErroModelo
from dados.gerar_dados import gerar

load_dotenv()

# No Streamlit Community Cloud a chave fica em "Secrets" (não existe .env lá).
if not os.getenv("ANTHROPIC_API_KEY", "").strip() or "coloque-sua-chave" in os.getenv("ANTHROPIC_API_KEY", ""):
    try:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass  # sem secrets configurados: o aviso abaixo orienta o usuário

# O banco não vai para o GitHub; se ele não existir (ex.: app publicado), é criado aqui.
if not CAMINHO_PADRAO.exists():
    gerar(CAMINHO_PADRAO)

st.set_page_config(page_title="Assistente SQL com IA", page_icon="🔎", layout="wide")

EXEMPLOS = [
    "Quantos pedidos atrasaram em março de 2025?",
    "Qual a taxa de atraso por tipo de veículo do entregador?",
    "Qual a nota média de pedidos atrasados e no prazo?",
    "Faturamento por mês em 2025",
    "Quais os 10 restaurantes com mais pedidos cancelados?",
    "Qual a taxa de atraso no horário de pico do jantar?",
]


@st.cache_resource
def carregar_assistente() -> AssistenteSQL:
    return AssistenteSQL()


def mostrar_grafico(tabela: pd.DataFrame):
    """Gráfico automático simples: 1 coluna de rótulo + 1 coluna numérica, até 31 linhas."""
    if tabela.shape[1] != 2 or not (2 <= len(tabela) <= 31):
        return
    rotulo, valor = tabela.columns
    if pd.api.types.is_numeric_dtype(tabela[valor]):
        st.bar_chart(tabela.set_index(rotulo)[valor])


st.title("🔎 Assistente SQL com IA")
st.caption("Pergunte em português sobre os dados de uma plataforma de delivery (dados fictícios de 2025). "
           "A IA gera o SQL, o sistema valida e executa em modo somente leitura.")

with st.sidebar:
    st.subheader("Exemplos de perguntas")
    for ex in EXEMPLOS:
        if st.button(ex, width="stretch"):
            st.session_state["pergunta"] = ex
    with st.expander("📘 Contexto do negócio e ideias de perguntas"):
        st.markdown((CAMINHO_ESQUEMA.parent.parent / "docs" / "contexto_do_negocio.md").read_text(encoding="utf-8"))
    with st.expander("Ver esquema do banco"):
        st.markdown(CAMINHO_ESQUEMA.read_text(encoding="utf-8"))

if not os.getenv("ANTHROPIC_API_KEY", "").strip() or "coloque-sua-chave" in os.getenv("ANTHROPIC_API_KEY", ""):
    st.error("Chave da API não encontrada. Copie `.env.example` para `.env` e coloque sua ANTHROPIC_API_KEY.")
    st.stop()

pergunta = st.text_input("Sua pergunta", key="pergunta",
                         placeholder="Ex.: Qual cidade teve mais pedidos atrasados em 2025?")

if st.button("Perguntar", type="primary") and pergunta.strip():
    with st.spinner("Gerando e executando a consulta..."):
        try:
            resposta = carregar_assistente().perguntar(pergunta.strip())
        except ErroModelo as e:
            st.error(str(e))
            st.stop()

    if resposta.sucesso:
        st.success(resposta.explicacao)
        col1, col2 = st.columns([3, 2])
        with col1:
            st.dataframe(resposta.tabela, width="stretch", hide_index=True)
            if resposta.truncado:
                st.info("O resultado foi limitado às primeiras 500 linhas.")
            mostrar_grafico(resposta.tabela)
        with col2:
            st.markdown("**SQL gerado (validado):**")
            st.code(resposta.sql, language="sql")
            if resposta.tentativas > 1:
                st.caption(f"O modelo corrigiu o SQL após um erro ({resposta.tentativas} tentativas).")
                for erro in resposta.historico_erros:
                    st.caption(f"• {erro}")
    else:
        st.warning(f"{resposta.erro}\n\n{resposta.explicacao}")
        if resposta.sql:
            st.code(resposta.sql, language="sql")
