"""Parâmetros da simulação estimados a partir da amostra real.

Modelo escolhido (usado por ``src/dados.py``), com tempos em segundos:

    nível da rodada:  L ~ Normal(log(mediana), sigma_rodada)
    antes  = exp(L + e1)
    depois = exp(L + log(1 - efeito) + e2),   e1, e2 ~ Normal(0, sigma_ruido)

Justificativa, a partir de ``data/amostra.csv``:

- os tempos são positivos e assimétricos à direita, então o modelo é
  lognormal: trabalha-se no log do tempo;
- as duas medições de uma rodada compartilham o estado da máquina naquele
  momento (``L``); a correlação entre os logs das duas condições mede quanto
  da variância vem desse componente compartilhado, e o resto é ruído de cada
  build (``e1``, ``e2``);
- ``mediana`` e a variância total vêm do log da condição sem cache (antes),
  que é o build de referência;
- ``efeito`` é a redução proporcional da mediana (0,05 = 5% mais rápido).
  Com ``efeito = 0``, antes e depois são intercambiáveis, logo
  ``d = depois − antes`` é simétrica em torno de zero e tem média zero: H₀ é
  verdadeira para o t pareado e para o Wilcoxon.

A amostra tem mais builds lentos (outliers) do que uma lognormal com esse
desvio produz; o modelo base não os reproduz, e a proporção observada fica
registrada para o cenário de violação de pressupostos (Q3, Sprint 2).
"""

from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import stats

import amostra


# Faixa de efeitos para as curvas de poder (Q2, Sprint 2): de 0 (H₀
# verdadeira) até 10% de redução. Com n = 30 e os parâmetros da amostra, o
# poder dos dois testes sai de ~5% e passa de 95% dentro dessa faixa.
EFEITOS = (0.0, 0.02, 0.04, 0.06, 0.08, 0.10)


def _outliers(x):
    """Quantidade de valores fora de [Q1 − 1,5·IQR, Q3 + 1,5·IQR]."""
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    return int(np.sum((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)))


def descritivas(antes, depois):
    """Estatísticas descritivas de antes, depois e ``d = depois − antes`` (s)."""
    antes = np.asarray(antes, dtype=float)
    depois = np.asarray(depois, dtype=float)
    linhas = []
    for nome, x in [("Sem cache (antes)", antes), ("Com cache (depois)", depois),
                    ("Diferença (depois − antes)", depois - antes)]:
        linhas.append({
            "Série": nome,
            "n": x.size,
            "Média (s)": float(np.mean(x)),
            "Mediana (s)": float(np.median(x)),
            "Desvio-padrão (s)": float(np.std(x, ddof=1)),
            "Mínimo (s)": float(np.min(x)),
            "Máximo (s)": float(np.max(x)),
            "Assimetria": float(stats.skew(x)),
            "Outliers (1,5·IQR)": _outliers(x),
        })
    return pd.DataFrame(linhas)


def estimar(antes, depois):
    """Estima os parâmetros do modelo a partir de pares reais (s).

    Retorna um dict com:
        mediana: mediana do tempo antes, ``exp(média de log(antes))`` (s);
        sigma_rodada: desvio-padrão do log compartilhado pelo par;
        sigma_ruido: desvio-padrão do log próprio de cada build;
        correlacao: correlação entre ``log(antes)`` e ``log(depois)``, limitada a [0, 1];
        efeito_real: redução proporcional observada, ``1 − exp(média de log(depois/antes))``;
        prop_outliers: proporção de outliers em antes (para a Q3).
    """
    antes = np.asarray(antes, dtype=float)
    depois = np.asarray(depois, dtype=float)
    if antes.shape != depois.shape or antes.ndim != 1 or antes.size < 3:
        raise ValueError("`antes` e `depois` devem ser vetores com o mesmo tamanho (≥ 3).")
    if not (np.all(antes > 0) and np.all(depois > 0)):
        raise ValueError("Os tempos devem ser positivos.")
    log_a, log_d = np.log(antes), np.log(depois)
    sigma_total = float(np.std(log_a, ddof=1))
    correlacao = float(np.clip(np.corrcoef(log_a, log_d)[0, 1], 0.0, 1.0))
    return {
        "mediana": float(np.exp(np.mean(log_a))),
        "sigma_rodada": float(np.sqrt(correlacao) * sigma_total),
        "sigma_ruido": float(np.sqrt(1 - correlacao) * sigma_total),
        "correlacao": correlacao,
        "efeito_real": float(1 - np.exp(np.mean(log_d - log_a))),
        "prop_outliers": _outliers(antes) / antes.size,
    }


@lru_cache(maxsize=1)
def _da_amostra():
    return estimar(*amostra.pares())


def da_amostra():
    """Parâmetros estimados de ``data/amostra.csv`` (cópia, para não alterar o cache)."""
    return dict(_da_amostra())


def parametros_gerador(parametros=None):
    """Somente os parâmetros aceitos por ``dados.gerar_pares``."""
    p = da_amostra() if parametros is None else parametros
    return {chave: p[chave] for chave in ("mediana", "sigma_rodada", "sigma_ruido")}


def _num(x, casas=2):
    return f"{x:.{casas}f}".replace(".", ",")


def justificativa(parametros=None):
    """Texto (2 a 4 frases) sobre a escolha dos parâmetros, para a seção 2."""
    p = da_amostra() if parametros is None else parametros
    return " ".join([
        f"Os tempos de build reais são positivos e assimétricos à direita, por "
        f"isso a simulação usa uma lognormal com a mediana da amostra sem cache "
        f"({_num(p['mediana'])} s).",
        f"O desvio do log ({_num(p['sigma_rodada'] ** 2 + p['sigma_ruido'] ** 2, 4)} "
        f"de variância) foi dividido pela correlação entre as duas medições de "
        f"cada rodada ({_num(p['correlacao'])}): uma parte é do estado da "
        f"máquina, comum ao par (σ = {_num(p['sigma_rodada'], 3)}), e o resto é "
        f"ruído de cada build (σ = {_num(p['sigma_ruido'], 3)}).",
        f"O efeito simulado é uma redução proporcional da mediana, de 0 a "
        f"{EFEITOS[-1]:.0%}; o cache real reduziu o tempo em "
        f"{p['efeito_real']:.0%}, efeito grande demais para diferenciar os testes.",
        f"A amostra tem {p['prop_outliers']:.0%} de builds lentos (outliers), "
        f"que o modelo base não reproduz e que serão usados no cenário de "
        f"violação de pressupostos.",
    ])
