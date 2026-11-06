"""Coleta os dados reais pareados: tempo de build do fzf sem e com cache do Go.

Cada rodada (par) mede o mesmo build duas vezes, na mesma máquina e em
sequência:

- ``sem_cache_s``: ``GOCACHE`` aponta para um diretório novo e vazio, então o
  Go recompila tudo (biblioteca padrão, dependências e o próprio fzf);
- ``com_cache_s``: ``GOCACHE`` aponta para um cache persistente já aquecido.

A ordem das duas medições em cada rodada é sorteada com semente fixa, para
que variações da máquina ao longo do tempo não favoreçam uma condição. Uma
rodada de aquecimento inicial é descartada. Os módulos já ficam baixados em
``GOMODCACHE`` antes das medições, para que a rede não entre no tempo.

Uso (da raiz do repositório; exige git e Go instalados):

    python scripts/coletar_builds.py --pares 30 --saida data/amostra.csv
"""

import argparse
import csv
import os
import platform
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


REPOSITORIO = "https://github.com/junegunn/fzf.git"
VERSAO = "v0.67.0"
SEMENTE = 42


def executar(comando, **kwargs):
    """Executa ``comando`` e interrompe a coleta se ele falhar."""
    subprocess.run(comando, check=True, **kwargs)


def build(projeto, gocache, gomodcache, binario):
    """Tempo de parede (s) de ``go build`` do projeto com o ``GOCACHE`` dado."""
    binario.unlink(missing_ok=True)
    ambiente = {**os.environ, "GOCACHE": str(gocache), "GOMODCACHE": str(gomodcache),
                "GOPROXY": "off"}
    inicio = time.perf_counter()
    executar(["go", "build", "-o", str(binario), "."], cwd=projeto, env=ambiente,
             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return time.perf_counter() - inicio


def medir(projeto, cache, gomodcache, binario, condicao):
    """Mede uma condição; sem cache usa um ``GOCACHE`` vazio, apagado em seguida."""
    if condicao == "com_cache":
        return build(projeto, cache, gomodcache, binario)
    vazio = Path(tempfile.mkdtemp(prefix="gocache-vazio-"))
    try:
        return build(projeto, vazio, gomodcache, binario)
    finally:
        shutil.rmtree(vazio, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pares", type=int, default=30)
    parser.add_argument("--saida", type=Path, default=Path("data/amostra.csv"))
    args = parser.parse_args()
    if args.pares < 1:
        parser.error("--pares deve ser positivo")

    rng = random.Random(SEMENTE)
    with tempfile.TemporaryDirectory(prefix="lab04-coleta-") as tmp:
        tmp = Path(tmp)
        projeto, cache, gomodcache = tmp / "fzf", tmp / "gocache", tmp / "gomod"
        binario = tmp / "fzf-bin"
        executar(["git", "clone", "--quiet", "--depth", "1", "--branch", VERSAO,
                  REPOSITORIO, str(projeto)], stderr=subprocess.DEVNULL)
        executar(["go", "mod", "download"], cwd=projeto,
                 env={**os.environ, "GOMODCACHE": str(gomodcache)})
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=projeto, check=True,
                                capture_output=True, text=True).stdout.strip()
        versao_go = subprocess.run(["go", "version"], check=True, capture_output=True,
                                   text=True).stdout.strip()

        # Aquecimento (descartado): enche o cache persistente e o cache de disco.
        for condicao in ("sem_cache", "com_cache"):
            medir(projeto, cache, gomodcache, binario, condicao)

        linhas = []
        for par in range(1, args.pares + 1):
            ordem = rng.sample(["sem_cache", "com_cache"], 2)
            tempos = {c: medir(projeto, cache, gomodcache, binario, c) for c in ordem}
            linhas.append({"par": par, "ordem": "-".join(ordem),
                           "sem_cache_s": f"{tempos['sem_cache']:.3f}",
                           "com_cache_s": f"{tempos['com_cache']:.3f}"})
            print(f"par {par:2d}: sem cache {tempos['sem_cache']:6.3f} s | "
                  f"com cache {tempos['com_cache']:6.3f} s", flush=True)

        args.saida.parent.mkdir(parents=True, exist_ok=True)
        with args.saida.open("w", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
            escritor.writeheader()
            escritor.writerows(linhas)

        # O Go grava os módulos baixados como somente leitura; sem isto o
        # diretório temporário não pode ser apagado.
        executar(["go", "clean", "-modcache"], env={**os.environ, "GOMODCACHE": str(gomodcache)})

    print(f"\n{len(linhas)} pares salvos em {args.saida}", file=sys.stderr)
    print(f"Projeto: {REPOSITORIO} {VERSAO} ({commit})", file=sys.stderr)
    print(f"{versao_go}; {platform.platform()}; {platform.machine()}; "
          f"{os.cpu_count()} CPUs", file=sys.stderr)


if __name__ == "__main__":
    main()
