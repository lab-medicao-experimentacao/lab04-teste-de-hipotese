"""Testes dos gráficos opcionais de exploração dos dados reais."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from graficos import exploracao  # noqa: E402


class TestExploracao(unittest.TestCase):
    def setUp(self):
        self.antes = np.array([5.0, 6.0, 7.0])
        self.depois = np.array([0.5, 0.6, 0.7])

    def test_pares_tem_linhas_e_pontos_das_duas_condicoes(self):
        figura = exploracao.pares(self.antes, self.depois)
        self.assertEqual(len(figura.data), 5)
        self.assertEqual(figura.data[-2].name, "Sem cache")
        self.assertEqual(figura.data[-1].name, "Com cache")
        self.assertIn("Tempo de build", figura.layout.yaxis.title.text)

    def test_diferencas_tem_histograma_e_referencia_zero(self):
        figura = exploracao.diferencas(self.antes, self.depois)
        self.assertEqual(len(figura.data), 1)
        self.assertEqual(figura.data[0].type, "histogram")
        self.assertEqual(figura.layout.shapes[0].x0, 0)

    def test_rejeita_vetores_incompativeis(self):
        with self.assertRaises(ValueError):
            exploracao.pares([1, 2], [1])


if __name__ == "__main__":
    unittest.main()
