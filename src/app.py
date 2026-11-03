"""Página inicial do dashboard; os resultados serão integrados pelo grupo."""

import streamlit as st

import aplicacao


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


@st.cache_data
def exemplo_simulado():
    antes, depois = aplicacao.conjunto_exemplo()
    return antes, depois, aplicacao.aplicar_testes(antes, depois)


antes, depois, resultados = exemplo_simulado()
mediana_antes, mediana_depois = aplicacao.medianas(antes, depois)
st.caption(
    f"Dados simulados com o gerador provisório (será substituído pelo gerador "
    f"calibrado com os dados reais): {aplicacao.N_EXEMPLO} pares, efeito "
    f"verdadeiro de {aplicacao.EFEITO_EXEMPLO:.0%} de redução no tempo de build, "
    f"semente {aplicacao.SEMENTE}, teste bicaudal (provisório) e "
    f"α = {aplicacao.ALFA:.2f}".replace(".", ",") + "."
)
col_antes, col_depois = st.columns(2)
col_antes.metric("Mediana antes", f"{mediana_antes:.1f} s".replace(".", ","))
col_depois.metric("Mediana depois", f"{mediana_depois:.1f} s".replace(".", ","))
st.dataframe(resultados, hide_index=True)
st.caption("Estatística: t para o t pareado e W+ para o Wilcoxon pareado.")
st.markdown(aplicacao.interpretar(resultados, aplicacao.EFEITO_EXEMPLO))
