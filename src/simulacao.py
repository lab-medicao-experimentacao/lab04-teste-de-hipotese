"""Simulações de erro tipo I e poder do t pareado × Wilcoxon pareado (Q1–Q3).

Cada *célula* da simulação é um par (cenário, tamanho de efeito): geram-se
``REPETICOES`` conjuntos de dados pareados, aplicam-se os dois testes a cada
um e conta-se a proporção de p-valores < α.

- **Q1 (erro tipo I):** efeito 0 no cenário base.
- **Q2 (poder):** efeitos crescentes (0 incluído) no cenário base.
- **Q3 (pressupostos violados):** Q1 e Q2 repetidas em cenários com n pequeno,
  *outliers* e ruído muito assimétrico.

Modelo de dados: o mesmo de ``dados.gerar_pares`` (ver ``parametros.py``),
com mediana e dispersões estimadas de ``data/amostra.csv``::

    L      ~ Normal(log(mediana), sigma_rodada)      nível comum ao par
    antes  = exp(L + e1)                             (s)
    depois = exp(L + log(1 - efeito) + e2)           (s)

``efeito`` é a redução proporcional da mediana (0,02 = 2% mais rápido). Com
``efeito = 0``, antes e depois são intercambiáveis: ``d = depois - antes`` é
simétrica em torno de zero e tem média zero, então H₀ vale para o t pareado e
para o Wilcoxon. Os cenários mudam só ``e1``/``e2`` ou o ruído:

- ``base`` e ``n_pequeno``: ``e1, e2 ~ Normal(0, sigma_ruido)``;
- ``outliers``: 10% dos ``e1``/``e2`` (sorteados de forma independente) têm
  desvio-padrão multiplicado por 5; a simetria sob H₀ é preservada;
- ``assimetrico``: ``depois = antes * (1 - efeito) + eps``, com ``eps`` de
  média 0, muito assimétrico (lognormal) e desvio-padrão igual ao de ``d``
  sob H₀ no modelo base. H₀ vale para o t (média 0), mas a simetria exigida
  pelo Wilcoxon é violada de propósito, e as taxas devem ser lidas assim.

Escolhas de cálculo (as mesmas de ``testes.py``): ``scipy.stats.ttest_rel`` e
``scipy.stats.wilcoxon(zero_method="wilcox", method="auto")``, ambos com a
mesma ``alternativa``, aplicados de forma vetorizada (``axis=1``). Há um teste
em ``tests/test_simulacao.py`` que confere a equivalência com ``testes.py``.

Reprodutibilidade: cada célula usa um gerador próprio, derivado de
``(semente, índice do cenário, índice do efeito)``; o resultado de uma célula
não depende das demais nem da ordem em que são calculadas. Nada usa o
gerador global do NumPy.

Formato do resultado (DataFrame "longo", uma linha por cenário × efeito ×
teste): ``cenario``, ``efeito``, ``teste`` (chave de ``estilo.ROTULOS``),
``taxa_rejeicao`` (proporção em [0, 1]), ``repeticoes``, ``erro_mc`` (erro
padrão de Monte Carlo da taxa) e ``n`` (pares por conjunto).
"""

import numpy as np
import pandas as pd
from scipy import stats

import parametros


REPETICOES = 10_000
SEMENTE = 42
ALFA = 0.05
ALTERNATIVA = "two-sided"  # bicaudal, como no restante do dashboard
EFEITOS = parametros.EFEITOS  # 0 a 10% de redução, como no G1

# Cenário base + situações que violam pressupostos do t (Q3).
CENARIOS = {
    "base": {
        "rotulo": "Base (n = 30, ruído normal)",
        "n": 30, "ruido_tipo": "normal",
    },
    "n_pequeno": {
        "rotulo": "n pequeno (n = 8)",
        "n": 8, "ruido_tipo": "normal",
    },
    "outliers": {
        "rotulo": "Outliers (10% das medições com ruído 5×)",
        "n": 30, "ruido_tipo": "contaminado",
    },
    "assimetrico": {
        "rotulo": "Ruído muito assimétrico (n = 15)",
        "n": 15, "ruido_tipo": "assimetrico",
    },
}

TESTES = ("t", "wilcoxon")

_FRACAO_OUTLIERS = 0.10
_FATOR_OUTLIERS = 5.0
_SIGMA_ASSIMETRIA = 1.0  # sigma da lognormal que gera o ruído assimétrico


def _sigma_d_h0(p):
    """Desvio-padrão (s) de ``d`` sob H₀ no modelo base lognormal."""
    mu, sr, se = np.log(p["mediana"]), p["sigma_rodada"], p["sigma_ruido"]
    var_x = (np.exp(sr**2 + se**2) - 1) * np.exp(2 * mu + sr**2 + se**2)
    cov = np.exp(2 * mu + sr**2 + se**2) * (np.exp(sr**2) - 1)
    return float(np.sqrt(2 * var_x - 2 * cov))


def _ruido_log(tipo, forma, sigma, rng):
    """Ruído ``e`` do log do tempo, normal ou contaminado por outliers."""
    e = rng.normal(0.0, sigma, size=forma)
    if tipo == "contaminado":
        outlier = rng.random(size=forma) < _FRACAO_OUTLIERS
        e = np.where(outlier, e * _FATOR_OUTLIERS, e)
    return e


def _eps_assimetrico(forma, dp, rng):
    """Lognormal centrada na média e escalada para desvio-padrão ``dp`` (s)."""
    s = _SIGMA_ASSIMETRIA
    media = np.exp(s**2 / 2)
    dp_base = np.sqrt((np.exp(s**2) - 1) * np.exp(s**2))
    return dp * (rng.lognormal(0.0, s, size=forma) - media) / dp_base


def gerar_diferencas(cenario, efeito, repeticoes, rng, parametros_gerador=None):
    """Gera ``repeticoes`` conjuntos de pares e devolve ``(antes, depois)``.

    Cada array tem forma ``(repeticoes, n)``, com ``n`` do cenário; a linha
    ``i`` de ``antes`` e de ``depois`` forma um conjunto pareado (o pareamento
    nunca é desfeito). Usa apenas ``rng``. Sem ``parametros_gerador``, usa os
    estimados da amostra real (chaves ``mediana``, ``sigma_rodada`` e
    ``sigma_ruido``).
    """
    if not 0 <= efeito < 1:
        raise ValueError(f"`efeito` deve estar em [0, 1) (recebido {efeito}).")
    p = parametros.parametros_gerador(parametros_gerador)
    spec = CENARIOS[cenario]
    forma = (repeticoes, spec["n"])
    nivel = rng.normal(np.log(p["mediana"]), p["sigma_rodada"], size=forma)
    tipo = spec["ruido_tipo"]
    if tipo == "assimetrico":
        antes = np.exp(nivel + rng.normal(0.0, p["sigma_ruido"], size=forma))
        eps = _eps_assimetrico(forma, _sigma_d_h0(p), rng)
        return antes, antes * (1 - efeito) + eps
    if tipo not in ("normal", "contaminado"):
        raise ValueError(f"Tipo de ruído desconhecido: {tipo!r}.")
    e1 = _ruido_log(tipo, forma, p["sigma_ruido"], rng)
    e2 = _ruido_log(tipo, forma, p["sigma_ruido"], rng)
    return np.exp(nivel + e1), np.exp(nivel + np.log1p(-efeito) + e2)


def taxas_de_rejeicao(antes, depois, alternativa=ALTERNATIVA, alfa=ALFA):
    """Proporção de p-valores < ``alfa`` de cada teste, nas linhas dos arrays.

    ``antes`` e ``depois`` têm forma ``(repeticoes, n)``. Devolve
    ``{"t": taxa, "wilcoxon": taxa}``.
    """
    p_t = stats.ttest_rel(depois, antes, axis=1, alternative=alternativa).pvalue
    p_w = stats.wilcoxon(
        depois - antes, axis=1, alternative=alternativa,
        zero_method="wilcox", method="auto",
    ).pvalue
    return {"t": float(np.mean(p_t < alfa)), "wilcoxon": float(np.mean(p_w < alfa))}


def simular_celula(cenario, efeito, repeticoes=REPETICOES, semente=SEMENTE,
                   alternativa=ALTERNATIVA, alfa=ALFA, parametros_gerador=None):
    """Simula um cenário e um efeito; devolve ``{"t": taxa, "wilcoxon": taxa}``."""
    i_cenario = list(CENARIOS).index(cenario)
    i_efeito = list(EFEITOS).index(efeito) if efeito in EFEITOS else int(round(efeito * 1e6))
    rng = np.random.default_rng([semente, i_cenario, i_efeito])
    antes, depois = gerar_diferencas(cenario, efeito, repeticoes, rng, parametros_gerador)
    return taxas_de_rejeicao(antes, depois, alternativa, alfa)


def simular(cenarios=None, efeitos=EFEITOS, repeticoes=REPETICOES, semente=SEMENTE,
            alternativa=ALTERNATIVA, alfa=ALFA, parametros_gerador=None):
    """Roda a simulação e devolve o DataFrame longo descrito no módulo."""
    linhas = []
    for cenario in (cenarios if cenarios is not None else CENARIOS):
        n = CENARIOS[cenario]["n"]
        for efeito in efeitos:
            taxas = simular_celula(
                cenario, efeito, repeticoes, semente, alternativa, alfa, parametros_gerador
            )
            for teste in TESTES:
                taxa = taxas[teste]
                linhas.append({
                    "cenario": cenario,
                    "efeito": float(efeito),
                    "teste": teste,
                    "taxa_rejeicao": taxa,
                    "repeticoes": int(repeticoes),
                    "erro_mc": float(np.sqrt(taxa * (1 - taxa) / repeticoes)),
                    "n": int(n),
                })
    return pd.DataFrame(linhas)


def q1_erro_tipo_i(**kwargs):
    """Q1: taxa de rejeição com H₀ verdadeira (efeito 0), cenário base."""
    return simular(cenarios=["base"], efeitos=(0.0,), **kwargs)


def q2_poder(**kwargs):
    """Q2: taxa de rejeição para os efeitos de ``EFEITOS``, cenário base."""
    return simular(cenarios=["base"], **kwargs)


def q3_pressupostos(**kwargs):
    """Q3: Q1 e Q2 nos cenários que violam pressupostos do t."""
    violacoes = [c for c in CENARIOS if c != "base"]
    return simular(cenarios=violacoes, **kwargs)


def simular_tudo(**kwargs):
    """Q1, Q2 e Q3 de uma vez (todos os cenários × todos os efeitos).

    O erro tipo I (Q1 e Q3) está nas linhas com ``efeito == 0``; o poder
    (Q2 e Q3), nas demais.
    """
    return simular(**kwargs)
