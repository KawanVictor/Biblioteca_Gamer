"""
Testes do projeto. Rode da raiz com:  python -m unittest
Cada teste usa um banco temporário; o biblioteca_gamer.db de verdade nunca é tocado.
"""

import os
import shutil
import tempfile
import unittest

from database import db


class TesteComBanco(unittest.TestCase):
    """Aponta o app para um banco vazio em pasta temporária durante o teste."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self._caminho_original = db.CAMINHO_DB
        db.CAMINHO_DB = os.path.join(self.pasta, "teste.db")
        db.cria_tabelas()

    def tearDown(self):
        db.CAMINHO_DB = self._caminho_original
        shutil.rmtree(self.pasta, ignore_errors=True)
