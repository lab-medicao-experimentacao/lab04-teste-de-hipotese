"""Aplicação dos dois testes a um conjunto simulado, com interpretação.

O conjunto de exemplo vem do gerador provisório (``dados_provisorio``); quando
``src/dados.py`` (Pessoa 2) existir, basta trocar o import de ``gerar_pares``.
O mesmo conjunto deve ser reutilizado no G2 via ``conjunto_exemplo()``.
"""

import numpy as np
import pandas as pd

import testes
from dados_provisorio import gerar_pares
from estilo import ROTULOS


N_EXEMPLO = 15
EFEITO_EXEMPLO = 0.10  # redução verdadeira de 10% no tempo de build
SEMENTE = 42
ALTERNATIVA = "two-sided"  # provisório até o grupo decidir H₁
ALFA = 0.05

MEDIDAS = {"t": "d_z", "wilcoxon": "r rank-bisserial"}


def conjunto_exemplo():
    """Devolve ``(antes, depois)`` do exemplo, sempre os mesmos (semente fixa)."""
    rng = np.random.default_rng(SEMENTE)
    return gerar_pares(N_EXEMPLO, EFEITO_EXEMPLO, rng)


def aplicar_testes(antes, depois, alternativa=ALTERNATIVA, alfa=ALFA):
    """Aplica o t pareado e o Wilcoxon pareado e devolve uma linha por teste.

    Colunas: Teste, Estatística (t ou W+), p-valor, Tamanho do efeito,
    Medida do efeito (d_z ou r rank-bisserial) e Decisão.
    """
    resultados = {
        "t": testes.t_pareado(antes, depois, alternativa, alfa),
        "wilcoxon": testes.wilcoxon_pareado(antes, depois, alternativa, alfa),
    }
    return pd.DataFrame(
        [
            {
                "Teste": ROTULOS[chave],
                "Estatística": r["estatistica"],
                "p-valor": r["p_valor"],
                "Tamanho do efeito": r["efeito"],
                "Medida do efeito": MEDIDAS[chave],
                "Decisão": "rejeita H₀" if r["rejeita"] else "não rejeita H₀",
            }
            for chave, r in resultados.items()
        ]
    )


def medianas(antes, depois):
    """Medianas de ``antes`` e ``depois`` (s), para a descrição do exemplo."""
    return float(np.median(antes)), float(np.median(depois))


def _num(x, casas=3):
    """Formata um número com vírgula decimal."""
    return f"{x:.{casas}f}".replace(".", ",")


def _p(p_valor):
    """Texto do p-valor: "p = 0,031" ou "p < 0,001"."""
    return "p < 0,001" if p_valor < 0.001 else f"p = {_num(p_valor)}"


def interpretar(resultados, efeito_verdadeiro, alfa=ALFA):
    """Gera de 2 a 4 frases interpretando ``aplicar_testes(...)``.

    ``efeito_verdadeiro`` é o efeito usado na simulação (0 = H₀ verdadeira),
    o que permite dizer se cada decisão foi correta ou um erro tipo I/II.
    """
    linhas = resultados.to_dict("records")
    rejeitam = [linha["Decisão"] == "rejeita H₀" for linha in linhas]
    partes = [
        f"o {linha['Teste']} {linha['Decisão']} ({_p(linha['p-valor'])})"
        for linha in linhas
    ]
    frases = [
        f"Com α = {_num(alfa, 2)}, {partes[0]} e {partes[1]}.",
        "Os dois testes concordam." if rejeitam[0] == rejeitam[1]
        else "Os dois testes discordam.",
    ]

    if efeito_verdadeiro == 0:
        contexto = "não há efeito (H₀ é verdadeira)"
        acerto, erro = "não rejeitar", "erro tipo I"
        errados = [linha["Teste"] for linha, r in zip(linhas, rejeitam) if r]
    else:
        contexto = f"há uma redução real de {efeito_verdadeiro:.0%} no tempo"
        acerto, erro = "rejeitar", "erro tipo II"
        errados = [linha["Teste"] for linha, r in zip(linhas, rejeitam) if not r]
    frases.append(
        f"Como os dados são simulados, o efeito verdadeiro é conhecido: "
        f"{contexto}, então {acerto} H₀ é a decisão correta."
    )
    if len(errados) == 2:
        frases.append(f"Logo, os dois testes cometeram {erro}.")
    elif errados:
        frases.append(f"Logo, o {errados[0]} cometeu {erro}.")
    else:
        frases.append("Logo, os dois testes acertaram neste exemplo.")
    return " ".join(frases)
