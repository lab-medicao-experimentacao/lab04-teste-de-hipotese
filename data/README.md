# Dados reais

Amostra pareada usada pelo grupo no par P2 (t pareado × Wilcoxon pareado): tempo de build de um projeto open-source em Go, **sem cache** e **com cache** de compilação, medido na mesma máquina.

## Arquivo `amostra.csv`

30 pares, um por linha. Cada linha é uma rodada: o mesmo build foi medido nas duas condições, uma logo após a outra.

| Coluna | Significado | Unidade |
|---|---|---|
| `par` | Número da rodada (1 a 30) | — |
| `ordem` | Ordem em que as duas condições foram medidas na rodada (`sem_cache-com_cache` ou `com_cache-sem_cache`) | — |
| `sem_cache_s` | Tempo de `go build` com `GOCACHE` apontando para um diretório novo e vazio: o Go recompila a biblioteca padrão, as dependências e o fzf | segundos (tempo de parede) |
| `com_cache_s` | Tempo de `go build` com `GOCACHE` apontando para um cache persistente já aquecido | segundos (tempo de parede) |

A diferença analisada pelos testes é `com_cache_s − sem_cache_s` (depois − antes).

## Fonte

- Projeto: [junegunn/fzf](https://github.com/junegunn/fzf), tag `v0.67.0`, commit `2ab923f3ae04d5e915e5ff4a9cd3bd515bfd1ea5`.
- Comando medido: `go build -o <binário> .` na raiz do projeto.

## Procedimento de coleta

Coleta feita em 5 de novembro de 2026 com `scripts/coletar_builds.py`:

```bash
python scripts/coletar_builds.py --pares 30 --saida data/amostra.csv
```

1. O script clona o fzf na tag acima em um diretório temporário e baixa os módulos (`go mod download`) antes das medições. Durante os builds, `GOPROXY=off` garante que a rede não entra no tempo.
2. Uma rodada de aquecimento nas duas condições é descartada. Ela enche o cache persistente e o cache de disco do sistema.
3. Em cada uma das 30 rodadas, a ordem das duas condições é sorteada com semente fixa (`random.Random(42)`), para que variações da máquina ao longo do tempo não favoreçam uma condição. Resultado: 13 rodadas começaram sem cache e 17 com cache.
4. O tempo é o tempo de parede (`time.perf_counter`) do processo `go build`. O binário anterior é apagado antes de cada build.

Ambiente: MacBook com Apple M1 (8 núcleos, 16 GB de RAM), macOS 26.6.2, Go 1.26.3 (`darwin/arm64`). A máquina estava em uso normal, com outros aplicativos abertos, sem isolamento de carga.

## Tratamento dos dados

Nenhum build falhou e nenhuma observação foi excluída. Não há valores ausentes. O script interrompe a coleta se algum build falhar.

## Resumo da amostra

| Condição | Média (s) | Mediana (s) | Desvio-padrão (s) | Mín.–máx. (s) | Assimetria |
|---|---|---|---|---|---|
| Sem cache | 5,895 | 5,805 | 0,607 | 4,940–7,934 | 1,34 |
| Com cache | 0,528 | 0,513 | 0,080 | 0,441–0,860 | 2,60 |
| Diferença (com − sem) | −5,368 | −5,314 | 0,593 | — | −1,21 |

Os dois tempos são assimétricos à direita, com alguns builds bem mais lentos que os demais. Com cache, o build levou em média 9% do tempo sem cache.
