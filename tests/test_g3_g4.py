"""Testes dos gráficos das simulações Q1 a Q3."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from graficos import g3, g4  # noqa: E402
import simulacao  # noqa: E402
from estilo import CORES  # noqa: E402


class TestG3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resultados = simulacao.simular_tudo(repeticoes=300)

    def test_mostra_um_barra_por_teste_e_cenario(self):
        figura = g3.figura(self.resultados)
        self.assertEqual(len(figura.data), 2)
        self.assertEqual([trace.marker.color for trace in figura.data], [
            CORES["t"], CORES["wilcoxon"],
        ])
        self.assertIn("erro tipo i", figura.layout.title.text.lower())
        self.assertIn("rejeição", figura.layout.yaxis.title.text)

    def test_explicacao_cobre_as_violacoes(self):
        texto = g3.explicacao(self.resultados)
        self.assertIn("outliers", texto)
        self.assertIn("assimétrico", texto)
        self.assertIn("5%", texto)


class TestG4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resultados = simulacao.simular_tudo(repeticoes=300)

    def test_mostra_duas_curvas_por_cenario(self):
        figura = g4.figura(self.resultados)
        self.assertEqual(len(figura.data), 8)
        self.assertEqual(figura.data[0].line.color, CORES["t"])
        self.assertEqual(figura.data[1].line.color, CORES["wilcoxon"])
        self.assertIn("Poder", figura.layout.title.text)

    def test_explicacao_indica_mudanca_de_vantagem(self):
        texto = g4.explicacao(self.resultados)
        self.assertIn("outliers", texto)
        self.assertIn("Wilcoxon", texto)
        self.assertIn("assimétrico", texto)


if __name__ == "__main__":
    unittest.main()
