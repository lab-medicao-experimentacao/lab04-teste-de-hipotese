"""Página inicial do dashboard; os resultados serão integrados pelo grupo."""

import streamlit as st

import amostra
import analise_real
import aplicacao
from graficos import exploracao, g1, g2, g3, g4


st.set_page_config(page_title="Lab04 — Testes de hipótese", layout="wide")

st.title("Testes de hipótese por dentro")
st.markdown(
    "[Dashboard local](http://localhost:8501) · "
    "[Repositório](https://github.com/lab-medicao-experimentacao/"
    "lab04-teste-de-hipotese) · "
    "[Kanban](https://github.com/orgs/lab-medicao-experimentacao/projects/4/views/2)"
)
st.caption("P2 · t pareado × Wilcoxon pareado")

st.header("1. Cenário")
st.markdown(
    "**Pergunta:** o cache de compilação altera o tempo de build do fzf?\n\n"
    "Em cada par, a diferença é o tempo com cache menos o tempo sem cache. "
    "Os testes são bicaudais para detectar tanto redução quanto aumento no tempo.\n\n"
    "**t pareado:** H₀: a média das diferenças é zero. "
    "H₁: a média das diferenças é diferente de zero.\n\n"
    "**Wilcoxon pareado:** H₀: a distribuição das diferenças é simétrica em torno de zero. "
    "Sob simetria, H₁: seu centro é diferente de zero.\n\n"
    f"**Fonte e procedimento de coleta:** {amostra.FONTE}. Detalhes em "
    "[`data/README.md`](https://github.com/lab-medicao-experimentacao/"
    "lab04-teste-de-hipotese/blob/main/data/README.md).\n\n"
    f"**Quantidade de pares:** {amostra.n_pares()}.\n\n"
    "**Expectativa para a Sprint 2:** com diferenças próximas da normalidade, "
    "esperamos maior poder do t pareado. Com valores extremos e diferenças ainda "
    "simétricas, esperamos que o Wilcoxon ganhe vantagem, pois usa postos e limita "
    "a influência da magnitude dos extremos. Essa previsão foi registrada após o "
    "exemplo da Sprint 1, para comparação com as simulações da Sprint 2."
)

st.header("2. Os dados")


@st.cache_data
def conjuntos_g1():
    return g1.conjuntos()


dados_g1 = conjuntos_g1()
st.plotly_chart(g1.figura(dados_g1["real"], dados_g1["simulado"]), width="stretch")
st.caption(
    f"Simulado: {amostra.n_pares()} pares gerados com os parâmetros estimados da "
    f"amostra, semente {g1.SEMENTE} e o efeito observado no cache real."
)
st.markdown(
    "**Explicação dos dados:** "
    + g1.explicacao(dados_g1["real"], dados_g1["simulado"])
)

st.header("3. Como os testes funcionam")


@st.cache_data
def exemplo_simulado():
    antes, depois = aplicacao.conjunto_exemplo()
    resultados = aplicacao.aplicar_testes(
        antes, depois, alternativa=aplicacao.ALTERNATIVA, alfa=aplicacao.ALFA
    )
    return antes, depois, resultados


antes, depois, resultados = exemplo_simulado()

# Integração G2: mesmo conjunto de exemplo da Aplicação abaixo.
st.plotly_chart(
    g2.figura(antes, depois, aplicacao.ALTERNATIVA, aplicacao.ALFA), width="stretch"
)
st.markdown(
    "**Explicação dos testes:** "
    + g2.explicacao(antes, depois, aplicacao.ALTERNATIVA, aplicacao.ALFA)
)
st.subheader("Aplicação a um conjunto simulado")
mediana_antes, mediana_depois = aplicacao.medianas(antes, depois)
st.caption(
    f"Dados simulados com o gerador calibrado pela amostra real: "
    f"{aplicacao.N_EXEMPLO} pares, efeito "
    f"verdadeiro de {aplicacao.EFEITO_EXEMPLO:.0%} de redução no tempo de build, "
    f"semente {aplicacao.SEMENTE}, testes bicaudais e "
    f"α = {aplicacao.ALFA:.2f}".replace(".", ",") + "."
)
col_antes, col_depois = st.columns(2)
col_antes.metric("Mediana antes", f"{mediana_antes:.1f} s".replace(".", ","))
col_depois.metric("Mediana depois", f"{mediana_depois:.1f} s".replace(".", ","))
st.dataframe(resultados, hide_index=True)
st.caption("Estatística: t para o t pareado e W+ para o Wilcoxon pareado.")
st.markdown(aplicacao.interpretar(resultados, aplicacao.EFEITO_EXEMPLO, alfa=aplicacao.ALFA))

st.header("4. Erro tipo I")


@st.cache_data
def resultados_simulacao():
    """Resultados reproduzíveis de Q1 a Q3, calculados uma vez por sessão."""
    import simulacao

    return simulacao.simular_tudo()


resultados_simulados = resultados_simulacao()
st.plotly_chart(g3.figura(resultados_simulados), width="stretch")
st.markdown("**Explicação do erro tipo I:** " + g3.explicacao(resultados_simulados))

st.header("5. Poder")
st.plotly_chart(g4.figura(resultados_simulados), width="stretch")
st.markdown("**Explicação do poder:** " + g4.explicacao(resultados_simulados))

st.header("6. Dados reais")
resultados_reais, resumo_real = analise_real.analisar()
st.caption("Testes bicaudais sobre as diferenças pareadas com cache − sem cache, com α = 0,05.")
st.dataframe(
    resultados_reais,
    hide_index=True,
    column_config={"p-valor": st.column_config.NumberColumn(format="%.3e")},
)
st.markdown(resumo_real)

with st.expander("Explorar os dados reais durante a apresentação"):
    st.markdown(
        "Use os controles do Plotly para passar o cursor sobre uma observação, "
        "ocultar uma condição pela legenda e ampliar uma faixa do gráfico."
    )
    visao_real = st.radio(
        "Visualização",
        ("Linhas dos pares", "Distribuição das diferenças"),
        horizontal=True,
    )
    sem_cache, com_cache = amostra.pares()
    if visao_real == "Linhas dos pares":
        st.plotly_chart(exploracao.pares(sem_cache, com_cache), width="stretch")
        st.caption(
            "Cada linha é uma rodada. A queda consistente entre os extremos da "
            "linha deixa visível por que a análise precisa respeitar o pareamento."
        )
    else:
        st.plotly_chart(exploracao.diferencas(sem_cache, com_cache), width="stretch")
        st.caption(
            "Valores abaixo de zero indicam builds mais rápidos com cache; a linha "
            "tracejada representa ausência de diferença entre as condições."
        )

st.header("7. Conclusão")
st.markdown(
    "Antes de simular, esperávamos que o t pareado tivesse mais poder quando as "
    "diferenças se comportassem aproximadamente como uma distribuição normal e "
    "que o Wilcoxon ganhasse com valores extremos. Os resultados confirmaram essa "
    "previsão: o t foi um pouco mais potente no cenário base e com n pequeno, "
    "enquanto o Wilcoxon foi claramente melhor quando havia outliers.\n\n"
    "Para este cenário, recomendamos o **t pareado** se a distribuição das "
    "diferenças não tiver outliers relevantes e a média for a medida de interesse; "
    "ele preservou o erro tipo I e teve mais poder nessas condições. Com outliers "
    "simétricos, recomendamos o **Wilcoxon pareado**, pois manteve a taxa próxima "
    "de 5% e detectou mais efeitos. Não usaríamos a aparente vantagem do Wilcoxon "
    "com ruído muito assimétrico para decidir, porque seu pressuposto de simetria "
    "foi violado e o teste ficou liberal.\n\n"
    "Nos 30 pares reais, os dois testes rejeitaram H₀ e apontaram uma redução "
    "grande do tempo com cache. A principal limitação é que as medições foram "
    "feitas em uma única máquina e projeto, sob uso normal, portanto a magnitude "
    "do ganho não deve ser generalizada para outros ambientes sem nova coleta."
)
