"""Geração dos pares simulados (tempo de build sem e com cache), calibrada pela amostra real.

Modelo (ver ``parametros.py``), com tempos em segundos:

    L ~ Normal(log(mediana), sigma_rodada)            nível comum ao par
    antes  = exp(L + e1)
    depois = exp(L + log(1 - efeito) + e2)            e1, e2 ~ Normal(0, sigma_ruido)

Sem parâmetros explícitos, usa os estimados de ``data/amostra.csv``. Toda a
aleatoriedade vem do ``np.random.Generator`` recebido; quem chama cria o
gerador com semente fixa, por exemplo ``np.random.default_rng(42)``.
"""

import numpy as np

import parametros


def gerar_pares(n, efeito, rng, mediana=None, sigma_rodada=None, sigma_ruido=None):
    """Gera ``n`` pares ``(antes, depois)`` de tempos de build, em segundos.

    ``efeito`` é a redução proporcional da mediana (0,05 = 5% mais rápido),
    com 0 <= efeito < 1. Com ``efeito=0``, antes e depois são
    intercambiáveis: ``d = depois − antes`` é simétrica em torno de zero, com
    média e mediana 0, então H₀ é verdadeira para o t pareado e para o
    Wilcoxon. Parâmetros omitidos (``None``) vêm da amostra real.
    """
    padrao = parametros.parametros_gerador()
    mediana = padrao["mediana"] if mediana is None else mediana
    sigma_rodada = padrao["sigma_rodada"] if sigma_rodada is None else sigma_rodada
    sigma_ruido = padrao["sigma_ruido"] if sigma_ruido is None else sigma_ruido

    if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError(f"`n` deve ser um inteiro positivo (recebido {n!r}).")
    if not 0 <= efeito < 1:
        raise ValueError(f"`efeito` deve estar em [0, 1) (recebido {efeito}).")
    if not mediana > 0:
        raise ValueError(f"`mediana` deve ser positiva (recebido {mediana}).")
    if not sigma_rodada >= 0:
        raise ValueError(f"`sigma_rodada` não pode ser negativo (recebido {sigma_rodada}).")
    if not sigma_ruido > 0:
        raise ValueError(f"`sigma_ruido` deve ser positivo (recebido {sigma_ruido}).")
    if not isinstance(rng, np.random.Generator):
        raise ValueError("`rng` deve ser um np.random.Generator (np.random.default_rng).")

    nivel = rng.normal(np.log(mediana), sigma_rodada, size=n)
    antes = np.exp(nivel + rng.normal(0.0, sigma_ruido, size=n))
    depois = np.exp(nivel + np.log1p(-efeito) + rng.normal(0.0, sigma_ruido, size=n))
    return antes, depois
