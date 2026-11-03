"""Testes de unidade de src/aplicacao.py (rodar da raiz: python -m unittest discover -s tests)."""

import re
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import aplicacao  # noqa: E402
import testes  # noqa: E402
from estilo import ROTULOS  # noqa: E402


COLUNAS = [
    "Teste", "Estatística", "p-valor", "Tamanho do efeito",
    "Medida do efeito", "Decisão",
]


def contar_frases(texto):
    return len(re.findall(r"[.!?](?:\s|$)", texto))


class TestConjuntoExemplo(unittest.TestCase):
    def test_deterministico(self):
        a1, d1 = aplicacao.conjunto_exemplo()
        a2, d2 = aplicacao.conjunto_exemplo()
        np.testing.assert_array_equal(a1, a2)
        np.testing.assert_array_equal(d1, d2)
        self.assertEqual(a1.size, aplicacao.N_EXEMPLO)


class TestAplicarTestes(unittest.TestCase):
    def setUp(self):
        self.antes, self.depois = aplicacao.conjunto_exemplo()
        self.tabela = aplicacao.aplicar_testes(self.antes, self.depois)

    def test_colunas_e_linhas(self):
        self.assertEqual(list(self.tabela.columns), COLUNAS)
        self.assertEqual(
            list(self.tabela["Teste"]), [ROTULOS["t"], ROTULOS["wilcoxon"]]
        )

    def test_valores_iguais_aos_testes(self):
        refs = [
            testes.t_pareado(self.antes, self.depois, aplicacao.ALTERNATIVA),
            testes.wilcoxon_pareado(self.antes, self.depois, aplicacao.ALTERNATIVA),
        ]
        for (_, linha), ref in zip(self.tabela.iterrows(), refs):
            self.assertEqual(linha["Estatística"], ref["estatistica"])
            self.assertEqual(linha["p-valor"], ref["p_valor"])
            self.assertEqual(linha["Tamanho do efeito"], ref["efeito"])
            esperado = "rejeita H₀" if ref["rejeita"] else "não rejeita H₀"
            self.assertEqual(linha["Decisão"], esperado)

    def test_alfa_muda_decisao(self):
        tabela = aplicacao.aplicar_testes([0] * 4, [1, 2, 3, 4], alfa=0.999)
        self.assertTrue((tabela["Decisão"] == "rejeita H₀").all())


class TestInterpretar(unittest.TestCase):
    def test_exemplo(self):
        tabela = aplicacao.aplicar_testes(*aplicacao.conjunto_exemplo())
        texto = aplicacao.interpretar(tabela, aplicacao.EFEITO_EXEMPLO)
        self.assertTrue(2 <= contar_frases(texto) <= 4, texto)
        self.assertIn("efeito verdadeiro é conhecido", texto)
        self.assertIn("10%", texto)
        self.assertIn("0,05", texto)
        self.assertNotRegex(texto, r"\d\.\d")  # vírgula decimal

    def test_erro_tipo_i_com_efeito_zero(self):
        # Diferenças todas negativas: os dois testes rejeitam H₀, que é
        # verdadeira por construção (efeito_verdadeiro = 0) -> erro tipo I.
        tabela = aplicacao.aplicar_testes([10] * 8, [9, 8, 7, 9.5, 8.5, 7.5, 6, 9.2])
        texto = aplicacao.interpretar(tabela, 0)
        self.assertTrue(2 <= contar_frases(texto) <= 4, texto)
        self.assertIn("erro tipo I", texto)
        self.assertNotIn("erro tipo II", texto)

    def test_erro_tipo_ii_os_dois_testes(self):
        # d = [-1, -2, -3, 6]: t não rejeita; Wilcoxon (n = 4) também não.
        tabela = aplicacao.aplicar_testes([0] * 4, [-1, -2, -3, 6])
        texto = aplicacao.interpretar(tabela, 0.1)
        self.assertIn("erro tipo II", texto)
        self.assertIn("concordam", texto)

    def test_p_valor_pequeno(self):
        tabela = aplicacao.aplicar_testes(*aplicacao.conjunto_exemplo())
        tabela["p-valor"] = [0.031, 0.0001]
        texto = aplicacao.interpretar(tabela, 0.1)
        self.assertIn("p = 0,031", texto)
        self.assertIn("p < 0,001", texto)


if __name__ == "__main__":
    unittest.main()
