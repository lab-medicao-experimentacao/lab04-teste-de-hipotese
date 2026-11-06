"""Testes de unidade de src/amostra.py (rodar da raiz: python -m unittest discover -s tests)."""

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import amostra  # noqa: E402


class TestAmostra(unittest.TestCase):
    def test_amostra_real(self):
        df = amostra.carregar()
        self.assertEqual(list(df.columns), list(amostra.COLUNAS))
        self.assertEqual(amostra.n_pares(), 30)
        self.assertEqual(df["par"].tolist(), list(range(1, 31)))
        self.assertTrue(df["ordem"].isin(["sem_cache-com_cache", "com_cache-sem_cache"]).all())

    def test_pares(self):
        antes, depois = amostra.pares()
        self.assertEqual(antes.shape, depois.shape)
        self.assertTrue(np.all(antes > 0) and np.all(depois > 0))
        self.assertLess(np.median(depois), np.median(antes))

    def _csv(self, conteudo):
        arquivo = Path(tempfile.mkdtemp()) / "amostra.csv"
        arquivo.write_text(conteudo)
        return arquivo

    def test_validacao(self):
        casos = [
            "par,ordem,sem_cache_s\n1,a,1.0\n",
            "par,ordem,sem_cache_s,com_cache_s\n1,a,1.0,\n",
            "par,ordem,sem_cache_s,com_cache_s\n1,a,1.0,-0.5\n",
        ]
        for conteudo in casos:
            with self.subTest(conteudo=conteudo), self.assertRaises(ValueError):
                amostra.carregar(self._csv(conteudo))


if __name__ == "__main__":
    unittest.main()
