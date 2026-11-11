"""Testes de src/simulacao.py (rodar da raiz: python -m unittest discover -s tests)."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import simulacao  # noqa: E402
import testes  # noqa: E402


COLUNAS = ["cenario", "efeito", "teste", "taxa_rejeicao", "repeticoes", "erro_mc", "n"]


class TestGerador(unittest.TestCase):
    def test_formas_e_pareamento(self):
        rng = np.random.default_rng(0)
        antes, depois = simulacao.gerar_diferencas("n_pequeno", 0.0, 50, rng)
        self.assertEqual(antes.shape, (50, 8))
        self.assertEqual(depois.shape, (50, 8))

    def test_ruido_tem_media_zero_em_todos_os_cenarios(self):
        for cenario in simulacao.CENARIOS:
            rng = np.random.default_rng(1)
            antes, depois = simulacao.gerar_diferencas(cenario, 0.0, 20_000, rng)
            d = depois - antes
            with self.subTest(cenario=cenario):
                self.assertAlmostEqual(float(d.mean()), 0.0, delta=0.15)

    def test_cenario_assimetrico_e_assimetrico_e_outliers_tem_caudas_pesadas(self):
        from scipy import stats

        rng = np.random.default_rng(2)
        a, d_ = simulacao.gerar_diferencas("assimetrico", 0.0, 5000, rng)
        self.assertGreater(stats.skew((d_ - a).ravel()), 2)
        a, d_ = simulacao.gerar_diferencas("outliers", 0.0, 5000, rng)
        self.assertGreater(stats.kurtosis((d_ - a).ravel()), 5)

    def test_efeito_invalido(self):
        with self.assertRaises(ValueError):
            simulacao.gerar_diferencas("base", 1.0, 10, np.random.default_rng(0))


class TestTaxas(unittest.TestCase):
    def test_vetorizado_igual_a_testes_py(self):
        for alt in ("two-sided", "less", "greater"):
            rng = np.random.default_rng(3)
            antes, depois = simulacao.gerar_diferencas("base", 0.02, 200, rng)
            esperado_t = np.mean(
                [testes.t_pareado(a, d, alt)["rejeita"] for a, d in zip(antes, depois)]
            )
            esperado_w = np.mean(
                [testes.wilcoxon_pareado(a, d, alt)["rejeita"] for a, d in zip(antes, depois)]
            )
            taxas = simulacao.taxas_de_rejeicao(antes, depois, alt)
            with self.subTest(alternativa=alt):
                self.assertAlmostEqual(taxas["t"], esperado_t)
                self.assertAlmostEqual(taxas["wilcoxon"], esperado_w)


class TestSimular(unittest.TestCase):
    def test_formato(self):
        df = simulacao.simular(["base"], (0.0, 0.05), repeticoes=100)
        self.assertEqual(list(df.columns), COLUNAS)
        self.assertEqual(len(df), 4)
        self.assertEqual(set(df["teste"]), {"t", "wilcoxon"})
        self.assertTrue(df["taxa_rejeicao"].between(0, 1).all())

    def test_reproduzivel_e_independente_da_ordem(self):
        a = simulacao.simular(["base", "n_pequeno"], (0.0, 0.03), repeticoes=300)
        b = simulacao.simular(["base", "n_pequeno"], (0.0, 0.03), repeticoes=300)
        self.assertTrue(a.equals(b))
        so_pequeno = simulacao.simular(["n_pequeno"], (0.0, 0.03), repeticoes=300)
        pequeno = a[a["cenario"] == "n_pequeno"].reset_index(drop=True)
        self.assertTrue(pequeno.equals(so_pequeno))

    def test_semente_diferente_muda_resultado(self):
        a = simulacao.simular(["base"], (0.02,), repeticoes=300, semente=1)
        b = simulacao.simular(["base"], (0.02,), repeticoes=300, semente=2)
        self.assertFalse(a["taxa_rejeicao"].equals(b["taxa_rejeicao"]))

    def test_erro_tipo_i_perto_de_5_por_cento_no_cenario_base(self):
        df = simulacao.q1_erro_tipo_i(repeticoes=4000)
        for taxa in df["taxa_rejeicao"]:
            self.assertAlmostEqual(taxa, 0.05, delta=0.015)

    def test_poder_cresce_com_o_efeito(self):
        df = simulacao.q2_poder(repeticoes=1000)
        for teste, g in df.groupby("teste"):
            poder = g.sort_values("efeito")["taxa_rejeicao"].to_numpy()
            with self.subTest(teste=teste):
                self.assertGreater(poder[-1], 0.9)
                self.assertTrue(np.all(np.diff(poder) > -0.05))

    def test_q3_cobre_so_as_violacoes(self):
        df = simulacao.q3_pressupostos(repeticoes=50)
        self.assertNotIn("base", set(df["cenario"]))
        self.assertEqual(
            set(df["cenario"]), {"n_pequeno", "outliers", "assimetrico"}
        )
        self.assertEqual(len(df), 3 * len(simulacao.EFEITOS) * 2)


if __name__ == "__main__":
    unittest.main()
