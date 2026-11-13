"""G3: taxas simuladas de erro tipo I por cenário."""

import numpy as np
import plotly.graph_objects as go

from estilo import CORES, ROTULOS


ALFA = 0.05


def dados_erro_tipo_i(resultados):
    """Filtra as linhas com efeito zero, em ordem dos cenários informados."""
    dados = resultados[np.isclose(resultados["efeito"], 0.0)].copy()
    if dados.empty:
        raise ValueError("São necessários resultados com efeito igual a zero.")
    return dados


def figura(resultados, alfa=ALFA):
    """Cria G3, comparando a taxa de rejeição com o nível nominal ``alfa``."""
    dados = dados_erro_tipo_i(resultados)
    cenarios = list(dict.fromkeys(dados["cenario"]))
    # Os rótulos legíveis ficam no módulo de simulação para manter uma só fonte.
    import simulacao
    rotulos = [simulacao.CENARIOS[cenario]["rotulo"] for cenario in cenarios]

    fig = go.Figure()
    for teste in ("t", "wilcoxon"):
        serie = dados[dados["teste"] == teste].set_index("cenario").loc[cenarios]
        fig.add_trace(go.Bar(
            x=rotulos,
            y=serie["taxa_rejeicao"] * 100,
            name=ROTULOS[teste],
            marker_color=CORES[teste],
            customdata=np.column_stack((serie["repeticoes"], serie["erro_mc"] * 100)),
            hovertemplate=("%{x}<br>Taxa de rejeição: %{y:.2f}%"
                           "<br>Repetições: %{customdata[0]:.0f}"
                           "<br>Erro MC: %{customdata[1]:.2f} p.p.<extra></extra>"),
        ))
    fig.add_hline(
        y=alfa * 100, line_dash="dash", line_color="#333333",
        annotation_text=f"nível nominal α = {alfa:.0%}", annotation_position="top left",
    )
    fig.update_layout(
        title="G3 — Erro tipo I por situação simulada",
        barmode="group", height=500, separators=",.",
        legend={"orientation": "h", "yanchor": "top", "y": -0.2,
                "xanchor": "left", "x": 0},
        margin={"b": 125},
    )
    fig.update_xaxes(title_text="Situação simulada")
    fig.update_yaxes(title_text="Taxa de rejeição com H₀ verdadeira (%)", range=[0, 22])
    return fig


def _pct(valor):
    return f"{valor * 100:.2f}".replace(".", ",") + "%"


def explicacao(resultados, alfa=ALFA):
    """Produz quatro frases que interpretam o G3 com as taxas observadas."""
    dados = dados_erro_tipo_i(resultados).set_index(["cenario", "teste"])
    taxa = lambda c, t: float(dados.loc[(c, t), "taxa_rejeicao"])
    base = f"t = {_pct(taxa('base', 't'))} e Wilcoxon = {_pct(taxa('base', 'wilcoxon'))}"
    pequeno = f"t = {_pct(taxa('n_pequeno', 't'))} e Wilcoxon = {_pct(taxa('n_pequeno', 'wilcoxon'))}"
    outliers = f"t = {_pct(taxa('outliers', 't'))} e Wilcoxon = {_pct(taxa('outliers', 'wilcoxon'))}"
    assimetrico = f"t = {_pct(taxa('assimetrico', 't'))} e Wilcoxon = {_pct(taxa('assimetrico', 'wilcoxon'))}"
    return " ".join([
        f"As barras mostram, em {int(dados['repeticoes'].iloc[0]):,} repetições por situação, a proporção de rejeições quando o efeito é zero; a linha tracejada marca os {alfa:.0%} esperados.".replace(",", ".", 1),
        f"No cenário base ({base}) e com n pequeno ({pequeno}), as taxas ficaram próximas do nível nominal, embora o Wilcoxon com n = 8 seja conservador.",
        f"Com outliers, o t ficou conservador ({outliers}), enquanto o Wilcoxon permaneceu perto de {alfa:.0%}.",
        f"No ruído assimétrico ({assimetrico}), ambos ficaram liberais, sobretudo o Wilcoxon, pois a simetria exigida por esse teste foi violada de propósito.",
    ])
