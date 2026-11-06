"""Testes de unidade de src/dados.py (rodar da raiz: python -m unittest discover -s tests)."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import parametros  # noqa: E402
from dados import gerar_pares  # noqa: E402


class TestGerarPares(unittest.TestCase):
    def test_formatos_e_positivos(self):
        antes, depois = gerar_pares(30, 0.1, np.random.default_rng(42))
        self.assertEqual(antes.shape, (30,))
        self.assertEqual(depois.shape, (30,))
        self.assertTrue(np.all(antes > 0) and np.all(depois > 0))

    def test_mesma_semente_reproduz(self):
        a1, d1 = gerar_pares(50, 0.05, np.random.default_rng(42))
        a2, d2 = gerar_pares(50, 0.05, np.random.default_rng(42))
        np.testing.assert_array_equal(a1, a2)
        np.testing.assert_array_equal(d1, d2)

    def test_sementes_diferentes_diferem(self):
        a1, _ = gerar_pares(50, 0.05, np.random.default_rng(42))
        a2, _ = gerar_pares(50, 0.05, np.random.default_rng(43))
        self.assertFalse(np.array_equal(a1, a2))

    def test_padrao_vem_da_amostra(self):
        p = parametros.da_amostra()
        antes, _ = gerar_pares(200_000, 0.0, np.random.default_rng(42))
        self.assertAlmostEqual(np.median(antes), p["mediana"], delta=0.01)
        dp_log = np.hypot(p["sigma_rodada"], p["sigma_ruido"])
        self.assertAlmostEqual(np.std(np.log(antes)), dp_log, delta=0.001)

    def test_parametros_explicitos(self):
        antes, depois = gerar_pares(200_000, 0.0, np.random.default_rng(42),
                                    mediana=120.0, sigma_rodada=0.2, sigma_ruido=0.1)
        self.assertAlmostEqual(np.median(antes), 120.0, delta=0.5)
        # Correlação dos logs = σ_rodada² / (σ_rodada² + σ_ruído²) = 0,8.
        corr = np.corrcoef(np.log(antes), np.log(depois))[0, 1]
        self.assertAlmostEqual(corr, 0.8, delta=0.005)

    def test_efeito_zero_h0_verdadeira(self):
        # d é simétrica em torno de 0: média e mediana próximas de 0 (com
        # n = 200 000 e dp(d) ≈ 0,7 s, o erro-padrão da média é ≈ 0,0016 s).
        antes, depois = gerar_pares(200_000, 0.0, np.random.default_rng(42))
        d = depois - antes
        self.assertAlmostEqual(np.mean(d), 0.0, delta=0.01)
        self.assertAlmostEqual(np.median(d), 0.0, delta=0.01)
        self.assertAlmostEqual(np.mean(d > 0), 0.5, delta=0.005)

    def test_efeito_reduz_mediana(self):
        antes, depois = gerar_pares(200_000, 0.1, np.random.default_rng(42))
        self.assertAlmostEqual(np.median(depois) / np.median(antes), 0.9, delta=0.005)

    def test_validacao(self):
        rng = np.random.default_rng(42)
        invalidos = [
            dict(n=0, efeito=0.1),
            dict(n=2.5, efeito=0.1),
            dict(n=True, efeito=0.1),
            dict(n=10, efeito=-0.1),
            dict(n=10, efeito=1.0),
            dict(n=10, efeito=0.1, mediana=0),
            dict(n=10, efeito=0.1, sigma_rodada=-1),
            dict(n=10, efeito=0.1, sigma_ruido=0),
        ]
        for kwargs in invalidos:
            with self.subTest(**kwargs), self.assertRaises(ValueError):
                gerar_pares(rng=rng, **kwargs)
        with self.assertRaises(ValueError):
            gerar_pares(10, 0.1, 42)


if __name__ == "__main__":
    unittest.main()
