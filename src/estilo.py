"""Cores e rótulos compartilhados por todos os gráficos do dashboard."""

# Paleta Okabe-Ito (segura para daltonismo): azul para o t, vermelhão para o
# Wilcoxon. Use sempre estas constantes, nunca cores soltas nos gráficos.
CORES = {"t": "#0072B2", "wilcoxon": "#D55E00"}

ROTULOS = {"t": "t pareado", "wilcoxon": "Wilcoxon pareado"}

# Origem dos dados no G1 (Okabe-Ito, distintas das cores dos testes): verde
# para os dados reais e roxo-avermelhado para os simulados.
CORES_DADOS = {"real": "#009E73", "simulado": "#CC79A7"}

ROTULOS_DADOS = {"real": "Real", "simulado": "Simulado"}
