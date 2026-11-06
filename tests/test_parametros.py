"""Testes de unidade de src/parametros.py (rodar da raiz: python -m unittest discover -s tests)."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import amostra  # noqa: E402
import parametros  # noqa: E402


class TestEstimar(unittest.TestCase):
    def test_recupera_parametros_conhecidos(self):
        # Pares gerados pelo próprio modelo, com n grande: a estimação deve
        # recuperar os valores usados na geração.
        rng = np.random.default_rng(42)
        n, mediana, s_rodada, s_ruido, efeito = 200_000, 6.0, 0.05, 0.08, 0.3
        nivel = rng.normal(np.log(mediana), s_rodada, n)
        antes = np.exp(nivel + rng.normal(0, s_ruido, n))
        depois = np.exp(nivel + np.log(1 - efeito) + rng.normal(0, s_ruido, n))
        p = parametros.estimar(antes, depois)
        # O estimador usa a variância de log(antes) = s_rodada² + s_ruido².
        self.assertAlmostEqual(p["mediana"], mediana, delta=0.01)
        self.assertAlmostEqual(p["sigma_rodada"], s_rodada, delta=0.003)
        self.assertAlmostEqual(p["sigma_ruido"], s_ruido, delta=0.003)
        self.assertAlmostEqual(p["efeito_real"], efeito, delta=0.002)

    def test_correlacao_limitada(self):
        # Correlação negativa vira 0: todo o desvio fica no ruído.
        antes = np.array([1.0, 2.0, 3.0, 4.0])
        p = parametros.estimar(antes, antes[::-1].copy())
        self.assertEqual(p["correlacao"], 0.0)
        self.assertEqual(p["sigma_rodada"], 0.0)
        self.assertAlmostEqual(p["sigma_ruido"], np.std(np.log(antes), ddof=1))

    def test_validacao(self):
        for antes, depois in [([1, 2, 3], [1, 2]), ([1, 2], [1, 2]),
                              ([1, 2, -3], [1, 2, 3]), ([1, 2, 3], [0, 2, 3])]:
            with self.subTest(antes=antes, depois=depois), self.assertRaises(ValueError):
                parametros.estimar(antes, depois)


class TestAmostraReal(unittest.TestCase):
    def test_valores_da_amostra(self):
        p = parametros.da_amostra()
        self.assertAlmostEqual(p["mediana"], 5.867, delta=0.001)
        self.assertAlmostEqual(p["correlacao"], 0.255, delta=0.001)
        self.assertAlmostEqual(p["sigma_rodada"], 0.0496, delta=0.0001)
        self.assertAlmostEqual(p["sigma_ruido"], 0.0847, delta=0.0001)
        self.assertAlmostEqual(p["efeito_real"], 0.911, delta=0.001)
        self.assertAlmostEqual(p["prop_lentos"], 0.1)

    def test_copia_nao_altera_cache(self):
        parametros.da_amostra()["mediana"] = -1
        self.assertGreater(parametros.da_amostra()["mediana"], 0)

    def test_parametros_gerador(self):
        self.assertEqual(set(parametros.parametros_gerador()),
                         {"mediana", "sigma_rodada", "sigma_ruido"})

    def test_descritivas(self):
        df = parametros.descritivas(*amostra.pares())
        self.assertEqual(len(df), 3)
        self.assertEqual(df["n"].tolist(), [30, 30, 30])
        self.assertTrue((df.loc[:1, "Assimetria"] > 0).all())  # assimetria à direita
        self.assertAlmostEqual(df.loc[2, "Média (s)"], -5.368, delta=0.001)

    def test_efeitos(self):
        self.assertGreaterEqual(len(parametros.EFEITOS), 5)
        self.assertEqual(parametros.EFEITOS[0], 0.0)
        self.assertEqual(list(parametros.EFEITOS), sorted(parametros.EFEITOS))

    def test_justificativa(self):
        texto = parametros.justificativa()
        self.assertIn("lognormal", texto)
        self.assertIn("5,87 s", texto)
        self.assertEqual(texto.count(". "), 3)  # 4 frases


if __name__ == "__main__":
    unittest.main()
