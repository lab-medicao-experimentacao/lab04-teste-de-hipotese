"""Testes de unidade de src/graficos/g2.py (rodar da raiz: python -m unittest discover -s tests)."""

import re
import sys
import unittest
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import aplicacao  # noqa: E402
import testes  # noqa: E402
from estilo import CORES  # noqa: E402
from graficos import g2  # noqa: E402


def rgb(cor):
    return tuple(int(cor[i : i + 2], 16) for i in (1, 3, 5))


def cores_da_figura(fig):
    """Cores (r, g, b) usadas em linhas, preenchimentos e barras."""
    textos = []
    for tr in fig.data:
        if isinstance(tr, go.Bar):
            textos += [tr.marker.color, tr.marker.line.color]
        else:
            textos += [tr.line.color, tr.fillcolor]
    encontradas = set()
    for texto in filter(None, textos):
        if texto.startswith("#"):
            encontradas.add(rgb(texto.upper()))
        else:
            encontradas.add(tuple(int(v) for v in re.findall(r"\d+", texto)[:3]))
    return encontradas


class TestDistribuicaoNulaW(unittest.TestCase):
    def test_n3_a_mao(self):
        valores, probs = g2.distribuicao_nula_w(3)
        np.testing.assert_array_equal(valores, np.arange(7))
        np.testing.assert_allclose(probs, np.array([1, 1, 1, 2, 1, 1, 1]) / 8)

    def test_soma_um_e_simetrica(self):
        for n in (1, 5, 15, 30, 50):
            valores, probs = g2.distribuicao_nula_w(n)
            self.assertEqual(valores[-1], n * (n + 1) // 2)
            self.assertAlmostEqual(probs.sum(), 1.0)
            np.testing.assert_allclose(probs, probs[::-1])

    def test_p_valor_igual_ao_scipy_exato(self):
        rng = np.random.default_rng(42)
        for n in (5, 10, 15, 25):
            _, probs = g2.distribuicao_nula_w(n)
            for _ in range(5):
                # Módulos distintos (sem empates) e sinais aleatórios.
                d = rng.permutation(np.arange(1, n + 1)) * rng.choice([-1, 1], n)
                w = int(d[d > 0].sum())  # |d| já são os postos 1..n
                for alt in testes.ALTERNATIVAS:
                    ref = stats.wilcoxon(d, alternative=alt, method="exact")
                    self.assertAlmostEqual(g2.p_valor_w(w, probs, alt), ref.pvalue)

    def test_n_invalido(self):
        for n in (0, -1, 2.5, True):
            with self.assertRaises(ValueError):
                g2.distribuicao_nula_w(n)


class TestRegioes(unittest.TestCase):
    def test_t_igual_ao_ppf(self):
        r = g2.regiao_rejeicao_t(14, "two-sided", 0.05)
        self.assertAlmostEqual(r["inferior"], stats.t.ppf(0.025, 14))
        self.assertAlmostEqual(r["superior"], stats.t.ppf(0.975, 14))
        self.assertAlmostEqual(
            g2.regiao_rejeicao_t(14, "less", 0.05)["inferior"], stats.t.ppf(0.05, 14)
        )
        self.assertIsNone(g2.regiao_rejeicao_t(14, "less", 0.05)["superior"])
        self.assertAlmostEqual(
            g2.regiao_rejeicao_t(14, "greater", 0.05)["superior"],
            stats.t.ppf(0.95, 14),
        )

    def test_w_n15_bicaudal_tabela(self):
        r = g2.regiao_rejeicao_w(15, "two-sided", 0.05)
        self.assertEqual((r["inferior"], r["superior"]), (25, 95))

    def test_w_tamanho_menor_que_alfa_e_maximo(self):
        for n in (6, 10, 15, 20):
            valores, probs = g2.distribuicao_nula_w(n)
            for alt in testes.ALTERNATIVAS:
                r = g2.regiao_rejeicao_w(n, alt, 0.05)
                self.assertLessEqual(r["tamanho"], 0.05)
                # Igual à soma das probabilidades dentro da região.
                dentro = np.zeros(valores.size, dtype=bool)
                if r["inferior"] is not None:
                    dentro |= valores <= r["inferior"]
                if r["superior"] is not None:
                    dentro |= valores >= r["superior"]
                self.assertAlmostEqual(r["tamanho"], probs[dentro].sum())
                # Maximal: o próximo valor fora da região já não rejeita.
                if r["inferior"] is not None:
                    self.assertGreaterEqual(
                        g2.p_valor_w(r["inferior"] + 1, probs, alt), 0.05
                    )
                if r["superior"] is not None:
                    self.assertGreaterEqual(
                        g2.p_valor_w(r["superior"] - 1, probs, alt), 0.05
                    )

    def test_w_n_pequeno_sem_regiao(self):
        r = g2.regiao_rejeicao_w(4, "two-sided", 0.05)
        self.assertIsNone(r["inferior"])
        self.assertIsNone(r["superior"])
        self.assertEqual(r["tamanho"], 0.0)


class TestFigura(unittest.TestCase):
    def setUp(self):
        self.antes, self.depois = aplicacao.conjunto_exemplo()

    def verificar(self, fig):
        self.assertIsInstance(fig, go.Figure)
        layout = fig.layout
        self.assertGreaterEqual(len(layout.annotations), 2)  # títulos dos subgráficos
        self.assertEqual(layout.xaxis.title.text, "Estatística t (adimensional)")
        self.assertEqual(
            layout.xaxis2.title.text, "Estatística W⁺ (soma dos postos positivos)"
        )
        self.assertEqual(layout.yaxis.title.text, "Densidade")
        self.assertTrue(layout.yaxis2.title.text)
        self.assertIn("G2", layout.title.text)
        self.assertEqual(cores_da_figura(fig), {rgb(c) for c in CORES.values()})
        self.assertEqual({tr.xaxis for tr in fig.data}, {"x", "x2"})

    def test_tres_alternativas(self):
        for alt in testes.ALTERNATIVAS:
            fig = g2.figura(self.antes, self.depois, alt, 0.05)
            self.verificar(fig)
            self.assertEqual(fig.layout.yaxis2.title.text, "Probabilidade")
            # A área do p-valor das barras soma o p-valor do testes.py.
            ref = testes.wilcoxon_pareado(self.antes, self.depois, alt)
            barras_p = [tr for tr in fig.data
                        if isinstance(tr, go.Bar) and "p-valor" in tr.name]
            self.assertAlmostEqual(sum(barras_p[0].y), ref["p_valor"])

    def test_legenda_com_virgula(self):
        fig = g2.figura(self.antes, self.depois, "two-sided", 0.05)
        nomes = " | ".join(tr.name for tr in fig.data)
        self.assertIn("região de rejeição (α = 0,05", nomes)
        self.assertIn("área do p-valor (p = 0,697)", nomes)
        self.assertIn("área do p-valor (p = 0,599)", nomes)

    def test_empates_usam_aproximacao_normal(self):
        antes, depois = np.round(self.antes), np.round(self.depois)
        self.assertEqual(
            testes.wilcoxon_pareado(antes, depois)["metodo"], "aproximação normal"
        )
        fig = g2.figura(antes, depois, "two-sided", 0.05)
        self.verificar(fig)
        self.assertIn("aproximação normal", fig.layout.annotations[1].text)
        self.assertFalse(any(isinstance(tr, go.Bar) for tr in fig.data))

    def test_normal_regiao_consistente_com_p(self):
        # Na fronteira da região, o p-valor normal com correção vale α.
        media, dp = g2.normal_w(self.antes, np.round(self.depois))
        regiao = g2._regiao_normal_w(media, dp, "two-sided", 0.05)
        z = (regiao["inferior"] + 0.5 - media) / dp
        self.assertAlmostEqual(2 * stats.norm.cdf(z), 0.05)


class TestExplicacao(unittest.TestCase):
    def test_exemplo(self):
        antes, depois = aplicacao.conjunto_exemplo()
        texto = g2.explicacao(antes, depois, aplicacao.ALTERNATIVA, aplicacao.ALFA)
        self.assertTrue(2 <= len(re.findall(r"[.!?](?:\s|$)", texto)) <= 4, texto)
        t = testes.t_pareado(antes, depois, aplicacao.ALTERNATIVA)
        self.assertIn(f"t = {t['estatistica']:.2f}".replace(".", ",").replace("-", "−"),
                      texto)
        self.assertIn("W⁺ ≤ 25 ou W⁺ ≥ 95", texto)
        self.assertIn("não é a probabilidade de H₀ ser verdadeira", texto)
        self.assertIn("duas caudas", texto)

    def test_unicaudal(self):
        antes, depois = aplicacao.conjunto_exemplo()
        self.assertIn("cauda inferior", g2.explicacao(antes, depois, "less", 0.05))
        self.assertIn("cauda superior", g2.explicacao(antes, depois, "greater", 0.05))


if __name__ == "__main__":
    unittest.main()
