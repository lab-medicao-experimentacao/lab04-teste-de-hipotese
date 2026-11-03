"""Testes pareados usados no laboratório: t pareado e Wilcoxon pareado.

Os dois testes analisam as diferenças ``d = depois - antes`` de cada par e
recebem o mesmo parâmetro ``alternativa``, com o significado do SciPy aplicado
a ``d``:

- ``"two-sided"``: ``d`` não está centrada em zero (há diferença);
- ``"less"``: ``d`` tende a ser negativa (``depois`` tende a ser menor que
  ``antes``, ex.: o cache reduziu o tempo de build);
- ``"greater"``: ``d`` tende a ser positiva (``depois`` tende a ser maior).

O t pareado compara a média das diferenças com zero; o Wilcoxon pareado usa os
postos de ``|d|`` e testa se as diferenças são simétricas em torno de zero.

Escolhas do Wilcoxon (as mesmas devem ser usadas no G2 e nas simulações):

- ``zero_method="wilcox"``: diferenças iguais a zero são descartadas antes de
  atribuir os postos; ``n`` passa a ser o número de diferenças não nulas.
- Empates em ``|d|`` recebem o posto médio.
- ``method="auto"`` (SciPy 1.18): com até 50 diferenças (contando os zeros) e
  sem zeros nem empates, o p-valor é exato; com zeros ou empates e até 13
  diferenças, é exato por permutação (todas as 2ⁿ trocas de sinal); nos demais
  casos, usa a aproximação normal com correção de continuidade.
- A estatística devolvida é sempre W+ (soma dos postos das diferenças
  positivas), qualquer que seja a alternativa.
"""

import numpy as np
from scipy import stats


ALTERNATIVAS = ("two-sided", "less", "greater")


def _validar(antes, depois, alternativa, alfa):
    """Valida as entradas e devolve as diferenças ``depois - antes``."""
    antes = np.asarray(antes, dtype=float)
    depois = np.asarray(depois, dtype=float)
    if antes.ndim != 1 or depois.ndim != 1:
        raise ValueError("`antes` e `depois` devem ser sequências unidimensionais.")
    if antes.shape != depois.shape:
        raise ValueError(
            f"`antes` e `depois` devem ter o mesmo tamanho "
            f"(recebidos {antes.size} e {depois.size})."
        )
    if np.isnan(antes).any() or np.isnan(depois).any():
        raise ValueError("`antes` e `depois` não podem conter valores NaN.")
    if alternativa not in ALTERNATIVAS:
        raise ValueError(
            f"`alternativa` deve ser uma de {ALTERNATIVAS} (recebido {alternativa!r})."
        )
    if not 0 < alfa < 1:
        raise ValueError(f"`alfa` deve estar entre 0 e 1 (recebido {alfa}).")
    return antes, depois, depois - antes


def t_pareado(antes, depois, alternativa="two-sided", alfa=0.05):
    """Aplica o teste t pareado às diferenças ``d = depois - antes``.

    ``alternativa`` segue o SciPy aplicado a ``d`` ("less": ``depois`` tende a
    ser menor que ``antes``). Aceita listas ou arrays NumPy do mesmo tamanho.

    Retorna um dict com:
        estatistica: t de ``scipy.stats.ttest_rel(depois, antes)``;
        p_valor: p-valor do teste;
        efeito: d de Cohen para diferenças, d_z = média(d) / dp(d, ddof=1);
        rejeita: ``p_valor < alfa``;
        n: número de pares;
        gl: graus de liberdade (n - 1).
    """
    antes, depois, d = _validar(antes, depois, alternativa, alfa)
    n = d.size
    if n < 2:
        raise ValueError("O t pareado precisa de pelo menos 2 pares.")

    res = stats.ttest_rel(depois, antes, alternative=alternativa)
    # Diferenças constantes têm desvio zero: d_z fica infinito ou indefinido.
    with np.errstate(divide="ignore", invalid="ignore"):
        efeito = float(np.mean(d) / np.std(d, ddof=1))
    p_valor = float(res.pvalue)
    return {
        "estatistica": float(res.statistic),
        "p_valor": p_valor,
        "efeito": efeito,
        "rejeita": bool(p_valor < alfa),
        "n": int(n),
        "gl": int(n - 1),
    }


def _metodo_wilcoxon(d):
    """Reproduz a escolha de ``method="auto"`` do SciPy 1.18 para estes dados."""
    tamanho = d.size  # o SciPy decide antes de descartar os zeros
    abs_nao_nulos = np.abs(d[d != 0])
    tem_zeros = abs_nao_nulos.size < tamanho
    tem_empates = np.unique(abs_nao_nulos).size < abs_nao_nulos.size
    if tamanho > 50:
        return "aproximação normal"
    if not (tem_zeros or tem_empates):
        return "exato"
    if tamanho <= 13:
        return "exato (permutação)"
    return "aproximação normal"


def wilcoxon_pareado(antes, depois, alternativa="two-sided", alfa=0.05):
    """Aplica o teste de Wilcoxon pareado (signed-rank) a ``d = depois - antes``.

    ``alternativa`` segue o SciPy aplicado a ``d`` ("less": ``depois`` tende a
    ser menor que ``antes``). Zeros são descartados (``zero_method="wilcox"``),
    empates recebem posto médio e o p-valor vem de
    ``scipy.stats.wilcoxon(d, zero_method="wilcox", method="auto")``.

    Retorna um dict com:
        estatistica: W+ (soma dos postos das diferenças positivas), sempre,
            inclusive no bicaudal (o SciPy devolve min(W+, W-) nesse caso);
        p_valor: p-valor do teste;
        efeito: correlação rank-bisserial pareada r = (W+ - W-) / (W+ + W-);
        rejeita: ``p_valor < alfa``;
        n: número de diferenças não nulas;
        metodo: "exato", "exato (permutação)" ou "aproximação normal",
            conforme a escolha do SciPy (ver docstring do módulo).
    """
    antes, depois, d = _validar(antes, depois, alternativa, alfa)
    nao_nulos = d[d != 0]
    n = nao_nulos.size
    if n == 0:
        raise ValueError(
            "O Wilcoxon pareado precisa de pelo menos uma diferença não nula."
        )

    postos = stats.rankdata(np.abs(nao_nulos))  # empates: posto médio
    w_mais = float(postos[nao_nulos > 0].sum())
    w_menos = float(postos[nao_nulos < 0].sum())

    res = stats.wilcoxon(
        d, alternative=alternativa, zero_method="wilcox", method="auto"
    )
    p_valor = float(res.pvalue)
    return {
        "estatistica": w_mais,
        "p_valor": p_valor,
        "efeito": (w_mais - w_menos) / (w_mais + w_menos),
        "rejeita": bool(p_valor < alfa),
        "n": int(n),
        "metodo": _metodo_wilcoxon(d),
    }
