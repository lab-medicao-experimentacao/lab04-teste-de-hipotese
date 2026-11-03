# Lab04 — Testes de hipótese

Laboratório de Medição e Experimentação de Software para comparar testes de hipótese por meio de dados reais, simulação e visualização.

- [Repositório](https://github.com/lab-medicao-experimentacao/lab04-teste-de-hipotese)
- [Kanban do grupo](https://github.com/orgs/lab-medicao-experimentacao/projects/4/views/2)
- [Enunciado completo](doc/enunciado.md)
- Dashboard: ainda não implementado ou publicado.

## Decisões do grupo

- **Par P2:** teste t pareado × Wilcoxon pareado.
- **Tecnologias:** Python, Streamlit e Plotly.
- **Cenário, pergunta, hipóteses e fonte dos dados reais:** a definir pelo grupo.

Os dados deverão preservar a correspondência entre as duas medições de cada par. Antes de simular, o grupo deverá registrar a expectativa sobre qual teste terá melhor desempenho e sua justificativa.

## Organização

```text
.
├── README.md
├── .gitignore
├── doc/
│   └── enunciado.md       # Requisitos originais do laboratório
├── data/
│   └── README.md          # Orientações para os dados reais
└── src/
    └── .gitkeep           # Reserva a pasta para o código Python
```

- `doc/`: enunciado e documentação de apoio. A entrega final será o dashboard, conforme o enunciado.
- `data/`: amostra real em CSV e documentação de sua origem e coleta.
- `src/`: código de geração dos dados simulados, aplicação dos testes e construção dos gráficos G1 e G2. Os arquivos serão acrescentados nas respectivas tarefas.

A estrutura base do dashboard definirá os pontos de integração para que cada responsável inclua seu gráfico e o texto explicativo de 2 a 4 frases.

## Ambiente

É necessário ter Python 3 com suporte a ambientes virtuais. Na raiz do repositório, prepare o ambiente:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

No Windows (PowerShell), a ativação é feita com `.venv\Scripts\Activate.ps1`.

As dependências e o comando único para abrir o dashboard serão adicionados junto da implementação da sua base, na Issue #4. Por enquanto, não há aplicação executável nesta estrutura.

As simulações deverão usar semente fixa, por exemplo `numpy.random.default_rng(42)`, para permitir a reprodução dos resultados.


