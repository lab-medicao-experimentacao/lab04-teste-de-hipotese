"""Testes de unidade de src/graficos/g1.py (rodar da raiz: python -m unittest discover -s tests)."""

import re
import sys
import unittest
from pathlib import Path

import numpy as np
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import amostra  # noqa: E402
from estilo import CORES_DADOS  # noqa: E402
from graficos import g1  # noqa: E402


def contar_frases(texto):
    return len(re.findall(r"[.!?](?:\s|$)", texto))


class TestConjuntos(unittest.TestCase):
    def test_real_e_simulado(self):
        c = g1.conjuntos()
        antes, depois = amostra.pares()
        np.testing.assert_array_equal(c["real"][0], antes)
        np.testing.assert_array_equal(c["real"][1], depois)
        self.assertEqual(c["simulado"][0].size, antes.size)
        self.assertEqual(c["simulado"][1].size, depois.size)

    def test_semente_fixa(self):
        a, b = g1.conjuntos(), g1.conjuntos()
        np.testing.assert_array_equal(a["simulado"][0], b["simulado"][0])
        np.testing.assert_array_equal(a["simulado"][1], b["simulado"][1])

    def test_simulado_na_faixa_do_real(self):
        c = g1.conjuntos()
        for real, sim in zip(c["real"], c["simulado"]):
            self.assertAlmostEqual(np.median(sim) / np.median(real), 1.0, delta=0.1)


class TestFigura(unittest.TestCase):
    def setUp(self):
        c = g1.conjuntos()
        self.real, self.simulado = c["real"], c["simulado"]
        self.fig = g1.figura(self.real, self.simulado)

    def test_histogramas(self):
        traces = self.fig.data
        self.assertEqual(len(traces), 4)
        self.assertTrue(all(isinstance(t, go.Histogram) for t in traces))
        self.assertEqual([t.xaxis for t in traces], ["x", "x", "x2", "x2"])
        # Real e simulado de cada condição usam as mesmas classes.
        self.assertEqual(traces[0].xbins, traces[1].xbins)
        self.assertEqual(traces[2].xbins, traces[3].xbins)
        np.testing.assert_array_equal(traces[0].x, self.real[0])
        np.testing.assert_array_equal(traces[3].x, self.simulado[1])

    def test_classes_cobrem_os_dados(self):
        for t in self.fig.data:
            self.assertLessEqual(t.xbins.start, np.min(t.x))
            self.assertGreater(t.xbins.end, np.max(t.x))

    def test_titulos_eixos_legenda_cores(self):
        layout = self.fig.layout
        self.assertIn("G1", layout.title.text)
        self.assertEqual([a.text for a in layout.annotations], list(g1.CONDICOES))
        for eixo in (layout.xaxis, layout.xaxis2):
            self.assertEqual(eixo.title.text, "Tempo de build (s)")
        for eixo in (layout.yaxis, layout.yaxis2):
            self.assertEqual(eixo.title.text, "Quantidade de builds")
        self.assertEqual(layout.barmode, "group")
        legenda = [t.name for t in self.fig.data if t.showlegend]
        self.assertEqual(legenda, ["Real (n = 30)", "Simulado (n = 30)"])
        self.assertEqual({t.marker.color for t in self.fig.data}, set(CORES_DADOS.values()))


class TestExplicacao(unittest.TestCase):
    def test_texto(self):
        c = g1.conjuntos()
        texto = g1.explicacao(c["real"], c["simulado"])
        self.assertTrue(2 <= contar_frases(texto) <= 4, texto)
        self.assertIn("assimétricos à direita", texto)
        self.assertIn("lognormal", texto)
        self.assertIn("5,80 s", texto)  # mediana real sem cache
        self.assertIn("3 builds reais", texto)

    def test_limite_lento(self):
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])  # Q1 = 2, Q3 = 4
        self.assertEqual(g1.limite_lento(x), 7.0)


if __name__ == "__main__":
    unittest.main()
