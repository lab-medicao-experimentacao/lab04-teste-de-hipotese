# Lab04 — Testes de hipótese

Laboratório de Medição e Experimentação de Software para comparar testes de hipótese por meio de dados reais, simulação e visualização.

- [Repositório](https://github.com/lab-medicao-experimentacao/lab04-teste-de-hipotese)
- [Kanban do grupo](https://github.com/orgs/lab-medicao-experimentacao/projects/4/views/2)
- [Enunciado completo](doc/enunciado.md)
- [Dashboard local](http://localhost:8501) (após iniciar o ambiente).

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
├── .dockerignore
├── Dockerfile
├── compose.yaml           # Ambiente do dashboard
├── requirements.txt       # Dependências Python
├── doc/
│   └── enunciado.md       # Requisitos originais do laboratório
├── data/
│   └── README.md          # Orientações para os dados reais
└── src/
    └── app.py             # Página inicial do dashboard
```

- `doc/`: enunciado e documentação de apoio. A entrega final será o dashboard, conforme o enunciado.
- `data/`: amostra real em CSV e documentação de sua origem e coleta.
- `src/`: código de geração dos dados simulados, aplicação dos testes e construção dos gráficos G1 e G2. Os arquivos serão acrescentados nas respectivas tarefas.

A página `src/app.py` contém as seções do dashboard e os pontos de integração de G1 e G2. Cada responsável deve incluir seu gráfico com `st.plotly_chart(fig)` e o texto explicativo de 2 a 4 frases na seção correspondente. Cenário e resultados pendentes estão identificados na página.

## Ambiente

Instale e inicie o Docker com Docker Compose disponível. Não é necessário instalar Python na máquina: o container utiliza Python 3.12 e as versões de Streamlit e Plotly declaradas em `requirements.txt`.

Na raiz do repositório, execute:

```bash
docker compose up --build
```

Abra [http://localhost:8501](http://localhost:8501). A primeira execução baixa a imagem e instala as dependências, exigindo acesso à internet. Para encerrar, pressione `Ctrl+C`; para remover os containers do projeto, execute `docker compose down`.

As pastas `src/` e `data/` são montadas no container para leitura. Alterações no código são refletidas no dashboard sem reconstruir a imagem. Ao mudar as dependências, execute novamente `docker compose up --build`.

### Execução sem Docker

Como alternativa, use Python 3.12 com um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run src/app.py
```

No Windows (PowerShell), a ativação é feita com `.venv\Scripts\Activate.ps1`.

As simulações deverão usar semente fixa, por exemplo `numpy.random.default_rng(42)`, para permitir a reprodução dos resultados.


