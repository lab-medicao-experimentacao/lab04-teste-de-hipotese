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
        self.assertEqual(len(at.dataframe), 2)
        self.assertIn("simulados", " ".join(c.value for c in at.caption))
        self.assertIn("calibrado pela amostra real", " ".join(c.value for c in at.caption))

    def test_g2_presente(self):
        at = AppTest.from_file(str(APP)).run(timeout=30)
        self.assertEqual(len(at.exception), 0, at.exception)
        self.assertEqual(len(at.get("plotly_chart")), 5)  # G1 a G4 e exploração
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

    def test_dados_reais_presentes(self):
        at = AppTest.from_file(str(APP)).run(timeout=30)
        self.assertEqual(len(at.exception), 0, at.exception)
        self.assertIn("6. Dados reais", [h.value for h in at.header])
        tabela = at.dataframe[1].value
        self.assertEqual(tabela["Decisão"].tolist(), ["rejeita H₀", "rejeita H₀"])
        self.assertTrue((tabela["p-valor"] < 0.05).all())
        self.assertTrue((tabela["Tamanho do efeito"] < 0).all())
        explicacao = " ".join(m.value for m in at.markdown)
        self.assertIn("Nos 30 pares", explicacao)
        self.assertIn("-5,37 s", explicacao)


if __name__ == "__main__":
    unittest.main()
