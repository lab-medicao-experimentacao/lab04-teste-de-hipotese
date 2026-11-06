"""Leitura da amostra real pareada (``data/amostra.csv``).

Cada linha é um par: o mesmo build do fzf medido sem cache (antes) e com o
cache do Go aquecido (depois). A documentação da coleta está em
``data/README.md``.
"""

from pathlib import Path

import pandas as pd


ARQUIVO = Path(__file__).resolve().parents[1] / "data" / "amostra.csv"
COLUNAS = ("par", "ordem", "sem_cache_s", "com_cache_s")

FONTE = (
    "tempo de `go build` do [fzf](https://github.com/junegunn/fzf) v0.67.0, "
    "medido em um MacBook Apple M1 com o cache de compilação do Go vazio "
    "(antes) e aquecido (depois), em ordem sorteada a cada rodada"
)


def carregar(arquivo=ARQUIVO):
    """Lê a amostra e valida colunas, tipos e valores (tempos positivos)."""
    df = pd.read_csv(arquivo)
    faltando = [c for c in COLUNAS if c not in df.columns]
    if faltando:
        raise ValueError(f"Colunas ausentes em {arquivo}: {faltando}.")
    tempos = df[["sem_cache_s", "com_cache_s"]]
    if tempos.isna().any().any() or not (tempos > 0).all().all():
        raise ValueError(f"Os tempos em {arquivo} devem ser positivos e sem ausentes.")
    return df


def pares(arquivo=ARQUIVO):
    """Devolve ``(antes, depois)`` em segundos: sem cache e com cache."""
    df = carregar(arquivo)
    return (df["sem_cache_s"].to_numpy(dtype=float),
            df["com_cache_s"].to_numpy(dtype=float))


def n_pares(arquivo=ARQUIVO):
    """Quantidade de pares da amostra."""
    return len(carregar(arquivo))
