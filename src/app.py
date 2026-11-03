"""Página inicial do dashboard; os resultados serão integrados pelo grupo."""

import streamlit as st


st.set_page_config(page_title="Lab04 — Testes de hipótese", layout="wide")

st.title("Testes de hipótese por dentro")
st.markdown(
    "[Dashboard local](http://localhost:8501) · "
    "[Repositório](https://github.com/lab-medicao-experimentacao/"
    "lab04-teste-de-hipotese) · "
    "[Kanban](https://github.com/orgs/lab-medicao-experimentacao/projects/4/views/2)"
)
st.caption("P2 · t pareado × Wilcoxon pareado")
st.info("Trabalho em desenvolvimento. Os dados e resultados ainda serão incluídos.")

st.header("1. Cenário")
st.markdown(
    "**Pergunta:** a definir.\n\n"
    "**H₀:** a definir.\n\n"
    "**H₁:** a definir.\n\n"
    "**Fonte e procedimento de coleta:** a definir.\n\n"
    "**Quantidade de pares:** a definir.\n\n"
    "**Expectativa antes da simulação:** a registrar pelo grupo, com justificativa."
)

st.header("2. Os dados")
# Integração G1: carregar a amostra, gerar a figura e usar st.plotly_chart(fig).
st.info("G1 — Histogramas dos dados reais e simulados: aguardando implementação.")
st.markdown(
    "**Explicação dos dados:** a preencher com 2 a 4 frases sobre a forma das "
    "distribuições e a escolha dos parâmetros da simulação."
)

st.header("3. Como os testes funcionam")
# Integração G2: gerar a figura sob H₀ e usar st.plotly_chart(fig).
st.info(
    "G2 — Distribuição da estatística sob H₀, região de rejeição e área do "
    "p-valor de um exemplo: aguardando implementação."
)
st.markdown(
    "**Explicação dos testes:** a preencher com 2 a 4 frases sobre o que cada "
    "teste compara, a região de rejeição e o significado do p-valor."
)
st.subheader("Aplicação a um conjunto simulado")
st.markdown(
    "**Estatísticas, p-valores e interpretação:** aguardando a aplicação dos "
    "dois testes ao conjunto simulado."
)
