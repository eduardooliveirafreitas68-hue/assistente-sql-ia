"""
Interface web do assistente (Streamlit).

Uso:
    streamlit run app.py
"""

import os
import sqlite3

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from assistente.assistente import AssistenteSQL
from assistente.banco import CAMINHO_PADRAO
from assistente.dicionario import carregar_dicionario
from assistente.llm import ErroModelo
from dados.gerar_dados import gerar

TABELAS = ["pedidos", "itens_pedido", "clientes", "restaurantes", "entregadores", "avaliacoes"]

load_dotenv()


def chave_configurada() -> bool:
    chave = os.getenv("ANTHROPIC_API_KEY", "").strip()
    return bool(chave) and "coloque-sua-chave" not in chave


# No Streamlit Community Cloud a chave fica em "Secrets" (não existe .env lá).
if not chave_configurada():
    try:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass  # sem secrets configurados: o aviso na aba "Perguntar" orienta o usuário

# O banco não vai para o GitHub; se ele não existir (ex.: app publicado), é criado aqui.
if not CAMINHO_PADRAO.exists():
    gerar(CAMINHO_PADRAO)

st.set_page_config(page_title="Assistente SQL com IA", page_icon="🔎", layout="wide")


@st.cache_resource
def carregar_assistente() -> AssistenteSQL:
    return AssistenteSQL()


@st.cache_data
def ler_tabela(nome: str) -> pd.DataFrame:
    con = sqlite3.connect(f"file:{CAMINHO_PADRAO.as_posix()}?mode=ro", uri=True)
    try:
        return pd.read_sql_query(f"SELECT * FROM {nome}", con)  # nome vem da lista fixa TABELAS
    finally:
        con.close()


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

aba_perguntar, aba_explorar = st.tabs(["💬 Perguntar", "📊 Explorar dados"])

# ---------------------------------------------------------------- Explorar dados
with aba_explorar:
    st.markdown("Veja os dados como numa planilha para ter ideias de perguntas. "
                "Clique no nome de uma coluna para ordenar.")
    escolhida = st.selectbox("Tabela", TABELAS)
    dados = ler_tabela(escolhida)
    st.caption(f"{len(dados):,} linhas · {dados.shape[1]} colunas".replace(",", "."))
    st.dataframe(dados, width="stretch", hide_index=True, height=420)
    st.download_button(f"⬇️ Baixar {escolhida}.csv", dados.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"{escolhida}.csv", mime="text/csv")
    with st.expander("O que significa cada coluna"):
        dic = carregar_dicionario()
        st.dataframe(dic[dic["tabela"] == escolhida].drop(columns="tabela"), width="stretch", hide_index=True)
    st.caption("Pedido atrasado = status 'entregue' e data_entrega maior que previsao_entrega. "
               "Ligações: pedidos → clientes, restaurantes e entregadores; itens_pedido e avaliacoes → pedidos.")

# ---------------------------------------------------------------- Perguntar
with aba_perguntar:
    if not chave_configurada():
        st.error("Chave da API não encontrada. Copie `.env.example` para `.env` e coloque sua ANTHROPIC_API_KEY.")
    else:
        pergunta = st.text_input("Sua pergunta", key="pergunta",
                                 placeholder="Escreva sua pergunta sobre os dados...")

        if st.button("Perguntar", type="primary") and pergunta.strip():
            with st.spinner("Gerando e executando a consulta..."):
                try:
                    resposta = carregar_assistente().perguntar(pergunta.strip())
                except ErroModelo as e:
                    resposta = None
                    st.error(str(e))

            if resposta is not None and resposta.sucesso:
                st.success(resposta.explicacao)
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.dataframe(resposta.tabela, width="stretch", hide_index=True)
                    if resposta.truncado:
                        st.info("O resultado foi limitado às primeiras 500 linhas.")
                    mostrar_grafico(resposta.tabela)
                with col2:
                    st.markdown("**SQL gerado (validado):**")
                    st.code(resposta.sql, language="sql", wrap_lines=True)
                    if resposta.tentativas > 1:
                        st.caption(f"O modelo corrigiu o SQL após um erro ({resposta.tentativas} tentativas).")
                        for erro in resposta.historico_erros:
                            st.caption(f"• {erro}")
            elif resposta is not None:
                st.warning(f"{resposta.erro}\n\n{resposta.explicacao}")
                if resposta.sql:
                    st.code(resposta.sql, language="sql", wrap_lines=True)
