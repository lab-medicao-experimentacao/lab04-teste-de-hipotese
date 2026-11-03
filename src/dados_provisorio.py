"""Gerador PROVISÓRIO de pares simulados (tempo de build antes/depois do cache).

Este módulo é temporário: será substituído por ``src/dados.py`` (Pessoa 2),
com parâmetros calibrados a partir da amostra real. A interface é a mesma
combinada pelo grupo, ``gerar_pares(n, efeito, rng, **params)``, para que a
troca seja apenas mudar o import. Os valores padrão abaixo são ilustrativos,
não vêm de dados reais.
"""

import numpy as np


def gerar_pares(n, efeito, rng, mediana=120.0, sigma=0.3, ruido=5.0):
    """Gera ``n`` pares ``(antes, depois)`` de tempos de build, em segundos.

    Modelo (efeito multiplicativo conhecido):
        antes ~ lognormal com mediana ``mediana`` (s) e desvio-padrão do log
            ``sigma`` (distribuição assimétrica à direita, como tempos reais);
        depois = antes * (1 - efeito) + eps, com eps ~ Normal(0, ``ruido``) (s).

    ``efeito`` é a redução proporcional do tempo (0,10 = 10% mais rápido),
    com 0 <= efeito < 1. Com ``efeito=0``, ``d = depois - antes = eps`` é
    simétrica em torno de zero, com média e mediana 0: H₀ é verdadeira tanto
    para o t pareado (média de d) quanto para o Wilcoxon (simetria de d em
    torno de 0). Usa apenas o gerador ``rng`` recebido
    (``np.random.default_rng``).
    """
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError(f"`n` deve ser um inteiro positivo (recebido {n!r}).")
    if not 0 <= efeito < 1:
        raise ValueError(f"`efeito` deve estar em [0, 1) (recebido {efeito}).")
    if not mediana > 0:
        raise ValueError(f"`mediana` deve ser positiva (recebido {mediana}).")
    if not sigma >= 0:
        raise ValueError(f"`sigma` não pode ser negativo (recebido {sigma}).")
    if not ruido > 0:
        raise ValueError(f"`ruido` deve ser positivo (recebido {ruido}).")
    if not isinstance(rng, np.random.Generator):
        raise ValueError("`rng` deve ser um np.random.Generator (np.random.default_rng).")

    antes = rng.lognormal(mean=np.log(mediana), sigma=sigma, size=n)
    depois = antes * (1 - efeito) + rng.normal(0.0, ruido, size=n)
    return antes, depois
