"""Testes de unidade de src/dados_provisorio.py (rodar da raiz: python -m unittest discover -s tests)."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dados_provisorio import gerar_pares  # noqa: E402


class TestGerarPares(unittest.TestCase):
    def test_formatos(self):
        antes, depois = gerar_pares(30, 0.1, np.random.default_rng(42))
        self.assertEqual(antes.shape, (30,))
        self.assertEqual(depois.shape, (30,))

    def test_mesma_semente_reproduz(self):
        a1, d1 = gerar_pares(50, 0.2, np.random.default_rng(42))
        a2, d2 = gerar_pares(50, 0.2, np.random.default_rng(42))
        np.testing.assert_array_equal(a1, a2)
        np.testing.assert_array_equal(d1, d2)

    def test_sementes_diferentes_diferem(self):
        a1, _ = gerar_pares(50, 0.2, np.random.default_rng(42))
        a2, _ = gerar_pares(50, 0.2, np.random.default_rng(43))
        self.assertFalse(np.array_equal(a1, a2))

    def test_mediana_de_antes(self):
        antes, _ = gerar_pares(100_000, 0.0, np.random.default_rng(42), mediana=120.0)
        self.assertAlmostEqual(np.median(antes), 120.0, delta=1.0)

    def test_efeito_zero_h0_verdadeira(self):
        # Com efeito 0, d = eps ~ N(0, 5): erro-padrão da média = 5 / sqrt(1e5)
        # ≈ 0,016 s; a tolerância de 0,1 s equivale a ~6 erros-padrão.
        antes, depois = gerar_pares(100_000, 0.0, np.random.default_rng(42))
        d = depois - antes
        self.assertAlmostEqual(np.mean(d), 0.0, delta=0.1)
        self.assertAlmostEqual(np.median(d), 0.0, delta=0.1)

    def test_efeito_positivo_reduz_tempo(self):
        antes, depois = gerar_pares(10_000, 0.1, np.random.default_rng(42))
        self.assertLess(np.mean(depois), np.mean(antes))
        # Redução média esperada: 10% da média de antes.
        self.assertAlmostEqual(
            np.mean(antes - depois) / np.mean(antes), 0.1, delta=0.01
        )

    def test_validacao(self):
        rng = np.random.default_rng(42)
        invalidos = [
            dict(n=0, efeito=0.1),
            dict(n=2.5, efeito=0.1),
            dict(n=10, efeito=-0.1),
            dict(n=10, efeito=1.0),
            dict(n=10, efeito=0.1, mediana=0),
            dict(n=10, efeito=0.1, sigma=-1),
            dict(n=10, efeito=0.1, ruido=0),
        ]
        for kwargs in invalidos:
            with self.subTest(**kwargs), self.assertRaises(ValueError):
                gerar_pares(rng=rng, **kwargs)
        with self.assertRaises(ValueError):
            gerar_pares(10, 0.1, 42)


if __name__ == "__main__":
    unittest.main()
