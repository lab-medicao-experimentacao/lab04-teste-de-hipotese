"""G2: distribuição da estatística sob H₀, região de rejeição e área do p-valor.

Um subgráfico por teste, ambos com a mesma convenção visual:

- distribuição sob H₀ na cor do teste (``estilo.CORES``);
- região de rejeição preenchida na cor do teste com transparência alta;
- área do p-valor do exemplo sobreposta, na cor do teste e hachurada (onde
  coincide com a região de rejeição, fica mais escura);
- estatística observada como linha vertical tracejada.

O t pareado usa a densidade t de Student com n − 1 gl. O Wilcoxon usa a
distribuição exata de W+ (soma dos postos positivos) quando o ``testes.py``
calcula o p-valor exato; caso contrário (zeros, empates ou n grande), usa a
aproximação normal com correção de continuidade, como o SciPy.

Decisão: rejeita-se H₀ quando ``p < alfa`` (o mesmo critério de
``testes.py``); as regiões de rejeição abaixo seguem esse critério.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

import testes
from estilo import CORES, ROTULOS


ALFA_REGIAO = 0.2  # transparência da região de rejeição
ALFA_P = 0.4  # transparência da área do p-valor (sobreposta à região)


# ---------------------------------------------------------------- cálculos


def distribuicao_nula_w(n):
    """Distribuição exata de W+ sob H₀ para ``n`` diferenças não nulas sem empates.

    Sob H₀ cada posto 1..n entra em W+ com probabilidade 1/2, de forma
    independente; a contagem de subconjuntos de postos com cada soma é obtida
    por programação dinâmica e dividida por 2ⁿ.

    Retorna ``(valores, probabilidades)``, com valores 0..n(n+1)/2.
    """
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError(f"`n` deve ser um inteiro positivo (recebido {n!r}).")
    maximo = n * (n + 1) // 2
    contagens = np.zeros(maximo + 1, dtype=object)  # inteiros exatos
    contagens[0] = 1
    for posto in range(1, n + 1):
        contagens[posto:] = contagens[posto:] + contagens[:-posto].copy()
    probabilidades = np.array([c / 2**n for c in contagens], dtype=float)
    return np.arange(maximo + 1), probabilidades


def p_valor_w(w, probabilidades, alternativa):
    """p-valor exato de W+ = ``w`` (inteiro), com a mesma definição do SciPy.

    "less": P(W+ ≤ w); "greater": P(W+ ≥ w); "two-sided":
    min(1, 2·min(P(W+ ≤ w), P(W+ ≥ w))).
    """
    w = int(w)
    cdf = probabilidades[: w + 1].sum()
    sf = probabilidades[w:].sum()
    if alternativa == "less":
        return float(cdf)
    if alternativa == "greater":
        return float(sf)
    return float(min(1.0, 2 * min(cdf, sf)))


def regiao_rejeicao_t(gl, alternativa, alfa):
    """Valores críticos do t: ``{"inferior": c ou None, "superior": c ou None}``.

    Rejeita H₀ se t ≤ inferior ou t ≥ superior (α/2 em cada cauda no bicaudal).
    """
    if alternativa == "less":
        return {"inferior": float(stats.t.ppf(alfa, gl)), "superior": None}
    if alternativa == "greater":
        return {"inferior": None, "superior": float(stats.t.ppf(1 - alfa, gl))}
    q = float(stats.t.ppf(1 - alfa / 2, gl))
    return {"inferior": -q, "superior": q}


def regiao_rejeicao_w(n, alternativa, alfa):
    """Região de rejeição exata de W+ para ``n`` diferenças não nulas sem empates.

    É o conjunto de valores de W+ cujo p-valor exato (``p_valor_w``) é menor
    que ``alfa``, ou seja, exatamente os valores em que o teste rejeita H₀.
    Como W+ é discreto, o tamanho real (probabilidade da região sob H₀) fica
    abaixo de ``alfa`` em geral.

    Retorna ``{"inferior", "superior", "tamanho"}``: rejeita se W+ ≤ inferior
    ou W+ ≥ superior (``None`` quando a cauda não existe ou nenhum valor
    alcança ``alfa``, o que acontece com n muito pequeno).
    """
    valores, probs = distribuicao_nula_w(n)
    rejeita = np.array([p_valor_w(w, probs, alternativa) < alfa for w in valores])
    centro = n * (n + 1) / 4
    baixo = valores[rejeita & (valores < centro)]
    alto = valores[rejeita & (valores > centro)]
    return {
        "inferior": int(baixo.max()) if baixo.size else None,
        "superior": int(alto.min()) if alto.size else None,
        "tamanho": float(probs[rejeita].sum()),
    }


def normal_w(antes, depois):
    """Média e desvio-padrão de W+ sob H₀ (aproximação normal do SciPy).

    Média n(n+1)/4 e variância n(n+1)(2n+1)/24, descontando
    Σ(t³ − t)/48 pelos grupos de empates em |d| (zeros descartados).
    """
    d = np.asarray(depois, dtype=float) - np.asarray(antes, dtype=float)
    d = d[d != 0]
    n = d.size
    _, empates = np.unique(np.abs(d), return_counts=True)
    variancia = n * (n + 1) * (2 * n + 1) / 24 - (empates**3 - empates).sum() / 48
    return n * (n + 1) / 4, float(np.sqrt(variancia))


def _regiao_normal_w(media, dp, alternativa, alfa):
    """Limites da região de rejeição de W+ na aproximação normal com correção.

    Equivalem a ``p < alfa`` com a correção de continuidade de 0,5 do SciPy.
    """
    if alternativa == "less":
        return {"inferior": media + stats.norm.ppf(alfa) * dp - 0.5, "superior": None}
    if alternativa == "greater":
        return {"inferior": None, "superior": media + stats.norm.ppf(1 - alfa) * dp + 0.5}
    q = stats.norm.ppf(1 - alfa / 2) * dp + 0.5
    return {"inferior": media - q, "superior": media + q}


def _area_p(obs, centro, alternativa, correcao=0.0):
    """Limites (como uma região de rejeição) da área do p-valor do observado."""
    if alternativa == "less":
        return {"inferior": obs + correcao, "superior": None}
    if alternativa == "greater":
        return {"inferior": None, "superior": obs - correcao}
    dist = max(abs(obs - centro) - correcao, 0.0)
    return {"inferior": centro - dist, "superior": centro + dist}


def _dentro(x, regiao):
    """Máscara dos ``x`` que caem na região (cauda inferior e/ou superior)."""
    x = np.asarray(x, dtype=float)
    mascara = np.zeros(x.shape, dtype=bool)
    if regiao["inferior"] is not None:
        mascara |= x <= regiao["inferior"] + 1e-9
    if regiao["superior"] is not None:
        mascara |= x >= regiao["superior"] - 1e-9
    return mascara


# ---------------------------------------------------------------- textos


def _num(x, casas=2):
    """Número com vírgula decimal e sinal de menos tipográfico."""
    return f"{x:.{casas}f}".replace(".", ",").replace("-", "−")


def _p(p):
    return "p < 0,001" if p < 0.001 else f"p = {_num(p, 3)}"


def _rgba(cor, alfa):
    """Converte ``#RRGGBB`` de ``estilo.CORES`` em ``rgba(...)`` com transparência."""
    r, g, b = (int(cor[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alfa})"


def _descrever(regiao, simbolo, casas):
    partes = []
    if regiao["inferior"] is not None:
        partes.append(f"{simbolo} ≤ {_num(regiao['inferior'], casas)}")
    if regiao["superior"] is not None:
        partes.append(f"{simbolo} ≥ {_num(regiao['superior'], casas)}")
    return " ou ".join(partes) if partes else "vazia"


# ---------------------------------------------------------------- figura


def _resultados(antes, depois, alternativa, alfa):
    """Resultados de ``testes.py`` e as regiões usadas no gráfico e no texto."""
    t = testes.t_pareado(antes, depois, alternativa, alfa)
    w = testes.wilcoxon_pareado(antes, depois, alternativa, alfa)
    t["regiao"] = regiao_rejeicao_t(t["gl"], alternativa, alfa)
    t["area_p"] = _area_p(t["estatistica"], 0.0, alternativa)
    w["exato"] = w["metodo"] == "exato"
    if w["exato"]:
        w["regiao"] = regiao_rejeicao_w(w["n"], alternativa, alfa)
        w["area_p"] = _area_p(w["estatistica"], w["n"] * (w["n"] + 1) / 4, alternativa)
    else:
        media, dp = normal_w(antes, depois)
        w["media"], w["dp"] = media, dp
        w["regiao"] = _regiao_normal_w(media, dp, alternativa, alfa)
        w["area_p"] = _area_p(w["estatistica"], media, alternativa, correcao=0.5)
    return t, w


def _curva(fig, x, y, mascara, cor, nome, alfa_cor, padrao, col, mostrar):
    """Preenche sob a curva onde ``mascara`` é verdadeira (pode ter duas caudas)."""
    primeira = True
    for trecho in np.split(np.arange(x.size), np.flatnonzero(np.diff(mascara)) + 1):
        if not mascara[trecho[0]]:
            continue
        fig.add_trace(
            go.Scatter(
                x=x[trecho], y=y[trecho], mode="lines", line={"width": 0},
                fill="tozeroy", fillcolor=_rgba(cor, alfa_cor),
                fillpattern={"shape": padrao, "fgcolor": cor} if padrao else None,
                name=nome, legendgroup=nome, showlegend=mostrar and primeira,
                hoverinfo="skip",
            ),
            row=1, col=col,
        )
        primeira = False


def _malha(x, regioes):
    """Inclui os limites das regiões na malha para o preenchimento começar neles."""
    extras = [v for r in regioes for v in (r["inferior"], r["superior"]) if v is not None]
    return np.unique(np.concatenate([x, np.asarray(extras, dtype=float)]))


def figura(antes, depois, alternativa, alfa):
    """G2: distribuição sob H₀, região de rejeição e área do p-valor dos dois testes.

    ``antes`` e ``depois`` são o conjunto de exemplo; estatísticas e p-valores
    vêm de ``testes.t_pareado`` e ``testes.wilcoxon_pareado``.
    """
    t, w = _resultados(antes, depois, alternativa, alfa)
    rotulo_alfa = f"α = {_num(alfa)}"
    titulo_w = ROTULOS["wilcoxon"] + (
        " — distribuição exata de W⁺" if w["exato"]
        else " — aproximação normal de W⁺"
        + (" (p do teste por permutação)" if "permutação" in w["metodo"] else "")
    )
    fig = make_subplots(
        rows=1, cols=2, horizontal_spacing=0.08,
        subplot_titles=(f"{ROTULOS['t']} — t de Student com {t['gl']} gl", titulo_w),
    )

    # t pareado: densidade t com n − 1 gl.
    cor = CORES["t"]
    limite = max(4.0, abs(t["estatistica"]) + 0.5)
    x = _malha(np.linspace(-limite, limite, 801), [t["regiao"], t["area_p"]])
    y = stats.t.pdf(x, t["gl"])
    fig.add_trace(
        go.Scatter(x=x, y=y, mode="lines", line={"color": cor, "width": 2},
                   name=f"{ROTULOS['t']}: distribuição sob H₀"),
        row=1, col=1,
    )
    _curva(fig, x, y, _dentro(x, t["regiao"]), cor,
           f"{ROTULOS['t']}: região de rejeição ({rotulo_alfa})", ALFA_REGIAO, None, 1, True)
    _curva(fig, x, y, _dentro(x, t["area_p"]), cor,
           f"{ROTULOS['t']}: área do p-valor ({_p(t['p_valor'])})", ALFA_P, "/", 1, True)
    fig.add_vline(
        x=t["estatistica"], line={"color": cor, "dash": "dash"}, row=1, col=1,
        annotation_text=f"t observado = {_num(t['estatistica'])}<br>{_p(t['p_valor'])}",
        annotation_position="top right" if t["estatistica"] < 0 else "top left",
    )

    # Wilcoxon pareado: W+ exata (barras) ou aproximação normal (curva).
    cor = CORES["wilcoxon"]
    nome_regiao = f"{ROTULOS['wilcoxon']}: região de rejeição ({rotulo_alfa}"
    nome_p = f"{ROTULOS['wilcoxon']}: área do p-valor ({_p(w['p_valor'])})"
    if w["exato"]:
        valores, probs = distribuicao_nula_w(w["n"])
        na_regiao, no_p = _dentro(valores, w["regiao"]), _dentro(valores, w["area_p"])
        nome_regiao += f"; tamanho real {_num(w['regiao']['tamanho'], 3)})"
        grupos = [
            (~na_regiao, f"{ROTULOS['wilcoxon']}: distribuição sob H₀", 0.0, ""),
            (na_regiao, nome_regiao, ALFA_REGIAO, ""),
            (no_p, nome_p, ALFA_P, "/"),
        ]
        for mascara, nome, alfa_cor, padrao in grupos:
            fig.add_trace(
                go.Bar(
                    x=valores[mascara], y=probs[mascara], name=nome, width=0.9,
                    marker={"color": _rgba(cor, alfa_cor), "line": {"color": cor, "width": 1},
                            "pattern": {"shape": padrao, "fgcolor": cor}},
                ),
                row=1, col=2,
            )
        xmin, xmax = -0.5, valores[-1] + 0.5
    else:
        media, dp = w["media"], w["dp"]
        xmin = min(0.0, w["estatistica"] - 1)
        xmax = max(w["n"] * (w["n"] + 1) / 2, w["estatistica"] + 1)
        x = _malha(np.linspace(xmin, xmax, 801), [w["regiao"], w["area_p"]])
        y = stats.norm.pdf(x, media, dp)
        fig.add_trace(
            go.Scatter(x=x, y=y, mode="lines", line={"color": cor, "width": 2},
                       name=f"{ROTULOS['wilcoxon']}: aproximação normal sob H₀"),
            row=1, col=2,
        )
        _curva(fig, x, y, _dentro(x, w["regiao"]), cor, nome_regiao + ")",
               ALFA_REGIAO, None, 2, True)
        _curva(fig, x, y, _dentro(x, w["area_p"]), cor, nome_p, ALFA_P, "/", 2, True)
    fig.add_vline(
        x=w["estatistica"], line={"color": cor, "dash": "dash"}, row=1, col=2,
        annotation_text=(f"W⁺ observado = {_num(w['estatistica'], 1).replace(',0', '')}"
                         f"<br>{_p(w['p_valor'])}"),
        annotation_position="top right" if w["estatistica"] < (xmin + xmax) / 2 else "top left",
    )

    fig.update_xaxes(title_text="Estatística t (adimensional)", range=[-limite, limite],
                     row=1, col=1)
    fig.update_xaxes(title_text="Estatística W⁺ (soma dos postos positivos)",
                     range=[xmin, xmax], row=1, col=2)
    fig.update_yaxes(title_text="Densidade", rangemode="tozero", row=1, col=1)
    fig.update_yaxes(title_text="Densidade" if not w["exato"] else "Probabilidade",
                     rangemode="tozero", row=1, col=2)
    fig.update_layout(
        title={"text": "G2 — Distribuição da estatística sob H₀"},
        barmode="overlay", bargap=0, separators=",.", height=520,
        legend={"orientation": "h", "yanchor": "top", "y": -0.18, "xanchor": "left", "x": 0},
        margin={"b": 150},
    )
    return fig


def explicacao(antes, depois, alternativa, alfa):
    """Texto de 3 a 4 frases sobre o G2, com os números do exemplo."""
    t, w = _resultados(antes, depois, alternativa, alfa)
    caudas = {
        "two-sided": "nas duas caudas porque o teste é bicaudal",
        "less": "só na cauda inferior porque H₁ é unilateral, depois < antes",
        "greater": "só na cauda superior porque H₁ é unilateral, depois > antes",
    }[alternativa]
    if w["exato"]:
        regiao_w = (f"{_descrever(w['regiao'], 'W⁺', 0)}, com tamanho real "
                    f"{_num(w['regiao']['tamanho'], 3)} porque W⁺ é discreto")
    else:
        regiao_w = f"{_descrever(w['regiao'], 'W⁺', 1)}, pela aproximação normal"
    w_obs = _num(w["estatistica"], 1).replace(",0", "")
    return " ".join([
        f"O t pareado divide a média das diferenças (depois − antes) pelo seu "
        f"erro-padrão e compara o resultado com a t de Student com {t['gl']} gl; "
        f"o Wilcoxon ordena os |d|, atribui postos e soma os postos das "
        f"diferenças positivas (W⁺), cuja distribuição sob H₀ supõe cada sinal "
        f"igualmente provável.",
        f"A região de rejeição reúne os valores mais extremos da estatística, "
        f"improváveis se H₀ for verdadeira, com probabilidade total "
        f"α = {_num(alfa)}, e fica {caudas} "
        f"({_descrever(t['regiao'], 't', 3)}; {regiao_w}).",
        f"No exemplo, t = {_num(t['estatistica'])} dá {_p(t['p_valor'])} e "
        f"W⁺ = {w_obs} dá {_p(w['p_valor'])}: supondo H₀ verdadeira, essa é a "
        f"probabilidade de obter uma estatística tão ou mais extrema que a "
        f"observada (a área hachurada).",
        "O p-valor não é a probabilidade de H₀ ser verdadeira nem a de o "
        "resultado ser obra do acaso.",
    ])
