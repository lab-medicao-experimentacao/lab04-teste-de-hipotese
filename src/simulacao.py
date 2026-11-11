"""Simulações de erro tipo I e poder do t pareado × Wilcoxon pareado (Q1–Q3).

Cada *célula* da simulação é um par (cenário, tamanho de efeito): geram-se
``REPETICOES`` conjuntos de dados pareados, aplicam-se os dois testes a cada
um e conta-se a proporção de p-valores < α.

- **Q1 (erro tipo I):** efeito 0 no cenário base.
- **Q2 (poder):** efeitos crescentes (0 incluído) no cenário base.
- **Q3 (pressupostos violados):** Q1 e Q2 repetidas em cenários com n pequeno,
  *outliers* e ruído muito assimétrico.

Modelo de dados (o mesmo do gerador provisório ``dados_provisorio``; os
valores de ``PARAMETROS_BASE`` serão recalibrados com a amostra real)::

    antes  ~ lognormal(mediana, sigma)           (s)
    depois = antes * (1 - efeito) + eps          (s)

``efeito`` é a redução proporcional do tempo (0,02 = 2% mais rápido). Com
``efeito = 0``, ``d = depois - antes = eps``; ``eps`` tem média 0 em todos os
cenários, então H₀ do t pareado (média de d = 0) é verdadeira. Nos cenários
``normal`` e ``outliers``, ``eps`` também é simétrico em torno de 0 (H₀ do
Wilcoxon verdadeira). No cenário ``assimetrico``, ``eps`` tem média 0 mas é
muito assimétrico (mediana < 0): H₀ vale para o t, mas a simetria exigida
pelo Wilcoxon é violada de propósito, e as taxas devem ser lidas com isso em
mente.

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


REPETICOES = 10_000
SEMENTE = 42
ALFA = 0.05
ALTERNATIVA = "two-sided"  # provisório até o grupo decidir H₁
EFEITOS = (0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06)

# Parâmetros provisórios (iguais aos de dados_provisorio.gerar_pares).
PARAMETROS_BASE = {"mediana": 120.0, "sigma": 0.3, "ruido": 5.0}

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
        "rotulo": "Outliers (10% dos pares com ruído 10×)",
        "n": 30, "ruido_tipo": "contaminado",
    },
    "assimetrico": {
        "rotulo": "Ruído muito assimétrico (n = 15)",
        "n": 15, "ruido_tipo": "assimetrico",
    },
}

TESTES = ("t", "wilcoxon")

_FRACAO_OUTLIERS = 0.10
_FATOR_OUTLIERS = 10.0
_SIGMA_ASSIMETRIA = 1.0  # sigma da lognormal que gera o ruído assimétrico


def _ruido(tipo, forma, ruido, rng):
    """Sorteia ``eps`` (s) com média 0 e a ``forma`` pedida."""
    if tipo == "normal":
        return rng.normal(0.0, ruido, size=forma)
    if tipo == "contaminado":
        eps = rng.normal(0.0, ruido, size=forma)
        outlier = rng.random(size=forma) < _FRACAO_OUTLIERS
        return np.where(outlier, eps * _FATOR_OUTLIERS, eps)
    if tipo == "assimetrico":
        # Lognormal centrada na média e escalada para desvio-padrão = ruido.
        s = _SIGMA_ASSIMETRIA
        media = np.exp(s**2 / 2)
        dp = np.sqrt((np.exp(s**2) - 1) * np.exp(s**2))
        return ruido * (rng.lognormal(0.0, s, size=forma) - media) / dp
    raise ValueError(f"Tipo de ruído desconhecido: {tipo!r}.")


def gerar_diferencas(cenario, efeito, repeticoes, rng, parametros=None):
    """Gera ``repeticoes`` conjuntos de pares e devolve ``(antes, depois)``.

    Cada array tem forma ``(repeticoes, n)``, com ``n`` do cenário; a linha
    ``i`` de ``antes`` e de ``depois`` forma um conjunto pareado (o pareamento
    nunca é desfeito). Usa apenas ``rng``.
    """
    if not 0 <= efeito < 1:
        raise ValueError(f"`efeito` deve estar em [0, 1) (recebido {efeito}).")
    p = {**PARAMETROS_BASE, **(parametros or {})}
    spec = CENARIOS[cenario]
    forma = (repeticoes, spec["n"])
    antes = rng.lognormal(np.log(p["mediana"]), p["sigma"], size=forma)
    eps = _ruido(spec["ruido_tipo"], forma, p["ruido"], rng)
    return antes, antes * (1 - efeito) + eps


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
                   alternativa=ALTERNATIVA, alfa=ALFA, parametros=None):
    """Simula um cenário e um efeito; devolve ``{"t": taxa, "wilcoxon": taxa}``."""
    i_cenario = list(CENARIOS).index(cenario)
    i_efeito = list(EFEITOS).index(efeito) if efeito in EFEITOS else int(round(efeito * 1e6))
    rng = np.random.default_rng([semente, i_cenario, i_efeito])
    antes, depois = gerar_diferencas(cenario, efeito, repeticoes, rng, parametros)
    return taxas_de_rejeicao(antes, depois, alternativa, alfa)


def simular(cenarios=None, efeitos=EFEITOS, repeticoes=REPETICOES, semente=SEMENTE,
            alternativa=ALTERNATIVA, alfa=ALFA, parametros=None):
    """Roda a simulação e devolve o DataFrame longo descrito no módulo."""
    linhas = []
    for cenario in (cenarios if cenarios is not None else CENARIOS):
        n = CENARIOS[cenario]["n"]
        for efeito in efeitos:
            taxas = simular_celula(
                cenario, efeito, repeticoes, semente, alternativa, alfa, parametros
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
