"""Testes de unidade de src/testes.py (rodar da raiz: python -m unittest discover -s tests)."""

import sys
import unittest
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import testes  # noqa: E402


RNG = np.random.default_rng(42)
ANTES = RNG.normal(100, 10, 25)
DEPOIS = ANTES + RNG.normal(-3, 5, 25)


class TestTPareado(unittest.TestCase):
    def test_igual_ao_scipy(self):
        for alt in testes.ALTERNATIVAS:
            r = testes.t_pareado(ANTES, DEPOIS, alt)
            ref = stats.ttest_rel(DEPOIS, ANTES, alternative=alt)
            self.assertAlmostEqual(r["estatistica"], ref.statistic)
            self.assertAlmostEqual(r["p_valor"], ref.pvalue)
            self.assertEqual(r["n"], 25)
            self.assertEqual(r["gl"], 24)

    def test_chaves(self):
        r = testes.t_pareado(ANTES, DEPOIS)
        self.assertEqual(
            set(r), {"estatistica", "p_valor", "efeito", "rejeita", "n", "gl"}
        )

    def test_d_z_calculado_a_mao(self):
        # d = [1, 2, 3, 4]: média 2,5; dp = sqrt(5/3).
        r = testes.t_pareado([0, 0, 0, 0], [1, 2, 3, 4])
        self.assertAlmostEqual(r["efeito"], 2.5 / np.sqrt(5 / 3))

    def test_aceita_listas(self):
        r_lista = testes.t_pareado(list(ANTES), list(DEPOIS))
        r_array = testes.t_pareado(ANTES, DEPOIS)
        self.assertEqual(r_lista, r_array)


class TestWilcoxonPareado(unittest.TestCase):
    def test_p_valor_igual_ao_scipy(self):
        d = DEPOIS - ANTES
        for alt in testes.ALTERNATIVAS:
            r = testes.wilcoxon_pareado(ANTES, DEPOIS, alt)
            ref = stats.wilcoxon(d, alternative=alt, zero_method="wilcox", method="auto")
            self.assertAlmostEqual(r["p_valor"], ref.pvalue)
            self.assertEqual(r["metodo"], "exato")

    def test_estatistica_sempre_w_mais(self):
        d = DEPOIS - ANTES
        w_mais = stats.wilcoxon(d, alternative="greater").statistic
        for alt in testes.ALTERNATIVAS:
            r = testes.wilcoxon_pareado(ANTES, DEPOIS, alt)
            self.assertAlmostEqual(r["estatistica"], w_mais)

    def test_chaves(self):
        r = testes.wilcoxon_pareado(ANTES, DEPOIS)
        self.assertEqual(
            set(r), {"estatistica", "p_valor", "efeito", "rejeita", "n", "metodo"}
        )

    def test_w_mais_calculado_a_mao(self):
        # d = [3, -1, 4, -2, 0, 5]: o zero sai; postos de |d| = 3, 1, 4, 2, 5.
        # W+ = 3 + 4 + 5 = 12, W- = 1 + 2 = 3, r = (12 - 3) / 15 = 0,6.
        r = testes.wilcoxon_pareado([0] * 6, [3, -1, 4, -2, 0, 5])
        self.assertEqual(r["estatistica"], 12.0)
        self.assertEqual(r["n"], 5)
        self.assertAlmostEqual(r["efeito"], 0.6)
        self.assertEqual(r["metodo"], "exato (permutação)")

    def test_empates_com_posto_medio(self):
        # d = [2, -2, 1, 3]: postos de |d| = 2,5; 2,5; 1; 4.
        # W+ = 2,5 + 1 + 4 = 7,5, W- = 2,5, r = 5 / 10 = 0,5.
        r = testes.wilcoxon_pareado([0] * 4, [2, -2, 1, 3])
        self.assertEqual(r["estatistica"], 7.5)
        self.assertAlmostEqual(r["efeito"], 0.5)

    def test_metodo_aproximacao_normal(self):
        # Mais de 50 diferenças: o SciPy usa a aproximação normal.
        antes = RNG.normal(size=60)
        depois = antes + RNG.normal(size=60)
        r = testes.wilcoxon_pareado(antes, depois)
        ref = stats.wilcoxon(depois - antes, method="asymptotic")
        self.assertEqual(r["metodo"], "aproximação normal")
        self.assertAlmostEqual(r["p_valor"], ref.pvalue)


class TestDecisaoEDirecao(unittest.TestCase):
    def test_rejeita_coerente_com_alfa(self):
        for funcao in (testes.t_pareado, testes.wilcoxon_pareado):
            for alfa in (0.001, 0.01, 0.05, 0.5):
                r = funcao(ANTES, DEPOIS, alfa=alfa)
                self.assertEqual(r["rejeita"], r["p_valor"] < alfa)

    def test_direcao_unicaudal(self):
        # DEPOIS tende a ser menor que ANTES: "less" rejeita, "greater" não.
        for funcao in (testes.t_pareado, testes.wilcoxon_pareado):
            menor = funcao(ANTES, DEPOIS, "less")
            maior = funcao(ANTES, DEPOIS, "greater")
            self.assertTrue(menor["rejeita"])
            self.assertFalse(maior["rejeita"])
            self.assertLess(menor["p_valor"], maior["p_valor"])
            self.assertLess(menor["efeito"], 0)


class TestValidacao(unittest.TestCase):
    def verificar_erro(self, *args, **kwargs):
        for funcao in (testes.t_pareado, testes.wilcoxon_pareado):
            with self.assertRaises(ValueError):
                funcao(*args, **kwargs)

    def test_tamanhos_diferentes(self):
        self.verificar_erro([1, 2, 3], [1, 2])

    def test_nan(self):
        self.verificar_erro([1, 2, np.nan], [1, 2, 3])
        self.verificar_erro([1, 2, 3], [np.nan, 2, 3])

    def test_alternativa_invalida(self):
        self.verificar_erro(ANTES, DEPOIS, "bicaudal")

    def test_alfa_fora_do_intervalo(self):
        for alfa in (0, 1, -0.1, 1.5):
            self.verificar_erro(ANTES, DEPOIS, alfa=alfa)

    def test_t_com_menos_de_dois_pares(self):
        with self.assertRaisesRegex(ValueError, "pelo menos 2 pares"):
            testes.t_pareado([1], [2])

    def test_wilcoxon_sem_diferencas_nao_nulas(self):
        with self.assertRaisesRegex(ValueError, "diferença não nula"):
            testes.wilcoxon_pareado([1, 2, 3], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
