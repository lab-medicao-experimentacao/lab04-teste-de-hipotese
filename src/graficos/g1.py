"""G1: dados reais ao lado dos simulados, um histograma por condição.

Um subgráfico por condição (sem cache e com cache). Em cada um, os
histogramas real e simulado ficam sobrepostos, com as mesmas classes, para
que a forma possa ser comparada diretamente. As condições têm escalas
próprias porque o cache reduz o tempo em cerca de 11 vezes.

O conjunto simulado tem o mesmo n da amostra real, semente fixa e o efeito
observado na amostra (``parametros.da_amostra()["efeito_real"]``), para que a
condição com cache seja comparável. Nas simulações de Q1 a Q3 o efeito varia
na faixa de ``parametros.EFEITOS``.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import amostra
import parametros
from dados import gerar_pares
from estilo import CORES_DADOS, ROTULOS_DADOS


SEMENTE = 42
CONDICOES = ("Sem cache (antes)", "Com cache (depois)")
OPACIDADE = 0.6


def conjuntos(semente=SEMENTE):
    """Devolve ``{"real": (antes, depois), "simulado": (antes, depois)}`` em segundos."""
    real = amostra.pares()
    efeito = parametros.da_amostra()["efeito_real"]
    simulado = gerar_pares(real[0].size, efeito, np.random.default_rng(semente))
    return {"real": real, "simulado": simulado}


def _classes(*series, n_classes=12):
    """Classes comuns às séries: ``{"start", "end", "size"}`` para ``go.Histogram``."""
    todos = np.concatenate(series)
    inicio, fim = float(todos.min()), float(todos.max())
    tamanho = (fim - inicio) / n_classes
    return {"start": inicio, "end": fim + tamanho * 1e-6, "size": tamanho}


def figura(real, simulado):
    """G1: histogramas real × simulado de cada condição.

    ``real`` e ``simulado`` são pares ``(antes, depois)`` em segundos, como
    os devolvidos por ``conjuntos()``.
    """
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.08, subplot_titles=CONDICOES)
    for col, (x_real, x_sim) in enumerate(zip(real, simulado), start=1):
        classes = _classes(x_real, x_sim)
        for origem, x in (("real", x_real), ("simulado", x_sim)):
            fig.add_trace(
                go.Histogram(
                    x=x, xbins=classes, autobinx=False, opacity=OPACIDADE,
                    name=f"{ROTULOS_DADOS[origem]} (n = {np.size(x)})",
                    legendgroup=origem, showlegend=col == 1,
                    marker={"color": CORES_DADOS[origem],
                            "line": {"color": CORES_DADOS[origem], "width": 1}},
                    hovertemplate="%{x} s: %{y} builds<extra></extra>",
                ),
                row=1, col=col,
            )
        fig.update_xaxes(title_text="Tempo de build (s)", row=1, col=col)
        fig.update_yaxes(title_text="Quantidade de builds", row=1, col=col)
    fig.update_layout(
        title={"text": "G1 — Tempo de build real × simulado, por condição"},
        barmode="overlay", separators=",.", height=460,
        legend={"orientation": "h", "yanchor": "top", "y": -0.2, "xanchor": "left", "x": 0},
        margin={"b": 110},
    )
    return fig


def _num(x, casas=2):
    return f"{x:.{casas}f}".replace(".", ",")


def limite_lento(x):
    """Limite de build lento: Q3 + 1,5·IQR de ``x`` (s)."""
    q1, q3 = np.percentile(x, [25, 75])
    return float(q3 + 1.5 * (q3 - q1))


def _frase_outliers(ra, sa):
    """Quantidade de builds lentos (sem cache) real × simulada."""
    limite = limite_lento(ra)
    n_real, n_sim = int(np.sum(ra > limite)), int(np.sum(sa > limite))
    return (f"acima de {_num(limite)} s, limite de outlier da amostra real, há "
            f"{n_real} builds reais e {n_sim} simulados sem cache")


def explicacao(real, simulado, p=None):
    """Texto de 4 frases sobre o G1: forma dos dados e escolha dos parâmetros."""
    p = parametros.da_amostra() if p is None else p
    (ra, rd), (sa, sd) = real, simulado
    return " ".join([
        f"Os tempos reais são assimétricos à direita: sem cache, a mediana é "
        f"{_num(np.median(ra))} s, mas há builds lentos de até {_num(np.max(ra))} s; "
        f"com cache, a mediana cai para {_num(np.median(rd))} s.",
        f"Por isso a simulação usa uma lognormal com mediana {_num(p['mediana'])} s "
        f"e divide a variação do log em uma parte comum ao par, do estado da "
        f"máquina (σ = {_num(p['sigma_rodada'], 3)}), e uma parte de cada build "
        f"(σ = {_num(p['sigma_ruido'], 3)}), conforme a correlação "
        f"{_num(p['correlacao'])} entre as duas medições de cada rodada.",
        f"Com o efeito observado ({p['efeito_real']:.0%} de redução), os simulados "
        f"ficam na mesma faixa dos reais (medianas de {_num(np.median(sa))} s e "
        f"{_num(np.median(sd))} s); {_frase_outliers(ra, sa)}.",
        f"Nas simulações de erro tipo I e poder, o efeito vai de 0 a "
        f"{parametros.EFEITOS[-1]:.0%}, porque {p['efeito_real']:.0%} seria "
        f"detectado sempre pelos dois testes, e os builds lentos serão "
        f"exagerados no cenário de violação de pressupostos.",
    ])
