"""
main.py
Ponto de entrada - prepara banco e inicia UI.
"""

from controllers.controller import cria_tabelas
from views.ui import iniciar

if __name__ == "__main__":
    cria_tabelas()
    iniciar()
