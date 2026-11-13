"""G4: curvas de poder do t pareado e Wilcoxon por cenário."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import simulacao
from estilo import CORES, ROTULOS


def figura(resultados):
    """Cria G4 com uma curva de cada teste em cada situação simulada."""
    cenarios = list(dict.fromkeys(resultados["cenario"]))
    fig = make_subplots(
        rows=2, cols=2, horizontal_spacing=0.10, vertical_spacing=0.16,
        subplot_titles=[simulacao.CENARIOS[c]["rotulo"] for c in cenarios],
    )
    for indice, cenario in enumerate(cenarios):
        row, col = divmod(indice, 2)
        for teste in ("t", "wilcoxon"):
            dados = resultados[(resultados["cenario"] == cenario) &
                               (resultados["teste"] == teste)].sort_values("efeito")
            fig.add_trace(go.Scatter(
                x=dados["efeito"] * 100, y=dados["taxa_rejeicao"] * 100,
                mode="lines+markers", name=ROTULOS[teste], legendgroup=teste,
                showlegend=indice == 0, line={"color": CORES[teste], "width": 3},
                marker={"size": 7},
                customdata=dados["repeticoes"],
                hovertemplate=("Redução: %{x:.0f}%<br>Poder: %{y:.2f}%"
                               "<br>Repetições: %{customdata:.0f}<extra></extra>"),
            ), row=row + 1, col=col + 1)
        fig.update_xaxes(title_text="Redução verdadeira no tempo (%)", row=row + 1, col=col + 1)
        fig.update_yaxes(title_text="Proporção de rejeições (%)", range=[0, 105], row=row + 1, col=col + 1)
    fig.update_layout(
        title="G4 — Poder por tamanho de efeito e situação simulada",
        height=720, separators=",.",
        legend={"orientation": "h", "yanchor": "top", "y": -0.10,
                "xanchor": "left", "x": 0}, margin={"b": 90},
    )
    return fig


def _pct(valor):
    return f"{valor * 100:.1f}".replace(".", ",") + "%"


def explicacao(resultados):
    """Produz quatro frases que interpretam as curvas de poder do G4."""
    dados = resultados.set_index(["cenario", "efeito", "teste"])
    efeitos = sorted(resultados["efeito"].unique())
    efeito_meio = efeitos[len(efeitos) // 2]
    taxa = lambda c, t: float(dados.loc[(c, efeito_meio, t), "taxa_rejeicao"])
    return " ".join([
        "Cada curva mostra a proporção de conjuntos em que H₀ foi rejeitada para uma redução verdadeira do tempo; no ponto 0%, ela também reproduz o erro tipo I.",
        f"No cenário base, o t pareado teve ligeiramente mais poder que o Wilcoxon, por exemplo {_pct(taxa('base', 't'))} contra {_pct(taxa('base', 'wilcoxon'))} para redução de {efeito_meio:.0%}, e a mesma vantagem aparece com n pequeno.",
        f"Com outliers, a vantagem muda para o Wilcoxon ({_pct(taxa('outliers', 'wilcoxon'))} contra {_pct(taxa('outliers', 't'))} no efeito intermediário), porque os postos reduzem a influência dos valores extremos.",
        f"O Wilcoxon também parece mais potente no ruído assimétrico ({_pct(taxa('assimetrico', 'wilcoxon'))} contra {_pct(taxa('assimetrico', 't'))}), mas essa comparação não sustenta uma recomendação: nesse cenário seu erro tipo I já estava inflado por violar a simetria.",
    ])
