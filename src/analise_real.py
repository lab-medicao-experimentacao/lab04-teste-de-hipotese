"""Resultados dos testes e magnitude observada nos tempos de build reais."""

import amostra
import aplicacao


def analisar():
    sem_cache, com_cache = amostra.pares()
    resultados = aplicacao.aplicar_testes(sem_cache, com_cache)
    media_sem = float(sem_cache.mean())
    media_com = float(com_cache.mean())
    diferenca = float((com_cache - sem_cache).mean())

    rejeitam = resultados.loc[resultados["Decisão"] == "rejeita H₀", "Teste"]
    if len(rejeitam) == len(resultados):
        evidencia = "Os dois testes indicam diferença no tempo de build."
    elif rejeitam.empty:
        evidencia = "Os dois testes ficaram sem evidência suficiente de diferença."
    else:
        evidencia = f"Apenas o {rejeitam.iloc[0]} indicou diferença no tempo de build."

    tempo_sem = f"{media_sem:.2f}".replace(".", ",")
    tempo_com = f"{media_com:.2f}".replace(".", ",")
    diferenca_s = f"{diferenca:+.2f}".replace(".", ",")
    resumo = (
        f"{evidencia} Nos {len(sem_cache)} pares, o tempo médio passou de "
        f"{tempo_sem} s sem cache para {tempo_com} s com cache "
        f"(diferença média com − sem cache de {diferenca_s} s)."
    )
    return resultados, resumo
