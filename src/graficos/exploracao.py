"""Gráficos opcionais para explorar os pares reais durante a apresentação."""

import numpy as np
import plotly.graph_objects as go

from estilo import CORES_DADOS


COR_SEM_CACHE = "#E69F00"  # laranja Okabe-Ito
COR_COM_CACHE = "#009E73"  # verde Okabe-Ito
COR_LINHA = "rgba(80, 80, 80, 0.38)"


def _validar(sem_cache, com_cache):
    sem_cache = np.asarray(sem_cache, dtype=float)
    com_cache = np.asarray(com_cache, dtype=float)
    if sem_cache.ndim != 1 or com_cache.ndim != 1 or sem_cache.shape != com_cache.shape:
        raise ValueError("Os tempos devem ser vetores unidimensionais do mesmo tamanho.")
    if sem_cache.size == 0:
        raise ValueError("É necessário informar pelo menos um par.")
    return sem_cache, com_cache


def pares(sem_cache, com_cache):
    """Mostra cada par real como uma linha entre as duas condições."""
    sem_cache, com_cache = _validar(sem_cache, com_cache)
    numero_par = np.arange(1, sem_cache.size + 1)
    fig = go.Figure()
    for par, antes, depois in zip(numero_par, sem_cache, com_cache):
        fig.add_trace(go.Scatter(
            x=["Sem cache", "Com cache"], y=[antes, depois], mode="lines",
            line={"color": COR_LINHA, "width": 1.5}, showlegend=False,
            hovertemplate=(f"Par {par}<br>%{{x}}: %{{y:.3f}} s<extra></extra>"),
        ))
    fig.add_trace(go.Scatter(
        x=np.repeat("Sem cache", sem_cache.size), y=sem_cache, mode="markers",
        name="Sem cache", marker={"color": COR_SEM_CACHE, "size": 8},
        customdata=numero_par,
        hovertemplate="Par %{customdata}<br>Sem cache: %{y:.3f} s<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=np.repeat("Com cache", com_cache.size), y=com_cache, mode="markers",
        name="Com cache", marker={"color": COR_COM_CACHE, "size": 8},
        customdata=numero_par,
        hovertemplate="Par %{customdata}<br>Com cache: %{y:.3f} s<extra></extra>",
    ))
    fig.update_layout(
        title="Exploração — Cada rodada antes e depois do cache",
        height=540, separators=",.",
        legend={"orientation": "h", "yanchor": "top", "y": -0.13,
                "xanchor": "left", "x": 0}, margin={"b": 80},
    )
    fig.update_xaxes(title_text="Condição")
    fig.update_yaxes(title_text="Tempo de build (s)", rangemode="tozero")
    return fig


def diferencas(sem_cache, com_cache):
    """Mostra a distribuição de ``com_cache − sem_cache`` e a referência zero."""
    sem_cache, com_cache = _validar(sem_cache, com_cache)
    diferenca = com_cache - sem_cache
    fig = go.Figure(go.Histogram(
        x=diferenca, nbinsx=10, name="Diferenças observadas",
        marker={"color": CORES_DADOS["real"], "line": {"color": CORES_DADOS["real"], "width": 1}},
        hovertemplate="Diferença: %{x:.2f} s<br>Pares: %{y}<extra></extra>",
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="#333333", annotation_text="sem diferença")
    fig.update_layout(
        title="Exploração — Distribuição das diferenças pareadas",
        height=460, separators=",.", showlegend=False,
    )
    fig.update_xaxes(title_text="Diferença: com cache − sem cache (s)")
    fig.update_yaxes(title_text="Quantidade de pares")
    return fig
