"""Teste de fumaça do dashboard (rodar da raiz: python -m unittest discover -s tests)."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "src" / "app.py"


class TestApp(unittest.TestCase):
    def test_carrega_sem_excecao(self):
        at = AppTest.from_file(str(APP)).run(timeout=30)
        self.assertEqual(len(at.exception), 0, at.exception)
        subtitulos = [s.value for s in at.subheader]
        self.assertIn("Aplicação a um conjunto simulado", subtitulos)
        self.assertEqual(len(at.dataframe), 1)
        self.assertIn("simulados", " ".join(c.value for c in at.caption))
        self.assertIn("calibrado pela amostra real", " ".join(c.value for c in at.caption))

    def test_g2_presente(self):
        at = AppTest.from_file(str(APP)).run(timeout=30)
        self.assertEqual(len(at.exception), 0, at.exception)
        self.assertEqual(len(at.get("plotly_chart")), 2)  # G1 e G2
        explicacao = " ".join(m.value for m in at.markdown)
        self.assertIn("Explicação dos testes", explicacao)
        self.assertIn("W⁺ = 50", explicacao)

    def test_g1_presente(self):
        at = AppTest.from_file(str(APP)).run(timeout=30)
        self.assertEqual(len(at.exception), 0, at.exception)
        explicacao = " ".join(m.value for m in at.markdown)
        self.assertIn("Explicação dos dados", explicacao)
        self.assertIn("lognormal", explicacao)
        self.assertNotIn("a preencher", explicacao)
        self.assertIn("semente 42", " ".join(c.value for c in at.caption))


if __name__ == "__main__":
    unittest.main()
